"""Regression: sql_result_truncation must come from config, not a hardcoded constant.

The guard prevents large SQL result sets from overflowing the LLM context window.
Making it configurable lets operators tune the limit without touching source code.
"""

import asyncio
from types import SimpleNamespace

import pytest

import agent.nodes.compose_answer as compose_answer_module
from agent.nodes.compose_answer import compose_answer
from db.schemas import SqlQueryResult


class _FakeClient:
    last_variables: dict = {}

    async def acomplete(self, prompt: str, variables: dict) -> SimpleNamespace:
        _FakeClient.last_variables = variables
        return SimpleNamespace(content="answer")


def _run_with_sql(state: dict) -> None:
    asyncio.run(compose_answer(state))


def _sql_state(rows: list[dict], sql: str) -> dict:
    # intent must be a Northwind/reporting query so compose_answer takes the SQL
    # branch (and therefore reaches the truncation logic under test).
    return {
        "question": "how many?",
        "intent": SimpleNamespace(intent="northwind_query"),
        "sql_result": SqlQueryResult(
            sql=sql,
            rationale="test",
            row_count=1,
            rows=rows,
        ),
        "thinking": [],
    }


def test_sql_rows_truncated_to_config_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    # Confirms compose_answer reads the truncation limit from get_config(), not a
    # hardcoded constant — changing the setting changes how many chars reach the LLM.
    limit = 50
    monkeypatch.setattr(compose_answer_module, "client", _FakeClient())
    monkeypatch.setattr(
        compose_answer_module,
        "get_config",
        lambda: SimpleNamespace(sql_result_truncation=limit),
    )

    _run_with_sql(_sql_state([{"col": "x" * 200}], "SELECT col FROM t"))

    rows_sent = _FakeClient.last_variables["rows"]
    assert len(rows_sent) == limit, (
        f"rows should be truncated to {limit} chars, got {len(rows_sent)}"
    )


def test_sql_rows_not_truncated_when_under_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(compose_answer_module, "client", _FakeClient())
    monkeypatch.setattr(
        compose_answer_module,
        "get_config",
        lambda: SimpleNamespace(sql_result_truncation=8000),
    )

    _run_with_sql(_sql_state([{"id": 1, "name": "Alice"}], "SELECT id, name FROM t"))

    rows_sent = _FakeClient.last_variables["rows"]
    assert len(rows_sent) < 8000


def test_compose_answer_strips_thinking_blocks_from_llm_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reasoning models can return content as typed blocks; only the text block
    # should reach the user-facing answer in state.
    class _FakeClientWithThinking:
        async def acomplete(self, prompt: str, variables: dict) -> SimpleNamespace:
            return SimpleNamespace(
                content=[
                    {"type": "thinking", "thinking": "internal reasoning"},
                    {"type": "text", "text": "The answer is 42."},
                ]
            )

    monkeypatch.setattr(compose_answer_module, "client", _FakeClientWithThinking())
    monkeypatch.setattr(
        compose_answer_module,
        "get_config",
        lambda: SimpleNamespace(sql_result_truncation=8000),
    )

    result = asyncio.run(compose_answer(_sql_state([{"id": 1}], "SELECT id FROM t")))

    assert result["answer"] == "The answer is 42."
