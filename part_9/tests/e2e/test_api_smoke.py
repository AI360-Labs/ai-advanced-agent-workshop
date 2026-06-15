from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from agent.state import IntentResult
import api.deps as deps
from api.app import app


class FakeGraph:
    """Minimal graph stub for in-process API smoke tests (no LLM, no DB)."""

    async def ainvoke(self, input_state: dict, config: dict | None = None) -> dict:
        return {
            "question": input_state["question"],
            "intent": IntentResult(
                intent="northwind_query",
                reason="test stub",
            ),
            "answer": "Stub answer: 3 orders.",
        }

    def get_state(self, config: dict | None = None) -> SimpleNamespace:
        return SimpleNamespace(next=())


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(deps, "graph", FakeGraph())
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_structured_response(client: TestClient) -> None:
    response = client.post(
        "/chat",
        json={"session_id": "smoke-1", "question": "How many orders?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "smoke-1"
    assert body["intent"] == "northwind_query"
    assert "Stub answer" in body["answer"]
    assert body["reason"] == "test stub"


def test_openapi_schema_lists_chat_route(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/chat" in paths
    assert "/health" in paths
