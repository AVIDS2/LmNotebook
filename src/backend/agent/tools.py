"""
Standardized Toolset for the Origin Agent.
Converted from hardcoded workers into reusable, schema-defined tools.
"""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from services.note_service import NoteService
from services.rag_service import RAGService
import json

# Instantiate services
note_service = NoteService()
rag_service = RAGService()

@tool
async def search_knowledge(query: str) -> str:
    """
    Search across all user notes using semantic search.
    Use this when the user asks a question about their knowledge base, 
    asks 'what do I have on X', or needs to find related information.
    """
    print(f"[TOOL] Tool: search_knowledge -> {query}")
    results = await rag_service.search(query, top_k=5)
    if not results:
        return "No relevant notes found for this query."
    
    formatted = []
    for r in results:
        formatted.append(f"Title: {r['title']}\nID: {r.get('id', 'N/A')}\nSnippet: {r['content'][:300]}...")
    
    return "\n\n---\n\n".join(formatted)

@tool
async def read_note_content(note_id: str) -> str:
    """
    Read the full, detailed content of a specific note by its ID.
    Use this when you need the exact text of 'the current note' or a specific note found via search.
    """
    print(f"[TOOL] Tool: read_note_content -> {note_id}")
    note = await note_service.get_note(note_id)
    if not note:
        return f"Error: Note with ID {note_id} not found."
    
    content = note.get('plainText') or note.get('content') or ""
    return f"Title: {note['title']}\nContent:\n{content}"

@tool
async def list_recent_notes(limit: int = 8) -> str:
    """
    List the most recently updated or created notes.
    Use this when the user asks 'what did I write recently' or 'show all my notes'.
    """
    print(f"[TOOL] Tool: list_recent_notes -> limit={limit}")
    notes = await rag_service.list_all_notes(limit=limit)
    if not notes:
        return "There are no notes in the database yet."
    
    note_list = "\n".join([f"• 「{n['title']}」 (ID: {n['id']})" for n in notes])
    return f"Recent Notes:\n{note_list}"

@tool
async def update_note(note_id: str, instruction: str, force_rewrite: bool = False) -> str:
    """
    Update an existing note's content based on instructions.
    - note_id: The ID of the note to update.
    - instruction: Precise editing instructions (e.g. 'Add a paragraph about Rust', 'Fix typos in section 2').
    - force_rewrite: Set to True ONLY if the user wants to start over with a completely new topic.
    """
    print(f"[TOOL] Tool: update_note -> ID: {note_id}, Instr: {instruction}")
    
    # 1. Fetch current content
    note = await note_service.get_note(note_id)
    if not note:
        return f"Error: Note {note_id} not found."
    
    current_content = note.get('plainText') or note.get('content') or ""
    
    # 2. Heuristic check for "Clear" intent to avoid LLM "formatting" it as a summary
    destructive_keywords = ["清空", "删除所有内容", "clear all", "empty content"]
    if any(k in instruction.lower() for k in destructive_keywords) and not force_rewrite:
        new_content = "" # Completely empty
        if "保留标题" in instruction or "标题" in instruction:
            new_content = f"# {note.get('title', 'Untitled')}\n\n(内容已清空)"
        
        await note_service.update_note(note_id=note_id, content=new_content)
        return f"Successfully updated note 「{note['title']}」. (Note content cleared as requested)"

    # 3. Reasoning for the Edit
    from core.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    llm = get_llm()
    
    if force_rewrite:
        sys_prompt = "你是一个创意写作助手。输出要求：仅输出 Markdown 正文，严禁包含任何如“好的”、“这是修改后的视频”等开场白或解释。"
        user_prompt = f"写作要求：{instruction}"
    else:
        sys_prompt = """你是一个精确的文本编辑助手。
规则：
1. 仅输出最终完成修改后的 Markdown 完整正文。
2. 严禁包含任何如“好的”、“已为您完成”、“Editor Synchronized”等解释性文字、开场白或结尾总结。
3. 如果指令要求清空或删除，请输出空字符串。
4. 保持原有 Markdown 格式的严谨性。"""
        user_prompt = f"### 原始内容：\n{current_content}\n\n### 修改指令：\n{instruction}\n\n请直接输出修改后的全文本内容："

    response = await llm.ainvoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
    new_content = response.content.strip()
    
    # Anti-Chatter Safety: If model outputs conversational filler like "Here is your update:", strip it.
    # A common pattern is triple backticks or leading sentences.
    if new_content.startswith("```markdown"):
        new_content = new_content.split("```markdown")[1].split("```")[0].strip()
    elif new_content.startswith("```"):
        new_content = new_content.split("```")[1].split("```")[0].strip()
    
    # 3. Persistence
    await note_service.update_note(note_id=note_id, content=new_content)
    
    return f"Successfully updated note 「{note['title']}」. The user can now see the changes in the editor."

@tool
async def create_note(title: str, content: str) -> str:
    """
    Create a brand new note with a title and content.
    Use this when the user explicitly asks to 'create a note' or 'save this as a note'.
    """
    print(f"[TOOL] Tool: create_note -> {title}")
    note = await note_service.create_note(title=title, content=content)
    return f"Successfully created note 「{title}」 with ID: {note['id']}"

@tool
async def delete_note(note_id: str) -> str:
    """
    Delete a specific note by its ID.
    Use this ONLY when the user explicitly asks to 'delete', 'remove', or 'trash' a note.
    """
    print(f"[TOOL] Tool: delete_note -> {note_id}")
    success = await note_service.delete_note(note_id)
    if success:
        return f"Successfully deleted note {note_id}."
    return f"Error: Failed to delete note {note_id}. It might not exist."

def get_all_agent_tools():
    """Returns a list of tools for the LLM to use."""
    return [
        search_knowledge,
        read_note_content,
        list_recent_notes,
        update_note,
        create_note,
        delete_note
    ]
