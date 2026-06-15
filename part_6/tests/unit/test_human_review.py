from types import SimpleNamespace

import pytest
from langgraph.graph import END

import agent.nodes.human_review as hr_module
from agent.graph import route_after_review
from agent.nodes.human_review import APOLOGY, human_review


@pytest.fixture(autouse=True)
def mock_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        hr_module,
        "get_config",
        lambda: SimpleNamespace(human_review_max_retries=3),
    )


def test_route_ends_when_approved() -> None:
    assert route_after_review({"approved": True}) == END


def test_route_retries_when_not_approved() -> None:
    assert route_after_review({"retry_count": 1}) == "recognize_intent"


def test_human_review_exhausted_retries() -> None:
    state = {"answer": "some draft", "retry_count": 3}
    result = human_review(state)
    assert result["answer"] == APOLOGY
    assert result.get("approved") is True


def test_blank_feedback_does_not_approve(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: a refusal (approved not set) with empty feedback must NOT be
    read as approval — that would let a rejection silently pass the review gate.
    It has to route back for a revision instead, counting against the retries."""
    monkeypatch.setattr(hr_module, "interrupt", lambda payload: {"approved": False})
    result = hr_module.human_review(
        {"question": "original question", "answer": "draft", "retry_count": 0}
    )

    assert result.get("approved") is not True
    assert result["retry_count"] == 1
    assert hr_module.REVIEW_GENERIC_REVISION in result["question"]


def test_uses_settings_human_review_max_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HUMAN_REVIEW_MAX_RETRIES is read from config, not hardcoded — changing it
    changes the exhaustion threshold."""
    monkeypatch.setattr(
        hr_module,
        "get_config",
        lambda: SimpleNamespace(human_review_max_retries=1),
    )

    result = hr_module.human_review({"answer": "some draft", "retry_count": 1})

    assert result["answer"] == APOLOGY
    assert result.get("approved") is True
