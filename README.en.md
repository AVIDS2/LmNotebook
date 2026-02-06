# Origin Notes

[中文](README.md) | [English](README.en.md)

Origin Notes is a local-first AI note app built with Electron + Vue 3 + Python. All data stays on your machine by default.

## Key Features

### Notes
- Rich text editor (headings, lists, tasks, code, tables, math)
- Images stored locally
- Categories, pinning, trash, batch operations
- Full-text search
- Drag-and-drop ordering
- Auto-save

### AI Assistant (Origin)
- LangGraph-based agent with tool calling
- RAG search over your notes (FAISS)
- Multi-provider LLM via OpenAI-compatible protocol
- Streaming responses
- Note CRUD via tools (create / update / rename / delete / categorize)

### Data
- Local SQLite storage (better-sqlite3)
- Configurable data directory
- Automatic backups
- Export/Import (JSON, Markdown)

## Tech Stack

- Frontend: Electron + Vue 3 + TypeScript + Pinia + TipTap
- Backend: Python + FastAPI + LangGraph + LangChain
- Vector Search: FAISS
- Storage: SQLite

## Quick Start

### Requirements
- Node.js 18+
- Python 3.10+
- pnpm / npm

### Install

```bash
# Frontend deps
npm install

# Backend deps
cd src/backend
pip install -r requirements.txt
```

### Configure

Copy `src/backend/.env.example` to `src/backend/.env` and set the keys you need.

```env
# OpenAI-compatible provider (OpenAI / DeepSeek / Gemini / etc.)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key
MODEL_NAME=gpt-4o-mini

# Embeddings (DashScope default in this repo)
DASHSCOPE_API_KEY=your_dashscope_key
EMBEDDING_MODEL=embedding-2
```

You can also manage model providers in the app UI (Model Settings). This persists to `models.json` in the user data directory and overrides `.env` defaults.

### Run (Dev)

```bash
# Backend
cd src/backend
python main.py

# Frontend (new terminal)
npm run dev
```

## Packaging

See `PACKAGING.md` for the correct packaging flow. Important: use the `backend_env` virtual environment when running PyInstaller.

## Docs Index

- `PACKAGING.md` - Packaging flow (backend_env required)
- `src/backend/README.md` - Backend setup and architecture
- `docs/dev/` - Developer notes and investigation logs

## Project Structure

```text
src/
  main/           Electron main process
  preload/        IPC bridge
  renderer/       Vue app
    components/
    stores/
    database/
    services/
  backend/        Python backend
    agent/        LangGraph agent
    api/          FastAPI routes
    core/         LLM config
    services/     RAG + note services
```

## License

MIT
