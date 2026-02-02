"""
LangGraph StateGraph Core Definition.

This module defines the main agent graph using LangGraph 1.x StateGraph.
It implements a production-grade ReAct pattern with:
- Intent-based routing (Fast Chat vs Tool-using Agent)
- Doom Loop detection (inspired by OpenCode)
- Streaming support with multiple modes
- Persistent memory via SQLite checkpointer

Architecture:
    START → router → [fast_chat → END]
                   → [agent → tools → agent...] → END
"""
import json
import hashlib
import os
from typing import Literal, Optional, Callable, Any

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from agent.state import NoteAgentState
from core.llm import get_llm
from core.config import settings


# ============================================================================
# CONSTANTS
# ============================================================================

MAX_TOOL_CALLS = 10  # Maximum tool execution rounds (increased for complex tasks)
DOOM_LOOP_THRESHOLD = 3  # Same tool+input triggers safety stop (OpenCode style)
MAX_RECOVER = 2  # Maximum recover attempts before forced end

# Write operations: success = workflow done
WRITE_TOOLS = {"delete_note", "create_note", "rename_note", "update_note", "set_note_category"}

# Checkpointer database path (in user data directory)
CHECKPOINT_DB_PATH = os.path.join(settings.data_directory, "checkpoints.db")


# ============================================================================
# SYSTEM PROMPTS (loaded from files like OpenCode)
# ============================================================================

_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def _load_prompt(name: str) -> str:
    """Load prompt from prompts/ folder."""
    with open(os.path.join(_PROMPT_DIR, f"{name}.txt"), "r", encoding="utf-8") as f:
        return f.read()

SUPERVISOR_PROMPT = _load_prompt("supervisor")
FAST_CHAT_PROMPT = _load_prompt("fast_chat")


# ============================================================================
# GRAPH BUILDER CLASS
# ============================================================================

