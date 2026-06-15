"""Thin MLflow wiring kept in one place so nodes/scripts stay MLflow-agnostic.

``setup_mlflow`` points the client at a tracking store and experiment.
``enable_autolog`` turns on LangGraph trace capture, but only when the operator
opts in with ``MLFLOW_TRACING=1`` — so importing this module costs nothing and a
normal run carries no tracing overhead.
"""

import os

import mlflow

from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TRACKING_URI = "file:./mlruns"
DEFAULT_EXPERIMENT = "agentic-rag"


def setup_mlflow(experiment: str | None = None) -> None:
    """Resolve the tracking store + experiment from env (with local defaults).

    ``MLFLOW_TRACKING_URI`` defaults to a local ``./mlruns`` directory so the
    workshop needs no server. ``MLFLOW_EXPERIMENT`` (or the ``experiment`` arg)
    names the experiment runs are grouped under.
    """
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI)
    experiment_name = experiment or os.getenv("MLFLOW_EXPERIMENT", DEFAULT_EXPERIMENT)
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    logger.debug(f"MLflow tracking_uri={tracking_uri} experiment={experiment_name}")


def enable_autolog() -> bool:
    """Enable MLflow autolog tracing of live LangGraph runs when opted in.

    Returns ``True`` if tracing was enabled, ``False`` (a no-op) otherwise. Guard
    with the return value so callers can log that tracing is on.
    """
    if os.getenv("MLFLOW_TRACING") != "1":
        return False

    import mlflow.langchain

    setup_mlflow()
    mlflow.langchain.autolog()
    logger.info("MLflow LangGraph autolog enabled (MLFLOW_TRACING=1)")
    return True
