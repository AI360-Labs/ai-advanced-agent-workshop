import pytest
from pydantic import ValidationError

from api.schemas import ChatRequest, ChatResponse, HealthResponse, ResumeRequest


def test_chat_request_requires_question() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(session_id="s1", question="")


def test_chat_response_fields() -> None:
    response = ChatResponse(
        session_id="s1",
        answer="hello",
        intent="northwind_query",
        reason="data query",
    )

    assert response.paused_for_review is False


def test_health_response_default() -> None:
    assert HealthResponse().status == "ok"


def test_resume_request_defaults_to_not_approved() -> None:
    """A review gate must require an explicit approval, so a body carrying only
    a session_id must NOT default to approved — otherwise an empty resume would
    silently pass the gate."""
    assert ResumeRequest(session_id="s1").approved is False
