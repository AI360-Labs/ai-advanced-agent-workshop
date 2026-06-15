"""Lock the precision/recall/accuracy definitions against a hand-computed case.

These tests must fail if the *meaning* of a metric drifts — e.g. if precision
and recall were ever swapped, or a missed ``security_breach`` stopped hurting
recall. That mislabel is the costly one (a breach we waved through), so recall
on that class is the number we most need to trust.
"""

import pytest

from eval.metrics import evaluate


def test_perfect_predictions_score_one() -> None:
    labels = ["a", "b", "a", "c"]

    metrics = evaluate(labels, labels)

    assert metrics.accuracy == 1.0
    assert metrics.macro_precision == 1.0
    assert metrics.macro_recall == 1.0


def test_precision_and_recall_diverge_for_a_missed_class() -> None:
    # Ground truth has two security_breach examples; the model catches one and
    # mislabels the other as out_of_scope, while also wrongly flagging a benign
    # question as security_breach.
    labels = [
        "security_breach",
        "security_breach",
        "out_of_scope",
    ]
    predictions = [
        "security_breach",  # caught
        "out_of_scope",  # missed breach -> hurts recall
        "security_breach",  # false alarm -> hurts precision
    ]

    metrics = evaluate(predictions, labels)
    by_label = {c.label: c for c in metrics.per_class}

    breach = by_label["security_breach"]
    # Predicted breach twice, only one was real -> precision 1/2.
    assert breach.precision == pytest.approx(0.5)
    # Two real breaches, only one caught -> recall 1/2.
    assert breach.recall == pytest.approx(0.5)
    assert breach.support == 2
    # 1 of 3 examples labelled correctly.
    assert metrics.accuracy == pytest.approx(1 / 3)


def test_class_never_predicted_has_zero_recall_not_a_crash() -> None:
    labels = ["a", "a"]
    predictions = ["b", "b"]

    metrics = evaluate(predictions, labels)
    by_label = {c.label: c for c in metrics.per_class}

    # 'a' is never predicted: recall 0, and precision is reported as 0.0
    # (undefined: nothing predicted as 'a') rather than raising.
    assert by_label["a"].recall == 0.0
    assert by_label["a"].precision == 0.0
    # 'b' is predicted twice but never correct -> precision 0.
    assert by_label["b"].precision == 0.0
    assert metrics.accuracy == 0.0


def test_length_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="same length"):
        evaluate(["a"], ["a", "b"])


def test_empty_dataset_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        evaluate([], [])
