# Agentic RAG Training — LangGraph SQL Agent

Hands-on training to build a production-shaped LangGraph agent over a Northwind PostgreSQL database and report documents.

## Parts (cumulative snapshots)

| Part | Topic |
|------|--------|
| [part_1](part_1/) | Pydantic, config, LLM client |
| [part_2](part_2/) | Agent state, intent recognition, determinism tests |
| [part_3](part_3/) | SQLAlchemy ORM (mandatory tables only) |
| [part_4](part_4/) | Guarded SQL + vector retrieval nodes |
| [part_5](part_5/) | Graph assembly and routing |
| [part_6](part_6/) | Human-in-the-loop |
| [part_7](part_7/) | SQLite conversation persistence |
| [part_8](part_8/) | FastAPI wrapper |
| [part_9](part_9/) | E2E smoke tests |
| [part_10](part_10/) | MLflow observability + intent evaluation metrics |

Each folder has its own `pyproject.toml` and `uv` environment. Start in `part_1` and progress sequentially; later parts copy the previous part and add new material.

## Quick start (latest part)

```bash
cd part_10
cp settings/.env.example settings/.env.dev
```

Fill in `settings/.env.dev`:

| Variable | Purpose |
|----------|---------|
| `OPEN_ROUTER_API_KEY` | LLM + query embeddings (OpenRouter) |
| `DATABASE_URL` | **Postgres** connection (`postgresql+asyncpg://…`) — Northwind + RAG documents |
| `SQLITE_PATH` | Local SQLite file for conversation log (default `agent.db`) |
| `EMBEDDING_MODEL` | e.g. `openai/text-embedding-3-small` |

```bash
uv sync
uv run python -m pytest
```
