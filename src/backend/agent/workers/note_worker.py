"""
Note Worker - Handles CRUD operations on notes.
Can create, update, and manage notes based on agent decisions.
"""
from typing import Dict, Any, Callable, List
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from services.note_service import NoteService


NOTE_SYSTEM_PROMPT = """你是笔记管理专家。你可以帮助用户创建、编辑和管理他们的笔记。

## 你可以执行的操作：
1. **创建笔记**: 根据用户的要求创建新笔记
2. **更新笔记**: 修改现有笔记的内容
3. **总结**: 将多个笔记内容总结成一个新笔记

## 输出格式：
- 成功后告诉用户操作结果
- 如果需要更多信息，礼貌地询问用户
"""


def create_note_worker(llm) -> Callable:
    """
    Create a Note Worker for note CRUD operations.
    """
    note_service = NoteService()
    
    async def note_worker(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute note operations."""
        messages = state.get("messages", [])
        worker_input = state.get("worker_input", "")
        note_context = state.get("note_context", "")
        active_note_id = state.get("active_note_id")
        
        # Parse the intent from worker input with history
        intent = await _parse_note_intent(llm, worker_input, messages)
        print(f"📝 Note Worker Intent: {intent}")
        
        import json
        
        if intent["action"] == "create":
            title = intent.get("title", "新笔记")
            content = intent.get("content", "") or intent.get("content_hint", "")
            
            if not content and worker_input:
                content = await _generate_note_content(llm, worker_input, messages)
            
            note = await note_service.create_note(
                title=title,
                content=content,
                category_id=intent.get("category_id")
            )
            
            response = json.dumps({
                "tool_call": "note_created",
                "note_id": note["id"],
                "title": title,
                "message": f"✅ 已成功创建笔记「{title}」！"
            })
            
        elif intent["action"] == "update":
            note_id = intent.get("note_id") or active_note_id
            
            if not note_id:
                return {
                    "response": "请指定要更新的笔记。你可以先打开一篇笔记。",
                    "messages": messages + [AIMessage(content="请指定要更新的笔记。")]
                }
            
            update_data = {}
            if intent.get("title"):
                update_data["title"] = intent["title"]
            
            # If there's a description/instruction, use LLM to modify the content
            edit_desc = intent.get("description")
            if edit_desc and note_context:
                from langchain_core.messages import SystemMessage
                edit_prompt = f"""<system>
你是一个精确的文本编辑助手。根据用户的指令，修改当前的笔记内容。
保持原有的 Markdown 格式。只返回修改后的全部新内容，不要有说明文字。

当前内容：
{note_context}

修改要求：
{edit_desc}
</system>
新的完整内容："""
                edit_response = await llm.ainvoke([HumanMessage(content=edit_prompt)])
                new_content = edit_response.content.strip()
                # Clean up potential code blocks returned by LLM
                if new_content.startswith("```"):
                     import re
                     new_content = re.sub(r'^```[a-z]*\n', '', new_content)
                     new_content = re.sub(r'\n```$', '', new_content)
                
                update_data["content"] = new_content

            elif intent.get("content"):
                update_data["content"] = intent["content"]

            await note_service.update_note(note_id=note_id, **update_data)
            
            # Send note_updated tool_call to refresh UI
            # If content was updated, we can also use format_apply logic to update editor immediately
            response_msg = "✅ 笔记已更新！"
            if "content" in update_data:
                response = json.dumps({
                    "tool_call": "format_apply", # Reuse format_apply to update editor UI directly
                    "formatted_html": update_data["content"],
                    "message": "✅ 内容已按要求修改并应用！"
                })
            else:
                response = json.dumps({
                    "tool_call": "note_updated",
                    "note_id": note_id,
                    "message": response_msg
                })
                
        elif intent["action"] == "delete":
            note_id = intent.get("note_id") or active_note_id
            if not note_id:
                response = "请告诉我你想删除哪篇笔记。如果是当前打开的笔记，直接说‘删除这篇’即可。"
            else:
                await note_service.delete_note(note_id)
                response = json.dumps({
                    "tool_call": "note_deleted",
                    "note_id": note_id,
                    "message": "🗑️ 笔记已成功移至回收站。"
                })

        elif intent["action"] == "summarize":
            if note_context:
                summary = await _summarize_content(llm, note_context)
                response = json.dumps({
                    "tool_call": "note_summarized",
                    "content": summary,
                    "message": f"📋 **内容摘要**：\n\n{summary}"
                })
            else:
                response = "请先打开一篇笔记，我才能帮你总结。"
        else:
            response = "请告诉我你想对笔记做什么操作：创建、修改、删除或总结？"
        
        return {
            "response": response,
            "messages": messages + [AIMessage(content=response)],
        }
    
    return note_worker


async def _parse_note_intent(llm, input_text: str, messages: List[Any] = None) -> Dict[str, Any]:
    """Parse user intent for note operations with context."""
    history_ctx = ""
    if messages:
        # Last 2 messages for quick context
        ctx = messages[-2:]
        history_ctx = "\n".join([f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content[:200]}" for m in ctx])

    prompt = f"""<system>
分析用户的笔记操作意图。参考之前的对话上下文。

输出格式示例：
{{"action": "create", "title": "标题"}}
{{"action": "update", "title": "新标题", "description": "修改描述"}}
{{"action": "delete"}}
{{"action": "summarize"}}

规则：
1. 如果用户描述了具体的编辑行为，路由到 update。
2. 如果是创建笔记但没给名字，请基于上下文推断一个合适的标题。
3. 仅输出 JSON。
</system>

<context>
{history_ctx}
</context>

User Message: {input_text}
Plan:"""
    
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        import json
        import re
        content = response.content.strip()
        json_match = re.search(r'\{[^}]+\}', content)
        if json_match:
            return json.loads(json_match.group())
        return {"action": "unknown"}
    except:
        return {"action": "unknown"}


async def _generate_note_content(llm, request: str, messages: List[Any] = None) -> str:
    """Generate note content based on user request and conversation context."""
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    
    final_messages = [
        SystemMessage(content="你是一个笔记助手。基于用户的要求和之前的对话上下文，生成结构化的笔记内容。使用 Markdown 格式，包含标题、列表等。如果用户提到'之前的内容'或'这个知识点'，请参考对话历史。对于数学公式，请优先使用 LaTeX 格式。"),
    ]
    
    if messages:
        # Include last few messages for context
        history = (messages or [])[-6:]
        for m in history:
            if isinstance(m, (HumanMessage, AIMessage)):
                final_messages.append(m)
            
    # Add current request if not already at the end
    if not messages or messages[-1].content != request:
        final_messages.append(HumanMessage(content=request))
    
    result = await llm.ainvoke(final_messages)
    return result.content


async def _summarize_content(llm, content: str) -> str:
    """Summarize note content."""
    from langchain_core.messages import SystemMessage, HumanMessage
    messages = [
        SystemMessage(content="将以下内容总结成简洁的摘要，保留关键信息。"),
        HumanMessage(content=content)
    ]
    result = await llm.ainvoke(messages)
    return result.content
