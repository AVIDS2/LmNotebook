# Origin Notes 交接说明（给 Claude）

更新时间：2026-02-07  
交接目标：让后续开发可以在当前基础上继续完成 Agent 成熟化，不重复踩坑。

## 1. 当前项目状态（事实）

### 1.1 当前有改动的文件（`git status --short`）

- `docs/release-checklist.md`（modified）
- `package.json`（modified）
- `src/backend/agent/graph.py`（modified）
- `src/backend/agent/state.py`（modified）
- `src/backend/agent/stream_adapter.py`（modified）
- `src/backend/agent/supervisor.py`（modified）
- `src/backend/api/chat.py`（modified）
- `src/backend/main.py`（modified）
- `src/renderer/src/components/agent/AgentBubble.vue`（modified）
- `.editorconfig`（untracked）
- `.gitattributes`（untracked）
- `docs/dev/agent-maturity-p0-plan.md`（untracked）
- `scripts/dev_utf8.ps1`（untracked）

### 1.2 已落地能力（可用但部分仍需稳定）

- LangGraph 工具审批链路已接入：后端可发 `approval_required`，前端可 `Accept/Reject/Auto-Accept`。
- 写操作有策略判定入口（`graph.py` 中 `_evaluate_tool_policy`），不再是散落判断。
- Agent 执行面板/任务卡基础 UI 已实现（`AgentBubble.vue`）。
- SSE 流适配仍兼容旧格式，同时新增审批事件透传（`stream_adapter.py`）。
- 一批中文乱码文案已修复（尤其是 Agent 面板里的历史栏、右键菜单等）。

### 1.3 二次核实结果（对照代码）

以下状态基于当前代码核实，不是口头估计。

#### 已解决

1. 审批事件基础链路可用  
   - 后端可发 `approval_required`（`src/backend/agent/stream_adapter.py`）。  
   - 前端可处理审批并执行 `Accept/Reject/Auto-Accept`（`src/renderer/src/components/agent/AgentBubble.vue`）。
2. 写策略统一入口已存在  
   - `_evaluate_tool_policy` 已在工具执行前调用（`src/backend/agent/graph.py`）。
3. `resume` 入参链路已打通  
   - API 请求支持 `resume`，Supervisor 使用 `Command(resume=...)` 恢复（`src/backend/api/chat.py`, `src/backend/agent/supervisor.py`）。
4. 执行面板 / 任务卡 / Structured diff UI 已存在  
   - 组件中已有任务卡、执行记录、diff 展示相关结构（`AgentBubble.vue`）。

#### 部分解决（有代码，但体验或一致性仍不稳）

1. 状态文案与时序  
   - 前端已有 `displayStatusText`、审批后即时置为“执行中”；  
   - 但流里仍有 `Thinking...` / `Executing approved task...` 混用路径，存在体验不一致风险。
2. 实时刷新  
   - 已有 `note_updated` 事件处理与 `refreshUpdatedNoteRealtime` 调用；  
   - 但历史反馈显示仍存在“需切换笔记才刷新”的场景，需继续回归验证。
3. 乱码治理  
   - 可见文案已修一批；  
   - 组件内仍有少量历史乱码注释/非关键字符串残留，建议后续清理。

#### 未完成（仍是后续任务）

1. 真正“二阶段审批”（Manual 模式下：审批后才生成最终写入内容）  
   - 当前仍是审批前已做大量生成准备，`Accept` 后看起来“秒完成”。
2. 独立 `policy_node`（图节点级）  
   - 目前是函数级策略，不是 StateGraph 的独立节点。
3. `resume` 防串台的严格校验  
   - 还未看到 `session_id + approval_id/tool_call_id` 的硬性一致性校验与拒绝策略。
4. 统一事件契约（包含 `approval_resolved` 等）  
   - 目前有 `approval_required`，但事件体系仍未完全收敛。

## 2. 当前核心问题（按紧急度）

### P0（最优先）

1. 审批流程心智不一致：  
   用户感知是“点 Accept 后秒完成”，原因是审批前模型已完成大量内容准备。  
   目标：切为“二阶段”——审批前仅任务卡，审批后才生成+执行写入。

2. 状态机时序偶发错位：  
   仍会出现“等待确认执行/思考中/执行中”展示混杂。

3. `__resume__` 恢复偶发串成闲聊回复：  
   日志出现恢复后返回 “Hello! How can I assist...”，而不是继续目标任务。

4. 笔记更新后实时刷新不稳定：  
   有时需要切换笔记才看到新内容。

### P1（其次）

5. 事件契约需收敛：`approval_required`、tool running/completed、note_updated 仍有重复或时序不清。

