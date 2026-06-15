# agentic-rag — Part 8: FastAPI Service

Builds on Part 7. Wraps the LangGraph agent in a FastAPI REST API with three chat endpoints
and interactive Swagger documentation at `/docs`.

| New file | Purpose |
|----------|---------|
| `api/schemas.py` | Pydantic request/response models (`ChatRequest`, `ChatResponse`, `ResumeRequest`) |
| `api/deps.py` | Compiles and caches the graph as a singleton |
| `api/app.py` | FastAPI app with all endpoints |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Blocking — runs the agent and returns the final answer |
| `POST` | `/chat/resume` | Resumes a paused thread after human review |

## Requirements

Same as Part 7, plus `fastapi`, `uvicorn`, and `httpx` (installed automatically via `uv sync`).

## Usage

```bash
uv sync
uvicorn api.app:app --reload --port 8000
# Open http://localhost:8000/docs
```

## Development

```bash
uv run ruff check . && uv run ruff format .
uv run pytest
```

> 💾 **Commit at the end of every workshop part.** Once the checklist is green, save your
> progress with a commit named after the part you just finished, e.g.:
>
> ```bash
> git add -A
> git commit -m "Part 8: FastAPI service — chat and resume endpoints"
> ```
>
> This gives you a clean checkpoint per part, so you can always see what each step added.
