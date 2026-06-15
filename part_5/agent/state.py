from db.schemas import QuerySelection
import operator
from typing import Any, Annotated, Literal, NotRequired, TypedDict

from pydantic import BaseModel

from db.schemas import ReportMatch, SqlQueryResult

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
    """Graph state passed between nodes; ``thinking`` grows via operator.add."""

    question: str
    intent: NotRequired[IntentResult]
    query_selection: NotRequired[QuerySelection]
    sql_result: NotRequired[SqlQueryResult]
    document_matches: NotRequired[list[ReportMatch]]
    answer: NotRequired[str]
    thinking: Annotated[list[str], operator.add]
    retry_count: NotRequired[int]
    user_feedback: NotRequired[str | None]
    approved: NotRequired[bool]

StateUpdate = dict[str, Any]
