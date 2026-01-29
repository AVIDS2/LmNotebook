"""
Agent Supervisor - Orchestrator of Thinking and Action.
Enterprise-grade implementation with Autonomous ReAct Loop.
"""
from typing import List, Dict, Any, Optional, AsyncIterator, Union
import asyncio
import json
import markdown

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
from langchain_core.utils.function_calling import convert_to_openai_tool

from core.config import settings
from core.llm import get_llm
from .tools import get_all_agent_tools


# Master System Prompt
SUPERVISOR_PROMPT = """你是一个拥有自主性、思考能力的企业级知识助手 "Origin"。
你的工作模式是基于 **ReAct (Reasoning and Acting)** 框架的。

### 核心准则：
1. **工具决策自理**：当用户提出问题，你首先分析：我是否需要查阅现有的笔记？还是这属于“通用百科知识”？
2. **严防“私货”驱动**：
   - 对于涉及用户**个人资产**（如“我的账号”、“我昨天的感悟”）的问题，**必须**调用工具，严禁编造。
   - 对于涉及**客观通用知识**（如“拉格朗日中值定理”、“Python 语法”）的问题，如果工具未搜到内容，你可以基于自身知识库回复，但**必须声明**：“在您的笔记中未找到相关记录，以下是基于通用知识的解答”。
4. **专业交互**：最终回复必须逻辑清晰。如果是对笔记进行了优化或格式调整，应当明确指出改进了哪些地方。
5. **持久化优先**：凡是涉及“修改格式”、“优化排版”、“整理笔记”的要求，必须通过 `update_note` 工具将修改保存到编辑器中，然后再给用户一段自然语言总结。

### 处理流程：
- **Thought**: 思考下一步该做什么，为什么要这么做。
- **Action**: 调用最合适的工具（search_knowledge, read_note_content, list_recent_notes 等）。
- **Observation**: 观察工具反馈的数据。
- **Final Answer**: 基于事实给出最终结论。

⚠️ **警告**：如果工具返回“未找到内容”，请如实告知，严禁脑补。
"""

