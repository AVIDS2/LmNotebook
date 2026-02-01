# LangGraph 1.x 升级计划

> 📅 创建时间: 2026-02-01
> 🎯 目标: 将 Origin Notes Agent 从"手写 ReAct 循环"升级到"LangGraph 1.x StateGraph"

---

## 📊 现状分析

### 当前架构

```
supervisor.py (手写循环)
├── classify_intent() → 意图分类（CHAT/TASK）
├── invoke_stream() → 核心方法
│   ├── while turn < max_turns:  ← 手写循环
│   │   ├── model_with_tools.astream() ← 直接调 LLM
│   │   ├── if tool_calls: ← 手动判断
│   │   └── execute_tool_call() ← 手动执行
│   └── yield JSON chunks ← SSE 输出
└── SessionManager ← 状态持久化
```

### 前端数据格式 (SSE)

```json
// 状态更新
{"type": "status", "text": "🧠 思考中..."}

// 工具调用事件
{"tool_call": "note_created", "note_id": "xxx"}
{"tool_call": "note_updated", "note_id": "xxx"}
{"tool_call": "note_categorized", "note_id": "xxx", "category_id": "xxx"}
{"tool_call": "note_deleted", "note_id": "xxx"}

// 文本内容
{"text": "这是 AI 回复..."}

// 错误
{"error": "错误信息"}
```

### 依赖版本

| 包 | 当前版本 | 目标版本 |
|---|---------|---------|
| langgraph | >=0.2.60 | **>=1.0.7** |
| langchain | >=0.3.14 | >=1.0.0 |
| langchain-openai | >=0.2.14 | 最新 |

---

## 🎯 目标架构

### LangGraph StateGraph 设计

```
┌─────────────────────────────────────────────────────────────────┐
│              NoteAgentGraph (StateGraph)                        │
│                                                                 │
│   START ──► router ──►┬──► fast_chat ────────────────► END     │
│                       │                                         │
│                       └──► agent ──► tools ──┐                  │
│                              ▲               │                  │
│                              └───────────────┘                  │
│                           (循环 + tool_call_count 检测)          │
│                                                                 │
│   关键节点:                                                      │
│   ├── router: 意图路由 (基于 classify_intent)                    │
│   ├── fast_chat: 直接对话（无工具）                              │
│   ├── agent: LLM + Tool Binding                                 │
│   └── tools: ToolNode 执行                                      │
│                                                                 │
│   流式输出: stream_mode=["messages", "updates", "custom"]       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 状态定义 (TypedDict)

```python
from typing import Annotated, Optional, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class NoteAgentState(TypedDict):
    """Agent 状态 - LangGraph 1.x 规范"""
    
    # 核心消息历史（支持消息累加）
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 上下文信息
    active_note_id: Optional[str]
    active_note_title: Optional[str]
    context_note_id: Optional[str]
    context_note_title: Optional[str]
    note_content: Optional[str]
    selected_text: Optional[str]
    
    # 路由控制
    intent: str  # "CHAT" or "TASK"
    
    # 安全机制
    tool_call_count: int  # Doom Loop 检测
    last_tool_name: Optional[str]
    last_tool_input_hash: Optional[str]
```

---

## 🔄 后端-前端数据流对比

### 现有格式 (保持兼容)

```
Backend                           Frontend (AgentBubble.vue)
──────────                        ────────────────────────────
yield {"type": "status", ...}  →  currentStatus.value = "..."
yield {"tool_call": "...", ...} → handleToolCallEvent()
yield {"text": "..."}           → messages[i].content += "..."
yield {"error": "..."}          → isError = true
```

### 升级后格式 (保持完全兼容)

LangGraph 的流式输出会被转换成相同的 SSE 格式，**前端无需修改**。

```python
# 新的 stream 适配器
async def langgraph_stream_to_sse(graph, input_state, config):
    """将 LangGraph stream 转换为现有 SSE 格式"""
    
    async for mode, chunk in graph.astream(
        input_state,
        config,
        stream_mode=["messages", "updates", "custom"]
    ):
        if mode == "messages":
            # LLM token → {"text": "..."}
            if hasattr(chunk, 'content') and chunk.content:
                yield json.dumps({"text": chunk.content})
                
        elif mode == "custom":
            # 工具进度 → {"type": "status", "text": "..."}
            yield json.dumps({"type": "status", "text": chunk})
            
        elif mode == "updates":
            # 工具完成事件 → {"tool_call": "...", ...}
            if "tools" in chunk:
                # 解析工具结果，生成相应事件
                pass
