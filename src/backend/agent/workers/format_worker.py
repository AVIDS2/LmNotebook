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
        try:
            import sys
            sys.stdout.buffer.write((msg + '\n').encode('utf-8', errors='replace'))
            sys.stdout.buffer.flush()
        except Exception:
            print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))


# Enterprise Format Worker Prompt
FORMAT_SYSTEM_PROMPT = """<system>
浣犳槸鏂囨湰缇庡寲涓撳銆傚皢娣蜂贡鐨勬枃鏈浆鍖栦负娓呮櫚銆佷笓涓氱殑 Markdown 鏍煎紡銆?

<rules>
1. 璇嗗埆鏂囨湰鐨勭被鍨嬶紙浼氳璁板綍銆佹妧鏈瑪璁般€佹棩璁般€佸垪琛ㄧ瓑锛?
2. 鏍规嵁绫诲瀷閫夋嫨鏈€浣虫牸寮?
3. 娣诲姞閫傚綋鐨勬爣棰樺眰绾э紙# ## ###锛?
4. 浣跨敤鍒楄〃缁勭粐骞惰淇℃伅
5. 閲嶈鍐呭 **鍔犵矖**
6. 淇濈暀鍘熷淇℃伅锛屼笉娣诲姞铏氭瀯鍐呭
7. 浠ｇ爜鍧楃敤 ```language``` 鍖呰９
</rules>

<output>
鐩存帴杈撳嚭鏍煎紡鍖栧悗鐨?Markdown锛屼笉瑕佸寘鍚В閲婃垨璇存槑銆?
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
            for trigger in ["鏍煎紡鍖?, "缇庡寲", "鎺掔増", "鏁寸悊", "鏍煎紡鍒?]:
                if trigger in worker_input:
                    idx = worker_input.find(trigger)
                    text_to_format = worker_input[idx + len(trigger):].strip()
                    if text_to_format.startswith("锛?) or text_to_format.startswith(":"):
                        text_to_format = text_to_format[1:].strip()
                    break
        
        if not text_to_format:
            return {
                "response": "璇烽€夋嫨闇€瑕佹牸寮忓寲鐨勬枃鏈紝鎴栬€呭彂閫佷綘鎯虫暣鐞嗙殑鍐呭銆?,
                "tool_calls": ["format_text"],
            }
        
        safe_print(f"[FMT] Formatting text ({len(text_to_format)} chars)")
        
        try:
            response = llm.invoke([
                SystemMessage(content=FORMAT_SYSTEM_PROMPT),
                HumanMessage(content=f"璇锋牸寮忓寲浠ヤ笅鏂囨湰锛歕n\n{text_to_format}")
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
                "response": "鏍煎紡鍖栨椂鍑虹幇闂锛岃绋嶅悗鍐嶈瘯銆?,
                "tool_calls": ["format_text"],
            }
    
    return format_worker


