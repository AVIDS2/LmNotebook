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
        try:
            import sys
            sys.stdout.buffer.write((msg + '\n').encode('utf-8', errors='replace'))
            sys.stdout.buffer.flush()
        except Exception:
            print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))


NOTE_SYSTEM_PROMPT = """浣犳槸绗旇绠＄悊涓撳銆備綘鍙互甯姪鐢ㄦ埛鍒涘缓銆佺紪杈戝拰绠＄悊浠栦滑鐨勭瑪璁般€?

## 浣犲彲浠ユ墽琛岀殑鎿嶄綔锛?
1. **鍒涘缓绗旇**: 鏍规嵁鐢ㄦ埛鐨勮姹傚垱寤烘柊绗旇
2. **鏇存柊绗旇**: 淇敼鐜版湁绗旇鐨勫唴瀹?
3. **鎬荤粨**: 灏嗗涓瑪璁板唴瀹规€荤粨鎴愪竴涓柊绗旇

## 杈撳嚭鏍煎紡锛?
- 鎴愬姛鍚庡憡璇夌敤鎴锋搷浣滅粨鏋?
- 濡傛灉闇€瑕佹洿澶氫俊鎭紝绀艰矊鍦拌闂敤鎴?
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
            title = intent.get("title", "鏂扮瑪璁?)
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
                    "response": "璇锋寚瀹氳鏇存柊鐨勭瑪璁般€備綘鍙互鍏堟墦寮€涓€绡囩瑪璁般€?,
                    "messages": messages + [AIMessage(content="璇锋寚瀹氳鏇存柊鐨勭瑪璁般€?)]
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
                    sys_prompt = "浣犳槸涓€涓簿纭殑鏂囨湰缂栬緫鍔╂墜銆備綘鐨勪换鍔℃槸鏍规嵁鐢ㄦ埛鐨勪慨鏀硅姹傚绗旇杩涜**灞€閮ㄦ洿鏂?*銆俓n鍏抽敭瑙勫垯锛歕n1. **淇濇寔绋冲畾鎬?*锛氶櫎闈炵敤鎴锋槑纭姹傚垹闄ゆ垨閲嶅啓鏁翠釜绗旇锛屽惁鍒欏繀椤讳繚鐣欏綋鍓嶅唴瀹逛腑涓庢寚浠ゆ棤鍏崇殑鎵€鏈夐儴鍒嗐€俓n2. **绮剧‘淇敼**锛氬彧閽堝鎸囦护鎻愬強鐨勬钀姐€佹爣棰樻垨鍙ュ瓙杩涜鎿嶄綔銆俓n3. **鎷掔粷瑕嗙洊**锛氫弗绂佸湪鏈幏鏄庣‘鎺堟潈鐨勬儏鍐典笅鎿呰嚜鎶婂唴瀹圭畝鍖栨垚鍙湁涓€灏忛儴鍒嗗唴瀹广€?
                    user_content = f"### 鍘熷绗旇鍐呭 (蹇呴』浣滀负鍩虹淇濆瓨)锛歕n{note_context}\n\n### 淇敼鎸囦护 (浠呮墽琛屾澶勬搷浣?锛歕n{edit_desc}"
                else:
                    sys_prompt = "浣犳槸涓€涓瑪璁板唴瀹圭敓鎴愬姪鎵嬨€傜敤鎴峰笇鏈涢噸鍐欐垨濉厖杩欑瘒绗旇鐨勫唴瀹广€傝鏍规嵁瑕佹眰鐢熸垚瀹屾暣鐨勩€佺粨鏋勬竻鏅扮殑 Markdown 绗旇鍐呭銆?
                    user_content = f"鍐欎綔瑕佹眰锛歕n{edit_desc}\n\n璇风洿鎺ョ敓鎴愬唴瀹癸紝涓嶈鏈夊紑鍦虹櫧銆?

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
                response = "璇峰憡璇夋垜浣犳兂鍒犻櫎鍝瘒绗旇銆傚鏋滄槸褰撳墠鎵撳紑鐨勭瑪璁帮紝鐩存帴璇粹€樺垹闄よ繖绡団€欏嵆鍙€?
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
            response = "璇峰憡璇夋垜浣犳兂瀵圭瑪璁板仛浠€涔堟搷浣滐細鍒涘缓銆佷慨鏀广€佸垹闄ゆ垨鎬荤粨锛?
        
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
鍒嗘瀽鐢ㄦ埛鐨勭瑪璁版搷浣滄剰鍥俱€傚弬鑰冧箣鍓嶇殑瀵硅瘽涓婁笅鏂囥€?

杈撳嚭鏍煎紡绀轰緥锛?
{{"action": "create", "title": "鏍囬"}}
{{"action": "update", "title": "鏂版爣棰?, "description": "淇敼鎻忚堪"}}
{{"action": "delete"}}
{{"action": "summarize"}}

瑙勫垯锛?
1. **update**: 娑夊強鍐呭鐨勪换浣曚慨鏀癸紙鍖呮嫭**鍒犻櫎鏌愬彞璇?*銆?*灞€閮ㄩ噸鍐?*銆佽ˉ鍏呫€佺籂閿欙級銆?
   - 濡傛灉鐢ㄦ埛鎰忓浘鏄?*瀹屽叏閲嶅啓**銆?*鏇存崲涓婚**銆?*娓呯┖閲嶆潵**鎴?*鐢变簬涓婚涓嶇闇€瑕佹帹鍊掗噸鍐?*锛堝鈥滄妸杩欑瘒绗旇鏀规垚X鈥濓級锛岃璁剧疆 `"force_rewrite": true`銆?
   - 濡傛灉鍙槸**灞€閮ㄥ井璋?*锛堝鈥滀慨鏀圭浜旂珷鈥濄€佲€滄妸杩欐鍐呭鏀逛竴涓嬧€濄€佲€滃垹闄ょ涓€琛屸€濓級锛?*缁濆绂佹**璁剧疆 `force_rewrite` 涓?true銆?
2. **閲嶈瑙勫垯**锛氬鏋滅敤鎴疯姹傗€滄妸绗旇鏀瑰啓鎴怷鈥濇垨鏇存崲涓婚锛?*蹇呴』**鍦?JSON 涓悓鏃惰缃?`"title": "X"`锛岀‘淇濇爣棰樺拰鏂板唴瀹逛竴鑷淬€?
3. **delete**: 鍙湁鐢ㄦ埛鏄庣‘璇粹€滃垹闄?*杩欑瘒绗旇**鈥濄€佲€滃垹闄?*鏂囦欢**鈥濄€佲€滄妸杩欎釜绗旇**绉诲埌鍥炴敹绔?*鈥濇椂锛屾墠鏄?delete銆?
4. **summarize**: 浠呴檺鈥滄€荤粨鈥濄€佲€滄憳瑕佲€濄€?
5. **绂佹杈撳嚭姝ｆ枃**: JSON 涓?*涓嶈**鍖呭惈 `content` 瀛楁銆備粎濉啓 `description` 璁╁悗缁?Writer 鐢熸垚銆?
6. 浠呰緭鍑?JSON銆?
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
        SystemMessage(content="浣犳槸涓€涓瑪璁板姪鎵嬨€傚熀浜庣敤鎴风殑瑕佹眰鍜屼箣鍓嶇殑瀵硅瘽涓婁笅鏂囷紝鐢熸垚缁撴瀯鍖栫殑绗旇鍐呭銆備娇鐢?Markdown 鏍煎紡锛屽寘鍚爣棰樸€佸垪琛ㄧ瓑銆傚鏋滅敤鎴锋彁鍒?涔嬪墠鐨勫唴瀹?鎴?杩欎釜鐭ヨ瘑鐐?锛岃鍙傝€冨璇濆巻鍙层€傚浜庢暟瀛﹀叕寮忥紝璇蜂紭鍏堜娇鐢?LaTeX 鏍煎紡銆?),
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
        SystemMessage(content="灏嗕互涓嬪唴瀹规€荤粨鎴愮畝娲佺殑鎽樿锛屼繚鐣欏叧閿俊鎭€?),
        HumanMessage(content=content)
    ]
    result = await llm.ainvoke(messages)
    return result.content


async def _chat_after_action(llm, action: str, context: str) -> str:
    """Generate a quick, natural human-like response after an action."""
    from langchain_core.messages import SystemMessage, HumanMessage
    
    prompt = f"""<system>