```

---

## 📁 文件变更计划

### 新增文件

| 文件 | 描述 |
|-----|------|
| `agent/graph.py` | LangGraph StateGraph 核心定义 |
| `agent/nodes.py` | 图节点函数（router, agent, tools） |
| `agent/stream_adapter.py` | LangGraph → SSE 格式转换器 |

### 修改文件

| 文件 | 变更 |
|-----|------|
| `requirements.txt` | 升级 langgraph>=1.0.7 |
| `agent/supervisor.py` | 重构为使用 Graph |
| `agent/state.py` | 更新 State 定义 |
| `agent/tools.py` | 添加 Doom Loop 检测 + stream_writer |

### 保持不变

| 文件 | 原因 |
|-----|------|
| `api/chat.py` | SSE 格式兼容，无需修改 |
| 前端所有文件 | 后端保持相同输出格式 |

---

## 🛡️ 安全机制

### 1. Doom Loop 检测（借鉴 OpenCode）

```python
DOOM_LOOP_THRESHOLD = 3

def check_doom_loop(state: NoteAgentState, tool_name: str, tool_input: dict) -> bool:
    """检测是否陷入死循环"""
    input_hash = hashlib.md5(json.dumps(tool_input, sort_keys=True).encode()).hexdigest()
    
    if (state.get("last_tool_name") == tool_name and 
        state.get("last_tool_input_hash") == input_hash):
        count = state.get("tool_call_count", 0) + 1
        if count >= DOOM_LOOP_THRESHOLD:
            return True  # 触发 Doom Loop
    return False
```

### 2. 最大轮次限制

```python
MAX_TURNS = 5

def should_continue(state: NoteAgentState) -> Literal["continue", "end"]:
    """判断是否继续执行"""
    if state.get("tool_call_count", 0) >= MAX_TURNS:
        return "end"
    # ... 其他检查
```

---

## 🚀 实施步骤

### Phase 1: 升级依赖 ✅ DONE

1. ✅ 更新 `requirements.txt`
2. ✅ 运行 `pip install --force-reinstall langgraph langgraph-prebuilt`
3. ✅ 验证版本 (langgraph 1.0.7)

### Phase 2: 创建 Graph 核心 ✅ DONE

1. ✅ 创建 `agent/graph.py` - StateGraph 定义
2. ✅ 更新 `agent/state.py` - 新状态定义 (NoteAgentState)
3. ✅ 实现节点函数和条件路由

### Phase 3: 流式适配器 ✅ DONE

1. ✅ 创建 `agent/stream_adapter.py`
2. ✅ 确保输出格式与现有前端兼容

### Phase 4: 重构 Supervisor ✅ DONE

1. ✅ 修改 `supervisor.py` 使用新 Graph
2. ✅ 保持 API 接口不变 (invoke_stream)

### Phase 5: 测试验证 🔄 IN PROGRESS

1. ✅ 基本导入测试通过
2. ✅ AgentSupervisor 实例化成功
3. ⬜️ 集成测试 API 端点
4. ⬜️ 前端兼容性测试

---

## ✅ 验收标准

1. **功能等价**: 所有现有功能正常工作
2. **前端兼容**: 前端无需任何修改
3. **流式输出**: 响应速度不低于当前
4. **Doom Loop**: 连续 3 次相同操作自动停止
5. **可观测性**: 清晰的日志记录每个节点执行

---

## 🎤 面试话术准备

升级完成后，你可以这样讲：

> "我的 Agent 使用 **LangGraph 1.x StateGraph** 构建：
> 
> 1. **架构**：图节点包括 Router（意图分类）、Agent（LLM 推理）和 ToolNode（工具执行）
> 2. **流式输出**：使用 `stream_mode=["messages", "updates", "custom"]` 实现多模式并行流
> 3. **安全机制**：借鉴 OpenCode 的 Doom Loop 检测，防止无限循环
> 4. **状态管理**：使用 TypedDict + `add_messages` 注解实现消息累加
> 5. **设计决策**：选择 LangGraph 而非自研是因为它是 LangChain 生态标准，降低维护成本"

---

## 📚 参考资料

- LangGraph 1.0 官方文档: https://langchain-ai.github.io/langgraph/
- OpenCode 源码: `.for_look/opencode-dev/packages/opencode/src/session/`
- 当前前端消息处理: `src/renderer/src/components/agent/AgentBubble.vue`
