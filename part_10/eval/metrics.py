"""Multi-class classification metrics, computed by code (Rule 5: no model here).

Standard textbook definitions, per class:

* **precision** = TP / (TP + FP) — of everything we *predicted* as this class,
  how much was right. Undefined (reported as 0.0) when nothing was predicted.
* **recall** = TP / (TP + FN) — of everything that *actually* was this class,
  how much we caught. Undefined (reported as 0.0) when the class never appears.
* **accuracy** = correct / total — fraction of examples labelled correctly.

``macro_precision`` / ``macro_recall`` are the unweighted means across every
class seen in either the predictions or the labels (so a class the model never
predicts still drags the average down via its 0.0 precision).
"""

from collections import Counter
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ClassMetrics:
    """Per-class precision/recall and how many examples truly had this label."""

    label: str
    precision: float
    recall: float
    support: int


@dataclass(frozen=True)
class EvaluationMetrics:
    """Aggregate result of one evaluation pass over a labelled dataset."""

    accuracy: float
    macro_precision: float
    macro_recall: float
    per_class: list[ClassMetrics]


def _safe_ratio(numerator: int, denominator: int) -> float:
    """A zero denominator means the metric is undefined; report 0.0, not a crash."""
    return numerator / denominator if denominator else 0.0


def evaluate(predictions: Sequence[str], labels: Sequence[str]) -> EvaluationMetrics:
    """Compute accuracy plus per-class and macro precision/recall.

    ``predictions[i]`` is the model's guess for the example whose true class is
    ``labels[i]``; the two sequences must line up positionally.
    """
    if len(predictions) != len(labels):
        raise ValueError(
            f"predictions ({len(predictions)}) and labels ({len(labels)}) "
            "must have the same length"
        )
    if not labels:
        raise ValueError("cannot evaluate an empty dataset")

    classes = sorted(set(labels) | set(predictions))

    true_positives: Counter[str] = Counter()
    predicted_totals: Counter[str] = Counter()
    actual_totals: Counter[str] = Counter()

    for predicted, actual in zip(predictions, labels):
        predicted_totals[predicted] += 1
        actual_totals[actual] += 1
        if predicted == actual:
            true_positives[actual] += 1

    per_class = [
        ClassMetrics(
            label=cls,
            precision=_safe_ratio(true_positives[cls], predicted_totals[cls]),
            recall=_safe_ratio(true_positives[cls], actual_totals[cls]),
            support=actual_totals[cls],
        )
        for cls in classes
    ]

    correct = sum(true_positives.values())
    accuracy = _safe_ratio(correct, len(labels))
    macro_precision = _safe_ratio(sum(c.precision for c in per_class), len(classes))
    macro_recall = _safe_ratio(sum(c.recall for c in per_class), len(classes))

    return EvaluationMetrics(
        accuracy=accuracy,
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        per_class=per_class,
    )
