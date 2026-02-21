# LmNotebook

[中文](README.md) | [English](README.en.md)

LmNotebook 是一款本地优先的 AI 笔记应用，面向个人与小团队。
应用采用 Electron + Vue 3 + FastAPI + LangGraph 架构，默认将笔记、向量索引和会话数据保存在本地设备。

## 为什么是 LmNotebook

- Local-first: 数据默认本地，离线可读写
- Model-flexible: 兼容多模型提供商与多模型切换
- Agent-ready: 支持 Ask / Agent 模式与工具审批流
- Release-ready: Windows / macOS / Linux 发布链路

## 核心能力

### 笔记系统

- Markdown 编辑与结构化排版（标题、列表、代码、表格、公式）
- 文件夹 / 分类 / 置顶 / 回收站
- 全文搜索与快速过滤
- 自动保存与本地备份

### AI Agent

- LangGraph 工作流编排
- 工具调用：读取、搜索、创建、更新、重命名、分类、删除
- 审批流：手动审核 / 自动接受
- 会话模式：Ask（只读）/ Agent（可执行）
- 附件输入：图片与文件上传、粘贴、拖拽

### RAG 与检索

- 本地 FAISS 向量检索
- 笔记增量向量同步
- 可配置 Embedding 模型

## 技术栈

- 前端：Electron + Vue 3 + TypeScript + Pinia + TipTap
- 后端：Python + FastAPI + LangGraph + LangChain
- 检索：FAISS
- 存储：SQLite

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.10+
- npm 或 pnpm

### 安装依赖

```bash
npm install
cd src/backend
pip install -r requirements.txt
```

### 配置模型

复制 `src/backend/.env.example` 为 `src/backend/.env`：

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key
MODEL_NAME=gpt-4o-mini

DASHSCOPE_API_KEY=your_dashscope_key
EMBEDDING_MODEL=text-embedding-v3
```

你也可以在应用内 `Model Settings` 中配置模型，设置会写入用户目录并覆盖 `.env` 默认值。

### 开发运行

```bash
# backend
cd src/backend
python main.py

# frontend (new terminal)
npm run dev
```

## 打包与发布

- 打包说明：`PACKAGING.md`
- Release 检查清单：`docs/release-checklist.md`

## 文档

- 后端说明：`src/backend/README.md`
- 开发记录：`docs/dev/`
- 设计与计划：`docs/plans/`

## 许可证

MIT
