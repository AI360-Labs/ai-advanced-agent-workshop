# Part 10 — MLflow observability & agent evaluation

Builds on Part 9. Adds an offline evaluation harness that scores the intent classifier (precision, recall, accuracy) and logs each run to MLflow, plus an opt-in MLflow trace of live agent runs.

| New file | Purpose |
|----------|---------|
| `eval/metrics.py` | Pure precision / recall / accuracy math (no LLM, no MLflow) |
| `eval/run_intent_eval.py` | Runs the live intent classifier over the dataset and logs metrics to MLflow |
| `utils/observability.py` | `setup_mlflow()` + flag-guarded `enable_autolog()` for live-run tracing |
| `tests/unit/test_metrics.py` | Offline unit tests pinning the metric definitions |

## Requirements

Same as Part 9, plus `mlflow` (added to `pyproject.toml`). No tracking server is required — runs are written to a local `./mlruns` directory by default.

## Setup

```bash
uv sync
cp settings/.env.example settings/.env.dev
# Fill in OPEN_ROUTER_API_KEY, DATABASE_URL
uv run pytest                            # unit + e2e tests (metric tests need no creds)
uv run python -m eval.run_intent_eval    # live intent eval -> logs a run to ./mlruns
uv run mlflow ui                         # browse results at http://127.0.0.1:5000
```

## Development

```bash
uv run ruff check . && uv run ruff format .
uv run pytest
```

---

## Evaluation & Observability

### Metrics

`eval/run_intent_eval.py` classifies every labelled example in [tests/fixtures/intent_dataset.csv](tests/fixtures/intent_dataset.csv) with the real intent node, then scores the predictions against the ground-truth labels and logs one MLflow run containing:

- **params** — task, temperature, model pool, dataset size.
- **metrics** — `accuracy`, `macro_precision`, `macro_recall`, and per-class `precision_<intent>` / `recall_<intent>`.
- **artifact** — `predictions.json`, the full per-example prediction table.

The metric math lives in `eval/metrics.py` and is pure (code, not the model — Rule 5), so it is unit-tested offline. Standard definitions: precision = TP / (TP + FP), recall = TP / (TP + FN), accuracy = correct / total.

### Tracing live runs

Tracing is off by default. Set `MLFLOW_TRACING=1` so `main.py` calls `mlflow.langchain.autolog()` and records each LangGraph run as an MLflow trace:

```bash
MLFLOW_TRACING=1 uv run python main.py
```

Both the eval harness and the tracer honour `MLFLOW_TRACKING_URI` (default `file:./mlruns`) and `MLFLOW_EXPERIMENT` (default `agentic-rag`).
