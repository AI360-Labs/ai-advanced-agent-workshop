# Part 7 — Conversation persistence (SQLite)

Builds on Part 6. We persist each completed Q&A turn to a local **SQLite** file
(`agent.db`). PostgreSQL stays read-only for Northwind and document search;
conversation history goes to SQLite so every participant gets persistence with no
extra setup. A new `persist_turn` graph node writes the turn, and all terminal
paths (approved answers and refusals) funnel through it before `END`.

## Roadmap

1. Add a `session_id` field to `AgentState` in `agent/state.py`
2. Define `Conversation` and `Message` ORM models in `db/persistence_models.py`
3. Create the SQLite engine, session factory, and `init_db()` in `db/sqlite.py` (adds the `aiosqlite` dependency and a `sqlite_path` setting)
4. Implement insert helpers in `db/persistence.py`
5. Create the `persist_turn` node in `agent/nodes/persist.py`
6. Route all terminal paths through `persist_turn` in `agent/graph.py`
7. Add tests in `tests/unit/test_persistence_models.py` and update `tests/unit/test_human_review.py`

## Layout (added to Part 6)

```text
part_7/
├── agent/
│   ├── graph.py                # Routes terminal paths to persist_turn
│   ├── state.py                # Adds session_id
│   └── nodes/
│       └── persist.py          # Saves each completed turn
├── config/
│   └── settings.py             # Adds sqlite_path field
├── db/
│   ├── persistence_models.py   # SQLite-compatible Conversation / Message ORM
│   ├── sqlite.py               # Async SQLite engine, session factory, init_db()
│   └── persistence.py          # Insert helpers for conversation/message rows
└── tests/unit/
    ├── test_human_review.py    # Routing now resolves to persist_turn
    └── test_persistence_models.py
```

## Why SQLite

The Northwind read path uses PostgreSQL (`db/session.py`). Conversation history uses
a separate local SQLite engine (`db/sqlite.py`) via the `sqlite+aiosqlite:///`
async URL — this needs the `aiosqlite` driver. Models use cross-platform
`Uuid` and `JSON` column types instead of PostgreSQL-specific `JSONB`. The path is
configurable through the `SQLITE_PATH` environment variable and defaults to
`agent.db`.

## Persistence node — `agent/nodes/persist.py`

```python
async def persist_turn(state: AgentState) -> dict:
    """Write the completed Q&A turn to the local SQLite database."""
    session_id = state.get("session_id", "default")
    ...
    await init_db()
    async with get_sqlite_session_factory()() as session:
        await save_agent_turn(session, session_id, question, answer, steps)
    return {}
```

`init_db()` creates `agent.db` and its tables on the first turn (idempotent
afterwards). `save_agent_turn` stores the user question and assistant answer (plus
a `steps` payload of thinking/intent/sql) in a single transaction.

## Routing — `agent/graph.py`

`route_after_review` now returns `"persist_turn"` instead of `END` when an answer
is approved, and the `refuse` path also flows into `persist_turn`. `persist_turn`
is the single terminal node before `END`.

See [db/schema_reference.md](db/schema_reference.md).
