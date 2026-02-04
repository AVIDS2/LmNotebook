"""
Note Worker - Handles CRUD operations on notes.
Can create, update, and manage notes based on agent decisions.
"""
from typing import Dict, Any, Callable, List
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from services.note_service import NoteService


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', errors='replace').decode('gbk'))


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
        safe_print(f"[NOTE] Note Worker Intent: {intent}")
        
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
            
            # Chat after action
            human_msg = await _chat_after_action(llm, "create", context=f"Created note: {title}")
            
            response = json.dumps({
                "tool_call": "note_created",
                "note_id": note["id"],
                "title": title,
                "message": human_msg
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
            
            # If there's a description/instruction, use LLM to modify OR generate the content
            edit_desc = intent.get("description")
            if edit_desc:
                from langchain_core.messages import SystemMessage
                
                # HEURISTIC REMOVED: Now relying on LLM's "force_rewrite" flag
                if intent.get("force_rewrite", False):
                    safe_print(f"[WARN] Force Overwrite triggered by LLM intent.")
                    note_context = "" # FORCE EMPTY CONTEXT
            
                if note_context and len(note_context) > 10:
                    sys_prompt = "你是一个精确的文本编辑助手。你的任务是根据用户的修改要求对笔记进行**局部更新**。\n关键规则：\n1. **保持稳定性**：除非用户明确要求删除或重写整个笔记，否则必须保留当前内容中与指令无关的所有部分。\n2. **精确修改**：只针对指令提及的段落、标题或句子进行操作。\n3. **拒绝覆盖**：严禁在未获明确授权的情况下擅自把内容简化成只有一小部分内容。"
                    user_content = f"### 原始笔记内容 (必须作为基础保存)：\n{note_context}\n\n### 修改指令 (仅执行此处操作)：\n{edit_desc}"
                else:
                    sys_prompt = "你是一个笔记内容生成助手。用户希望重写或填充这篇笔记的内容。请根据要求生成完整的、结构清晰的 Markdown 笔记内容。"
                    user_content = f"写作要求：\n{edit_desc}\n\n请直接生成内容，不要有开场白。"

                edit_response = await llm.ainvoke([
                    SystemMessage(content=sys_prompt),
                    HumanMessage(content=user_content)
                ])
                new_content = edit_response.content.strip()
                
                # Clean up potential code blocks
                import re
                if new_content.startswith("```"):
                     new_content = re.sub(r'^```[a-z]*\n', '', new_content)
                     new_content = re.sub(r'\n```$', '', new_content)
                
                update_data["content"] = new_content

            elif intent.get("content"):
                update_data["content"] = intent["content"]

            await note_service.update_note(note_id=note_id, **update_data)
            
            # Send note_updated tool_call to refresh UI
            # If content was updated, we can also use format_apply logic to update editor immediately
            # Chat after action
            update_desc = f"Updated note {note_id}. "
            if "title" in update_data: update_desc += f"Changed title to {update_data['title']}. "
            if "content" in update_data: update_desc += "Rewrote content based on instructions. "
            
            human_msg = await _chat_after_action(llm, "update", context=update_desc)

            if "content" in update_data:
                response = json.dumps({
                    "tool_call": "format_apply", # Reuse format_apply to update editor UI directly
                    "formatted_html": update_data["content"],
                    "message": human_msg
                })
            else:
                response = json.dumps({
                    "tool_call": "note_updated",
                    "note_id": note_id,
                    "message": human_msg
                })
                
        elif intent["action"] == "delete":
            note_id = intent.get("note_id") or active_note_id
            if not note_id:
                response = "请告诉我你想删除哪篇笔记。如果是当前打开的笔记，直接说‘删除这篇’即可。"
            else:
                await note_service.delete_note(note_id)
                # Chat after action
                human_msg = await _chat_after_action(llm, "delete", context=f"Deleted note: {note_id}")
                
                response = json.dumps({
                    "tool_call": "note_deleted",
                    "note_id": note_id,
                    "message": human_msg
                })

        elif intent["action"] == "summarize":
            if note_context:
                summary = await _summarize_content(llm, note_context)
                response = json.dumps({
                    "tool_call": "note_summarized",
                    "content": summary,
                    "message": f"**Summary**:\n\n{summary}"
                })
            else:
                response = "I need to know which note you want to summarize. Please open a note first, or tell me the title."
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
        # Last 3 messages for richer context
        ctx = messages[-3:]
        history_ctx = "\n".join([f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content[:2000]}" for m in ctx])

    prompt = f"""<system>
分析用户的笔记操作意图。参考之前的对话上下文。

输出格式示例：
{{"action": "create", "title": "标题"}}
{{"action": "update", "title": "新标题", "description": "修改描述"}}
{{"action": "delete"}}
{{"action": "summarize"}}

规则：
1. **update**: 涉及内容的任何修改（包括**删除某句话**、**局部重写**、补充、纠错）。
   - 如果用户意图是**完全重写**、**更换主题**、**清空重来**或**由于主题不符需要推倒重写**（如“把这篇笔记改成X”），请设置 `"force_rewrite": true`。
   - 如果只是**局部微调**（如“修改第五章”、“把这段内容改一下”、“删除第一行”），**绝对禁止**设置 `force_rewrite` 为 true。
2. **重要规则**：如果用户要求“把笔记改写成X”或更换主题，**必须**在 JSON 中同时设置 `"title": "X"`，确保标题和新内容一致。
3. **delete**: 只有用户明确说“删除**这篇笔记**”、“删除**文件**”、“把这个笔记**移到回收站**”时，才是 delete。
4. **summarize**: 仅限“总结”、“摘要”。
5. **禁止输出正文**: JSON 中**不要**包含 `content` 字段。仅填写 `description` 让后续 Writer 生成。
6. 仅输出 JSON。
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


async def _chat_after_action(llm, action: str, context: str) -> str:
    """Generate a quick, natural human-like response after an action."""
    from langchain_core.messages import SystemMessage, HumanMessage
    
    prompt = f"""<system>
你是一个专业的笔记助手 Agent。你刚刚成功执行了一个操作（{action}）。
请生成一句自然、稍微带点个性的回复给用户。
不要只说“已完成”，要结合刚才的操作细节（Context）说点有用的。
比如：如果重写了笔记，可以说“搞定！这篇文章现在结构更清晰了，重点补充了XXX。”
语气：专业、热情、像个真人伙伴。
限制：50字以内。
</system>

Context:
{context}

Response:"""
    
    try:
        res = await llm.ainvoke([HumanMessage(content=prompt)])
        return res.content.strip().replace('"', '')
    except:
        return "操作已完成。"
