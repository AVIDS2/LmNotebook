"""
Agent Supervisor - LangGraph 1.x Edition.

This module provides the main entry point for the AI agent.
It has been refactored from a hand-written ReAct loop to use
LangGraph's StateGraph for production-grade agent orchestration.

Key Improvements:
1. Graph-based State Machine (LangGraph StateGraph)
2. Declarative node and edge definitions
3. Built-in checkpointing support
4. Doom Loop detection
5. Multi-mode streaming

API Compatibility:
- invoke_stream() signature unchanged
- SSE format unchanged (frontend requires NO changes)
"""
import json
import re
from typing import Optional, List, Dict, Any, AsyncIterator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from core.llm import get_llm
from agent.tools import get_all_agent_tools
from agent.state import NoteAgentState, create_initial_state
from agent.graph import create_note_agent_graph, NoteAgentGraph
from agent.stream_adapter import langgraph_stream_to_sse

# Import session manager for state persistence
from core.session_manager import SessionManager


# ============================================================================
# LEGACY PROMPTS (kept for reference and fast_chat fallback)
# ============================================================================

SUPERVISOR_PROMPT = """
你是一个拥有自主性、思考能力的企业级知识助手 "Origin"。
你的工作模式是基于 **ReAct (Reasoning and Acting)** 框架的。

### 核心准则：
1. **工具决策自理**：当用户提出问题，你首先分析：我是否需要查阅现有的笔记？还是这属于"通用百科知识"？
2. **拒绝无意义搜索**：
   - 如果问题属于**通用知识**（Python 语法、历史事件、科学常识），**直接回答**，禁止调用工具。
   - 如果问题需要用户**个人笔记/数据**，再调用 `search_knowledge` 或 `read_note_content`。
3. **工具失败时不要重复**：如果工具返回"未找到"、"无结果"，**不要再调用同一工具**，直接告知用户。
4. **诚实第一**：当无法回答时，坦诚告知用户，而非编造信息。

### 重要：操作当前笔记
当用户提到"这篇笔记"、"当前笔记"、"这个"等指代词时：
- 首先检查是否有 `active_note_id` 上下文
- 如果需要读取内容，先调用 `read_note_content` 工具
- 如果需要修改，使用 `update_note` 工具

### ⚠️ 分类操作规则（严格遵守）：
- 笔记的**分类/标签**只能通过 `set_note_category` 工具操作
- **绝对禁止**通过 `update_note` 修改笔记内容来添加分类信息
- 用户说"归类到 X"、"打标签"、"分类为"时 → 使用 `set_note_category`
- 用户说"修改内容"、"编辑正文" → 使用 `update_note`
"""


# ============================================================================
# AGENT SUPERVISOR CLASS
# ============================================================================

# Shared graph instance to persist MemorySaver across requests
# Shared resources for singleton pattern
_shared_graph = None
_shared_checkpointer = None

async def get_agent_graph():
    """Return a singleton instance of the compiled graph with SQLite checkpointer."""
    global _shared_graph, _shared_checkpointer
    
    if _shared_graph is None:
        from agent.graph import create_note_agent_graph, CHECKPOINT_DB_PATH
        from agent.tools import get_all_agent_tools
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        import aiosqlite
        
        print(f"[Agent] Initializing graph with SQLite checkpointer: {CHECKPOINT_DB_PATH}")
        
        # Create persistent SQLite checkpointer
        # AsyncSqliteSaver needs to be initialized with a connection
        conn = await aiosqlite.connect(CHECKPOINT_DB_PATH)
        _shared_checkpointer = AsyncSqliteSaver(conn)
        
        # Setup the checkpointer tables
        await _shared_checkpointer.setup()
        
        # Build graph with checkpointer
        _shared_graph = await create_note_agent_graph(
            tools=get_all_agent_tools(),
            checkpointer=_shared_checkpointer
        )
        
        print("[Agent] Graph initialized with persistent memory")
    
    return _shared_graph


def sanitize_message_history(messages: list) -> list:
    """
    Clean up message history to ensure valid tool_calls/tool_message pairs.
    Removes orphaned tool_calls that don't have corresponding tool responses.
    """
    if not messages:
        return messages
    
    # Find all tool_call_ids that have responses
    responded_ids = set()
    for msg in messages:
        if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
            responded_ids.add(msg.tool_call_id)
    
    # Filter messages: remove AIMessages with tool_calls that have no responses
    sanitized = []
    for msg in messages:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            # Check if ALL tool_calls have responses
            all_responded = all(
                tc.get('id') in responded_ids 
                for tc in msg.tool_calls
            )
            if not all_responded:
                # Convert to regular AIMessage without tool_calls
                from langchain_core.messages import AIMessage
                sanitized.append(AIMessage(content=msg.content or "[Previous action was interrupted]"))
                print(f"[Agent] Sanitized orphaned tool_calls message")
                continue
        sanitized.append(msg)
    
    return sanitized


