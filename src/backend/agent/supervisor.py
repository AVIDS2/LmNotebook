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

    async def _has_pending_interrupt(self, session_id: str) -> bool:
        """
        Return True when latest checkpoint has unresolved approval interrupt writes.

        Supports multiple LangGraph SQLite schemas:
        - modern: writes(channel='__interrupt__', checkpoint_id=...)
        - legacy: writes(task_path LIKE '%__interrupt__%')
        """
        if not session_id:
            return False
        try:
            from agent.graph import CHECKPOINT_DB_PATH
            import aiosqlite
            async with aiosqlite.connect(CHECKPOINT_DB_PATH) as db:
                cp_cursor = await db.execute(
                    "SELECT checkpoint_id FROM checkpoints WHERE thread_id = ? ORDER BY checkpoint_id DESC LIMIT 1",
                    (session_id,),
                )
                cp_row = await cp_cursor.fetchone()
                latest_checkpoint_id = cp_row[0] if cp_row else None

                cols_cursor = await db.execute("PRAGMA table_info(writes)")
                cols_rows = await cols_cursor.fetchall()
                write_cols = {row[1] for row in cols_rows if row and len(row) > 1}

                if {"channel", "checkpoint_id"}.issubset(write_cols) and latest_checkpoint_id:
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM writes WHERE thread_id = ? AND checkpoint_id = ? AND channel = '__interrupt__'",
                        (session_id, latest_checkpoint_id),
                    )
                    row = await cursor.fetchone()
                    return bool(row and row[0] > 0)

                if "task_path" in write_cols:
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM writes WHERE thread_id = ? AND task_path LIKE '%__interrupt__%'",
                        (session_id,),
                    )
                    row = await cursor.fetchone()
                    return bool(row and row[0] > 0)

                return False
        except Exception as e:
            safe_print(f"[Agent] Pending interrupt check failed (non-fatal): {e}")
            return False

    async def _checkpoint_has_orphan_tool_calls(self, session_id: str) -> bool:
        """
        Detect orphaned/malformed tool calls in latest checkpoint.
        """
        if not session_id:
            return False
        try:
            from agent.graph import CHECKPOINT_DB_PATH
            import aiosqlite
            from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

            async with aiosqlite.connect(CHECKPOINT_DB_PATH) as db:
                cursor = await db.execute(
                    "SELECT type, checkpoint FROM checkpoints WHERE thread_id = ? ORDER BY checkpoint_id DESC LIMIT 1",
                    (session_id,),
                )
                row = await cursor.fetchone()
                if not row:
                    return False

            serde = JsonPlusSerializer()
            checkpoint_data = serde.loads_typed((row[0], row[1]))
            messages = checkpoint_data.get("channel_values", {}).get("messages", [])
            if not messages:
                return False

            responded_ids = {
                getattr(msg, "tool_call_id", None)
                for msg in messages
                if getattr(msg, "tool_call_id", None)
            }
            for msg in messages:
                tool_calls = list(getattr(msg, "tool_calls", []) or [])
                invalid_tool_calls = list(getattr(msg, "invalid_tool_calls", []) or [])
                if invalid_tool_calls:
                    return True
                if not tool_calls:
                    continue
                for tc in tool_calls:
                    tc_id = str((tc or {}).get("id", "")).strip()
                    if not tc_id or tc_id not in responded_ids:
                        return True
            return False
        except Exception as e:
            safe_print(f"[Agent] Orphan tool_call check failed (non-fatal): {e}")
            return False

    async def _clear_thread_checkpoint_state(self, session_id: str) -> None:
        """
        Clear corrupted LangGraph state for one thread (conversation memory only).
        """
        if not session_id:
            return
        from agent.graph import CHECKPOINT_DB_PATH
        import aiosqlite

        async with aiosqlite.connect(CHECKPOINT_DB_PATH) as db:
            await db.execute("DELETE FROM writes WHERE thread_id = ?", (session_id,))
            await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (session_id,))
            await db.commit()
        safe_print(f"[Agent] Cleared corrupted checkpoint state for session {session_id}")

    def _build_live_state_update(
        self,
        *,
        auto_accept_writes: bool,
        active_note_id: Optional[str],
        active_note_title: Optional[str],
        context_note_id: Optional[str],
        context_note_title: Optional[str],
        note_content: Optional[str],
        selected_text: Optional[str],
        attachment_context: Optional[str],
        use_knowledge: bool,
        agent_mode: str,
    ) -> dict:
        """Build runtime state update payload shared by resume/cancel flows."""
        return {
            "auto_accept_writes": auto_accept_writes,
            "active_note_id": active_note_id,
            "active_note_title": active_note_title,
            "context_note_id": context_note_id,
            "context_note_title": context_note_title,
            "note_content": note_content,
            "selected_text": selected_text,
            "attachment_context": attachment_context,
            "use_knowledge": use_knowledge,
            "agent_mode": agent_mode if agent_mode in {"ask", "agent"} else "agent",
        }

    def _interpret_inline_approval_text(self, message: str) -> Optional[bool]:
        """
        Parse lightweight user replies for pending approval interrupts.
        Returns:
          - True  -> approve
          - False -> reject
          - None  -> unrelated message
        """
        if not isinstance(message, str):
            return None
        normalized = message.strip().lower()
        if not normalized:
            return None
        normalized = re.sub(r"[\s`'\"，。,.!?！？；;：:、~\-_/]+", "", normalized)
        if not normalized:
            return None

        positive_tokens = {
            "是", "是的", "好", "好的", "继续", "确认", "同意", "批准", "通过",
            "yes", "y", "ok", "okay", "approve", "approved", "continue", "go", "sure",
        }
        negative_tokens = {
            "否", "不是", "不", "不要", "取消", "拒绝", "不同意", "驳回",
            "no", "n", "reject", "cancel", "stop",
        }

        if normalized in positive_tokens:
            return True
        if normalized in negative_tokens:
            return False
        return None

    def _build_user_message_and_attachment_context(
        self,
        message: str,
        attachments: Optional[List[Dict[str, Any]]],
    ) -> tuple[HumanMessage, Optional[str]]:
        """
        Build a HumanMessage that supports multimodal image inputs and
        extract readable file context for the graph.
        """
        attachment_list = attachments or []
        if not attachment_list:
            return HumanMessage(content=message), None

        content_blocks: List[Dict[str, Any]] = []
        message_text = (message or "").strip()
        if message_text:
            content_blocks.append({"type": "text", "text": message_text})

        attachment_context_chunks: List[str] = []
        for idx, att in enumerate(attachment_list, start=1):
            if not isinstance(att, dict):
                continue
            kind = str(att.get("kind", "file") or "file").strip().lower()
            name = str(att.get("name", "") or f"attachment-{idx}")
            mime_type = str(att.get("mime_type", "") or "").strip()
            size_bytes = att.get("size_bytes")
            size_label = f"{size_bytes} bytes" if isinstance(size_bytes, int) and size_bytes >= 0 else "unknown-size"

            if kind == "image":
                data_url = str(att.get("data_url", "") or "").strip()
                if data_url:
                    content_blocks.append({"type": "text", "text": f"[Attached image: {name}]"})
                    content_blocks.append({"type": "image_url", "image_url": {"url": data_url}})
                else:
                    attachment_context_chunks.append(
                        f"[Image attachment missing data]\nname: {name}\nmime: {mime_type or 'unknown'}\nsize: {size_label}"
                    )
                continue

            file_text = str(att.get("text_content", "") or "").strip()
            if file_text:
                if len(file_text) > 12000:
                    file_text = file_text[:12000] + "\n...[truncated]"
                attachment_context_chunks.append(
                    f"[Attached file {idx}]\nname: {name}\nmime: {mime_type or 'unknown'}\nsize: {size_label}\ncontent:\n{file_text}"
                )
            else:
                attachment_context_chunks.append(
                    f"[Attached file {idx}]\nname: {name}\nmime: {mime_type or 'unknown'}\nsize: {size_label}\ncontent: (not readable text)"
                )

        if not content_blocks:
            fallback_text = message_text or "Please consider the provided attachments."
            content_blocks.append({"type": "text", "text": fallback_text})

        attachment_context = "\n\n".join(attachment_context_chunks).strip() or None
        return HumanMessage(content=content_blocks), attachment_context
    
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
        agent_mode: str = "agent",
        resume: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
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
        
        # Build multimodal user message + text attachment context
        user_message, attachment_context = self._build_user_message_and_attachment_context(
            message=message,
            attachments=attachments,
        )

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
            attachment_context=attachment_context,
            use_knowledge=use_knowledge,
            auto_accept_writes=auto_accept_writes,
            agent_mode=agent_mode,
        )

        # ================================================================
        # STEP 3: LangGraph config with thread_id for checkpointing
        # ================================================================
        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }

        live_state_update = self._build_live_state_update(
            auto_accept_writes=auto_accept_writes,
            active_note_id=active_note_id,
            active_note_title=active_note_title,
            context_note_id=context_note_id,
            context_note_title=context_note_title,
            note_content=context_notes_info if context_notes_info else note_context,
            selected_text=selected_text,
            attachment_context=attachment_context,
            use_knowledge=use_knowledge,
            agent_mode=agent_mode,
        )

        # If pending approval exists and no explicit resume payload is supplied,
        # support inline confirm/reject text (e.g., "是"/"继续"/"取消").
        if resume is None and await self._has_pending_interrupt(session_id):
            inline_decision = self._interpret_inline_approval_text(message)
            if inline_decision is not None:
                safe_print(f"[Agent] Interpreted inline approval decision: {inline_decision}")
                resume = inline_decision
            else:
                safe_print("[Agent] Pending approval exists; waiting for explicit approve/reject")
                yield json.dumps({
                    "error": (
                        "There is a pending write approval. "
                        "Please approve/reject in the review UI, or reply with '是/继续' (approve) "
                        "or '取消/拒绝' (reject)."
                    )
                })
                return

        # Auto-heal corrupted session memory before model invocation.
        # This handles old checkpoints that still contain orphaned tool_calls.
        if resume is None:
            try:
                has_orphan_tool_calls = await self._checkpoint_has_orphan_tool_calls(session_id)
                has_pending_interrupt = await self._has_pending_interrupt(session_id)
                if has_orphan_tool_calls and not has_pending_interrupt:
                    safe_print(
                        "[Agent] Corrupted checkpoint detected (orphan tool_calls). "
                        "Auto-clearing session state before new turn."
                    )
                    await self._clear_thread_checkpoint_state(session_id)
            except Exception as heal_err:
                safe_print(f"[Agent] Auto-heal pre-check failed (non-fatal): {heal_err}")
        
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
            graph_input = Command(resume=resume, update=live_state_update)
        else:
            initial_state["messages"] = [user_message]
            graph_input = initial_state
        
        # ================================================================
        # STEP 4: Stream via LangGraph with SSE adapter
        # ================================================================
        try:
            safe_print(f"[Agent] Starting LangGraph stream (Session: {session_id})")
            
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


