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
    # Add instruction to prevent LLM from repeating content in response
    return f"Title: {note['title']}\nContent:\n{content}\n\n[SYSTEM: Content retrieved successfully. DO NOT repeat this content in your response.]"

@tool
async def rename_note(note_id: str, new_title: str) -> str:
    """
    Rename a note's title (NOT the content).
    Use this when the user wants to change the note's name/title.
    - note_id: The ID of the note to rename.
    - new_title: The new title for the note.
    
    NOTE: This changes the note's TITLE, not its content. 
    To modify content, use update_note instead.
    """
    print(f"[TOOL] Tool: rename_note -> ID: {note_id}, New Title: {new_title}")
    
    note = await note_service.get_note(note_id)
    if not note:
        return f"Error: Note {note_id} not found."
    
    old_title = note.get('title', 'Untitled')
    await note_service.update_note(note_id=note_id, title=new_title)
    
    return f"Successfully renamed note from '{old_title}' to '{new_title}'"

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
    - instruction: Precise editing instructions (e.g., 'Add a paragraph', 'Fix typo').
    - force_rewrite: Set to True ONLY if the user wants to start over with a new topic.
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
        user_prompt = f"待修改的原始内容：\n---\n{current_content}\n---\n修改指令：{instruction}\n\n请直接输出修改后的全文本内容，严禁包含任何前言、摘要或 Markdown 以外的解释性文字："

    response = await llm.ainvoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
    new_content = response.content.strip()
    
    # Anti-Chatter Safety: If model outputs conversational filler like "Here is your update:", strip it.
    # A common pattern is triple backticks or leading sentences.
    if new_content.startswith("```markdown"):
        new_content = new_content.split("```markdown")[1].split("```")[0].strip()
    elif new_content.startswith("```"):
        new_content = new_content.split("```")[1].split("```")[0].strip()
    
    # Fix: Clean up excessive blank lines (reduce to max 1 blank line between paragraphs)
    import re
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)  # 3+ newlines → 2 newlines (1 blank line)
    
    # 3. Persistence
    # CRITICAL FIX: Convert Markdown -> HTML before saving
    import markdown
    html_content = markdown.markdown(new_content, extensions=['fenced_code', 'tables'])
    
    # Fix: Remove empty <p> tags that cause excessive spacing
    html_content = re.sub(r'<p>\s*</p>', '', html_content)
    
    await note_service.update_note(note_id=note_id, content=html_content)
    
    return f"Successfully updated note (ID: {note_id}) 「{note['title']}」. The user can now see the changes in the editor. [SYSTEM: DO NOT output the note content. Just confirm the update briefly.]"

@tool
async def create_note(title: str, content: str) -> str:
    """
    Create a brand new note with a title and content.
    - title: Clear, concise title for the note.
    - content: Full note body in Markdown. (Only create content the user asked for).
    """
    print(f"[TOOL] Tool: create_note -> {title}")
    
    # Fix: Clean up excessive blank lines
    import re
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # CRITICAL FIX: Convert Markdown -> HTML
    import markdown
    html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
    
    # Fix: Remove empty <p> tags
    html_content = re.sub(r'<p>\s*</p>', '', html_content)
    
    note = await note_service.create_note(title=title, content=html_content)
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

@tool
async def list_categories() -> str:
    """
    List all available categories that notes can be organized into.
    Use this when you need to know what categories exist, or when the user asks about their categories.
    IMPORTANT: When using set_note_category, you MUST use the exact category_id returned here.
    """
    print(f"[TOOL] Tool: list_categories")
    categories = await note_service.get_all_categories()
    if not categories:
        return "No categories exist yet. The user can create categories in the sidebar."
    
    cat_list = "\n".join([f"• {c['name']} → category_id: \"{c['id']}\"" for c in categories])
    return f"Available Categories (use the category_id value for set_note_category):\n{cat_list}"

@tool
async def set_note_category(note_id: str, category_id: str) -> str:
    """
    Assign a category/tag to a note for organization.
    - note_id: The ID of the note to categorize.
    - category_id: The exact ID of the category to assign. Use list_categories first.
    - TO REMOVE A CATEGORY: Pass an empty string "" as the category_id.
    """
    print(f"[TOOL] Tool: set_note_category -> Note: {note_id}, Category: '{category_id}'")
    
    # Handle 'clear category' intent
    if not category_id or category_id.lower() in ["none", "null", "undefined"]:
        success = await note_service.set_note_category(note_id, None)
        if success:
            print("[TOOL] Successfully cleared category (set to Uncategorized)")
            return "Successfully removed category from note (it is now Uncategorized)."
        return f"Error: Failed to update note {note_id}."

    # Validate category exists
    categories = await note_service.get_all_categories()
    valid_ids = [c['id'] for c in categories]
    cat_names = {c['id']: c['name'] for c in categories}
    
    if category_id not in valid_ids:
        # Fallback: Check if AI passed a Name instead of an ID
        name_to_id = {c['name']: c['id'] for c in categories}
        if category_id in name_to_id:
            category_id = name_to_id[category_id]
        else:
            suggestions = ", ".join([f'"{cid}" ({cat_names[cid]})' for cid in valid_ids])
            return f"Error: Category '{category_id}' does not exist. Use a valid ID from list_categories or an empty string \"\" to remove. Valid IDs: {suggestions}"
    
    success = await note_service.set_note_category(note_id, category_id)
    if success:
        cat_name = cat_names.get(category_id, "Unknown")
        return f"Successfully assigned note to category 「{cat_name}」"
    
    return f"Error: Failed to update note {note_id}. Note might not exist or is in trash."

def get_all_agent_tools():
    """Returns a list of tools for the LLM to use."""
    return [
        search_knowledge,
        read_note_content,
        rename_note,
        list_recent_notes,
        update_note,
        create_note,
        delete_note,
        list_categories,
        set_note_category
    ]
