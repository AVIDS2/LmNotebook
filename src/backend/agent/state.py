"""
Agent State Definition for LangGraph 1.x.

This module defines the state schema using TypedDict with proper annotations
for the LangGraph StateGraph architecture.
"""
from typing import TypedDict, Annotated, Optional, List, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class NoteAgentState(TypedDict, total=False):
    """
    State schema for the Note Agent using LangGraph 1.x.
    
    Key Design Decisions:
    1. Uses `add_messages` reducer for automatic message accumulation
    2. Includes context fields for note-aware operations
    3. Has safety mechanisms for Doom Loop detection
    
    Attributes:
        messages: Conversation history with automatic message merging
        active_note_id: Current note being viewed/edited
        active_note_title: Title of the current note
        context_note_id: Explicitly referenced note ID (via @ mention)
        context_note_title: Title of the referenced note
        note_content: Current note content for context
        selected_text: User-selected text for operations
        intent: Routing intent ("CHAT" or "TASK")
        tool_call_count: Counter for Doom Loop detection
        last_tool_name: Last executed tool name
        last_tool_input_hash: Hash of last tool input (for duplicate detection)
        session_id: Server-side session identifier
        use_knowledge: Whether to force search knowledge base (@)
    """
    
    # Core message history - uses add_messages reducer for automatic accumulation
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Note context
    active_note_id: Optional[str]
    active_note_title: Optional[str]
    context_note_id: Optional[str]
    context_note_title: Optional[str]
    note_content: Optional[str]
    selected_text: Optional[str]
    
    # Routing control
    intent: str  # "CHAT" or "TASK"
    
    # Safety mechanisms (Doom Loop detection - inspired by OpenCode)
    tool_call_count: int
    last_tool_name: Optional[str]
    last_tool_input_hash: Optional[str]
    
    # Session management
    session_id: str
    
    # Feature flags
    use_knowledge: bool
    auto_accept_writes: bool
    agent_mode: str  # "ask" | "agent"
    write_authorized: Optional[bool]
    
    # Workflow state machine
    workflow_done: bool       # System-level task completion flag
    next_tool_call: Optional[dict]  # Single tool to execute (for chat-tool-chat pattern)


# Default state factory
def create_initial_state(
    session_id: str,
    active_note_id: Optional[str] = None,
    active_note_title: Optional[str] = None,
    context_note_id: Optional[str] = None,
    context_note_title: Optional[str] = None,
    note_content: Optional[str] = None,
    selected_text: Optional[str] = None,
    use_knowledge: bool = False,
    auto_accept_writes: bool = True,
    agent_mode: str = "agent",
) -> NoteAgentState:
    """Create an initial state with default values."""
    return NoteAgentState(
        messages=[],
        active_note_id=active_note_id,
        active_note_title=active_note_title,
        context_note_id=context_note_id,
        context_note_title=context_note_title,
        note_content=note_content,
        selected_text=selected_text,
        intent="TASK",  # Default to TASK, router will override
        tool_call_count=0,
        last_tool_name=None,
        last_tool_input_hash=None,
        session_id=session_id,
        use_knowledge=use_knowledge,
        auto_accept_writes=auto_accept_writes,
        agent_mode=agent_mode if agent_mode in {"ask", "agent"} else "agent",
        write_authorized=None,
        workflow_done=False,
        next_tool_call=None,
    )
