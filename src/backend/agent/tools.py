"""
Standardized Toolset for the Origin Agent.
Converted from hardcoded workers into reusable, schema-defined tools.
"""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from services.note_service import NoteService
from services.rag_service import RAGService
import json
import re
import markdown
import html as html_lib

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

# Instantiate services
note_service = NoteService()
rag_service = RAGService()


def _count_markdown_structures(text: str) -> dict:
    if not text:
        return {"headings": 0, "lists": 0, "tables": 0, "code_fences": 0}
    headings = len(re.findall(r"(?m)^\s{0,3}#{1,6}\s+\S", text))
    lists = len(re.findall(r"(?m)^\s{0,3}(?:[-*+]|\d+\.)\s+\S", text))
    table_rows = len(re.findall(r"(?m)^\s*\|.+\|\s*$", text))
    code_fences = len(re.findall(r"(?m)^\s*```", text))
    return {"headings": headings, "lists": lists, "tables": table_rows, "code_fences": code_fences}


def _looks_like_structure_regression(original: str, edited: str) -> bool:
    """
    Guardrail: if original has clear markdown structure and edited collapses to plain text,
    force one strict retry before persisting.
    """
    if not original or not edited:
        return False
    if len(original) < 160:
        return False

    before = _count_markdown_structures(original)
    after = _count_markdown_structures(edited)

    # If source had meaningful structure, but output lost nearly all structure.
    had_structure = (
        before["headings"] >= 1
        or before["lists"] >= 3
        or before["tables"] >= 2
        or before["code_fences"] >= 2
    )
    collapsed = (
        after["headings"] == 0
        and after["lists"] <= 1
        and after["tables"] == 0
        and after["code_fences"] == 0
    )
    return had_structure and collapsed


def _html_to_editable_text(html_content: str) -> str:
    """
    Convert stored HTML into a readable multiline text fallback for editing/matching.
    This is only used when markdownSource is missing.
    """
    if not html_content:
        return ""
    text = html_content
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|li|tr|h[1-6]|blockquote|pre|table|ul|ol)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

@tool
async def search_knowledge(query: str) -> str:
    """
    Search across all user notes using semantic search.
    Use this when the user asks a question about their knowledge base, 
    asks 'what do I have on X', or needs to find related information.
    
    Returns note previews with content. For simple Q&A, the preview may be enough.
    Only call read_note_content if you need the COMPLETE content for detailed analysis.
    """
    safe_print(f"[TOOL] Tool: search_knowledge -> {query}")
    results = await rag_service.search(query, top_k=5)
    if not results:
        return "No relevant notes found for this query."
    
    formatted = []
    for r in results:
        # Return more content (1500 chars) to reduce need for read_note_content
        content_preview = r['content'][:1500] + "..." if len(r['content']) > 1500 else r['content']
        formatted.append(f"Title: {r['title']}\nID: {r.get('id', 'N/A')}\nContent: {content_preview}")
    
    result_text = "\n\n---\n\n".join(formatted)
    return f"{result_text}\n\n[NOTE: If content is truncated (...), use read_note_content(note_id) for full text.]"

@tool
async def read_note_content(note_id: str) -> str:
    """
    Read the full, detailed content of a specific note by its ID.
    Use this when you need the exact text of 'the current note' or a specific note found via search.
    """
    safe_print(f"[TOOL] Tool: read_note_content -> {note_id}")
    note = await note_service.get_note(note_id)
    if not note:
        return f"Error: Note with ID {note_id} not found."
    
    # Prefer markdownSource so the agent sees real structure (headings/lists/tables).
    content = (
        note.get('markdownSource')
        or note.get('plainText')
        or _html_to_editable_text(note.get('content') or "")
        or ""
    )
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
    safe_print(f"[TOOL] Tool: rename_note -> ID: {note_id}, New Title: {new_title}")
    
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
    safe_print(f"[TOOL] Tool: list_recent_notes -> limit={limit}")
    notes = await rag_service.list_all_notes(limit=limit)
    if not notes:
        return "There are no notes in the database yet."
    
    note_list = "\n".join([f"- {n['title']} (ID: {n['id']})" for n in notes])
    return f"Recent Notes:\n{note_list}"

