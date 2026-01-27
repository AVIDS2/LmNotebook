"""
Agent Supervisor - Enterprise-grade implementation with structured prompts.
Based on Cursor AI, Devin, and LangChain best practices.
"""
from typing import List, Dict, Any, Optional, AsyncIterator
import asyncio
import json
import markdown

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from core.llm import get_llm
from .workers.knowledge_worker import create_knowledge_worker
from .workers.note_worker import create_note_worker
from .workers.format_worker import create_format_worker


# Enterprise-grade System Prompt with XML Structure
SUPERVISOR_PROMPT = """<system>
你是 Origin Notes 的 AI 助手，名叫 "Origin"。

<identity>
- 你是一个专业、友好、高效的个人知识管理助手
- 你可以访问用户的笔记数据库，帮助用户搜索、整理和创建内容
- 你的回复简洁有力，使用中文
</identity>

<tools>
你有以下工具可以使用：

1. **search_notes** - 在用户的笔记库中语义搜索
   触发词: "搜索", "查找", "找一下", "有没有", "我之前写过", "相关笔记"
   
2. **create_note** - 创建新笔记
   触发词: "新建笔记", "创建笔记", "帮我记录", "写一个笔记"

3. **format_text** - 美化和格式化文本
   触发词: "格式化", "美化", "排版", "整理格式", "格式刷"

4. **summarize** - 总结笔记或选中内容
   触发词: "总结", "概括", "摘要"
</tools>

<guidelines>
1. 当用户的问题匹配工具触发词时，使用对应工具
2. 普通聊天（问候、闲聊、一般问题）直接回答，不需要工具
3. 工具调用成功后，告诉用户具体做了什么
4. 搜索无结果时，告知用户并给出建议
5. 不要编造不存在的笔记内容
6. 保持回复简洁自然
</guidelines>

<output_format>
- 使用简洁的中文回复
- 引用笔记时用「笔记标题」
- 代码或格式化内容使用 Markdown
- 操作成功用 ✅，警告用 ⚠️
</output_format>
</system>"""


class AgentSupervisor:
    """
    Hierarchical Agent Supervisor with enterprise-grade prompts.
    """
    
    def __init__(self):
        self.llm = get_llm()
        self._knowledge_worker = None
        self._note_worker = None
        self._format_worker = None
    
    def _get_knowledge_worker(self):
        if self._knowledge_worker is None:
            self._knowledge_worker = create_knowledge_worker(self.llm)
        return self._knowledge_worker
    
    def _get_note_worker(self):
        if self._note_worker is None:
            self._note_worker = create_note_worker(self.llm)
        return self._note_worker
    
    def _get_format_worker(self):
        if self._format_worker is None:
            self._format_worker = create_format_worker(self.llm)
        return self._format_worker

    def _prepare_history(self, history: Optional[List[Any]]) -> List[Any]:
        """Convert list of dicts or ChatMessage objects to LangChain message objects."""
        full_history = []
        if history:
            for h in history:
                # Handle both dict and Pydantic objects
                role = h.get("role", "user") if isinstance(h, dict) else getattr(h, "role", "user")
                content = h.get("content", "") if isinstance(h, dict) else getattr(h, "content", "")
                
                if role == "user":
                    full_history.append(HumanMessage(content=content))
                else:
                    full_history.append(AIMessage(content=content))
        return full_history
    
    async def _route_intent(self, message: str, history: List[Dict[str, str]] = None) -> str:
        """
        Semantic Intent Routing with Context Awareness.
        """
        history_context = ""
        if history:
            # Format last few messages for context
            ctx = (history or [])[-3:]
            history_context = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')[:100]}" for m in ctx])

        router_prompt = f"""<system>
你是 Origin Notes 的智能路由中枢。分析用户输入和对话历史，将意图路由到正确的 Worker。

可选 Worker：
1. **knowledge** (知识检索): 检索、列出、查看存储的多篇内容。
2. **note** (写操作): 创建、编辑标题/正文、删除笔记。
   - ⚠️ **规则**: 凡是针对当前或某篇笔记的“修改”、“改名”、“删除”指令，必须由 **note** 处理。
3. **format** (排版): 美化文本。
4. **summarize** (总结提炼)。
5. **chat** (通用问答): 闲聊、科普。

<context>
{history_context}
</context>

<instruction>
仅输出 Worker 名称（knowledge, note, format, summarize, chat）。
</instruction>
</system>

User: {message}
Router:"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=router_prompt)])
            intent = response.content.strip().lower()
            import re
            intent = re.sub(r'[^a-z]', '', intent)
            valid_intents = ["knowledge", "note", "format", "summarize", "chat"]
            return intent if intent in valid_intents else "chat"
        except:
            return "chat"

    async def _plan_knowledge_action(self, query: str) -> Dict[str, Any]:
        """Plan the knowledge retrieval strategy using LLM."""
        planner_prompt = f"""<system>
