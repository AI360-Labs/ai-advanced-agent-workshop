from db.schemas import QuerySelection
from typing import Any, Annotated, Literal, NotRequired, TypedDict

from pydantic import BaseModel

from db.schemas import ReportMatch, SqlQueryResult


def thinking_reducer(old: list[str], new: list[str] | None) -> list[str]:
    """Merge rule for the ``thinking`` log. ``None`` is a reset signal sent at
    the start of a new turn → wipe the old turn's steps. Otherwise append, just
    like ``operator.add``, so steps still accumulate within a single turn."""
    if new is None:
        return []
    return old + new


# Two retrieval paths, one reporting intent, two refusals.
Intent = Literal[
    "northwind_query",
    "document_search",
    "reporting",
    "out_of_scope",
    "security_breach",
]


class IntentResult(BaseModel):
    """LLM-boundary: Pydantic-validated classification of the user's question."""

    intent: Intent
    reason: str


class AgentState(TypedDict):
    """Graph state passed between nodes; ``thinking`` accumulates within a turn
    and is reset each turn via ``thinking_reducer`` (None signal)."""

    question: str
    intent: NotRequired[IntentResult]
    query_selection: NotRequired[QuerySelection]
    sql_result: NotRequired[SqlQueryResult]
    document_matches: NotRequired[list[ReportMatch]]
    answer: NotRequired[str]
    thinking: Annotated[list[str], thinking_reducer]
    retry_count: NotRequired[int]
    user_feedback: NotRequired[str | None]
    approved: NotRequired[bool]

StateUpdate = dict[str, Any]
