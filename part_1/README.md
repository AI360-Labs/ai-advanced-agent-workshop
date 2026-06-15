# agentic-rag — Part 1: Foundation

Welcome 👋 This is the **starting point for the workshop**. You'll fork this folder into your
own repo and build the agentic RAG system on top of it, part by part. Part 1 is the
foundation everything else depends on: typed configuration, one shared logger, and an async
LLM client with automatic model fallback.

By the end of this part you'll be able to run `main.py` and watch a real LLM call return a
poem and a validated, structured summary — proof that your config, secrets, and model client
are all wired up correctly.

## What's in this part

| File | Purpose |
|------|---------|
| `config/settings.py` | Reads secrets from `settings/.env.{APP_ENV}` via `pydantic-settings` |
| `config/tasks.yaml` | Model pool and temperature per task (no secrets, version-controlled) |
| `utils/logger.py` | Single shared logger — reads `LOG_LEVEL` from config |
| `utils/llm_client.py` | `LLMClient` — task-scoped wrapper over `litellm.Router` via OpenRouter |
| `main.py` | A runnable example that ties it all together |

The key idea: **secrets** (your API key) live in gitignored `.env` files, while **behaviour**
(which models each task uses, at what temperature) lives in a committed `config/tasks.yaml`.
One LLM client, configured per task, with provider fallback for free.

## Requirements

- Python ≥ 3.13 — managed for you by `uv`, no separate install needed
- [`uv`](https://docs.astral.sh/uv/) — the package manager and project runner
- An [OpenRouter API key](https://openrouter.ai/keys) — for the LLM calls

## Setup

1. **Install dependencies** (this also creates the virtual environment):

   ```bash
   uv sync
   ```

2. **Create your secrets file** from the committed template:

   ```bash
   cp settings/.env.example settings/.env.dev
   ```

3. **Add your key.** Open `settings/.env.dev` and paste your real key into
   `OPEN_ROUTER_API_KEY`. This file is gitignored, so your secret never gets committed.

`APP_ENV` (an OS environment variable, default `dev`) selects which `.env.*` file is loaded —
that single switch is the whole dev/prod split. Behavioural config (models, temperatures)
lives in `config/tasks.yaml`; secrets live only in the gitignored `settings/.env.*` files.

## Run it

```bash
uv run main.py
```

You should see logs for each LLM client being created (task, temperature, model list), then a
generated poem and a validated `ServerSummary` object. If a model in the pool is busy, watch
the litellm router fall back to the next one automatically — that's the resilience built into
the client.

## Development

Run the checklist before every commit:

```bash
uv run ruff check . && uv run ruff format .   # lint + format
uv run pytest                                  # tests green
```

A green `ruff` and a green `pytest` is the definition of "ready to commit" in this project.

> 💾 **Commit at the end of every workshop part.** Once the checklist is green, save your
> progress with a commit named after the part you just finished, e.g.:
>
> ```bash
> git add -A
> git commit -m "Part 1: foundation — config, logger, LLM client"
> ```
>
> This gives you a clean checkpoint per part, so you can always see what each step added.

## Where to go next

Once `main.py` runs and the tests pass, you're ready to build on this foundation. Later parts
add agent state, a LangGraph graph, a SQL/document retrieval layer, human-in-the-loop review,
and a FastAPI wrapper — each one a cumulative snapshot that copies the previous part and adds
new material.
