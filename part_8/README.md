# Part 8 — FastAPI service: chat & resume endpoints

Builds on Part 7. We wrap the LangGraph **agent** in a **FastAPI** REST API: typed
request/response **schemas**, a cached compiled-graph **dependency**, chat endpoints, and
interactive Swagger documentation at `/docs`.

## Roadmap

1. Define request/response **schemas** (`ChatRequest`, `ChatResponse`, `ResumeRequest`)
2. Compile and cache the graph once as a **singleton dependency**
3. Expose the agent over **HTTP** endpoints (health, chat, resume)
4. Browse and try it live through **Swagger** at `/docs`
5. Tests: unit tests for the API schemas

## Layout (added to Part 7)

```text
part_8/
├── api/
│   ├── __init__.py
│   ├── schemas.py          # ChatRequest, ChatResponse, ResumeRequest
│   ├── deps.py             # compiles and caches the graph as a singleton
│   └── app.py              # FastAPI app with all endpoints
└── tests/
    └── unit/test_api_schemas.py
```

## Endpoints

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
