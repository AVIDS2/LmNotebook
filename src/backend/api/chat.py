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


class ChatRequest(BaseModel):
    """Chat request payload."""
    message: str = Field(..., description="User message")
    history: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
    note_context: Optional[str] = Field(None, description="Current note content for context")
    selected_text: Optional[str] = Field(None, description="User-selected text for formatting")
    active_note_id: Optional[str] = Field(None, description="Current note ID")

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
            print(f">> Starting stream for: {request.message[:50]}...")
            async for chunk in supervisor.invoke_stream(
                message=request.message,
                history=request.history_dicts, 
                note_context=request.note_context,
                selected_text=request.selected_text,
                active_note_id=request.active_note_id
            ):
                chunk_count += 1
                elapsed = time.time() - start_time
                print(f">> Chunk #{chunk_count} at {elapsed:.2f}s: {repr(chunk[:30] if len(chunk) > 30 else chunk)}")
                
                # Check if chunk is a JSON control message (status or tool_call)
                if isinstance(chunk, str) and (chunk.startswith('{"type":') or chunk.startswith('{"tool_call":')):
                    yield f"data: {chunk}\n\n"
                else:
                    # Normal text chunk
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