@tool
async def update_note(note_id: str, instruction: str, force_rewrite: bool = False) -> str:
    """
    Update an existing note's content based on instructions.
    - note_id: The ID of the note to update.
    - instruction: Precise editing instructions (e.g., 'Add a paragraph', 'Fix typo').
    - force_rewrite: Set to True ONLY if the user wants to start over with a new topic.
    
    SPECIAL CASE - FORMAT/ORGANIZE INSTRUCTIONS:
    When the instruction contains words like "鏁寸悊鏍煎紡", "format", "organize", "鎺掔増":
    - DO NOT change any original text content
    - DO NOT add, remove, or modify any words
    - ONLY adjust: headings, bullet points, spacing, code blocks, emphasis
    - Create clear visual hierarchy with proper Markdown structure
    - Preserve ALL original information exactly as written
    """
    safe_print(f"[TOOL] Tool: update_note -> ID: {note_id}, Instr: {instruction}")
    
    # 1. Fetch current content
    note = await note_service.get_note(note_id)
    if not note:
        return f"Error: Note {note_id} not found."
    
    # CRITICAL: use markdownSource as the editing baseline to preserve Markdown layout.
    # plainText is whitespace-collapsed and will destroy structure if used as source.
    current_content = (
        note.get('markdownSource')
        or _html_to_editable_text(note.get('content') or "")
        or note.get('plainText')
        or ""
    )
    html_content_original = note.get('content') or ""
    
    # IMAGE PRESERVATION: Extract existing images from HTML content
    image_pattern = r'<img[^>]+>'
    existing_img_tags = re.findall(image_pattern, html_content_original)
    if existing_img_tags:
        safe_print(f"[TOOL] Found {len(existing_img_tags)} existing image(s) to preserve")
    
    # 2. Heuristic check for "Clear" intent
    destructive_keywords = ["clear all", "empty content"]
    destructive_keywords_cn = ["清空", "删除所有内容"]
    all_destructive = destructive_keywords + destructive_keywords_cn
    
    if any(k in instruction.lower() for k in all_destructive) and not force_rewrite:
        html_result = ""
        # Preserve images unless explicitly asked to remove them
        if existing_img_tags and "image" not in instruction.lower():
            for img_tag in existing_img_tags:
                html_result += f"<p>{img_tag}</p>\n"
        
        await note_service.update_note(note_id=note_id, content=html_result, markdown_source="")
        return f"Successfully updated note (ID: {note_id}). (Content cleared, images preserved)"

    # 3. LLM Edit
    from core.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    llm = get_llm()
    
    if force_rewrite:
        sys_prompt = "You are a creative writing assistant. Output only Markdown content, no explanations."
        user_prompt = f"Writing request: {instruction}"
    else:
        sys_prompt = """You are a precise text editing assistant.

RULES:
1. Output ONLY the final edited Markdown content.
2. NO explanations, greetings, or summaries.
3. If asked to clear/delete, output empty string.
4. Preserve Markdown formatting.
5. Do NOT handle images - they are preserved automatically.

SPECIAL RULE FOR FORMAT/ORGANIZE REQUESTS:
If the user asks to "format", "organize", "tidy up", "鏁寸悊鏍煎紡", "鎺掔増", or similar:
- DO NOT change any text content (no adding, removing, or rephrasing words)
- ONLY adjust structure: headings, lists, code blocks, emphasis, spacing
- Create clear visual hierarchy
- The output must contain the EXACT same words as input
- IMPORTANT: Preserve semantic relationships between text blocks.
- IMPORTANT: For table-like data, keep row/column mapping exactly:
  - Do NOT swap cells across rows/columns
  - Keep header-value alignment unchanged
  - Do NOT merge/split rows unless it is pure syntax normalization with identical meaning
- IMPORTANT: If content is already a valid table, keep the same data model and only normalize Markdown syntax.
- IMPORTANT: If you see repeating patterns that look like table data (e.g., header words followed by corresponding values in groups), reconstruct them as Markdown tables using | syntax while preserving original mappings exactly."""
        user_prompt = f"Original content:\n---\n{current_content}\n---\nEdit instruction: {instruction}\n\nOutput the edited content directly:"

    response = await llm.ainvoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
    new_content = response.content.strip()

    if (not force_rewrite) and _looks_like_structure_regression(current_content, new_content):
        safe_print("[TOOL] Detected markdown structure regression, retrying with stricter preservation prompt")
        strict_sys_prompt = sys_prompt + """

STRICT OUTPUT QUALITY GATE:
- Keep Markdown structure readable and renderable.
- Preserve headings, lists, and tables when they exist in source.
- Never flatten the entire note into one plain paragraph.
- Return ONLY Markdown content, no commentary."""
        retry = await llm.ainvoke([SystemMessage(content=strict_sys_prompt), HumanMessage(content=user_prompt)])
        retry_content = retry.content.strip()
        if retry_content:
            new_content = retry_content
    
    # Strip markdown code blocks if present
    if new_content.startswith("```markdown"):
        new_content = new_content.split("```markdown")[1].split("```")[0].strip()
    elif new_content.startswith("```"):
        new_content = new_content.split("```")[1].split("```")[0].strip()
    
    # Clean up excessive blank lines
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)
    
    # Convert Markdown -> HTML
    html_content = markdown.markdown(new_content, extensions=['fenced_code', 'tables'])
    html_content = re.sub(r'<p>\s*</p>', '', html_content)
    
    # IMAGE PRESERVATION: Append existing images at the end
    if existing_img_tags:
        safe_print(f"[TOOL] Preserving {len(existing_img_tags)} image(s) in updated content")
        for img_tag in existing_img_tags:
            html_content += f"\n<p>{img_tag}</p>"
    
    await note_service.update_note(note_id=note_id, content=html_content, markdown_source=new_content)
    
    return f"Successfully updated note (ID: {note_id}). [SYSTEM: DO NOT output the note content.]"