你是 Origin Notes 的知识库规划师。分析用户的查询，决定使用哪种检索策略。

可选策略：
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
            response = await self.llm.ainvoke([HumanMessage(content=planner_prompt)])
            content = response.content.strip()
            
            # Clean markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.replace("```", "").strip()
                
            import re
            # Try to extract JSON
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
            return json.loads(content)
        except Exception as e:
            print(f"⚠️ Planning failed, defaulting to search: {e}")
            return {"action": "search", "query": query}

    async def invoke(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        note_context: Optional[str] = None,
        selected_text: Optional[str] = None,
        active_note_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Invoke the agent with a user message."""
        
        # Build messages for context
        full_history = self._prepare_history(history)
        
        # Parse intent using LLM (The "True" Agentic Way)
        print(f"🧠 Semantic Routing for: '{message}'")
        intent = await self._route_intent(message, history)
        print(f"🎯 Intent routed to: {intent}")
        
        # Build state
        state = {
            "messages": full_history + [HumanMessage(content=message)],
            "note_context": note_context,
            "active_note_id": active_note_id,
            "selected_text": selected_text,
            "worker_input": message,
            "response": "",
            "tool_calls": [],
        }
        
        try:
            if intent == "knowledge":
                print("📚 Routing to Knowledge Worker...")
                worker = self._get_knowledge_worker()
                result = await worker(state)
                return {
                    "response": result.get("response", "搜索时出现问题。"),
                    "tool_calls": ["search_notes"],
                }
            
            elif intent == "note":
                print("📝 Routing to Note Worker...")
                worker = self._get_note_worker()
                result = await worker(state)
                return {
                    "response": result.get("response", "笔记操作时出现问题。"),
                    "tool_calls": ["create_note"],
                }
            
            elif intent == "summarize":
                print("📋 Routing to summarize...")
                if note_context:
                    # Summarize the current note
                    summary_prompt = f"请简洁地总结以下内容：\n\n{note_context[:2000]}"
                    response = self.llm.invoke([
                        SystemMessage(content="你是总结专家。用简洁的要点总结内容。"),
                        HumanMessage(content=summary_prompt)
                    ])
                    return {
                        "response": f"📋 **内容摘要**\n\n{response.content}",
                        "tool_calls": ["summarize"],
                    }
                else:
                    return {
                        "response": "请先打开一篇笔记，我才能帮你总结内容。",
                        "tool_calls": [],
                    }
            
            elif intent == "format":
                print("✨ Routing to Format Worker...")
                worker = self._get_format_worker()
                result = await worker(state)
                return {
                    "response": result.get("response", "格式化时出现问题。"),
                    "tool_calls": ["format_text"],
                }
            
            else:
                # Direct chat - most common path
                print("💬 Direct chat response...")
                # Ensure we include the system prompt for persona consistency
                chat_messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + full_history + [HumanMessage(content=message)]
                response = self.llm.invoke(chat_messages)
                return {
                    "response": response.content,
                    "tool_calls": [],
                }
        
        except Exception as e:
            print(f"❌ Error in AgentSupervisor: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "response": "抱歉，处理请求时出错了。请稍后再试。",
                "tool_calls": ["error"],
            }
    
    async def stream(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        note_context: Optional[str] = None,
        selected_text: Optional[str] = None,
        active_note_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Stream agent responses with Semantic Routing.
        Matches the logic of invoke() but for streaming.
        """
        try:
            # 1. Route Intent
            intent = await self._route_intent(message, history)
            print(f"🧠 Streaming Intent routed to: {intent}")

            # Common state for workers
            full_history = self._prepare_history(history)
            
            state = {
                "messages": full_history + [HumanMessage(content=message)],
                "note_context": note_context,
                "active_note_id": active_note_id,
                "selected_text": selected_text,
                "worker_input": message,
                "response": "",
                "tool_calls": [],
            }

            # Define status messages for each intent
            STATUS_MESSAGES = {
                "knowledge": "📚 正在搜索笔记...",
                "note": "📝 正在创建笔记...",
                "format": "✨ 正在优化格式...",
                "summarize": "📋 正在总结内容...",
                "chat": "💭 思考中..."
            }
            
            # Send status message first (as JSON with type: status)
            status_msg = STATUS_MESSAGES.get(intent, "💭 思考中...")
            yield json.dumps({"type": "status", "text": status_msg})

            if intent == "knowledge":
                print("📚 Routing stream to Knowledge Worker...")
                # Get RAG service and plan
                from services.rag_service import RAGService
                rag_service = RAGService()
                await rag_service._ensure_loaded()
                
                # Plan the action using LLM
                plan = await self._plan_knowledge_action(message)
                print(f"🧠 Knowledge Plan: {plan}")
                
                if plan['action'] in ['list_recent', 'list_all']:
                    # Static list - no LLM generation needed, yield directly
                    title_prefix = "🕒 **最近的笔记**" if plan['action'] == 'list_recent' else "📚 **你的笔记列表**"
                    notes = await rag_service.list_all_notes(limit=plan.get('limit', 8))
                    
                    if not notes:
                        yield "目前还没有保存的笔记。你可以开始创建新笔记！"
                    else:
                        note_list = "\n".join([f"• **「{n['title']}」**" for n in notes])
                        yield f"{title_prefix}（共 {len(notes)} 篇）\n\n{note_list}\n\n💡 你可以直接问我关于这些笔记的具体问题。"
                
                elif plan['action'] == 'search':
                    # Search + LLM synthesis - TRUE STREAMING
                    search_query = plan.get('query', message)
                    results = await rag_service.search(search_query, top_k=5)
                    print(f"📊 Found {len(results)} results")
                    
                    if not results:
                        yield f"抱歉，关于「{search_query}」，我没有在笔记中找到相关内容。"
                    else:
                        # Build context
                        context_parts = []
                        for r in results[:3]:
                            title = r.get('title', '无标题')
                            content = r.get('content', '')[:1000]
                            context_parts.append(f"**「{title}」**\n{content}")
                        context = "\n\n---\n\n".join(context_parts)
                        
                        # TRUE STREAMING with LLM
                        synthesis_prompt = f"用户问题：{message}\n\n参考笔记内容：\n{context}\n\n请根据笔记内容回答用户问题。"
                        async for chunk in self.llm.astream([
                            SystemMessage(content="你是知识检索专家。根据用户的笔记内容回答问题，引用时使用「笔记标题」格式。"),
                            HumanMessage(content=synthesis_prompt)
                        ]):
                            if chunk.content:
                                yield chunk.content
                else:
                    yield "我不确定该如何查找该内容。"
                
            elif intent == "note":
                print("📝 Routing stream to Note Worker...")
                worker = self._get_note_worker()
                result = await worker(state)
                yield result["response"]
                
            elif intent == "format":
                # Special WPS-style direct format brush
                print("✨ Format brush triggered via stream...")
                formatted_md = await self.format_text(selected_text or note_context or message, note_context)
                
                # Convert to HTML for direct TipTap injection
                formatted_html = markdown.markdown(formatted_md, extensions=['fenced_code', 'tables', 'nl2br'])
                
                yield json.dumps({
                    "tool_call": "format_apply",
                    "formatted_html": formatted_html,
                    "formatted_md": formatted_md
                })
                
            elif intent == "summarize":
                # Summarize current note
                print("📝 Summarizing current note...")
                if note_context:
                    summary_prompt = f"请总结以下笔记内容的要点：\n\n{note_context}"
                    async for chunk in self.llm.astream([
                        SystemMessage(content="你是一个专业的笔记总结专家。请用简洁清晰的语言总结笔记的核心要点。"),
                        HumanMessage(content=summary_prompt)
                    ]):
                        if chunk.content:
                            yield chunk.content
                else:
                    yield "请先打开一篇笔记，我才能为你总结内容。"
                
            else:
                # Direct chat with context awareness
                context_hint = ""
                if note_context:
                    context_hint = f"\n\n[当前用户正在编辑的笔记内容：\n{note_context[:2000]}...]"
                
                user_message = message + context_hint if context_hint else message
                chat_messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + full_history + [HumanMessage(content=user_message)]
                
                async for chunk in self.llm.astream(chat_messages):
                    if chunk.content:
                        yield chunk.content
                        
        except Exception as e:
            print(f"❌ Stream error: {e}")
            import traceback
            traceback.print_exc()
            yield f"抱歉，处理流式请求时遇到错误: {str(e)}"
    
    async def format_text(
        self,
        text: str,
        context: Optional[str] = None,
    ) -> str:
        """Direct call to FormatWorker."""
        state = {
            "messages": [HumanMessage(content=f"请格式化：\n\n{text}")],
            "selected_text": text,
            "note_context": context,
            "worker_input": text,
        }
        
        try:
            worker = self._get_format_worker()
            result = await worker(state)
            return result.get("response", text)
        except Exception as e:
            print(f"❌ Error in format_text: {e}")
            return text
