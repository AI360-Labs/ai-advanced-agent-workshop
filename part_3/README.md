# agentic-rag — Part 3: Data Layer

Builds on Part 2. Adds the async database layer: SQLAlchemy ORM models for the Northwind
tables, Pydantic row schemas, a connection-pooled async session, and a strict table allowlist
that limits what the SQL agent can query.

| New file | Purpose |
|----------|---------|
| `db/allowlist.py` | `ALLOWED_TABLES` frozenset — guards what the agent can query |
| `db/models.py` | SQLAlchemy ORM models for Northwind tables and `documents.reports` |
| `db/schemas.py` | Pydantic row schemas (`ProductRow`, `ReportMatch`, `SqlQueryResult`, …) |
| `db/session.py` | Lazy-init `AsyncEngine` + `async_sessionmaker`; `get_session()` yields scoped sessions |
| `db/schema_reference.md` | Human-readable schema reference used in LLM prompts |

`config/settings.py` gains three new variables — add them to `settings/.env.dev`:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://…` — must use the async dialect |
| `EMBEDDING_MODEL` | e.g. `openai/text-embedding-3-small` |
| `LLM_MAX_RETRIES` | Max structured-output retry attempts (default 2) |

## Requirements

- Python ≥ 3.13, [`uv`](https://docs.astral.sh/uv/), a running PostgreSQL instance

## Setup

```bash
uv sync
cp settings/.env.example settings/.env.dev
# Fill in DATABASE_URL, EMBEDDING_MODEL
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
> git commit -m "Part 3: data layer — ORM models, row schemas, async session"
> ```
>
> This gives you a clean checkpoint per part, so you can always see what each step added.
