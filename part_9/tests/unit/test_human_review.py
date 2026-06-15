import asyncio
from types import SimpleNamespace

import pytest

import agent.nodes.human_review as hr_module
import agent.nodes.intent as intent_module
from agent.graph import route_after_review
from agent.node_messages import ANSWER_REVISIONS_EXHAUSTED, REVIEW_GENERIC_REVISION
from agent.nodes.human_review import human_review
from agent.state import IntentResult


@pytest.fixture(autouse=True)
def mock_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        hr_module,
        "get_config",
        lambda: SimpleNamespace(human_review_max_retries=3),
    )


def test_route_persists_when_approved() -> None:
    assert route_after_review({"approved": True}) == "persist_turn"


def test_route_retries_when_not_approved() -> None:
    assert route_after_review({"retry_count": 1}) == "recognize_intent"


def test_human_review_exhausted_retries() -> None:
    state = {"answer": "some draft", "retry_count": 3}
    result = human_review(state)
    assert result["answer"] == ANSWER_REVISIONS_EXHAUSTED
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
    assert REVIEW_GENERIC_REVISION in result["question"]


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

    assert result["answer"] == ANSWER_REVISIONS_EXHAUSTED
    assert result.get("approved") is True


def test_new_turn_clears_leaked_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: with a persistent thread_id, `approved` from a prior approved turn
    must not survive into the next turn. If it did, human_review would short-circuit
    (return {}) and the answer would be persisted without review. recognize_intent is
    the per-turn entry point and must reset the per-turn flags."""
    fixed = IntentResult(intent="northwind_query", reason="data query")

    class FakeClient:
        async def astructured(
            self, prompt: str, variables: dict, schema: type
        ) -> IntentResult:
            return fixed

    monkeypatch.setattr(intent_module, "client", FakeClient())

    assert human_review({"approved": True, "answer": "draft"}) == {}

    leaked = {"question": "a new question", "approved": True, "user_feedback": "stale"}
    update = asyncio.run(intent_module.recognize_intent(leaked))

    assert update["approved"] is False
    assert update["user_feedback"] is None