浣犳槸涓€涓笓涓氱殑绗旇鍔╂墜 Agent銆備綘鍒氬垰鎴愬姛鎵ц浜嗕竴涓搷浣滐紙{action}锛夈€?
璇风敓鎴愪竴鍙ヨ嚜鐒躲€佺◢寰甫鐐逛釜鎬х殑鍥炲缁欑敤鎴枫€?
涓嶈鍙鈥滃凡瀹屾垚鈥濓紝瑕佺粨鍚堝垰鎵嶇殑鎿嶄綔缁嗚妭锛圕ontext锛夎鐐规湁鐢ㄧ殑銆?
姣斿锛氬鏋滈噸鍐欎簡绗旇锛屽彲浠ヨ鈥滄悶瀹氾紒杩欑瘒鏂囩珷鐜板湪缁撴瀯鏇存竻鏅颁簡锛岄噸鐐硅ˉ鍏呬簡XXX銆傗€?
璇皵锛氫笓涓氥€佺儹鎯呫€佸儚涓湡浜轰紮浼淬€?
闄愬埗锛?0瀛椾互鍐呫€?
</system>

Context:
{context}

Response:"""
    
    try:
        res = await llm.ainvoke([HumanMessage(content=prompt)])
        return res.content.strip().replace('"', '')
    except:
        return "鎿嶄綔宸插畬鎴愩€?


