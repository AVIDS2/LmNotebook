# LmNotebook

[中文](README.md) | [English](README.en.md)

LmNotebook is a local-first AI notebook for individuals and small teams.
It is built with Electron + Vue 3 + FastAPI + LangGraph, with notes, vector index, and chat session data stored locally by default.

## Why LmNotebook

- Local-first: your data stays on your machine by default
- Model-flexible: multi-provider and multi-model switching
- Agent-ready: Ask / Agent modes with approval workflow
- Release-ready: Windows / macOS / Linux distribution pipeline

## Core Capabilities

### Notes

- Markdown editing with structured formatting (headings, lists, code, tables, math)
- Folders / categories / pin / trash
- Full-text search and quick filtering
- Auto-save and local backup

### AI Agent

- LangGraph-based orchestration
- Tool calls: read, search, create, update, rename, categorize, delete
- Approval workflow: manual review / auto-accept
- Session modes: Ask (read-only) / Agent (action-enabled)
- Attachments: image and file upload, paste, drag-and-drop

### RAG

- Local FAISS vector retrieval
- Incremental note vector sync
- Configurable embedding model

## Tech Stack

- Frontend: Electron + Vue 3 + TypeScript + Pinia + TipTap
- Backend: Python + FastAPI + LangGraph + LangChain
- Retrieval: FAISS
- Storage: SQLite

## Quick Start

### Requirements

- Node.js 18+
- Python 3.10+
- npm or pnpm

### Install

```bash
npm install
cd src/backend
pip install -r requirements.txt
```

### Configure Models

Copy `src/backend/.env.example` to `src/backend/.env`:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key
MODEL_NAME=gpt-4o-mini

DASHSCOPE_API_KEY=your_dashscope_key
EMBEDDING_MODEL=text-embedding-v3
```

You can also manage providers and models from in-app `Model Settings`. UI config is persisted in the user data directory and overrides `.env` defaults.

### Run (Dev)

```bash
# backend
cd src/backend
python main.py

# frontend (new terminal)
npm run dev
```

## Packaging and Release

- Packaging guide: `PACKAGING.md`
- Release checklist: `docs/release-checklist.md`

## Docs

- Backend docs: `src/backend/README.md`
- Dev notes: `docs/dev/`
- Plans and design docs: `docs/plans/`

## License

MIT
