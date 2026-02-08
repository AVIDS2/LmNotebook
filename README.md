# Origin Notes

[中文](README.md) | [English](README.en.md)

Origin Notes 是一款本地优先的 AI 笔记应用，基于 Electron + Vue 3 + Python 构建，数据默认保存在本机。

## 项目概览

- Electron 主进程负责窗口/托盘、SQLite 数据库、图片存储与备份，数据目录默认在 `Documents/OriginNotes`（可在应用内迁移）。
- 预加载脚本通过 `window.electronAPI` 暴露 IPC 能力，渲染进程使用 Vue 3 + Pinia + TipTap 实现笔记 UI。
- AI 后端为 FastAPI + LangGraph，默认监听 `127.0.0.1:8765`，处理聊天、向量同步与 RAG 检索，前端通过 HTTP 调用。

## 核心功能

### 笔记
- 富文本编辑（标题、列表、任务、代码、表格、公式）
- 图片本地存储
- 分类、置顶、回收站、批量操作
- 全文搜索
- 拖拽排序
- 自动保存

### AI 助手 (Origin)
- 基于 LangGraph 的 agent + 工具调用
- 基于 FAISS 的知识库检索（RAG）
- 通过 OpenAI-compatible 协议接入多家模型
- 流式输出
- 笔记工具：创建 / 更新 / 重命名 / 删除 / 分类

### 数据
- 本地 SQLite 存储（better-sqlite3）
- 可配置数据目录
- 自动备份
- 导出/导入（JSON、Markdown）

## 技术栈

- 前端：Electron + Vue 3 + TypeScript + Pinia + TipTap
- 后端：Python + FastAPI + LangGraph + LangChain
- 向量检索：FAISS
- 存储：SQLite

## 快速开始

### 环境要求
- Node.js 18+
- Python 3.10+
- pnpm / npm

### 安装

```bash
# 前端依赖
npm install

# 后端依赖
cd src/backend
pip install -r requirements.txt
```

### 配置

复制 `src/backend/.env.example` 为 `src/backend/.env` 并设置必要的环境变量。

```env
# OpenAI-compatible provider (OpenAI / DeepSeek / Gemini / etc.)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key
MODEL_NAME=gpt-4o-mini

# Embeddings (本仓库默认 DashScope)
DASHSCOPE_API_KEY=your_dashscope_key
EMBEDDING_MODEL=embedding-2
```

也可以在应用内的 Model Settings 中配置模型提供商。配置会保存到用户数据目录下的 `models.json`，并覆盖 `.env` 默认值。

### 开发运行

```bash
# 启动后端
cd src/backend
python main.py

# 启动前端（新终端）
npm run dev
```

## 打包

详见 `PACKAGING.md`。注意：使用 PyInstaller 时必须激活 `backend_env` 虚拟环境。

## 文档索引

- `PACKAGING.md` - 打包流程（必须使用 backend_env）
- `src/backend/README.md` - 后端说明与架构
- `docs/dev/` - 开发记录与排查日志

## 目录结构

```text
src/
  main/           Electron 主进程
  preload/        IPC 桥接
  renderer/       Vue 应用
    components/
    stores/
    database/
    services/
  backend/        Python 后端
    agent/        LangGraph agent
    api/          FastAPI 路由
    core/         LLM 配置
    services/     RAG + note 服务
```

## License

MIT
