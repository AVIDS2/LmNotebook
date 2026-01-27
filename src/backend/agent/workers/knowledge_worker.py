"""
Knowledge Worker - Enterprise-grade Agentic RAG implementation.
Optimized for Gemini and intelligent retrieval.
"""
from typing import Dict, Any, Callable, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

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
- 永远不要编造不存在的内容
- 如果搜索无结果，明确告诉用户
- 给出的信息必须来自实际的笔记
- 引用笔记时使用「笔记标题」格式
- 如果用户只是想看所有的笔记或最近的笔记，请友善地列出来
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
        
        print(f"🔍 Knowledge Agent processing: {query}")
        
        # Enterprise Pattern: LLM decides the strategy (Search vs List vs Recent)
        plan = await _plan_knowledge_action(llm, query)
        print(f"🧠 Knowledge Plan: {plan}")
        
        if plan['action'] == 'list_recent':
            return await _list_notes(rag_service, title_prefix="🕒 **最近的笔记**", limit=plan.get('limit', 8))
            
        elif plan['action'] == 'list_all':
            return await _list_notes(rag_service, title_prefix="📚 **你的笔记列表**", limit=plan.get('limit', 10))
            
        elif plan['action'] == 'search':
            # Execute semantic search with the optimized query from the plan
            search_query = plan.get('query', query)
            results = await rag_service.search(search_query, top_k=5)
            print(f"📊 Found {len(results)} results")
            
            if not results:
                response = f"抱歉，关于「{search_query}」，我没有在笔记中找到相关内容。"
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

<instruction>
请以纯 JSON 格式输出，不要包含 Markdown 标记。
</instruction>
</system>

User: {query}
Plan:"""

    try:
        response = await llm.ainvoke([HumanMessage(content=PLANNER_PROMPT.format(query=query))])
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
        print(f"⚠️ Planning failed, defaulting to search: {e}")
        return {"action": "search", "query": query}


async def _list_notes(rag_service: RAGService, title_prefix="📚 **你的笔记**", limit=8) -> Dict[str, Any]:
    """List available notes."""
    notes = await rag_service.list_all_notes(limit=limit)
    
    print(f"📝 _list_notes called, got {len(notes) if notes else 0} notes")
    if notes:
        for n in notes[:3]:
            print(f"   - Title: {n.get('title', 'MISSING')}, ID: {n.get('id', 'MISSING')}")
    
    if not notes:
        return {
            "response": "目前还没有保存的笔记。你可以开始创建新笔记！",
            "tool_calls": ["search_notes"],
        }
    
    note_list = "\n".join([f"• **「{n['title']}」**" for n in notes])
    response = f"{title_prefix}（共 {len(notes)} 篇）\n\n{note_list}\n\n💡 你可以直接问我关于这些笔记的具体问题。"
    
    print(f"📝 Response preview: {response[:200]}...")
    
    return {
        "response": response,
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
