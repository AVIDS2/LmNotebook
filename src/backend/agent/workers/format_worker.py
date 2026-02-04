"""
Format Worker - Enterprise-grade text beautification.
"""
from typing import Dict, Any, Callable
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', errors='replace').decode('gbk'))


# Enterprise Format Worker Prompt
FORMAT_SYSTEM_PROMPT = """<system>
你是文本美化专家。将混乱的文本转化为清晰、专业的 Markdown 格式。

<rules>
1. 识别文本的类型（会议记录、技术笔记、日记、列表等）
2. 根据类型选择最佳格式
3. 添加适当的标题层级（# ## ###）
4. 使用列表组织并行信息
5. 重要内容 **加粗**
6. 保留原始信息，不添加虚构内容
7. 代码块用 ```language``` 包裹
</rules>

<output>
直接输出格式化后的 Markdown，不要包含解释或说明。
</output>
</system>"""


def create_format_worker(llm) -> Callable:
    """Create a Format Worker for text beautification."""
    
    async def format_worker(state: Dict[str, Any]) -> Dict[str, Any]:
        """Format and beautify text."""
        messages = state.get("messages", [])
        selected_text = state.get("selected_text", "")
        worker_input = state.get("worker_input", "")
        note_context = state.get("note_context", "")
        
        # Determine what to format
        text_to_format = selected_text or note_context
        
        # If no text provided, try to extract from the message
        if not text_to_format and worker_input:
            # Remove trigger words
            for trigger in ["格式化", "美化", "排版", "整理", "格式刷"]:
                if trigger in worker_input:
                    idx = worker_input.find(trigger)
                    text_to_format = worker_input[idx + len(trigger):].strip()
                    if text_to_format.startswith("：") or text_to_format.startswith(":"):
                        text_to_format = text_to_format[1:].strip()
                    break
        
        if not text_to_format:
            return {
                "response": "请选择需要格式化的文本，或者发送你想整理的内容。",
                "tool_calls": ["format_text"],
            }
        
        safe_print(f"[FMT] Formatting text ({len(text_to_format)} chars)")
        
        try:
            response = llm.invoke([
                SystemMessage(content=FORMAT_SYSTEM_PROMPT),
                HumanMessage(content=f"请格式化以下文本：\n\n{text_to_format}")
            ])
            
            formatted = response.content.strip()
            
            return {
                "response": f"**Format Complete**\n\n{formatted}",
                "formatted_text": formatted,
                "tool_calls": ["format_text"],
            }
        except Exception as e:
            safe_print(f"[ERR] Format error: {e}")
            return {
                "response": "格式化时出现问题，请稍后再试。",
                "tool_calls": ["format_text"],
            }
    
    return format_worker
