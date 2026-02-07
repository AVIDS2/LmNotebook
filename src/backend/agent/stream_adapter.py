"""
Stream Adapter for LangGraph -> SSE Format.

This module provides adapters to convert LangGraph streaming output
to the existing SSE (Server-Sent Events) format used by the frontend.

This ensures BACKWARD COMPATIBILITY - the frontend requires NO changes.

Frontend expects these formats:
- {"type": "status", "text": "Thinking..."}
- {"tool_call": "note_created", "note_id": "xxx"}
- {"text": "AI response content..."}
- {"error": "Error message"}
"""
import json
import re
import asyncio
import httpx
from typing import AsyncGenerator, Any, Dict
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from services.note_service import NoteService


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', errors='replace').decode('gbk'))




# ============================================================================
# STATUS LABELS (matching frontend expectations)
# ============================================================================

TOOL_STATUS_LABELS = {
    "search_knowledge": "Searching knowledge",
    "read_note_content": "Reading note",
    "rename_note": "Renaming note",
    "list_recent_notes": "Listing notes",
    "update_note": "Updating note",
    "create_note": "Creating note",
    "delete_note": "Deleting note",
    "list_categories": "Loading categories",
    "set_note_category": "Setting category",
}

WRITE_TOOLS = {
    "delete_note",
    "create_note",
    "rename_note",
    "update_note",
    "set_note_category",
}

_note_service = NoteService()


def _build_note_title_lookup(input_state: Any) -> Dict[str, str]:
    """
    Build a note_id -> note_title map from current request context.
    """
    if not isinstance(input_state, dict):
        return {}

    lookup: Dict[str, str] = {}
    pairs = [
        ("active_note_id", "active_note_title"),
        ("context_note_id", "context_note_title"),
    ]
    for note_id_key, note_title_key in pairs:
        note_id = input_state.get(note_id_key)
        note_title = input_state.get(note_title_key)
        if isinstance(note_id, str) and note_id and isinstance(note_title, str) and note_title.strip():
            lookup[note_id] = note_title.strip()
    return lookup


def _extract_note_title_from_args(tool_name: str, tool_args: dict, note_title_lookup: Dict[str, str] | None = None) -> str:
    """
    Extract note title from tool arguments for display.
    Returns empty string if not applicable.
    """
    # Tool args that contain note_title
    if 'note_title' in tool_args:
        return tool_args['note_title']
    if 'title' in tool_args:
        return tool_args['title']
    if 'new_title' in tool_args:
        return tool_args['new_title']
    # For read/update operations, try to resolve note_id to a known title.
    if 'note_id' in tool_args:
        note_id = tool_args['note_id']
        if isinstance(note_id, str) and note_title_lookup:
            if note_id in note_title_lookup:
                return note_title_lookup[note_id]
    return ""


async def _resolve_note_title(tool_name: str, tool_args: dict, note_title_lookup: Dict[str, str]) -> str:
    """
    Resolve user-facing note title for status labels.
    Priority:
    1) explicit title args
    2) context lookup by note_id
    3) database lookup by note_id
    """
    title = _extract_note_title_from_args(tool_name, tool_args, note_title_lookup)
    if title:
        return title

    note_id = tool_args.get("note_id")
    if not isinstance(note_id, str) or not note_id:
        return ""

    try:
        note = await _note_service.get_note(note_id)
    except Exception:
        return ""

    if isinstance(note, dict):
        note_title = note.get("title")
        if isinstance(note_title, str):
            return note_title.strip()
    return ""


# ============================================================================
# STREAM ADAPTERS
# ============================================================================

