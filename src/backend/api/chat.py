"""
Chat API endpoints.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from agent.supervisor import AgentSupervisor

router = APIRouter()


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

    @property
    def history_dicts(self) -> List[dict]:
        return [{"role": m.role, "content": m.content} for m in self.history]


class ChatResponse(BaseModel):
    """Chat response payload."""
    response: str = Field(..., description="Agent response")
    tool_calls: List[str] = Field(default_factory=list, description="Tools that were called")


@router.post("/invoke", response_model=ChatResponse)
async def invoke_agent(request: ChatRequest):
    """
    Invoke the agent with a user message.
    Returns the complete response after processing.
    """
    try:
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
        print(f"❌ Chat API Error: {e}")
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
            supervisor = AgentSupervisor()
            print(f">> Starting stream for: {request.message[:50]}... (Session: {request.session_id})")
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
                use_knowledge=request.use_knowledge
            ):
                chunk_count += 1
                elapsed = time.time() - start_time
                print(f">> Chunk #{chunk_count} at {elapsed:.2f}s: {repr(chunk[:30] if len(chunk) > 30 else chunk)}")
                
                # Check if chunk is already a JSON message (status, tool_call, or text)
                if isinstance(chunk, str) and chunk.startswith('{'):
                    yield f"data: {chunk}\n\n"
                else:
                    # Fallback for any raw text (shouldn't happen now)
                    encoded = json.dumps({"text": chunk})
                    yield f"data: {encoded}\n\n"
            print(f">> Stream complete: {chunk_count} chunks in {time.time() - start_time:.2f}s")
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"X Stream error: {e}")
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
        print(f"[API] Error getting checkpoint messages: {e}")
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
        print(f"[API] Error listing sessions: {e}")
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
        print(f"[API] Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
