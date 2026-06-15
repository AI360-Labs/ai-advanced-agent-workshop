from agent.graph import route_after_intent
from agent.state import IntentResult


def state_with_intent(intent: str) -> dict:
    return {
        "question": "test",
        "intent": IntentResult(intent=intent, reason="test"),
    }


def test_routes_security_to_refuse() -> None:
    assert route_after_intent(state_with_intent("security_breach")) == "refuse"


def test_routes_document_search() -> None:
    assert (
        route_after_intent(state_with_intent("document_search")) == "search_documents"
    )


def test_routes_reporting_to_select() -> None:
    assert route_after_intent(state_with_intent("reporting")) == "select_query"
