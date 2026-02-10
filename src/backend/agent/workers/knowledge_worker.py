"""
Knowledge Worker - Enterprise-grade Agentic RAG implementation.
Optimized for Gemini and intelligent retrieval.
"""
from typing import Dict, Any, Callable, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from core.config import settings
from services.rag_service import RAGService


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


# Enterprise Knowledge Worker Prompt
KNOWLEDGE_SYSTEM_PROMPT = """<system>
浣犳槸鐭ヨ瘑妫€绱笓瀹躲€備綘鐨勪换鍔℃槸鍦ㄧ敤鎴风殑绗旇搴撲腑鎵惧埌鏈€鐩稿叧鐨勪俊鎭€?

<workflow>
1. 鍒嗘瀽鐢ㄦ埛闂鐨勭湡姝ｆ剰鍥?
2. 灏嗛棶棰樻敼鍐欎负鏇村ソ鐨勬悳绱㈡煡璇紙璇箟鍏抽敭璇嶏級
3. 鎵ц鎼滅储
4. 缁煎悎鍥炵瓟锛屽紩鐢ㄥ叿浣撴潵婧?
</workflow>

<rules>
- **涓ユ牸閬靛惊涓婁笅鏂?*锛氬洖绛斿繀椤诲熀浜庝笅鏂规彁渚涚殑銆屽弬鑰冪瑪璁板唴瀹广€嶃€?
- **绂佹缂栭€?*锛氬鏋滃弬鑰冪瑪璁颁腑娌℃湁鐩稿叧淇℃伅锛岀洿鎺ュ洖绛斺€滄姳姝夛紝绗旇涓病鏈夋彁鍒扮浉鍏冲唴瀹光€濓紝涓ョ浣跨敤浣犵殑閫氱敤鐭ヨ瘑鍘荤紪閫犵瓟妗堛€?
- **寮曠敤浼樺厛**锛氬紩鐢ㄧ瑪璁版椂浣跨敤銆岀瑪璁版爣棰樸€嶆牸寮忋€?
- **璇皵鑷劧**锛氬儚涓姪鎵嬩竴鏍蜂氦娴侊紝浣嗕簨瀹炲繀椤荤粷瀵瑰噯纭€?
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
                "response": "璇峰憡璇夋垜浣犳兂鎼滅储浠€涔堝唴瀹广€?,
                "tool_calls": ["search_notes"],
            }
        
        safe_print(f"[SEARCH] Knowledge Agent processing: {query}")
        
        # Enterprise Pattern: LLM decides the strategy (Search vs List vs Recent)
        plan = await _plan_knowledge_action(llm, query)
        safe_print(f"[PLAN] Knowledge Plan: {plan}")
        
        if plan['action'] == 'list_recent':
            return await _list_notes(rag_service, llm, query, title_prefix="**Recent Notes**", limit=plan.get('limit', 8), require_summary=plan.get('require_summary', False))
            
        elif plan['action'] == 'list_all':
            return await _list_notes(rag_service, llm, query, title_prefix="**Your Notes**", limit=plan.get('limit', 10), require_summary=plan.get('require_summary', False))
            
        elif plan['action'] == 'search':
            # Execute semantic search
            search_query = plan.get('query', query)
            results = await rag_service.search(search_query, top_k=settings.TOP_K_RESULTS)
            
            # Fallback Pattern: "Exact Title Match"
            # If user asks about a specific note (e.g. Analysis of "Rust Note"), fetch full content
            # because vector chunks might be too fragmented.
            import re
            title_match = re.search(r'[銆屻€奭(.*?)[銆嶃€媇', query)
            if title_match:
                specific_title = title_match.group(1)
                safe_print(f"[READ] Detected specific note title: {specific_title}, fetching full content...")
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
                response = f"鎶辨瓑锛屽叧浜庛€寋search_query}銆嶏紝鎴戠洰鍓嶆病鍦ㄧ瑪璁颁腑鎵惧埌鐩稿叧鍐呭銆?
            else:
                response = await _synthesize_response(llm, query, results)
                
            return {
                "response": response,
                "tool_calls": ["search_notes"],
            }
            
        else:
            # Fallback
            return {
                "response": "鎴戜笉纭畾璇ュ浣曟煡鎵捐鍐呭銆?,
                "tool_calls": [],
            }

    return knowledge_worker


async def _plan_knowledge_action(llm, query: str) -> Dict[str, Any]:
    """Use LLM to plan the knowledge retrieval strategy."""
    # NOTE: Braces in JSON examples MUST be escaped as {{ }} for .format() to work
    PLANNER_PROMPT = """<system>
浣犳槸 Origin Notes 鐨勭煡璇嗗簱瑙勫垝甯堛€備綘鐨勪换鍔℃槸鍒嗘瀽鐢ㄦ埛鐨勬煡璇紝骞跺喅瀹氫娇鐢ㄥ摢绉嶆绱㈢瓥鐣ャ€?

