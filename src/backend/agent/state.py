"""
Agent state definition.
"""
from typing import TypedDict, List, Optional, Any


class AgentState(TypedDict, total=False):
    """
    State schema for the Agent.
    
    Attributes:
        messages: Conversation history
        note_context: Current note content for reference
        selected_text: User-selected text for operations
        worker_input: Input for the selected worker
        response: Final response to return
        tool_calls: List of tools that were called
    """
    messages: List[Any]
    note_context: Optional[str]
    selected_text: Optional[str]
    worker_input: str
    response: str
    tool_calls: List[str]

