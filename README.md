# Origin Notes

简约风格的本地 AI 笔记应用，专注快速记录与智能检索。基于 Electron + Vue 3 + Python 构建，数据完全保存在本地。

## 核心特性

### 笔记功能

- 富文本编辑（标题、列表、任务清单、代码块、表格、数学公式）
- 图片粘贴与本地存储
- 分类管理（新建/重命名/删除/拖拽排序）
- 置顶、回收站、批量操作
- 全文搜索（关键词高亮）
- 拖拽排序笔记
- 自动保存（防抖 600ms）

### AI 助手 (Origin)

- 基于 RAG 的笔记知识库搜索
- 智能问答（支持多种 LLM：OpenAI、阿里云、DeepSeek 等）
- 笔记内容读取、创建、更新、删除
- 对话历史记录（置顶/重命名/删除）
- 流式输出，实时响应

### 数据管理

- 本地 SQLite 存储（WAL 模式优化）
- 自定义数据目录
- 自动备份
- JSON 导入/导出
- Markdown 导出

## 技术栈

- **前端**：Electron + Vue 3 + TypeScript + Pinia + TipTap
- **后端**：Python + FastAPI + LangGraph + ChromaDB
- **数据库**：SQLite (better-sqlite3) + 向量索引

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

复制 `src/backend/.env.example` 为 `src/backend/.env`，配置 LLM API：

```env
# 阿里云（推荐）
LLM_PROVIDER=aliyun
DASHSCOPE_API_KEY=your_api_key

# 或 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
```

### 启动开发

```bash
# 启动后端
cd src/backend
python main.py

# 启动前端（新终端）
npm run dev
```

### 打包发布

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux
```

## 项目结构

```
src/
  main/           Electron 主进程
  preload/        预加载脚本（IPC 桥接）
  renderer/       渲染进程（Vue 应用）
    components/   视图组件
    stores/       Pinia 状态管理
    database/     数据仓库
    services/     业务服务
  backend/        Python 后端
    agent/        LangGraph AI Agent
    api/          FastAPI 路由
    core/         LLM 配置
    services/     RAG 服务
```

## 许可协议

MIT License