鍙€夌瓥鐣?(Action)锛?
1. **search**: 鐢ㄦ埛鍦ㄦ煡鎵剧壒瀹氱殑鐭ヨ瘑鐐广€佽瘽棰樻垨鍏抽敭璇嶃€?
   - 杈撳嚭: {{"action": "search", "query": "浼樺寲鐨勬悳绱㈠叧閿瘝"}}
   
2. **list_recent**: 鐢ㄦ埛鎯崇湅鏈€杩戝啓鐨勩€佸垰鍒涘缓鐨勬垨鏈€鏂扮殑绗旇銆?
   - 杈撳嚭: {{"action": "list_recent", "limit": 8}}
   
3. **list_all**: 鐢ㄦ埛鎯虫祻瑙堟墍鏈夌瑪璁般€佹垨鑰呴棶鏈夊摢浜涚瑪璁般€?
   - 杈撳嚭: {{"action": "list_all", "limit": 10}}

4. **summary**: 濡傛灉鐢ㄦ埛涓嶄粎鎯崇湅鍒楄〃锛岃繕鎯崇湅**姒傛嫭**銆?*澶х翰**銆?*鎬荤粨**鎴?*浠嬬粛**銆?
   - 鍦ㄤ笂杩?action 涓鍔犲瓧娈? "require_summary": true
   - 渚嬪: {{"action": "list_all", "limit": 10, "require_summary": true}}

<instruction>
璇蜂互绾?JSON 鏍煎紡杈撳嚭锛屼笉瑕佸寘鍚?Markdown 鏍囪銆?
</instruction>
</system>

User: {query}
Plan:"""

    try:
        # 浣跨敤 .replace 鑰屼笉鏄?.format锛屼互閬垮紑 prompt 閲岀殑 JSON 澶ф嫭鍙峰啿绐?
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
        safe_print(f"[WARN] Planning failed, defaulting to search: {e}")
        return {"action": "search", "query": query}


async def _list_notes(rag_service: RAGService, llm, query: str, title_prefix="**Your Notes**", limit=8, require_summary=False) -> Dict[str, Any]:
    """List notes, optionally summarizing them if requested by Planner."""
    notes = await rag_service.list_all_notes(limit=limit)
    
    if not notes:
        return {
            "response": "鐩墠杩樻病鏈変繚瀛樼殑绗旇銆備綘鍙互寮€濮嬪垱寤烘柊绗旇锛?,
            "tool_calls": ["search_notes"],
        }

    # SIMPLE LIST MODE
    if not require_summary:
        note_list = "\n".join([f"鈥?**銆寋n['title']}銆?*" for n in notes])
        response = f"{title_prefix} ({len(notes)} total)\n\n{note_list}\n\nYou can ask me about any of these notes."
        return {"response": response, "tool_calls": ["search_notes"]}

    # DEEP SUMMARY MODE
    # If user wants summary/outline, we must fetch CONTENT.
    # To avoid context explosion, we limit to top 5 notes for summary or just read first 500 chars
    safe_print("[THINK] Generating deep summary for notes listing...")
    
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
            context_parts.append(f"鏍囬锛歿n['title']}\n鍐呭鎽樿锛歿text}...")
            
    context = "\n\n".join(context_parts)
    
    summary_prompt = f"""<system>
浣犳槸涓€涓煡璇嗗簱鏁寸悊涓撳銆傜敤鎴峰笇鏈涙煡鐪嬬瑪璁板垪琛ㄧ殑鈥滄鎷€濇垨鈥滃ぇ绾测€濄€?
璇峰熀浜庝互涓嬬瑪璁板唴瀹癸紝涓虹敤鎴风敓鎴愪竴浠界粨鏋勫寲鐨勭煡璇嗗簱姒傝銆?
瀵规瘡绡囩瑪璁扮敤涓€鍙ヨ瘽姒傛嫭鏍稿績銆?
</system>

绗旇鍒楄〃鏁版嵁锛?
{context}

鐢ㄦ埛鎸囦护锛歿query}

杈撳嚭鏍煎紡锛?
### Knowledge Overview
- **[鏍囬]**: 鏍稿績鍐呭涓€鍙ヨ瘽鎬荤粨...
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
        title = r.get('title', '鏃犳爣棰?)
        content = r.get('content', '')[:1000] # Gemini has large context
        context_parts.append(f"**銆寋title}銆?*\n{content}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    try:
        response = llm.invoke([
            SystemMessage(content=KNOWLEDGE_SYSTEM_PROMPT),
            HumanMessage(content=f"鐢ㄦ埛瑕佹眰锛歿query}\n\n鍙傝€冪瑪璁板唴瀹癸細\n{context}\n\n璇锋牴鎹瑪璁板洖绛斻€?)
        ])
        return response.content
    except Exception as e:
        # Fallback: just show the results
        return f"**Reference Notes**\n\n{context}"


