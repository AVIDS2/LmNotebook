"""
Knowledge Worker - Enterprise-grade Agentic RAG implementation.
Optimized for Gemini and intelligent retrieval.
"""
from typing import Dict, Any, Callable, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from core.config import settings
from services.rag_service import RAGService


# Enterprise Knowledge Worker Prompt
KNOWLEDGE_SYSTEM_PROMPT = """<system>
你是知识检索专家。你的任务是在用户的笔记库中找到最相关的信息。

<workflow>
1. 分析用户问题的真正意图
2. 将问题改写为更好的搜索查询（语义关键词）
3. 执行搜索
4. 综合回答，引用具体来源
</workflow>

<rules>
- **严格遵循上下文**：回答必须基于下方提供的「参考笔记内容」。
- **禁止编造**：如果参考笔记中没有相关信息，直接回答“抱歉，笔记中没有提到相关内容”，严禁使用你的通用知识去编造答案。
- **引用优先**：引用笔记时使用「笔记标题」格式。
- **语气自然**：像个助手一样交流，但事实必须绝对准确。
</rules>
</system>"""


def create_knowledge_worker(llm) -> Callable:
    """Create a Knowledge Worker for RAG-based note search."""
    rag_service = RAGService()
    
    async def knowledge_worker(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge search using LLM planning."""
        messages = state.get("messages", [])
        worker_input = state.get("worker_input", "")
        
        # Get the user's query
        query = worker_input
        if not query and messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    query = msg.content
                    break
        
        if not query:
            return {
                "response": "请告诉我你想搜索什么内容。",
                "tool_calls": ["search_notes"],
            }
        
        print(f"[SEARCH] Knowledge Agent processing: {query}")
        
        # Enterprise Pattern: LLM decides the strategy (Search vs List vs Recent)
        plan = await _plan_knowledge_action(llm, query)
        print(f"[PLAN] Knowledge Plan: {plan}")
        
        if plan['action'] == 'list_recent':
            return await _list_notes(rag_service, llm, query, title_prefix="🕒 **最近的笔记**", limit=plan.get('limit', 8), require_summary=plan.get('require_summary', False))
            
        elif plan['action'] == 'list_all':
            return await _list_notes(rag_service, llm, query, title_prefix="📚 **你的笔记列表**", limit=plan.get('limit', 10), require_summary=plan.get('require_summary', False))
            
        elif plan['action'] == 'search':
            # Execute semantic search
            search_query = plan.get('query', query)
            results = await rag_service.search(search_query, top_k=settings.TOP_K_RESULTS)
            
            # Fallback Pattern: "Exact Title Match"
            # If user asks about a specific note (e.g. Analysis of "Rust Note"), fetch full content
            # because vector chunks might be too fragmented.
            import re
            title_match = re.search(r'[「《](.*?)[」》]', query)
            if title_match:
                specific_title = title_match.group(1)
                print(f"[READ] Detected specific note title: {specific_title}, fetching full content...")
                from services.note_service import NoteService
                note_svc = NoteService()
                # We need a method to find by title, for now let's iterate or rely on search result ID if available
                # Optimization: check if any search result has high similarity to title
                target_note = None
                
                # First check if it's already in results
                for r in results:
                    if specific_title in r['title']:
                        target_note = r
                        break
                
                # If not in vectors, try DB search (fuzzy)
                if not target_note:
                    all_notes = await note_svc.get_all_notes()
                    for n in all_notes:
                        if specific_title in n['title']:
                            # Fetch full content
                            full = await note_svc.get_note(n['id'])
                            target_note = {"title": n['title'], "content": full['plainText']}
                            break
                
                if target_note:
                    # Prepend the FULL content of the specific note to results
                    # This gives LLM the complete context to answer "specific cases"
                    results.insert(0, target_note)

            if not results:
                response = f"抱歉，关于「{search_query}」，我目前没在笔记中找到相关内容。"
            else:
                response = await _synthesize_response(llm, query, results)
                
            return {
                "response": response,
                "tool_calls": ["search_notes"],
            }
            
        else:
            # Fallback
            return {
                "response": "我不确定该如何查找该内容。",
                "tool_calls": [],
            }

    return knowledge_worker


async def _plan_knowledge_action(llm, query: str) -> Dict[str, Any]:
    """Use LLM to plan the knowledge retrieval strategy."""
    # NOTE: Braces in JSON examples MUST be escaped as {{ }} for .format() to work
    PLANNER_PROMPT = """<system>
你是 Origin Notes 的知识库规划师。你的任务是分析用户的查询，并决定使用哪种检索策略。

可选策略 (Action)：
1. **search**: 用户在查找特定的知识点、话题或关键词。
   - 输出: {{"action": "search", "query": "优化的搜索关键词"}}
   
2. **list_recent**: 用户想看最近写的、刚创建的或最新的笔记。
   - 输出: {{"action": "list_recent", "limit": 8}}
   
3. **list_all**: 用户想浏览所有笔记、或者问有哪些笔记。
   - 输出: {{"action": "list_all", "limit": 10}}

4. **summary**: 如果用户不仅想看列表，还想看**概括**、**大纲**、**总结**或**介绍**。
   - 在上述 action 中增加字段: "require_summary": true
   - 例如: {{"action": "list_all", "limit": 10, "require_summary": true}}

<instruction>
请以纯 JSON 格式输出，不要包含 Markdown 标记。
</instruction>
</system>

User: {query}
Plan:"""

    try:
        # 使用 .replace 而不是 .format，以避开 prompt 里的 JSON 大括号冲突
        formatted_prompt = PLANNER_PROMPT.replace("{query}", query)
        response = await llm.ainvoke([HumanMessage(content=formatted_prompt)])
        content = response.content.strip()
        
        # Clean markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.replace("```", "").strip()
            
        import json
        plan = json.loads(content)
        return plan
    except Exception as e:
        print(f"[WARN] Planning failed, defaulting to search: {e}")
        return {"action": "search", "query": query}


async def _list_notes(rag_service: RAGService, llm, query: str, title_prefix="📚 **你的笔记**", limit=8, require_summary=False) -> Dict[str, Any]:
    """List notes, optionally summarizing them if requested by Planner."""
    notes = await rag_service.list_all_notes(limit=limit)
    
    if not notes:
        return {
            "response": "目前还没有保存的笔记。你可以开始创建新笔记！",
            "tool_calls": ["search_notes"],
        }

    # SIMPLE LIST MODE
    if not require_summary:
        note_list = "\n".join([f"• **「{n['title']}」**" for n in notes])
        response = f"{title_prefix}（共 {len(notes)} 篇）\n\n{note_list}\n\n💡 你可以直接问我关于这些笔记的具体问题。"
        return {"response": response, "tool_calls": ["search_notes"]}

    # DEEP SUMMARY MODE
    # If user wants summary/outline, we must fetch CONTENT.
    # To avoid context explosion, we limit to top 5 notes for summary or just read first 500 chars
    print("[THINK] Generating deep summary for notes listing...")
    
    # Fetch content (RAGService list_all_notes usually returns content="" for perf, so we might need re-fetch or use what we have)
    # The current list_all_notes implementation (based on previous edits) might return empty content.
    # Let's assume we need to fetch. Ideally rag_service should support this, but for now let's try direct DB fetch if content is missing
    # Or just rely on what we have if rag_service was updated.
    # Safety: let's re-fetch via ID to be sure
    from services.note_service import NoteService
    note_svc = NoteService()
    
    context_parts = []
    for n in notes[:6]: # Limit to 6 to save tokens
        full_note = await note_svc.get_note(n['id'])
        if full_note:
            text = full_note.get('plainText', '')[:2500] # Expanded to 2500 chars for deeper summary
            context_parts.append(f"标题：{n['title']}\n内容摘要：{text}...")
            
    context = "\n\n".join(context_parts)
    
    summary_prompt = f"""<system>
你是一个知识库整理专家。用户希望查看笔记列表的“概括”或“大纲”。
请基于以下笔记内容，为用户生成一份结构化的知识库概览。
对每篇笔记用一句话概括核心。
</system>

笔记列表数据：
{context}

用户指令：{query}

输出格式：
### 📚 知识库概览
- **[标题]**: 核心内容一句话总结...
...
"""
    response_msg = await llm.ainvoke([HumanMessage(content=summary_prompt)])
    
    return {
        "response": response_msg.content,
        "tool_calls": ["search_notes"],
    }


async def _synthesize_response(llm, query: str, results: list) -> str:
    """Synthesize a helpful response from search results."""
    # Build context from results
    context_parts = []
    for i, r in enumerate(results[:3], 1):
        title = r.get('title', '无标题')
        content = r.get('content', '')[:1000] # Gemini has large context
        context_parts.append(f"**「{title}」**\n{content}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    try:
        response = llm.invoke([
            SystemMessage(content=KNOWLEDGE_SYSTEM_PROMPT),
            HumanMessage(content=f"用户要求：{query}\n\n参考笔记内容：\n{context}\n\n请根据笔记回答。")
        ])
        return response.content
    except Exception as e:
        # Fallback: just show the results
        return f"📚 **参考笔记**\n\n{context}"
