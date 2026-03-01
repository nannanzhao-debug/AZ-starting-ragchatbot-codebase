# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the application (from repo root)
./run.sh
# Or manually:
cd backend && uv run uvicorn app:app --reload --port 8000

# Access points
# Web UI: http://localhost:8000
# API docs: http://localhost:8000/docs
```

There are no tests, linting, or formatting configured in this project.

**Always use `uv` to manage dependencies and run commands. Use `uv run` to execute any Python files. Do not use `pip` or `python` directly.**

## Architecture

This is a RAG (Retrieval-Augmented Generation) chatbot for querying course materials. FastAPI serves both the API and the frontend as static files.

### Backend (`backend/`)

**RAG pipeline flow:**
1. On startup, `app.py` triggers `RAGSystem.add_course_folder()` to ingest all `.txt` files from `docs/`
2. `DocumentProcessor` parses structured course files (title/instructor/lessons format), splits content into 800-char sentence-based chunks with 100-char overlap
3. `VectorStore` stores data in two ChromaDB collections:
   - `course_catalog` — course metadata, used for fuzzy course name resolution via vector similarity
   - `course_content` — content chunks for semantic search, filterable by course title and lesson number
4. On query, `AIGenerator` calls Claude (`claude-sonnet-4-20250514`) with a `search_course_content` tool definition
5. Claude decides whether to search or answer directly. If it calls the tool, `CourseSearchTool` executes the vector search and returns formatted results
6. Claude generates the final response using retrieved context
7. `SessionManager` maintains in-memory conversation history (2 exchanges max per session)

**Key orchestration:** `RAGSystem` (in `rag_system.py`) is the central coordinator — it wires together all components and is the only class `app.py` interacts with directly.

**Config:** All tunable parameters (model names, chunk size, max results, etc.) live in `config.py` as a dataclass. API key loaded from `.env`.

### Frontend (`frontend/`)

Vanilla HTML/JS/CSS served as static files by FastAPI. Uses `marked.js` (CDN) for markdown rendering. Two API calls: `POST /api/query` for chat, `GET /api/courses` for sidebar stats.

### Documents (`docs/`)

Course transcript files with a specific format: first 3 lines are metadata (title, link, instructor), then `Lesson N: Title` markers separate content. The parser in `document_processor.py` depends on this exact format.
