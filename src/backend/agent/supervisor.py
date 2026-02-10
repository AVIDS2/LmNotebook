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
from langgraph.types import Command

from core.llm import get_llm
from agent.tools import get_all_agent_tools
from agent.state import NoteAgentState, create_initial_state
from agent.graph import create_note_agent_graph, NoteAgentGraph
from agent.stream_adapter import langgraph_stream_to_sse


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            import sys
            sys.stdout.buffer.write((msg + '\n').encode('utf-8', errors='replace'))
            sys.stdout.buffer.flush()
        except Exception:
            print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))

# Import session manager for state persistence
from core.session_manager import SessionManager


# Note: Prompts are now loaded from prompts/*.txt files in graph.py


# ============================================================================
# AGENT SUPERVISOR CLASS
# ============================================================================

# Shared graph instance to persist MemorySaver across requests
# Shared resources for singleton pattern
_shared_graph = None
_shared_checkpointer = None

async def invalidate_agent_runtime_cache():
    """
    Invalidate cached LangGraph runtime so provider/model switches apply immediately.
    Called by model settings APIs after provider mutations.
    """
    global _shared_graph, _shared_checkpointer

    # Best effort: close underlying sqlite connection before dropping references.
    if _shared_checkpointer is not None:
        try:
            conn = getattr(_shared_checkpointer, "conn", None)
            if conn is not None:
                await conn.close()
        except Exception as e:
            safe_print(f"[Agent] Failed to close cached checkpointer cleanly: {e}")

    _shared_graph = None
    _shared_checkpointer = None
    safe_print("[Agent] Runtime cache invalidated (graph/checkpointer)")

