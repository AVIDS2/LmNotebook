"""
Chat API endpoints.
"""
from typing import Optional, List
import os
import sys
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from agent.supervisor import AgentSupervisor, invalidate_agent_runtime_cache
from core.model_manager import model_manager

router = APIRouter()


# Ensure UTF-8 logs in Windows terminals.
def configure_utf8_stdio():
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleCP(65001)
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


# Safe print without GBK fallback transcoding.
def safe_print(msg: str):
    """Print message safely while preserving UTF-8 text."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
            sys.stdout.flush()
        except Exception:
            print(msg.encode("ascii", errors="replace").decode("ascii"))


configure_utf8_stdio()


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")



import uuid

class ChatRequest(BaseModel):
    """Chat request payload."""
    message: str = Field(..., description="User message")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Session ID for server-side state")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Conversation history (Deprecated)")
    note_context: Optional[str] = Field(None, description="Current note content for context")
    selected_text: Optional[str] = Field(None, description="User-selected text for formatting")
    active_note_id: Optional[str] = Field(None, description="Current note ID")
    active_note_title: Optional[str] = Field(None, description="Current note Title")
    context_note_id: Optional[str] = Field(None, description="Explicitly referenced note ID (@)")
    context_note_title: Optional[str] = Field(None, description="Explicitly referenced note Title (@)")
    use_knowledge: bool = Field(False, description="Whether to search knowledge base first (@)")
    auto_accept_writes: bool = Field(True, description="Whether write tools are auto-approved without interrupt")
    model_provider_id: Optional[str] = Field(None, description="Model provider ID override for this request")
    model_name: Optional[str] = Field(None, description="Specific model name within the selected provider")
    resume: Optional[dict] = Field(None, description="Resume payload for LangGraph interrupt")

    @property
    def history_dicts(self) -> List[dict]:
        return [{"role": m.role, "content": m.content} for m in self.history]


class ChatResponse(BaseModel):
    """Chat response payload."""
    response: str = Field(..., description="Agent response")
    tool_calls: List[str] = Field(default_factory=list, description="Tools that were called")


async def apply_model_provider_override(provider_id: Optional[str], model_name: Optional[str] = None) -> bool:
    """
    Apply per-request model provider override.
    Returns True when a provider switch was applied, otherwise False.
    """
    changed = False
    if not provider_id and not model_name:
        return False

    providers = model_manager.get_providers() or []
    target = None
    if provider_id:
        target = next((p for p in providers if p.get("id") == provider_id), None)
        if target is None:
            safe_print(f"[MODEL] Requested provider not found: {provider_id}")
            return False
    else:
        target = model_manager.get_active_provider()
        if target is None:
            return False

    active = model_manager.get_active_provider()
    target_provider_id = target.get("id")
    requested_model = (model_name or "").strip()
    if requested_model:
        target_models = target.get("models") or ([target.get("modelName")] if target.get("modelName") else [])
        if requested_model not in target_models:
            safe_print(
                f"[MODEL] Requested model not found in provider: "
                f"{target_provider_id} / {requested_model}"
            )
            return False

    if provider_id and (not active or active.get("id") != target_provider_id):
        model_manager.set_active_provider(target_provider_id)
        changed = True
        # refresh active after switch
        active = model_manager.get_active_provider()

    if requested_model:
        current_model = (active or target).get("activeModel") or (active or target).get("modelName")
        if current_model != requested_model:
            if model_manager.set_provider_active_model(target_provider_id, requested_model):
                changed = True
            else:
                return False

    if changed:
        await invalidate_agent_runtime_cache()
        active_after = model_manager.get_active_provider() or target
        safe_print(
            f"[MODEL] Switched via request: "
            f"{active_after.get('name', target_provider_id)} / "
            f"{active_after.get('activeModel') or active_after.get('modelName') or 'unknown-model'}"
        )
    return changed


@router.post("/invoke", response_model=ChatResponse)
async def invoke_agent(request: ChatRequest):
    """
    Invoke the agent with a user message.
    Returns the complete response after processing.
    """
    try:
        await apply_model_provider_override(request.model_provider_id, request.model_name)
        supervisor = AgentSupervisor()
        # Note: Invoke method in supervisor also needs update ideally, but we focus on stream first
        result = await supervisor.invoke(
            message=request.message,
            history=request.history_dicts,
            note_context=request.note_context,
            selected_text=request.selected_text,
            active_note_id=request.active_note_id
        )
        return ChatResponse(
            response=result["response"],
            tool_calls=result.get("tool_calls", [])
        )
    except Exception as e:
        import traceback
        safe_print(f"[ERR] Chat API Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_agent(request: ChatRequest):
    """
    Stream agent responses in real-time.
    Returns Server-Sent Events for progressive display.
    """
    import json
    import time
    
    async def generate():
        chunk_count = 0
        start_time = time.time()
        try:
            await apply_model_provider_override(request.model_provider_id, request.model_name)
            supervisor = AgentSupervisor()
            safe_print(f">> Starting stream for: {request.message[:50]}... (Session: {request.session_id})")
            async for chunk in supervisor.invoke_stream(
                message=request.message,
                session_id=request.session_id,
                # history field is ignored by backend now
                note_context=request.note_context,
                selected_text=request.selected_text,
                active_note_id=request.active_note_id,
                active_note_title=request.active_note_title,
                context_note_id=request.context_note_id,
                context_note_title=request.context_note_title,
                use_knowledge=request.use_knowledge,
                auto_accept_writes=request.auto_accept_writes,
                resume=request.resume
            ):
                chunk_count += 1
                elapsed = time.time() - start_time
                preview = chunk[:120] + ("..." if len(chunk) > 120 else "")
                safe_print(f">> Chunk #{chunk_count} at {elapsed:.2f}s (len={len(chunk)}): {repr(preview)}")
                
                # Check if chunk is already a JSON message (status, tool_call, or text)
                if isinstance(chunk, str) and chunk.startswith('{'):
                    yield f"data: {chunk}\n\n"
                else:
                    # Fallback for any raw text (shouldn't happen now)
                    encoded = json.dumps({"text": chunk})
                    yield f"data: {encoded}\n\n"
            safe_print(f">> Stream complete: {chunk_count} chunks in {time.time() - start_time:.2f}s")
            yield "data: [DONE]\n\n"
        except Exception as e:
            safe_print(f"[ERR] Stream error: {e}")
            error_msg = json.dumps({"error": str(e)})
            yield f"data: {error_msg}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/format")
async def format_text(request: ChatRequest):
    """
    AI Format Brush endpoint.
    Returns both Markdown and HTML for TipTap integration.
    """
    if not request.selected_text and not request.note_context:
        raise HTTPException(
            status_code=400,
            detail="Either selected_text or note_context is required"
        )
    
    try:
        import markdown
        
        supervisor = AgentSupervisor()
        formatted_md = await supervisor.format_text(
            text=request.selected_text or request.note_context,
            context=request.note_context
        )
        
        # Convert MD to HTML for TipTap's setContent()
        formatted_html = markdown.markdown(
            formatted_md, 
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        
        return {
            "formatted_html": formatted_html,
            "formatted_md": formatted_md,
            "should_apply": True,
            "tool_call": "format_apply"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SESSION HISTORY APIs
# ============================================================================

async def _get_checkpoint_messages(checkpoint_db: str, thread_id: str):
    """
    Get messages from a checkpoint using LangGraph's serialization.
    """
    import aiosqlite
    
    try:
        # Use LangGraph's serde to properly deserialize
        from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
        
        serde = JsonPlusSerializer()
        
        async with aiosqlite.connect(checkpoint_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT type, checkpoint FROM checkpoints 
                WHERE thread_id = ? 
                ORDER BY checkpoint_id DESC 
                LIMIT 1
            """, (thread_id,))
            row = await cursor.fetchone()
            
            if not row or not row['checkpoint']:
                return []
            
            # Deserialize using LangGraph's serializer (needs type + data tuple)
            checkpoint_data = serde.loads_typed((row['type'], row['checkpoint']))
            channel_values = checkpoint_data.get('channel_values', {})
            raw_messages = channel_values.get('messages', [])
            
            messages = []
            for msg in raw_messages:
                role = None
                content = ""
                
                # LangGraph messages are LangChain message objects
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    if msg.type == 'human':
                        role = 'user'
                        content = msg.content
                    elif msg.type == 'ai':
                        role = 'assistant'
                        content = msg.content
                        # Skip empty AI messages (tool calls only)
                        if not content and hasattr(msg, 'tool_calls') and msg.tool_calls:
                            continue
                
                if role and content:
                    messages.append({"role": role, "content": content})
            
            return messages
    except Exception as e:
        safe_print(f"[API] Error getting checkpoint messages: {e}")
        import traceback
        traceback.print_exc()
        return []


