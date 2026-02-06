# Origin Notes Agent Backend

FastAPI backend for the Origin Notes agent. Built on LangGraph with OpenAI-compatible providers and local FAISS search.

## Quick Start

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8765
```

## Environment Variables

Core model settings (OpenAI-compatible protocol):
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `MODEL_NAME`

Embeddings (DashScope default in this repo):
- `DASHSCOPE_API_KEY`
- `EMBEDDING_MODEL`

You can also manage model providers inside the app UI. Providers are stored in `models.json` under the user data directory and override `.env` defaults.

## Architecture (Current)

- `LangGraph` state machine with router + tool loop
- SSE streaming adapter for the frontend chat UI
- Tools: note CRUD, category, knowledge search
- Vector search: FAISS + remote embeddings

Key modules:
- `agent/graph.py` - LangGraph state machine
- `agent/supervisor.py` - API entry + streaming
- `agent/tools.py` - tool implementations
- `services/rag_service.py` - FAISS + embeddings
- `services/note_service.py` - SQLite CRUD

## Health Check

`GET /health` returns provider/model info and configuration status.