class NoteAgentGraph:
    """
    Production-Grade Agent using LangGraph 1.x StateGraph.
    
    Key Technical Points (Interview-Ready):
    1. Graph-based State Machine - Explicit node and edge definitions
    2. Conditional Routing - Intent-based dynamic routing
    3. Checkpointing - Persistent SQLite storage for cross-session memory
    4. Doom Loop Detection - Prevents infinite tool loops
    5. Multi-mode Streaming - ["messages", "updates", "custom"]
    
    Usage:
        graph = NoteAgentGraph(tools=get_all_agent_tools())
        compiled = await graph.build()
        async for chunk in compiled.astream(state, stream_mode=["messages", "updates"]):
            ...
    """
    
    def __init__(self, tools: list, llm=None, checkpointer=None):
        """
        Initialize the agent graph.
        
        Args:
            tools: List of LangChain tools to bind to the agent
            llm: Optional LLM instance (defaults to get_llm())
            checkpointer: Optional checkpointer (defaults to AsyncSqliteSaver)
        """
        self.llm = llm or get_llm()
        self.tools = tools
        self.tool_node = ToolNode(tools)
        self.checkpointer = checkpointer  # Will be set during build()
        
        # Bind tools to LLM for function calling
        # parallel_tool_calls=False forces sequential execution: chat → tool → chat → tool
        self.model_with_tools = self.llm.bind_tools(tools, parallel_tool_calls=False)
        
    async def build(self, checkpointer=None) -> StateGraph:
        """
        Build and compile the StateGraph.
        
        Graph Structure:
            START → router → fast_chat → END
                          → agent → tools → agent (loop) → END
        
        Returns:
            Compiled StateGraph with checkpointer
        """
        workflow = StateGraph(NoteAgentState)
        
        # ====== Add Nodes ======
        workflow.add_node("router", self._router_node)
        workflow.add_node("fast_chat", self._fast_chat_node)
        workflow.add_node("agent", self._agent_node)
        
        # NEW: 3-node tool execution for chat-tool-chat pattern
        workflow.add_node("pick_one_tool", self._pick_one_tool_node)
        workflow.add_node("run_one_tool", self._run_one_tool_node)
        workflow.add_node("status", self._status_node)
        
        workflow.add_node("recover", self._recover_node)
        
        # ====== Add Edges ======
        # Entry point
        workflow.add_edge(START, "router")
        
        # Router → Conditional branch
        workflow.add_conditional_edges(
            "router",
            self._route_by_intent,
            {
                "CHAT": "fast_chat",
                "TASK": "agent"
            }
        )
        
        # Fast chat → End
        workflow.add_edge("fast_chat", END)
        
        # Agent → 3-way branch (continue/recover/end)
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "pick_one_tool",  # Changed: go to pick_one first
                "recover": "recover",
                "end": END
            }
        )
        
        # NEW: chat-tool-chat pipeline
        # pick_one_tool → run_one_tool → status → agent (loop)
        workflow.add_edge("pick_one_tool", "run_one_tool")
        workflow.add_edge("run_one_tool", "status")
        workflow.add_edge("status", "agent")
        
        # Recover → Agent (retry with prompt)
        workflow.add_edge("recover", "agent")
        
        # ====== Compile with Checkpointer ======
        # Use provided checkpointer or the one set during init
        cp = checkpointer or self.checkpointer
        return workflow.compile(checkpointer=cp)
    
    # ========================================================================
    # NODE IMPLEMENTATIONS
    # ========================================================================
    
    def _router_node(self, state: NoteAgentState) -> dict:
        """
        Intent classification node.
        Determines whether to use fast chat or tool-using agent.
        
        Returns:
            {"intent": "CHAT" | "TASK"}
        """
        # ========== Force TASK if use_knowledge is flagged (@) ==========
        if state.get("use_knowledge"):
            return {"intent": "TASK"}

        messages = state.get("messages", [])
        if not messages:
            return {"intent": "TASK"}
        
        last_message = messages[-1]
        if not hasattr(last_message, 'content'):
            return {"intent": "TASK"}
        
        query = last_message.content
        
        # ========== MODERN SEMANTIC ROUTING ==========
        # No more fragile keywords. We use the LLM to analyze the FULL context.
        context_summary = f"User just said: '{query}'"
        if len(messages) > 1:
            prev_msg = messages[-2]
            if hasattr(prev_msg, 'content'):
                context_summary = f"Context: Last AI said '{prev_msg.content}'. Now user says: '{query}'"

        classification_prompt = """
        You are the Intent Router for Origin Notes. 
        Analyze the conversation to decide if the next step should be a casual CHAT or a functional TASK.

        RULES:
        - 'TASK': Anything involving note operations (search, read, update, delete, categorize, list) OR follow-up feedback to a previous task (e.g., "no, that's wrong", "keep going", "it didn't work").
        - 'CHAT': Pure greetings, meta-questions about who you are, or casual closing (e.g., "thanks", "bye").

        CRITICAL: If the user is giving feedback on a previous action, it stays as a 'TASK'.

        {context}
        Output ONLY 'CHAT' or 'TASK':
        """
        
        try:
            resp = self.llm.invoke([
                HumanMessage(content=classification_prompt.format(context=context_summary))
            ])
            intent = resp.content.strip().upper()
            print(f"[ROUTER] Context-aware intent: {intent}")
            return {"intent": "TASK" if "TASK" in intent else "CHAT"}
        except Exception as e:
            print(f"[ROUTER] Error in classification: {e}")
            return {"intent": "TASK"} # Default to TASK to be safe
    
    def _route_by_intent(self, state: NoteAgentState) -> Literal["CHAT", "TASK"]:
        """Conditional routing based on intent."""
        return state.get("intent", "TASK")
    
    def _fast_chat_node(self, state: NoteAgentState) -> dict:
        """
        Fast chat node - Direct LLM response without tools.
        For general knowledge questions.
        """
        # Filter status messages from history
        filtered_messages = [
            m for m in state.get("messages", []) 
            if getattr(m, "additional_kwargs", {}).get("type") != "status_message"
        ]
        
        messages = [SystemMessage(content=FAST_CHAT_PROMPT)] + filtered_messages
        
        response = self.llm.invoke(messages)
        return {"messages": [response]}
    
    def _agent_node(self, state: NoteAgentState) -> dict:
        """
        Main agent node - LLM with tool binding.
        Handles reasoning and tool call decisions.
        
        Chat-First Architecture:
        - On first call (tool_count == 0), generate a brief plan message first
        - Then proceed with tool execution
        """
        # Build context message - OMNISCIENT VIEW of the notebook
        context_parts = []
        
        # ========== Current Note Context ==========
        if state.get("active_note_id"):
            context_parts.append("📝 CURRENT NOTE:")
            context_parts.append(f"  - ID: {state['active_note_id']}")
            if state.get("active_note_title"):
                context_parts.append(f"  - Title: {state['active_note_title']}")
            if state.get("active_note_category"):
                context_parts.append(f"  - Category: {state['active_note_category']}")
            context_parts.append("  - Content: (use read_note_content to view, update_note to modify)")
        
        # ========== Referenced Note (if different from active) ==========
        if state.get("context_note_id") and state.get("context_note_id") != state.get("active_note_id"):
            context_parts.append("\n📎 REFERENCED NOTE:")
            context_parts.append(f"  - ID: {state['context_note_id']}")
            if state.get("context_note_title"):
                context_parts.append(f"  - Title: {state['context_note_title']}")
        
        # ========== Content Preview ==========
        if state.get("note_content"):
            content_preview = state["note_content"][:300]
            context_parts.append(f"\n📄 CONTENT PREVIEW:\n{content_preview}...")
        
        # ========== Selected Text ==========
        if state.get("selected_text"):
            context_parts.append(f"\n✨ SELECTED TEXT:\n{state['selected_text']}")

        # ========== Knowledge Search Flag (@) ==========
        if state.get("use_knowledge"):
            context_parts.append("\n⚠️ CRITICAL INSTRUCTION:")
            context_parts.append("  - The user explicitly requested to search the KNOWLEDGE BASE.")
            context_parts.append("  - You MUST call `search_knowledge` BEFORE answering.")
            context_parts.append("  - Use the user's query as the search term.")
        
        # ========== Note Structure Explanation ==========
        context_parts.append("""
📘 NOTE STRUCTURE:
A note has two distinct parts:
- title: The note's name (modify with rename_note)
- content: The note's body text (modify with update_note)
These are SEPARATE. "Change the title" means rename_note, NOT adding a heading in content.""")
        
        context_msg = "\n".join(context_parts) if context_parts else "（无特定笔记上下文）"
        
        # Filter status messages from history to prevent "Status Pollution"
        filtered_history = [
            m for m in state.get("messages", []) 
            if getattr(m, "additional_kwargs", {}).get("type") != "status_message"
        ]

        # Build message list
        messages = [
            SystemMessage(content=SUPERVISOR_PROMPT),
            SystemMessage(content=f"[当前上下文]\n{context_msg}"),
        ] + filtered_history
        
        # Check if we're at max turns
        tool_count = state.get("tool_call_count", 0)
        if tool_count >= MAX_TOOL_CALLS:
            messages.append(HumanMessage(
                content="[SYSTEM]: 工具调用次数已达上限，请停止调用工具，直接给出最终回答。"
            ))
        
        # Invoke LLM with tools
        response = self.model_with_tools.invoke(messages)
        
        return {"messages": [response]}
    
    # ========================================================================
    # CHAT-TOOL-CHAT PATTERN: 3-NODE TOOL EXECUTION
    # ========================================================================
    
    def _pick_one_tool_node(self, state: NoteAgentState) -> dict:
        """
        Pick only the FIRST tool_call from agent output.
        Discards additional tool_calls to force one-at-a-time execution.
        """
        messages = state.get("messages", [])
        if not messages:
            return {"next_tool_call": None}
        
        last_message = messages[-1]
        
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return {"next_tool_call": None}
        
        # Take only the first tool_call
        first_tool = last_message.tool_calls[0]
        
        return {"next_tool_call": first_tool}
    
    async def _run_one_tool_node(self, state: NoteAgentState) -> dict:
        """
        Execute the single picked tool with Doom Loop detection.
        """
        next_tool_call = state.get("next_tool_call")
        if not next_tool_call:
            return {"messages": []}
        
        # Doom Loop Detection
        tool_call_count = state.get("tool_call_count", 0)
        last_tool_name = state.get("last_tool_name")
        last_tool_hash = state.get("last_tool_input_hash")
        
        current_tool_name = next_tool_call.get("name", "")
        current_input_hash = hashlib.md5(
            json.dumps(next_tool_call.get("args", {}), sort_keys=True).encode()
        ).hexdigest()
        
        # Check for doom loop
        if (current_tool_name == last_tool_name and 
            current_input_hash == last_tool_hash):
            consecutive = tool_call_count + 1
            if consecutive >= DOOM_LOOP_THRESHOLD:
                return {
                    "messages": [ToolMessage(
                        content=f"[DOOM LOOP DETECTED] 工具 {current_tool_name} 被连续调用了 {consecutive} 次。已自动终止。",
                        tool_call_id=next_tool_call.get("id", "doom_loop"),
                    )],
                    "tool_call_count": consecutive,
                    "next_tool_call": None,
                }
        
        # Create a minimal state for single tool execution
        # We need to create an AIMessage with just this one tool_call
        single_tool_message = AIMessage(content="", tool_calls=[next_tool_call])
        mini_state = {"messages": [single_tool_message]}
        
        # Execute via ToolNode
        result = await self.tool_node.ainvoke(mini_state)
        
        # Detect success
        tool_messages = result.get("messages", [])
        tool_success = False
        tool_result_content = ""
        if tool_messages:
            last_tool_msg = tool_messages[-1]
            tool_result_content = getattr(last_tool_msg, 'content', str(last_tool_msg))
            tool_success = not tool_result_content.strip().startswith("Error:")
        
        # Don't set workflow_done here - let agent decide when done
        # This allows multi-step tasks to continue
        
        return {
            "messages": tool_messages,
            "tool_call_count": tool_call_count + 1,
            "last_tool_name": current_tool_name,
            "last_tool_input_hash": current_input_hash,
            "next_tool_call": None,  # Clear after execution
        }
    
    def _status_node(self, state: NoteAgentState) -> dict:
        """
        Generate status message between tool executions.
        This creates the 'chat' in chat-tool-chat-tool pattern.
        """
        last_tool_name = state.get("last_tool_name", "")
        
        # Status message templates
        STATUS_TEMPLATES = {
            "delete_note": "✅ 删除完成，继续下一步...",
            "create_note": "✅ 笔记创建成功！",
            "rename_note": "✅ 标题已更新，继续下一步...",
            "update_note": "✅ 笔记内容已更新！",
            "set_note_category": "✅ 分类已设置！",
            "list_recent_notes": "📄 已获取笔记列表，继续处理...",
            "search_knowledge": "🔍 搜索完成，分析结果中...",
            "read_note_content": "📖 已读取笔记内容，继续处理...",
            "list_categories": "📁 已获取分类列表...",
        }
        
        status_text = STATUS_TEMPLATES.get(last_tool_name, f"✓ {last_tool_name} 执行完成")
        
        # CRITICAL: Mark as status_message to filter it out from LLM reasoning in next turn
        status_message = AIMessage(
            content=status_text, 
            additional_kwargs={"type": "status_message"}
        )
        
        print(f"[STATUS] Generating marked status message: {status_text}")
        
        return {"messages": [status_message]}
    
    def _should_continue(self, state: NoteAgentState) -> Literal["continue", "recover", "end"]:
        """
        Workflow state machine: determine whether to continue, recover, or end.
        
        3-way branching:
        - "continue": has tool_calls → execute tools
        - "recover": no tool_calls + workflow not done + has executed tools → retry
        - "end": workflow done OR first response is text-only OR recover exhausted
        """
        messages = state.get("messages", [])
        if not messages:
            return "end"
        
        last_message = messages[-1]
        
        # 1. Has tool_calls → continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            if state.get("tool_call_count", 0) >= MAX_TOOL_CALLS:
                return "end"
            return "continue"
        
        # 2. Workflow already done (write operation succeeded) → end
        if state.get("workflow_done", False):
            return "end"
        
        # 3. [REMOVED] Aggressive recovery caused double-generation. 
        # If the agent outputs text without tool calls, we assume it's the final answer.
        # This prevents the "Double Summary" bug.
        
        # 4. Otherwise → end (response is text-only, task complete)
        return "end"
    
    def _recover_node(self, state: NoteAgentState) -> dict:
        """
        Recovery node: when model output text but no tool_calls, prompt to continue or finish.
        Uses SystemMessage to ensure high priority.
        """
        recover_count = state.get("recover_count", 0)
        last_tool_name = state.get("last_tool_name", "")
        
        recover_prompt = f"""[SYSTEM] 上一步执行了工具 {last_tool_name}。

如果任务还没完成，请继续调用下一个工具。
如果所有工作已完成，请给出简短的完成确认（不要调用工具）。

直接行动，不要解释。"""

        messages = list(state.get("messages", []))
        messages.append(SystemMessage(content=recover_prompt))
        
        response = self.model_with_tools.invoke(messages)
        
        return {
            "messages": [response],
            "recover_count": recover_count + 1
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

async def create_note_agent_graph(tools: list, llm=None, checkpointer=None):
    """
    Factory function to create and compile the agent graph.
    
    Args:
        tools: List of LangChain tools
        llm: Optional LLM instance
        checkpointer: Optional checkpointer for persistence
    
    Returns:
        Compiled StateGraph ready for invocation
    """
    builder = NoteAgentGraph(tools=tools, llm=llm)
    return await builder.build(checkpointer=checkpointer)