@router.get("/sessions")
async def list_sessions():
    """
    List all chat sessions with their first message as preview.
    Returns sessions sorted by last update time.
    """
    import aiosqlite
    from core.config import settings
    import os
    
    checkpoint_db = os.path.join(settings.data_directory, "checkpoints.db")
    
    if not os.path.exists(checkpoint_db):
        return {"sessions": []}
    
    sessions = []
    try:
        async with aiosqlite.connect(checkpoint_db) as db:
            db.row_factory = aiosqlite.Row
            # Get unique thread_ids with their latest checkpoint
            cursor = await db.execute("""
                SELECT DISTINCT thread_id, MAX(checkpoint_id) as latest_checkpoint
                FROM checkpoints
                GROUP BY thread_id
                ORDER BY latest_checkpoint DESC
                LIMIT 50
            """)
            rows = await cursor.fetchall()
        
        for row in rows:
            thread_id = row['thread_id']
            messages = await _get_checkpoint_messages(checkpoint_db, thread_id)
            
            if not messages:
                continue
            
            # Use first user message as preview/title
            preview = "New conversation"
            for msg in messages:
                if msg['role'] == 'user':
                    content = msg['content']
                    preview = content[:60] + ('...' if len(content) > 60 else '')
                    break
            
            sessions.append({
                "id": thread_id,
                "preview": preview,
                "message_count": len(messages),
                "updated_at": row['latest_checkpoint']
            })
        
        return {"sessions": sessions}
    except Exception as e:
        safe_print(f"[API] Error listing sessions: {e}")
        import traceback
        traceback.print_exc()
        return {"sessions": []}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """
    Get all messages for a specific session.
    """
    from core.config import settings
    import os
    
    checkpoint_db = os.path.join(settings.data_directory, "checkpoints.db")
    
    if not os.path.exists(checkpoint_db):
        raise HTTPException(status_code=404, detail="No sessions found")
    
    messages = await _get_checkpoint_messages(checkpoint_db, session_id)
    
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found or empty")
    
    return {"session_id": session_id, "messages": messages}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a specific session and its checkpoints.
    """
    import aiosqlite
    from core.config import settings
    import os
    
    checkpoint_db = os.path.join(settings.data_directory, "checkpoints.db")
    
    if not os.path.exists(checkpoint_db):
        raise HTTPException(status_code=404, detail="No sessions found")
    
    try:
        async with aiosqlite.connect(checkpoint_db) as db:
            await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (session_id,))
            await db.execute("DELETE FROM writes WHERE thread_id = ?", (session_id,))
            await db.commit()
        
        return {"status": "success", "deleted": session_id}
    except Exception as e:
        safe_print(f"[API] Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LIGHTWEIGHT TEXT PROCESSING API (for selection-based AI operations)
# ============================================================================

class TextProcessRequest(BaseModel):
    """Request for lightweight text processing."""
    text: str = Field(..., description="Selected text to process")
    action: str = Field(..., description="Action: translate, explain, polish, summarize, expand, ask")
    target_lang: Optional[str] = Field("zh", description="Target language for translation")
    question: Optional[str] = Field(None, description="User's custom question for 'ask' action")

def _build_text_process_prompt(request: TextProcessRequest) -> str:
    action_prompts = {
        "translate": f"Translate the following text to {request.target_lang}. Output ONLY the translation, no explanations:\n\n{request.text}",
        "explain": f"Explain the following text in simple terms. Be concise:\n\n{request.text}",
        "polish": f"Polish and improve the following text. Keep the same meaning but make it clearer and more professional. Output ONLY the improved text:\n\n{request.text}",
        "summarize": f"Summarize the following text in 1-2 sentences. Output ONLY the summary:\n\n{request.text}",
        "expand": f"Expand on the following text with more details and examples. Keep the same style:\n\n{request.text}",
        "fix_grammar": f"Fix any grammar or spelling errors in the following text. Output ONLY the corrected text:\n\n{request.text}",
        "ask": f"Based on the following text, answer the user's question.\n\nText:\n{request.text}\n\nQuestion: {request.question or 'What is this about?'}\n\nProvide a helpful, concise answer:",
    }
    prompt = action_prompts.get(request.action)
    if not prompt:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
    return prompt

@router.post("/process-text/stream")
async def process_text_stream(request: TextProcessRequest):
    """
    Stream lightweight text processing for selected text.
    Returns Server-Sent Events: {"delta":"..."} chunks + [DONE].
    """
    from core.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    import json

    prompt = _build_text_process_prompt(request)

    async def generate():
        try:
            llm = get_llm()
            full_text = ""
            async for chunk in llm.astream([
                SystemMessage(content="You are a helpful text processing assistant. Follow instructions precisely. Do NOT use emoji in your output."),
                HumanMessage(content=prompt)
            ]):
                piece = getattr(chunk, "content", "")
                if isinstance(piece, list):
                    text_parts = []
                    for item in piece:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    piece = "".join(text_parts)
                if not isinstance(piece, str):
                    piece = str(piece or "")
                if not piece:
                    continue

                full_text += piece
                yield f"data: {json.dumps({'delta': piece}, ensure_ascii=False)}\n\n"

            final_text = full_text.strip()
            if final_text.startswith("```"):
                lines = final_text.split("\n")
                final_text = "\n".join(lines[1:-1]) if lines and lines[-1] == "```" else "\n".join(lines[1:])
            yield f"data: {json.dumps({'final': final_text}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            safe_print(f"[API] Text process stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/process-text")
async def process_text(request: TextProcessRequest):
    """
    Lightweight text processing for selected text.
    Does NOT go through the full agent - direct LLM call for speed.
    Returns processed text that can be used to replace selection.
    """
    from core.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    
    prompt = _build_text_process_prompt(request)
    
    try:
        llm = get_llm()
        response = await llm.ainvoke([
            SystemMessage(content="You are a helpful text processing assistant. Follow instructions precisely. Do NOT use emoji in your output."),
            HumanMessage(content=prompt)
        ])
        
        result = response.content.strip()
        
        # Clean up any markdown code blocks if present
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
        
        return {
            "original": request.text,
            "processed": result,
            "action": request.action
        }
    except Exception as e:
        safe_print(f"[API] Text process error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

