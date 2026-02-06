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
import re

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from agent.state import NoteAgentState
from core.llm import get_llm
from core.config import settings


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', errors='replace').decode('gbk'))


# ============================================================================
# CONSTANTS
# ============================================================================

MAX_TOOL_CALLS = 25  # Maximum tool execution rounds (supports complex multi-step tasks)
DOOM_LOOP_THRESHOLD = 3  # Same tool+input triggers safety stop (OpenCode style)

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
        
        # Agent → 2-way branch (continue/end)
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "pick_one_tool",
                "end": END
            }
        )
        
        # pick_one_tool → run_one_tool → status → agent (loop)
        workflow.add_edge("pick_one_tool", "run_one_tool")
        workflow.add_edge("run_one_tool", "status")
        workflow.add_edge("status", "agent")
        
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
            safe_print(f"[ROUTER] Context-aware intent: {intent}")
            return {"intent": "TASK" if "TASK" in intent else "CHAT"}
        except Exception as e:
            safe_print(f"[ROUTER] Error in classification: {e}")
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

        lang = self._detect_user_language(filtered_messages)
        lang_instruction = SystemMessage(content=f"Always respond in the user's language ({lang}).")
        messages = [SystemMessage(content=FAST_CHAT_PROMPT), lang_instruction] + filtered_messages
        
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
            context_parts.append("CURRENT NOTE:")
            context_parts.append(f"  - ID: {state['active_note_id']}")
            if state.get("active_note_title"):
                context_parts.append(f"  - Title: {state['active_note_title']}")
            if state.get("active_note_category"):
                context_parts.append(f"  - Category: {state['active_note_category']}")
            context_parts.append("  - Content: (use read_note_content to view, update_note to modify)")
        
        # ========== Referenced Note (if different from active) ==========
        if state.get("context_note_id") and state.get("context_note_id") != state.get("active_note_id"):
            context_parts.append("\nREFERENCED NOTE:")
            context_parts.append(f"  - ID: {state['context_note_id']}")
            if state.get("context_note_title"):
                context_parts.append(f"  - Title: {state['context_note_title']}")
        
        # ========== Full Note Content ==========
        # CRITICAL: Pass FULL content for summarization/analysis tasks
        if state.get("note_content"):
            note_content = state["note_content"]
            # Limit to 8000 chars to avoid token overflow, but much more than 300
            if len(note_content) > 8000:
                note_content = note_content[:8000] + "\n...[Content truncated due to length]"
            context_parts.append(f"\nFULL NOTE CONTENT:\n{note_content}")
        
        # ========== Selected Text ==========
        if state.get("selected_text"):
            context_parts.append(f"\nSELECTED TEXT:\n{state['selected_text']}")

        # ========== Knowledge Search Flag (@) ==========
        if state.get("use_knowledge"):
            context_parts.append("\n[CRITICAL INSTRUCTION]")
            context_parts.append("  - The user explicitly requested to search the KNOWLEDGE BASE.")
            context_parts.append("  - You MUST call `search_knowledge` BEFORE answering.")
            context_parts.append("  - Use the user's query as the search term.")
        
        # ========== Note Structure Explanation ==========
        context_parts.append("""
NOTE STRUCTURE:
A note has two distinct parts:
- title: The note's name (modify with rename_note)
- content: The note's body text (modify with update_note)
These are SEPARATE. "Change the title" means rename_note, NOT adding a heading in content.""")
        context_parts.append("""
TOOL USAGE:
When a tool requires note_id, ALWAYS use the exact ID shown in CURRENT NOTE or REFERENCED NOTE.
Do NOT use placeholders. If no ID is provided, ask for clarification.""")
        
        context_msg = "\n".join(context_parts) if context_parts else "（无特定笔记上下文）"
        
        # Filter status messages from history to prevent "Status Pollution"
        filtered_history = [
            m for m in state.get("messages", []) 
            if getattr(m, "additional_kwargs", {}).get("type") != "status_message"
        ]

        # Build message list
        lang = self._detect_user_language(filtered_history)
        lang_instruction = SystemMessage(content=f"Always respond in the user's language ({lang}).")

        messages = [
            SystemMessage(content=SUPERVISOR_PROMPT),
            SystemMessage(content=f"[当前上下文]\n{context_msg}"),
            lang_instruction,
        ] + filtered_history
        
        # Check if we're at max turns
        tool_count = state.get("tool_call_count", 0)
        if tool_count >= MAX_TOOL_CALLS:
            messages.append(HumanMessage(
                content="[SYSTEM]: 工具调用次数已达上限，请停止调用工具，直接给出最终回答。"
            ))
        
        # Invoke LLM with tools
        response = self.model_with_tools.invoke(messages)

        # Standard tool-loop guard:
        # For actionable TASK requests, first turn should enter tool loop immediately.
        # If model returns plain text only, force one retry with explicit tool-call requirement.
        if (
            state.get("intent") == "TASK"
            and tool_count == 0
            and not (hasattr(response, "tool_calls") and response.tool_calls)
            and self._task_requires_tool(state, filtered_history)
        ):
            forced_messages = messages + [
                SystemMessage(
                    content=(
                        "You are handling an actionable TASK. "
                        "Call exactly ONE tool now. "
                        "Do not output plain text in this step."
                    )
                )
            ]
            forced_response = self.model_with_tools.invoke(forced_messages)
            if hasattr(forced_response, "tool_calls") and forced_response.tool_calls:
                response = forced_response
        
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
        tool_args = next_tool_call.get("args", {}) or {}

        # Normalize tool args that depend on note_id to avoid placeholder usage.
        # This keeps agent behavior robust without hardcoding UI-specific strings.
        tool_args = self._normalize_note_id_args(tool_args, state)
        next_tool_call["args"] = tool_args

        current_input_hash = hashlib.md5(
            json.dumps(tool_args, sort_keys=True).encode()
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

    def _normalize_note_id_args(self, args: dict, state: NoteAgentState) -> dict:
        """
        Ensure note_id is a real ID when tools require it.
        If note_id is missing or malformed, fall back to active note in state.
        """
        if not isinstance(args, dict):
            return args

        note_id = args.get("note_id")
        active_note_id = state.get("active_note_id")

        if not note_id or not isinstance(note_id, str):
            if active_note_id:
                args["note_id"] = active_note_id
            return args

        # Accept both timestamp IDs and UUID IDs.
        # Fallback only for obvious placeholders or malformed ids.
        is_timestamp_id = bool(re.match(r"^\d{13}-[0-9a-f]{9}$", note_id))
        is_uuid_id = bool(re.match(r"^[0-9a-fA-F-]{32,36}$", note_id))
        if not (is_timestamp_id or is_uuid_id):
            if active_note_id:
                safe_print(f"[WARN] Normalizing note_id '{note_id}' -> '{active_note_id}'")
                args["note_id"] = active_note_id
        return args

    def _task_requires_tool(self, state: NoteAgentState, history: list) -> bool:
        """
        Decide if current TASK should enter tool loop immediately.
        Uses lightweight intent cues to avoid false forcing on purely conversational TASKs.
        """
        last_user_text = ""
        for msg in reversed(history):
            if getattr(msg, "type", "") == "human" and getattr(msg, "content", None):
                last_user_text = msg.content.lower()
                break

        actionable_cues = [
            "整理", "格式", "排版", "重写", "修改", "更新", "删除", "创建", "重命名", "分类",
            "format", "reformat", "tidy", "rewrite", "update", "delete", "create", "rename", "categorize",
        ]
        has_action_word = any(cue in last_user_text for cue in actionable_cues)

        # If note context exists, formatting/update style queries are expected to use tools.
        has_note_context = bool(state.get("active_note_id") or state.get("context_note_id"))
        return has_action_word and has_note_context

    def _detect_user_language(self, messages: list) -> str:
        """
        Lightweight language detection based on latest user message.
        Returns 'zh' when CJK chars are present, otherwise 'en'.
        """
        if not messages:
            return "en"

        last_user_text = ""
        for msg in reversed(messages):
            if getattr(msg, "type", "") == "human" and getattr(msg, "content", None):
                last_user_text = msg.content
                break

        if re.search(r"[\\u4e00-\\u9fff]", last_user_text):
            return "zh"
        return "en"
    
    def _status_node(self, state: NoteAgentState) -> dict:
        """
        Generate status message between tool executions.
        This creates the 'chat' in chat-tool-chat-tool pattern.
        """
        last_tool_name = state.get("last_tool_name", "")
        
        # Status message templates (no emoji for Windows GBK encoding safety)
        STATUS_TEMPLATES = {
            "delete_note": "[Done] Note deleted",
            "create_note": "[Done] Note created",
            "rename_note": "[Done] Title updated",
            "update_note": "[Done] Content updated",
            "set_note_category": "[Done] Category set",
            "list_recent_notes": "[Done] Notes listed",
            "search_knowledge": "[Done] Search complete",
            "read_note_content": "[Done] Content loaded",
            "list_categories": "[Done] Categories loaded",
        }
        
        status_text = STATUS_TEMPLATES.get(last_tool_name, f"✓ {last_tool_name} 执行完成")
        
        # CRITICAL: Mark as status_message to filter it out from LLM reasoning in next turn
        status_message = AIMessage(
            content=status_text, 
            additional_kwargs={"type": "status_message"}
        )
        
        safe_print(f"[STATUS] Generating marked status message: {status_text}")
        
        return {"messages": [status_message]}
    
    def _should_continue(self, state: NoteAgentState) -> Literal["continue", "end"]:
        """
        Workflow state machine: determine whether to continue or end.
        
        2-way branching:
        - "continue": has tool_calls → execute tools
        - "end": no tool_calls OR max turns reached
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
        
        # 2. No tool_calls → task complete, end
        return "end"


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
