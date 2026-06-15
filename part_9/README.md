# Part 9 — End-to-end smoke tests

Builds on Part 8. Adds in-process E2E smoke tests using a `FakeGraph` stub (no LLM, no DB required), a convenience server launcher, and a browser chat UI.

| New file | Purpose |
|----------|---------|
| `tests/e2e/test_api_smoke.py` | In-process FastAPI smoke tests — health, `/chat`, OpenAPI schema |
| `tests/unit/test_select_query.py` | Unit tests for the `select_query` routing node |
| `run_api.py` | Convenience entry point: `uv run python run_api.py` starts uvicorn on port 8000 |
| `ui.html` | Single-file browser chat UI — open after starting the server |

## Requirements

Same as Part 8. No additional dependencies.

## Setup

```bash
uv sync
cp settings/.env.example settings/.env.dev
# Fill in OPEN_ROUTER_API_KEY, DATABASE_URL
uv run pytest              # unit + e2e tests (e2e uses FakeGraph, no live creds needed)
uv run python run_api.py   # start the API, then open ui.html in a browser
```

## Development

```bash
uv run ruff check . && uv run ruff format .
uv run pytest
```

---

## API Documentation

When the server is running, interactive API documentation is available at `/docs` (Swagger UI) or `/redoc` (ReDoc).

### Endpoints

- `GET /health` - Health check status.
- `POST /chat` - Send a message to the agent and receive the final answer.
- `POST /chat/resume` - Resume a paused agent thread with approval or feedback.

To extend the API, define new request and response models in `api/schemas.py`, and register new endpoints in `api/app.py`. The graph is compiled into a singleton in `api/deps.py` to ensure fast subsequent requests.
