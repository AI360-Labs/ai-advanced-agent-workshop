from types import SimpleNamespace
from typing import Any

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, SecretStr

import utils.llm_client as llm_client
from utils.llm_client import LLMClient, to_openrouter


class Sample(BaseModel):
    name: str
    value: int


@pytest.fixture
def patch_config(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_config = SimpleNamespace(api_key=SecretStr("test-key"), llm_max_retries=2)
    fake_tasks = SimpleNamespace(
        max_output_tokens=256,
        task=lambda _: SimpleNamespace(temperature=0.0, models=["model-a"]),
    )
    monkeypatch.setattr(llm_client, "get_config", lambda: fake_config)
    monkeypatch.setattr(llm_client, "get_tasks", lambda: fake_tasks)


def structured_engine(*results: dict[str, Any]) -> object:
    """Fake engine whose structured runnable yields the given include_raw dicts."""
    responses = iter(results)

    class FakeEngine:
        def with_structured_output(
            self, schema: type[BaseModel], include_raw: bool = False
        ) -> RunnableLambda:
            return RunnableLambda(lambda _: next(responses))

    return FakeEngine()


def test_to_openrouter_adds_prefix() -> None:
    assert to_openrouter("gpt-4") == "openrouter/gpt-4"


def test_to_openrouter_keeps_existing_prefix() -> None:
    assert to_openrouter("openrouter/gpt-4") == "openrouter/gpt-4"


def test_complete_returns_message(patch_config: None) -> None:
    client = LLMClient(task="precise")
    client.engine = RunnableLambda(lambda _: AIMessage(content="hello"))

    message = client.complete("Say: {text}", {"text": "hi"})

    assert message.content == "hello"


def test_structured_returns_parsed(patch_config: None) -> None:
    client = LLMClient(task="precise")
    client.engine = structured_engine(
        {"parsed": Sample(name="x", value=1), "parsing_error": None, "raw": None}
    )

    result = client.structured("Extract: {text}", {"text": "log"}, Sample)

    assert result == Sample(name="x", value=1)


def test_structured_repairs_malformed_json(patch_config: None) -> None:
    client = LLMClient(task="precise")
    client.engine = structured_engine(
        {
            "parsed": None,
            "parsing_error": ValueError("bad json"),
            "raw": AIMessage(content='{"name": "x", "value": 1,}'),
        }
    )

    result = client.structured("Extract: {text}", {"text": "log"}, Sample)

    assert result == Sample(name="x", value=1)


def test_structured_honours_max_retries_from_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """max_retries=1 means exactly one LLM call — the limit comes from config, not hardcode."""
    fake_config = SimpleNamespace(api_key=SecretStr("test-key"), llm_max_retries=1)
    fake_tasks = SimpleNamespace(
        max_output_tokens=256,
        task=lambda _: SimpleNamespace(temperature=0.0, models=["model-a"]),
    )
    monkeypatch.setattr(llm_client, "get_config", lambda: fake_config)
    monkeypatch.setattr(llm_client, "get_tasks", lambda: fake_tasks)

    call_count = 0

    def _always_fail(_):
        nonlocal call_count
        call_count += 1
        return {
            "parsed": None,
            "parsing_error": ValueError("fail"),
            "raw": AIMessage(content="not json"),
        }

    class FailingEngine:
        def with_structured_output(self, schema, include_raw=False):
            return RunnableLambda(_always_fail)

    client = LLMClient(task="precise")
    client.engine = FailingEngine()

    with pytest.raises(ValueError):
        client.structured("Extract: {text}", {"text": "log"}, Sample)

    assert call_count == 1
