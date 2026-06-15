import pytest

from agent.graph import route_after_intent, route_after_selection
from agent.state import IntentResult
from db.schemas import QuerySelection


def state_with_intent(intent: str) -> dict:
    return {
        "question": "test",
        "intent": IntentResult(intent=intent, reason="test"),
    }


def test_routes_security_to_refuse() -> None:
    assert route_after_intent(state_with_intent("security_breach")) == "refuse"


def test_routes_out_of_scope_to_refuse() -> None:
    assert route_after_intent(state_with_intent("out_of_scope")) == "refuse"


def test_routes_document_search() -> None:
    assert (
        route_after_intent(state_with_intent("document_search")) == "search_documents"
    )


def test_routes_northwind_query_to_select() -> None:
    assert route_after_intent(state_with_intent("northwind_query")) == "select_query"


def test_routes_reporting_to_select() -> None:
    assert route_after_intent(state_with_intent("reporting")) == "select_query"


def test_unhandled_intent_raises() -> None:
    bad = {
        "question": "test",
        "intent": IntentResult.model_construct(intent="unknown", reason="test"),
    }
    with pytest.raises(ValueError, match="Unhandled intent"):
        route_after_intent(bad)


def test_route_after_selection_uses_catalog() -> None:
    state = {
        "query_selection": QuerySelection(
            query_name="count_orders_for_customer",
            params={"customer_id": "ALFKI"},
        )
    }
    assert route_after_selection(state) == "run_catalog_query"


def test_route_after_selection_falls_back_to_sql() -> None:
    assert route_after_selection({"query_selection": None}) == "run_sql_query"
    assert route_after_selection({}) == "run_sql_query"