@tool
async def create_note(title: str, content: str = "", category_id: Optional[str] = None) -> str:
    """
    Create a brand new note with a title and content.
    - title: Clear, concise title for the note.
    - content: Full note body in Markdown. (Only create content the user asked for).
    - category_id: Optional category ID to assign on creation. Use list_categories first.
    """
    safe_print(f"[TOOL] Tool: create_note -> {title} (category_id={category_id or 'none'})")
    
    if not content.strip():
        content = f"# {title}\n\n（待补充内容）"

    # Fix: Clean up excessive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # CRITICAL FIX: Convert Markdown -> HTML
    html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
    
    # Fix: Remove empty <p> tags
    html_content = re.sub(r'<p>\s*</p>', '', html_content)

    normalized_category_id = (category_id or "").strip() or None
    category_name = None
    if normalized_category_id:
        categories = await note_service.get_all_categories()
        category_map = {str(c.get("id", "")): str(c.get("name", "")) for c in categories}
        if normalized_category_id not in category_map:
            valid_ids = ", ".join(f'"{cid}"' for cid in category_map.keys())
            return (
                f"Error: Category '{normalized_category_id}' does not exist. "
                f"Use a valid category_id from list_categories. Valid IDs: {valid_ids}"
            )
        category_name = category_map[normalized_category_id]

    note = await note_service.create_note(
        title=title,
        content=html_content,
        markdown_source=content,
        category_id=normalized_category_id,
    )

    if normalized_category_id:
        return (
            f"Successfully created note with ID: {note['id']} "
            f"and assigned category: {category_name}"
        )
    return f"Successfully created note with ID: {note['id']}"

@tool
async def delete_note(note_id: str) -> str:
    """
    Delete a specific note by its ID.
    Use this ONLY when the user explicitly asks to 'delete', 'remove', or 'trash' a note.
    """
    safe_print(f"[TOOL] Tool: delete_note -> {note_id}")
    success = await note_service.delete_note(note_id)
    if success:
        return f"Successfully deleted note {note_id}."
    return f"Error: Failed to delete note {note_id}. It might not exist."