async def langgraph_stream_to_sse(
    graph,
    input_state: Any,
    config: Dict[str, Any],
) -> AsyncGenerator[str, None]:
    """
    Convert LangGraph streaming output to SSE format.
    
    This adapter ensures backward compatibility with the existing frontend.
    The frontend (AgentBubble.vue) expects specific JSON structures via SSE.
    
    Args:
        graph: Compiled LangGraph StateGraph
        input_state: Initial state dictionary
        config: LangGraph config (thread_id, etc.)
    
    Yields:
        JSON strings in SSE format
    """
    
    # Track state for event generation
    has_started = False
    
    # Track seen content to avoid duplicates
    seen_content_hashes = set()
    
    # Track pending tool calls by ID for proper completion matching
    pending_tools = {}
    
    # Buffer for accumulating text to filter out tool descriptions
    text_buffer = ""
    
    # Resolve note titles from request context so status labels can show user-friendly names.
    note_title_lookup = _build_note_title_lookup(input_state)

    try:
        # Use multi-mode streaming for rich feedback
        async for event in graph.astream(
            input_state,
            config,
            stream_mode=["messages", "updates"],
        ):
            mode, chunk = event if isinstance(event, tuple) else ("updates", event)
            
            # ============================================================
            # Handle "messages" mode - LLM tokens (streaming)
            # ============================================================
            if mode == "messages":
                # chunk is a tuple: (message, metadata)
                if isinstance(chunk, tuple):
                    message, metadata = chunk
                else:
                    message = chunk
                    metadata = {}
                
                # Get the node that generated this message
                langgraph_node = metadata.get("langgraph_node", "") if isinstance(metadata, dict) else ""
                
                # CRITICAL: Only stream content from 'agent' node.
                # 'status' node messages are internal workflow markers, NOT user-facing content.
                if langgraph_node != "agent":
                    continue
                
                # Only process AIMessage/AIMessageChunk content
                if isinstance(message, (AIMessage, AIMessageChunk)):
                    content = message.content
                    if content and isinstance(content, str):
                        # Skip classifications
                        if content.strip().upper() in ["CHAT", "TASK"]:
                            continue
                        
                        # Accumulate text into buffer
                        text_buffer += content
                        
                        # Check for sentence completion or significant buffer size
                        # Check for sentence completion or significant buffer size.
                        # Use robust punctuation detection to avoid encoding-related truncation.
                        if re.search(r"[。！？.!?\n]", text_buffer) or len(text_buffer) > 50:
                            chunk_text = text_buffer
                            if chunk_text.strip():
                                final_clean = chunk_text.strip()
                                # Record this content to avoid duplicates in 'updates' mode
                                seen_content_hashes.add(final_clean)
                                yield json.dumps({
                                    "part_type": "text",
                                    "delta": chunk_text
                                })
                            text_buffer = ""
                
            # ============================================================
            # Handle "updates" mode - Node state updates
            # ============================================================
            elif mode == "updates":
                # chunk is a dict like {"node_name": state_update}
                if not isinstance(chunk, dict):
                    continue

                # LangGraph interrupt payload (human-in-the-loop pause)
                if "__interrupt__" in chunk:
                    interrupts = chunk.get("__interrupt__") or []
                    payload = None
                    if interrupts:
                        first = interrupts[0]
                        payload = getattr(first, "value", None)
                        if payload is None and isinstance(first, dict):
                            payload = first.get("value")
                    if payload is not None:
                        yield json.dumps({
                            "type": "approval_required",
                            "approval": payload
                        })
                    continue
                
                for node_name, node_output in chunk.items():
                    # Skip if not a dict
                    if not isinstance(node_output, dict):
                        continue
                    
                    messages = node_output.get("messages", [])
                    
                    # ========== Router Node ==========
                    if node_name == "router":
                        if not has_started:
                            # Part-Based: status is still a separate event type
                            yield json.dumps({"type": "status", "text": "Thinking..."})
                            has_started = True
                    
                    # ========== Agent Node (tool calls) ==========
                    elif node_name == "agent":
                        auto_accept_writes = bool(node_output.get("auto_accept_writes", True))
                        for msg in messages:
                            # Emit tool call as Part
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tool_name = tc.get("name", "")
                                    tool_id = tc.get("id", "")
                                    tool_args = tc.get("args", {})
                                    
                                    # Track pending tools by ID for proper matching
                                    pending_tools[tool_id] = tool_name
                                    
                                    # Part-Based: Emit tool_part with status "running"
                                    base_label = TOOL_STATUS_LABELS.get(tool_name, tool_name)
                                    note_title = await _resolve_note_title(tool_name, tool_args, note_title_lookup)
                                    
                                    # Build display title with note name if available
                                    if note_title:
                                        title = f"{base_label}: {note_title}"
                                    else:
                                        title = base_label
                                    
                                    part_status = "running"
                                    if (not auto_accept_writes) and (tool_name in WRITE_TOOLS):
                                        part_status = "pending"

                                    yield json.dumps({
                                        "part_type": "tool",
                                        "tool": tool_name,
                                        "tool_id": tool_id,
                                        "status": part_status,
                                        "title": title,
                                        "input_preview": str(tool_args)[:80] if tool_args else ""
                                    })
                    
                    # ========== Run One Tool Node (results) ==========
                    # NOTE: Changed from 'tools' to 'run_one_tool' after 3-node refactor
                    elif node_name in ["tools", "run_one_tool"]:
                        for msg in messages:
                            if isinstance(msg, ToolMessage):
                                content = msg.content if hasattr(msg, 'content') else str(msg)
                                tool_call_id = getattr(msg, 'tool_call_id', None)
                                
                                # Match completed tool by ID
                                tool_name = pending_tools.pop(tool_call_id, None) if tool_call_id else None
                                if not tool_name:
                                    tool_name = "unknown"
                                
                                # Part-Based: Emit tool_part with status "completed"
                                output_summary = content[:100] + "..." if len(content) > 100 else content
                                yield json.dumps({
                                    "part_type": "tool",
                                    "tool": tool_name,
                                    "tool_id": tool_call_id,
                                    "status": "completed",
                                    "output": output_summary
                                })
                                
                                # Also emit legacy tool events for specific actions
                                for event in _extract_tool_events(tool_name, content):
                                    yield event
                    
                    # ========== Fast Chat / Final Response ==========
                    elif node_name == "fast_chat":
                        # Safety Check: If messages mode didn't push everything, 
                        # or if we need to emit a final complete message.
                        for msg in messages:
                            if isinstance(msg, (AIMessage, AIMessageChunk)):
                                content = msg.content
                                if content and isinstance(content, str):
                                    clean_content = content.strip()
                                    # Strict Deduplication: check if this exact or similar string was already seen
                                    is_duplicate = any(clean_content in seen or seen in clean_content for seen in [s for s in seen_content_hashes if isinstance(s, str)])
                                    if not is_duplicate:
                                        seen_content_hashes.add(clean_content)
                                        yield json.dumps({
                                            "part_type": "text",
                                            "delta": content
                                        })
    
    except asyncio.CancelledError:
        # Handle stream cancellation gracefully (prevents Event loop is closed errors)
        safe_print("[Stream] Stream cancelled by client")
        pass
    except httpx.TimeoutException as e:
        safe_print(f"[Stream] Timeout error: {e}")
        yield json.dumps({"error": "Request timeout, please retry"})
    except httpx.ConnectError as e:
        safe_print(f"[Stream] Connection error: {e}")
        yield json.dumps({"error": "Cannot connect to AI service, please check network"})
    except Exception as e:
        import traceback
        safe_print(f"[Stream] Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()
        error_msg = str(e) if str(e) else type(e).__name__
        yield json.dumps({"error": f"AI service error: {error_msg}"})
    finally:
        # Flush any remaining text in buffer at stream end
        if text_buffer:
            clean_text = text_buffer.strip()
            if clean_text and len(clean_text) > 2:
                yield json.dumps({
                    "part_type": "text",
                    "delta": clean_text
                })


def _extract_tool_events(tool_name: str, content: str) -> list:
    """
    Extract tool call events from tool results.
    
    These events trigger frontend actions like refreshing notes.
    
    Args:
        tool_name: Name of the executed tool
        content: Tool result content
    
    Returns:
        List of JSON strings for SSE
    """
    events = []

    if tool_name == "create_note" and "ID:" in content:
        match = re.search(r"ID:\s*([\w-]+)", content)
        if match:
            events.append(json.dumps({
                "tool_call": "note_created",
                "note_id": match.group(1)
            }))
    
    elif tool_name == "update_note" and "Successfully updated" in content:
        # Match (ID: xxx) format
        match = re.search(r"\(ID:\s*([\w-]+)\)", content)
        note_id = match.group(1) if match else "unknown"
        events.append(json.dumps({
            "tool_call": "note_updated",
            "note_id": note_id
        }))
    
    elif tool_name == "rename_note" and "Successfully renamed" in content:
        # Match note ID from the function call or content
        events.append(json.dumps({
            "tool_call": "note_renamed",
            "refresh": True  # Signal frontend to refresh note list
        }))
    
    elif tool_name == "delete_note" and "Successfully deleted" in content:
        match = re.search(r"note[:\s]*([\w-]+)", content, re.IGNORECASE)
        note_id = match.group(1) if match else "unknown"
        events.append(json.dumps({
            "tool_call": "note_deleted",
            "note_id": note_id
        }))
    
    elif tool_name == "set_note_category" and "Successfully assigned" in content:
        events.append(json.dumps({
            "tool_call": "note_categorized"
        }))
    
    return events


# ============================================================================
# SIMPLE STREAM ADAPTER (for non-streaming invocation)
# ============================================================================

async def invoke_and_stream(
    graph,
    input_state: Dict[str, Any],
    config: Dict[str, Any],
) -> AsyncGenerator[str, None]:
    """
    Invoke graph and stream the final response.
    
    This is a simpler adapter for cases where full streaming isn't needed.
    """
    yield json.dumps({"type": "status", "text": "Thinking..."})
    
    try:
        result = await graph.ainvoke(input_state, config)
        
        messages = result.get("messages", [])
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                if not hasattr(msg, 'tool_calls') or not msg.tool_calls:
                    yield json.dumps({"text": msg.content})
    
    except Exception as e:
        yield json.dumps({"error": str(e)})

