from pydantic import BaseModel


class MessageSteps(BaseModel):
    thinking: list[str]
    intent: dict | None = None


def test_message_steps_round_trip() -> None:
    steps = MessageSteps(
        thinking=["classifying intent"], intent={"intent": "reporting"}
    )
    data = steps.model_dump()

    restored = MessageSteps.model_validate(data)
    assert restored.thinking == ["classifying intent"]


def test_message_steps_accepts_no_intent() -> None:
    """Steps without intent serialize to None (refuse path skips intent/sql)."""
    steps = MessageSteps(thinking=["blocked: out of scope"])
    assert steps.intent is None
    assert steps.model_dump()["intent"] is None