@tool
async def patch_note(note_id: str, old_text: str, new_text: str) -> str:
    """
    Replace specific text in a note using search & replace (diff-style editing).
    This is more efficient than update_note for small, targeted changes.
    
    - note_id: The ID of the note to patch
    - old_text: The EXACT text to find and replace (must match exactly, including whitespace)
    - new_text: The replacement text
    
    Use this for:
    - Fixing typos
    - Replacing specific words or phrases
    - Small targeted edits
    
    For large rewrites or formatting changes, use update_note instead.
    """
    safe_print(f"[TOOL] Tool: patch_note -> ID: {note_id}, Replace: '{old_text[:30]}...' with '{new_text[:30]}...'")
    
    note = await note_service.get_note(note_id)
    if not note:
        return f"Error: Note {note_id} not found."
    
    # Get both HTML content and plain text
    html_content = note.get('content') or ""
    plain_text = _html_to_editable_text(html_content) or note.get('plainText') or ""
    markdown_source = note.get('markdownSource') or ""
    
    # Best path: patch markdownSource directly to preserve structure.
    if markdown_source and old_text in markdown_source:
        updated_md = markdown_source.replace(old_text, new_text, 1)
        updated_html = markdown.markdown(updated_md, extensions=['fenced_code', 'tables'])
        updated_html = re.sub(r'<p>\s*</p>', '', updated_html)
        await note_service.update_note(note_id=note_id, content=updated_html, markdown_source=updated_md)
        return f"Successfully patched note (ID: {note_id}). Replaced '{old_text[:30]}...' with '{new_text[:30]}...'"

    # Try to find in plain text or html
    if old_text not in plain_text and old_text not in html_content:
        # Fuzzy match attempt: try with normalized whitespace
        import re
        normalized_old = re.sub(r'\s+', ' ', old_text.strip())
        normalized_plain = re.sub(r'\s+', ' ', plain_text)
        
        if normalized_old not in normalized_plain:
            return f"Error: Could not find the text '{old_text[:50]}...' in the note. Make sure it matches exactly."
    
    # Replace in HTML content (preserves formatting)
    if old_text in html_content:
        updated_html = html_content.replace(old_text, new_text, 1)
        # We patched HTML directly and cannot guarantee markdown_source consistency.
        # Clear markdown_source to avoid stale source being read by the agent later.
        updated_md = None
    else:
        # If not found in HTML directly, we need to be more careful
        # This can happen when HTML has tags breaking up the text
        # For safety, do a simple replacement in plain text and regenerate
        updated_plain = plain_text.replace(old_text, new_text, 1)
        # Convert back to simple HTML paragraphs
        updated_html = ''.join(f'<p>{line}</p>' for line in updated_plain.split('\n') if line.strip())
        updated_md = updated_plain
    
    await note_service.update_note(note_id=note_id, content=updated_html, markdown_source=updated_md)
    
    return f"Successfully patched note (ID: {note_id}). Replaced '{old_text[:30]}...' with '{new_text[:30]}...'"

@tool
async def list_categories() -> str:
    """
    List all available categories that notes can be organized into.
    Use this when you need to know what categories exist, or when the user asks about their categories.
    IMPORTANT: When using set_note_category, you MUST use the exact category_id returned here.
    """
    safe_print(f"[TOOL] Tool: list_categories")
    categories = await note_service.get_all_categories()
    if not categories:
        return "No categories exist yet. The user can create categories in the sidebar."
    
    cat_list = "\n".join([f"- {c['name']} -> category_id: \"{c['id']}\"" for c in categories])
    return f"Available Categories (use the category_id value for set_note_category):\n{cat_list}"

@tool
async def set_note_category(note_id: str, category_id: str) -> str:
    """
    Assign a category/tag to a note for organization.
    - note_id: The ID of the note to categorize.
    - category_id: The exact ID of the category to assign. Use list_categories first.
    - TO REMOVE A CATEGORY: Pass an empty string "" as the category_id.
    """
    safe_print(f"[TOOL] Tool: set_note_category -> Note: {note_id}, Category: '{category_id}'")
    
    # Handle 'clear category' intent
    if not category_id or category_id.lower() in ["none", "null", "undefined"]:
        success = await note_service.set_note_category(note_id, None)
        if success:
            safe_print("[TOOL] Successfully cleared category (set to Uncategorized)")
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
        return f"Successfully assigned note to category: {cat_name}"
    
    return f"Error: Failed to update note {note_id}. Note might not exist or is in trash."

def get_all_agent_tools():
    """Returns a list of tools for the LLM to use."""
    return [
        search_knowledge,
        read_note_content,
        rename_note,
        list_recent_notes,
        update_note,
        patch_note,  # New: diff-style editing
        create_note,
        delete_note,
        list_categories,
        set_note_category
    ]
