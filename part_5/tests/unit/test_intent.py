import pytest
from pydantic import ValidationError

import agent.nodes.intent as intent_module
from agent.state import IntentResult
from tests.fixtures import INTENT_EXAMPLES
from prompts import load_prompt


def test_intent_result_accepts_valid() -> None:
    result = IntentResult(intent="northwind_query", reason="data query")

    assert result.intent == "northwind_query"


def test_intent_result_rejects_unknown_intent() -> None:
    with pytest.raises(ValidationError):
        IntentResult(intent="delete_everything", reason="x")


def test_dataset_covers_all_intents() -> None:
    expected = {ex.expected for ex in INTENT_EXAMPLES}

    assert expected == {
        "northwind_query",
        "document_search",
        "reporting",
        "out_of_scope",
        "security_breach",
    }
    assert all(ex.text.strip() for ex in INTENT_EXAMPLES)


def test_prompt_loads_and_mentions_intents() -> None:
    prompt = load_prompt("intent_recognition")

    assert "{question}" in prompt
    assert "security_breach" in prompt


def test_recognize_intent_returns_state_update(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed = IntentResult(intent="reporting", reason="asks for a report")

    class FakeClient:
        def structured(
            self, prompt: str, variables: dict, schema: type
        ) -> IntentResult:
            return fixed

    monkeypatch.setattr(intent_module, "client", FakeClient())

    update = intent_module.recognize_intent({"question": "give me a sales report"})

    assert update == {"intent": fixed}
