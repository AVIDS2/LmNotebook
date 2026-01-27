# Origin Notes Agent Backend

A FastAPI-powered AI agent backend using LangGraph Supervisor pattern with GLM-4.7-Flash.

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

- `GLM_API_KEY`: Your ZhipuAI API key (required)

## Architecture

```
Supervisor (GLM-4.7-Flash)
├── KnowledgeWorker (Agentic RAG + FAISS)
├── NoteWorker (CRUD operations)
└── FormatWorker (Markdown beautification)
```