class AgentSupervisor:
    """
    Production-Grade Agent Supervisor using LangGraph 1.x.
    
    This class handles the interface between the API and the stateful graph.
    It utilizes a shared singleton graph to ensure memory persistence.
    """
    
    def __init__(self):
        """Initialize the supervisor."""
        self.llm = get_llm()
        self.tools = get_all_agent_tools()
        self.session_manager = SessionManager()
        
        # Graph will be initialized lazily in invoke_stream
        self.graph = None
        
        # Keep model_with_tools for legacy compatibility
        self.model_with_tools = self.llm.bind_tools(self.tools)
        self.tools_map = {tool.name: tool for tool in self.tools}
    
    async def _ensure_graph(self):
        """Lazily initialize the graph with SQLite checkpointer."""
        if self.graph is None:
            self.graph = await get_agent_graph()
        return self.graph
    
    async def invoke_stream(
        self,
        message: str,
        session_id: str = "default",
        history: Optional[List[Dict[str, Any]]] = None,  # Deprecated, kept for compat
        note_context: Optional[str] = None,
        active_note_id: Optional[str] = None,
        active_note_title: Optional[str] = None,
        selected_text: Optional[str] = None,
        context_note_id: Optional[str] = None,
        context_note_title: Optional[str] = None,
        use_knowledge: bool = False
    ) -> AsyncIterator[str]:
        """
        Stream agent responses using LangGraph.
        
        This method maintains the exact same API as before for backward compatibility.
        The frontend SSE format is preserved through the stream adapter.
        
        Args:
            message: User message
            session_id: Session ID for state persistence (persisted to SQLite)
            history: Deprecated, ignored
            note_context: Current note content
            active_note_id: Current note ID
            active_note_title: Current note title
            selected_text: Selected text for operations
            context_note_id: Referenced note ID (@ mention)
            context_note_title: Referenced note title
            use_knowledge: Whether to search knowledge base first (@)
        
        Yields:
            JSON strings in SSE format (compatible with existing frontend)
        """
        # Ensure graph is initialized
        graph = await self._ensure_graph()
        
        # ================================================================
        # STEP 1: Build context (same as before)
        # ================================================================
        context_notes_info = ""
        
        # Handle Active Note
        if active_note_id:
            title = active_note_title or "Active Note"
            context_notes_info += f"\n[AUTO-INSPECTED NOTE]\nTitle: {title}\nID: {active_note_id}\nContent:\n{note_context or '(Empty)'}\n---\n"
        
        # Handle Referenced Note
        if context_note_id and context_note_id != active_note_id:
            try:
                from services.note_service import NoteService
                ns = NoteService()
                note = await ns.get_note(context_note_id)
                if note:
                    title = context_note_title or note.get('title', 'Referenced Note')
                    content = note.get('content') or note.get('plainText') or "(Empty)"
                    context_notes_info += f"\n[EXPLICITLY REFERENCED NOTE (@)]\nTitle: {title}\nID: {context_note_id}\nContent:\n{content}\n---\n"
                    print(f"[Agent] Loaded explicit context: {title}")
            except Exception as e:
                print(f"[Agent] Failed to load referenced note context: {e}")
        
        # ================================================================
        # STEP 2: Build initial state for LangGraph
        # ================================================================
        initial_state = create_initial_state(
            session_id=session_id,
            active_note_id=active_note_id,
            active_note_title=active_note_title,
            context_note_id=context_note_id,
            context_note_title=context_note_title,
            note_content=context_notes_info if context_notes_info else note_context,
            selected_text=selected_text,
            use_knowledge=use_knowledge,
        )
        
        # In LangGraph 1.x with checkpointer, we don't manually append the new message to history.
        # The checkpointer restores the history based on thread_id, and we only pass the NEW message.
        initial_state["messages"] = [HumanMessage(content=message)]
        
        # ================================================================
        # STEP 3: LangGraph config with thread_id for checkpointing
        # ================================================================
        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }
        
        # ================================================================
        # STEP 4: Stream via LangGraph with SSE adapter
        # ================================================================
        try:
            print(f"[Agent] Starting LangGraph stream (Session: {session_id})")
            
            # Pre-check: Validate checkpoint state before streaming
            # This prevents the "tool_calls must be followed by tool messages" error
            try:
                from agent.graph import CHECKPOINT_DB_PATH
                import aiosqlite
                from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
                
                async with aiosqlite.connect(CHECKPOINT_DB_PATH) as db:
                    cursor = await db.execute(
                        "SELECT checkpoint FROM checkpoints WHERE thread_id = ? ORDER BY checkpoint_id DESC LIMIT 1",
                        (session_id,)
                    )
                    row = await cursor.fetchone()
                    
                    if row:
                        serde = JsonPlusSerializer()
                        checkpoint_data = serde.loads(row[0])
                        
                        if checkpoint_data and 'channel_values' in checkpoint_data:
                            messages = checkpoint_data['channel_values'].get('messages', [])
                            
                            # Check for orphaned tool_calls (AIMessage with tool_calls but no following ToolMessage)
                            if messages:
                                last_msg = messages[-1]
                                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                                    # Last message has tool_calls - this is a corrupted state
                                    print(f"[Agent] Detected incomplete tool_calls in checkpoint, cleaning up...")
                                    await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (session_id,))
                                    await db.execute("DELETE FROM writes WHERE thread_id = ?", (session_id,))
                                    await db.commit()
                                    print(f"[Agent] Cleaned up corrupted checkpoint for session {session_id}")
                                    yield json.dumps({"type": "status", "text": "\\u2714 Session recovered"})
            except Exception as check_err:
                print(f"[Agent] Checkpoint pre-check failed (non-fatal): {check_err}")
            
            async for sse_chunk in langgraph_stream_to_sse(
                graph,
                initial_state,
                config
            ):
                yield sse_chunk
            
            yield json.dumps({"type": "status", "text": ""})  # Clear status
            
        except Exception as e:
            error_str = str(e)
            print(f"[Agent] LangGraph stream error: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if this is a corrupted checkpoint error (orphaned tool_calls)
            if "tool_calls" in error_str and "tool_call_id" in error_str:
                print(f"[Agent] Detected corrupted checkpoint for session {session_id}, clearing...")
                try:
                    # Clear the corrupted checkpoint by deleting from SQLite
                    from agent.graph import CHECKPOINT_DB_PATH
                    import aiosqlite
                    async with aiosqlite.connect(CHECKPOINT_DB_PATH) as db:
                        await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (session_id,))
                        await db.execute("DELETE FROM writes WHERE thread_id = ?", (session_id,))
                        await db.commit()
                    print(f"[Agent] Cleared corrupted checkpoint, please retry")
                    yield json.dumps({"error": "Session history was corrupted and has been cleared. Please try again."})
                except Exception as cleanup_err:
                    print(f"[Agent] Failed to clear checkpoint: {cleanup_err}")
                    yield json.dumps({"error": f"AI service error: {error_str}"})
            else:
                yield json.dumps({"error": str(e)})
    
    async def classify_intent(self, query: str) -> str:
        """
        Classify user intent (CHAT or TASK).
        
        This is now delegated to the router node in the graph,
        but kept here for backward compatibility.
        """
        classification_prompt = """
        Analyze user intent.
        Output ONLY one word: 'CHAT' or 'TASK'.

        Rules:
        - 'TASK': If user asks to perform ANY action, modify data, search info, clean up format, organize notes.
        - 'CHAT': ONLY for pure discussion, coding questions, or philosophy where specific note tools are NOT needed.

        User: {query}
        Intent:
        """
        try:
            resp = await self.llm.ainvoke([
                HumanMessage(content=classification_prompt.format(query=query))
            ])
            intent = resp.content.strip().upper().replace("'", "").replace('"', "")
            return "TASK" if "TASK" in intent else "CHAT"
        except Exception:
            return "TASK"
    
    async def invoke(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Non-streaming invocation (legacy compatibility).
        
        Collects streaming output and returns as a single response.
        """
        full_text = ""
        async for chunk in self.invoke_stream(*args, **kwargs):
            try:
                data = json.loads(chunk)
                if "text" in data:
                    full_text += data["text"]
            except json.JSONDecodeError:
                full_text += chunk
        
        return {"response": full_text, "tool_calls": []}
    
    async def format_text(self, text: str, context: Optional[str] = None) -> str:
        """
        Format text using AI (for format brush feature).
        
        This is a simple direct LLM call, doesn't need the full graph.
        """
        format_prompt = f"""
        请将以下文本进行格式化和优化，保持原意并提升可读性。
        使用 Markdown 格式输出。
        
        {"上下文:\n" + context if context else ""}
        
        需要格式化的文本:
        {text}
        
        格式化后的文本:
        """
        
        try:
            resp = await self.llm.ainvoke([HumanMessage(content=format_prompt)])
            return resp.content.strip()
        except Exception as e:
            print(f"[Agent] Format error: {e}")
            return text