class AgentSupervisor:
    """
    Autonomous Orchestrator using functional tool-calling and recursive reasoning.
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.tools = get_all_agent_tools()
        # Bind tools to the model (OpenAI Protocol compatible)
        self.model_with_tools = self.llm.bind_tools(self.tools)
        # Internal map for execution
        self.tools_map = {tool.name: tool for tool in self.tools}
    
    def _prepare_history(self, history: Optional[List[Any]]) -> List[BaseMessage]:
        """Convert list of dicts or ChatMessage objects to LangChain message objects."""
        full_history = []
        if history:
            for h in history:
                role = h.get("role", "user") if isinstance(h, dict) else getattr(h, "role", "user")
                content = h.get("content", "") if isinstance(h, dict) else getattr(h, "content", "")
                
                if role == "user":
                    full_history.append(HumanMessage(content=content))
                else:
                    full_history.append(AIMessage(content=content))
        return full_history

    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """Execute a single tool call and return the result as string."""
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        if tool_name not in self.tools_map:
            return f"Error: Tool {tool_name} not found."
            
        try:
            tool = self.tools_map[tool_name]
            # Execute async tool
            result = await tool.ainvoke(tool_args)
            
            # Special case for JSON string results (like update_note)
            if isinstance(result, str) and result.startswith("{"):
                return result
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    async def invoke_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        note_context: Optional[str] = None,
        active_note_id: Optional[str] = None,
        selected_text: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Multi-turn Autonomous Execution Loop.
        Implements the Reasoning -> Acting -> Observation loop.
        """
        try:
            # 1. Setup Initial State
            full_history = self._prepare_history(history)
            
            # Inject dynamic situational awareness
            current_situation = f"\n\n[Current Context]\nActive Note ID: {active_note_id or 'None'}\n"
            if note_context:
                current_situation += f"Quick Preview of Active Note (First 500 chars): {note_context[:500]}...\n"
                
            messages = [
                SystemMessage(content=SUPERVISOR_PROMPT + current_situation),
            ] + full_history + [
                HumanMessage(content=message)
            ]

            max_turns = 3 # Reduce turns to avoid excessive searching for common knowledge
            turn = 0
            
            while turn < max_turns:
                turn += 1
                
                # Check if this is the last chance to answer
                is_last_turn = (turn == max_turns)
                
                # UI Feedback
                if turn == 1:
                    yield json.dumps({"type": "status", "text": "🧠 思考中..."})
                
                # Ask the model (Thinking step)
                # If it's the last turn, we append a final instruction to stop tool use
                current_messages = messages
                if is_last_turn:
                    current_messages = messages + [HumanMessage(content="[SYSTEM]: 搜索次数已达上限。请不要再调用任何工具，直接基于现有信息或你的通用背景知识给出最终回答。")]

                ai_msg = await self.model_with_tools.ainvoke(current_messages)
                
                # Case A: Model wants to call tools (and we haven't hit the limit yet)
                if ai_msg.tool_calls and not is_last_turn:
                    messages.append(ai_msg)
                    
                    for tool_call in ai_msg.tool_calls:
                        tool_name = tool_call["name"]
                        
                        # UI Feedback
                        STATUS_LABELS = {
                            "search_knowledge": "📚 正在检索知识库...",
                            "read_note_content": "📖 正在读取笔记全文...",
                            "list_recent_notes": "📝 正在寻找笔记...",
                            "update_note": "⚙️ 正在执行笔记更新...",
                            "create_note": "🆕 正在创建新笔记...",
                            "delete_note": "🗑️ 正在清理笔记..."
                        }
                        yield json.dumps({"type": "status", "text": STATUS_LABELS.get(tool_name, f"🛠️ 调用 {tool_name}...")})
                        
                        # Execute
                        observation = await self._execute_tool_call(tool_call)
                        
                        # High-End UX: Trigger UI refresh for ALL data mutations
                        try:
                            if tool_name == "update_note" and "Successfully updated" in observation:
                                from services.note_service import NoteService
                                ns = NoteService()
                                note_data = await ns.get_note(tool_call["args"].get("note_id"))
                                if note_data:
                                    html_content = markdown.markdown(note_data.get("content", ""), extensions=['fenced_code', 'tables', 'nl2br'])
                                    yield json.dumps({"tool_call": "format_apply", "formatted_html": html_content})
                            
                            elif tool_name == "create_note" and "Successfully created" in observation:
                                # Extract ID using regex: ID: ([\w-]+)
                                match = re.search(r"ID:\s*([\w-]+)", observation)
                                note_id = match.group(1) if match else None
                                yield json.dumps({"tool_call": "note_created", "note_id": note_id, "message": "New note created and synced."})
                            
                            elif tool_name == "delete_note" and "Successfully deleted" in observation:
                                note_id = tool_call["args"].get("note_id")
                                yield json.dumps({"tool_call": "note_deleted", "note_id": note_id, "message": "Note deleted from library."})
                        except Exception as sync_err:
                            print(f"[WARN] UI Sync Warning: {sync_err}")

                        messages.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
                    
                    # Continue for next turn
                    continue
                
                # Case B: Model gives a final answer OR we forced it on the last turn
                else:
                    # Clear status for final output
                    yield json.dumps({"type": "status", "text": ""})
                    
                    # 1. First, yield whatever content we already got from ainvoke
                    if ai_msg.content:
                        yield ai_msg.content
                    
                    # 2. If it was a forced turn and content was empty, or we want a synthesis flow, 
                    # we could stream, but usually ai_msg.content has the answer now.
                    # Only stream if ai_msg.content is surprisingly short/missing
                    if not ai_msg.content.strip():
                        async for chunk in self.llm.astream(messages):
                            if chunk.content:
                                yield chunk.content
                    
                    return # Exit after final answer
            
            # Fallback if loop finishes without yield (should not happen with else block logic)
            yield "抱歉，任务处理轮次超限，未能生成有效回答。请尝试换个问法。"
                    
        except Exception as e:
            print(f"[ERR] Orchestration Error: {e}")
            import traceback
            traceback.print_exc()
            yield f"抱歉，系统逻辑层出现错误：{str(e)}"

    async def invoke(self, *args, **kwargs) -> Dict[str, Any]:
        """Legacy compatibility for non-streaming calls."""
        # Simple implementation: collect stream and return
        full_text = ""
        async for chunk in self.invoke_stream(*args, **kwargs):
            if not chunk.startswith("{"):
                full_text += chunk
        return {"response": full_text, "tool_calls": []}