async def get_agent_graph():
    """Return a singleton instance of the compiled graph with SQLite checkpointer."""
    global _shared_graph, _shared_checkpointer
    
    if _shared_graph is None:
        from agent.graph import create_note_agent_graph, CHECKPOINT_DB_PATH
        from agent.tools import get_all_agent_tools
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        import aiosqlite
        
        safe_print(f"[Agent] Initializing graph with SQLite checkpointer: {CHECKPOINT_DB_PATH}")
        
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
        
        safe_print("[Agent] Graph initialized with persistent memory")
    
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
                safe_print(f"[Agent] Sanitized orphaned tool_calls message")
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
        use_knowledge: bool = False,
        auto_accept_writes: bool = True,
        resume: Optional[Dict[str, Any]] = None,
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
                    # Prefer markdownSource for structured reasoning/editing context.
                    content = note.get('markdownSource') or note.get('plainText') or note.get('content') or "(Empty)"
                    context_notes_info += f"\n[EXPLICITLY REFERENCED NOTE (@)]\nTitle: {title}\nID: {context_note_id}\nContent:\n{content}\n---\n"
                    safe_print(f"[Agent] Loaded explicit context: {title}")
            except Exception as e:
                safe_print(f"[Agent] Failed to load referenced note context: {e}")
        
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
            auto_accept_writes=auto_accept_writes,
        )
        
        # In LangGraph 1.x with checkpointer, we don't manually append the full history.
        # For normal requests, pass only the new user message.
        # For approval resume, pass Command(resume=...) and do not inject a new user message.
        graph_input: Any
        if resume is not None:
            # Safety check: verify checkpoint exists before attempting resume.
            # If the checkpoint was cleared (e.g. by error recovery), resuming
            # would start a fresh graph with no context, causing "Hello!" replies.
            try:
                from agent.graph import CHECKPOINT_DB_PATH
                import aiosqlite
                async with aiosqlite.connect(CHECKPOINT_DB_PATH) as db:
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?",
                        (session_id,)
                    )
                    row = await cursor.fetchone()
                    if not row or row[0] == 0:
                        safe_print(f"[Agent] Resume requested but no checkpoint found for session {session_id}")
                        yield json.dumps({"error": "No pending approval found for this session. The session may have expired."})
                        return
            except Exception as e:
                safe_print(f"[Agent] Resume checkpoint check failed (non-fatal): {e}")

            # IMPORTANT:
            # Resume should also carry "live" UI/runtime state updates.
            # Without this, toggles changed during a pending approval (e.g. auto_accept_writes)
            # only take effect on the NEXT user turn, not the current resumed workflow.
            resume_update = {
                "auto_accept_writes": auto_accept_writes,
                "active_note_id": active_note_id,
                "active_note_title": active_note_title,
                "context_note_id": context_note_id,
                "context_note_title": context_note_title,
                "note_content": context_notes_info if context_notes_info else note_context,
                "selected_text": selected_text,
                "use_knowledge": use_knowledge,
            }
            graph_input = Command(resume=resume, update=resume_update)
        else:
            initial_state["messages"] = [HumanMessage(content=message)]
            graph_input = initial_state
        
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
            safe_print(f"[Agent] Starting LangGraph stream (Session: {session_id})")
            
            # Pre-check: Validate checkpoint state before streaming.
            # This prevents the "tool_calls must be followed by tool messages" error.
            #
            # IMPORTANT: When an approval interrupt is pending, the checkpoint
            # legitimately contains an AIMessage with tool_calls plus a pending
            # write (the interrupt payload).  We must NOT delete that checkpoint.
            # Only clear when tool_calls are truly orphaned (no pending interrupt).
            if resume is None:
                try:
                    from agent.graph import CHECKPOINT_DB_PATH
                    import aiosqlite
                    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
                    
                    async with aiosqlite.connect(CHECKPOINT_DB_PATH) as db:
                        cursor = await db.execute(
                            "SELECT type, checkpoint FROM checkpoints WHERE thread_id = ? ORDER BY checkpoint_id DESC LIMIT 1",
                            (session_id,)
                        )
                        row = await cursor.fetchone()
                        
                        if row:
                            serde = JsonPlusSerializer()
                            checkpoint_data = serde.loads_typed((row[0], row[1]))
                            
                            if checkpoint_data and 'channel_values' in checkpoint_data:
                                messages = checkpoint_data['channel_values'].get('messages', [])
                                
                                if messages:
                                    last_msg = messages[-1]
                                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                                        # Check if there is a pending interrupt (approval waiting).
                                        # If so, this is a legitimate state 鈥?do NOT clear.
                                        pending_cursor = await db.execute(
                                            "SELECT COUNT(*) FROM writes WHERE thread_id = ? AND task_path LIKE '%__interrupt__%'",
                                            (session_id,)
                                        )
                                        pending_row = await pending_cursor.fetchone()
                                        has_pending_interrupt = pending_row and pending_row[0] > 0
                                        
                                        if has_pending_interrupt:
                                            safe_print("[Agent] Checkpoint has pending approval interrupt, skipping cleanup")
                                        else:
                                            # Non-destructive safeguard: avoid deleting checkpoint data automatically.
                                            safe_print(
                                                "[Agent] Checkpoint has unresolved tool_calls without interrupt. "
                                                "Skip cleanup and wait for explicit user retry."
                                            )
                except Exception as check_err:
                    safe_print(f"[Agent] Checkpoint pre-check failed (non-fatal): {check_err}")
            
            async for sse_chunk in langgraph_stream_to_sse(
                graph,
                graph_input,
                config
            ):
                yield sse_chunk
            
            yield json.dumps({"type": "status", "text": ""})  # Clear status
            
        except Exception as e:
            error_str = str(e)
            safe_print(f"[Agent] LangGraph stream error: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if this is a corrupted checkpoint error (orphaned tool_calls).
            # Do not auto-clear during explicit approval resume requests.
            if resume is None and "tool_calls" in error_str and "tool_call_id" in error_str:
                safe_print(
                    f"[Agent] Checkpoint state appears invalid for session {session_id}. "
                    "Skipping destructive cleanup."
                )
                yield json.dumps({
                    "error": (
                        "Session state is inconsistent (pending tool call mismatch). "
                        "Please click New Chat or retry the same action."
                    )
                })
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
        # Build context section separately to avoid f-string backslash issues
        context_section = ""
        if context:
            context_section = "Context:\n" + context + "\n\n"
        
        format_prompt = f"""Please format and optimize the following text while preserving its meaning.
Output in Markdown format.
Do not add or remove factual content.
Preserve semantic relationships strictly, especially for table-like content:
- keep row/column alignment
- keep header-to-value mapping
- do not swap or remap cells

{context_section}Text to format:
{text}

Formatted text:
"""
        
        try:
            resp = await self.llm.ainvoke([HumanMessage(content=format_prompt)])
            return resp.content.strip()
        except Exception as e:
            safe_print(f"[Agent] Format error: {e}")
            return text


