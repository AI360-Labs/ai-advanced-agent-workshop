"""Evaluate the live intent classifier and log the metrics to MLflow.

This is the agent's *evaluation phase*: run every labelled example in
``tests/fixtures/intent_dataset.csv`` through the real intent node, score the
predictions against the ground-truth labels, and record params, precision /
recall / accuracy, and the full prediction table as one MLflow run.

Run it (needs a live LLM, like the integration tests):

    uv run python -m eval.run_intent_eval

Then inspect results with ``uv run mlflow ui`` → http://127.0.0.1:5000.
"""

import asyncio

import mlflow

from agent.nodes.intent import arecognize_intent
from config.settings import get_tasks
from eval.metrics import evaluate
from tests.fixtures import INTENT_EXAMPLES, IntentExample
from utils.logger import get_logger
from utils.observability import setup_mlflow, enable_autolog

logger = get_logger(__name__)

RUN_NAME = "intent-eval"


async def _predict(example: IntentExample) -> str:
    """Run one example through the real intent node and return its label."""
    update = await arecognize_intent({"question": example.text})
    return update["intent"].intent


async def _predict_all(examples: list[IntentExample]) -> list[str]:
    """Classify every example concurrently, preserving dataset order."""
    return await asyncio.gather(*(_predict(example) for example in examples))


def main() -> None:
    setup_mlflow()
    if enable_autolog():
        logger.info("MLflow tracing enabled")
    examples = INTENT_EXAMPLES
    labels = [example.expected for example in examples]
    predictions = asyncio.run(_predict_all(examples))

    metrics = evaluate(predictions, labels)
    task = get_tasks().task("intent")

    with mlflow.start_run(run_name=RUN_NAME):
        mlflow.log_params(
            {
                "task": "intent",
                "temperature": task.temperature,
                "models": ",".join(task.models),
                "dataset_size": len(examples),
            }
        )
        mlflow.log_metric("accuracy", metrics.accuracy)
        mlflow.log_metric("macro_precision", metrics.macro_precision)
        mlflow.log_metric("macro_recall", metrics.macro_recall)
        for cls in metrics.per_class:
            mlflow.log_metric(f"precision_{cls.label}", cls.precision)
            mlflow.log_metric(f"recall_{cls.label}", cls.recall)

        mlflow.log_dict(
            {
                "predictions": [
                    {
                        "text": example.text,
                        "expected": example.expected,
                        "predicted": predicted,
                        "correct": example.expected == predicted,
                    }
                    for example, predicted in zip(examples, predictions)
                ]
            },
            "predictions.json",
        )

    logger.info(
        f"accuracy={metrics.accuracy:.3f} "
        f"macro_precision={metrics.macro_precision:.3f} "
        f"macro_recall={metrics.macro_recall:.3f}"
    )


if __name__ == "__main__":
    main()
