# Part 10 — MLflow observability & agent evaluation

Builds on Part 9. We add an offline **evaluation** harness that scores the intent classifier
(precision, recall, accuracy) and logs each run to **MLflow**, plus an opt-in MLflow **trace**
of live agent runs. The metric math is pure code (not the model), so it's unit-tested offline.

## Roadmap

1. Write pure **metric math** (`precision` / `recall` / `accuracy`) with no LLM or MLflow deps
2. Build the **eval harness** that classifies the labelled dataset and logs an MLflow run
3. Add **observability** helpers: `setup_mlflow()` + a flag-guarded `enable_autolog()`
4. Trace **live agent runs** opt-in via `MLFLOW_TRACING=1`
5. Tests: offline unit tests pinning the metric definitions

## Layout (added to Part 9)

```text
part_10/
├── eval/
│   ├── __init__.py
│   ├── metrics.py            # pure precision / recall / accuracy math (no LLM, no MLflow)
│   └── run_intent_eval.py    # runs the live intent classifier, logs metrics to MLflow
├── utils/
│   └── observability.py      # setup_mlflow() + flag-guarded enable_autolog()
└── tests/
    └── unit/test_metrics.py  # offline tests pinning the metric definitions
```

## Requirements

Same as Part 9, plus `mlflow` (added to `pyproject.toml`). No tracking server is required —
runs are written to a local `./mlruns` directory by default.

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

> 💾 **Commit at the end of every workshop part.** Once the checklist is green, save your
> progress with a commit named after the part you just finished, e.g.:
>
> ```bash
> git add -A
> git commit -m "Part 10: MLflow observability — intent eval harness + live tracing"
> ```
>
> This gives you a clean checkpoint per part, so you can always see what each step added.

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