6. diff 审阅体验不稳定：  
   UI 有结构 diff 区，但触发和显示一致性不足。

7. 语言一致性：  
   用户中文输入仍偶发英文回复（策略应统一）。

## 3. 建议后续实施顺序（直接照此推进）

1. **二阶段审批落地（Manual Review 模式）**  
   - 阶段 A：仅产出任务卡（target / operation / impact / plan）。  
   - 阶段 B：`accept` 后再执行生成与写入。  
   - `Auto-Accept` 可保留快路径。

2. **状态机统一**  
   只允许：`pending_approval -> approved -> running -> completed/failed`。

3. **恢复链路防串台**  
   `resume` 必须校验 `session_id + approval_id/tool_call_id`，不匹配拒绝。

4. **实时刷新闭环**  
   `update_note` 成功后，若目标是当前打开笔记，立即触发 store 刷新和视图更新。

5. **事件契约统一（后端->前端）**  
   统一字段：`type`, `tool`, `tool_id`, `status`, `note_id`, `timestamp`, `message`。

6. **乱码收尾治理**  
   将 UI 文案集中化（后续可走 i18n），避免再次注入坏编码字符串。

## 4. 技术定位与代码入口

### 后端

- `src/backend/api/chat.py`
  - `/stream` 已支持 `resume`、`auto_accept_writes`。
  - 这里是请求入参与流输出主入口。
- `src/backend/agent/supervisor.py`
  - `invoke_stream()` 负责组装 `graph_input` 和 `Command(resume=...)`。
  - 有 checkpoint 预检与“损坏清理”逻辑，需重点看是否误清理。
- `src/backend/agent/graph.py`
  - 核心工作流、工具审批点、策略判定在这里。
  - 当前 `_evaluate_tool_policy` 是函数级策略（尚未拆成独立 `policy_node`）。
- `src/backend/agent/stream_adapter.py`
  - LangGraph 事件转 SSE 的关键层，前端是否正确显示基本由这里决定。
- `src/backend/agent/state.py`
  - 状态字段定义，涉及 `auto_accept_writes`、`next_tool_call`、`workflow_done`。

### 前端

- `src/renderer/src/components/agent/AgentBubble.vue`
  - 审批条、任务卡、执行记录、diff 展示、SSE chunk 解析均在该文件。
  - 当前复杂度高，是最需要控制改动范围的文件。

## 5. 验证清单（每次改动后必须跑）

1. 构建检查  
   - `npm run build`
   - `python -m py_compile src/backend/agent/graph.py`
   - `python -m py_compile src/backend/api/chat.py`
   - `python -m py_compile src/backend/agent/supervisor.py`
   - `python -m py_compile src/backend/agent/stream_adapter.py`

2. 交互回归（手测）
   - 新会话发送写请求（如“整理当前笔记格式”）：
     - 先看到任务卡 + 待审批
     - 点击 Accept 后才开始执行
     - 执行完成后状态正确收敛（无卡住转圈）
   - 点击 Reject：
     - 不修改笔记内容
   - 重新打开会话：
     - 执行记录可恢复，且不串到无关聊天
   - 中文输入：
     - 回复稳定中文，不出现乱码菜单文案

## 6. 打包与环境注意事项（非常重要）

以 `PACKAGING.md` 为准，关键点如下：

1. Python 打包必须使用仓库根目录 `backend_env`，不要用 conda base。  
2. 打包顺序：
   - `cd src/backend`
   - `..\..\backend_env\Scripts\activate`
   - `pyinstaller origin-backend.spec -y`
   - `cd ../..`
   - `npm run build:win`
3. 产物路径：
   - 后端：`src/backend/dist/origin_backend/`
   - 安装包：`dist/Origin Notes Setup 1.0.0.exe`

## 7. 编码与乱码风险说明

历史上已出现多次 UTF-8 / GBK 污染，尤其在：

- `AgentBubble.vue` 的硬编码文案
- Windows 终端日志打印

建议：

1. 强制文本文件 UTF-8（已新增 `.editorconfig` / `.gitattributes`，请继续遵守）。  
2. 不在 PowerShell 默认编码环境下做批量替换中文文案。  
3. 每次改 `AgentBubble.vue` 后立即跑构建并手测右键菜单、历史面板、输入框 placeholder。

## 8. 本次交接结论

- 骨架功能已具备：审批、执行、流式、任务卡、策略入口。  
- 当前主要是“稳定性与一致性收口”，不是从零重写。  
- 下一阶段应优先完成 P0 四项：二阶段审批、状态机收敛、resume 防串台、实时刷新闭环。
