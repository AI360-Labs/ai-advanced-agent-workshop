# Part 3 — Data layer: ORM models, schemas & async sessions

Builds on Part 2. We add the async **database layer** the SQL agent will sit on top of:
SQLAlchemy **ORM models** for the Northwind tables, Pydantic **row schemas**, a
connection-pooled **async session**, and a strict table **allowlist** that limits what the
agent can ever query.

## Roadmap

1. Define the **table allowlist** (`ALLOWED_TABLES` frozenset) — the agent's hard boundary
2. Map the Northwind tables (and `documents.reports`) as **ORM models**
3. Describe rows as typed Pydantic **schemas** for safe LLM input/output
4. Set up a lazy **async engine + session** with connection pooling
5. Write a human-readable **schema reference** for use inside prompts
6. Add three new **config variables** (`DATABASE_URL`, `EMBEDDING_MODEL`, `LLM_MAX_RETRIES`)
7. Tests: offline schema unit tests + an opt-in live DB connection test

## Layout (added to Part 2)

```text
part_3/
├── db/
│   ├── __init__.py
│   ├── allowlist.py            # ALLOWED_TABLES frozenset — guards what the agent can query
│   ├── models.py               # SQLAlchemy ORM models for Northwind + documents.reports
│   ├── schemas.py              # Pydantic row schemas (ProductRow, ReportMatch, SqlQueryResult, …)
│   ├── queries.py              # parameterised read queries over the allowed tables
│   ├── session.py              # lazy AsyncEngine + async_sessionmaker; get_session()
│   └── schema_reference.md     # human-readable schema reference used in LLM prompts
├── explanation_materials/
│   ├── ingest_reports_walkthrough.ipynb
│   └── reports/                # sample PDF reports to ingest
└── tests/
    ├── integration/test_db_connection.py
    └── unit/test_db_schemas.py
```

## New config variables

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
