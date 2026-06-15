from db.schemas import QuerySelection
import operator
from typing import Any, Annotated, Literal, NotRequired, TypedDict

from pydantic import BaseModel

from db.schemas import ReportMatch, SqlQueryResult

# The five intents the agent understands. Two are retrieval paths
# (northwind_query, document_search), one is a reporting ask, and two are
# refusals (out_of_scope, security_breach).
Intent = Literal[
    "northwind_query",
    "document_search",
    "reporting",
    "out_of_scope",
    "security_breach",
]


class IntentResult(BaseModel):
    """Validated classification of the user's question (the LLM boundary).

    The ``Intent`` Literal already constrains allowed values — Pydantic rejects
    anything outside the five recognised intents.  ``reason`` is a short
    explanation shown back to the customer when the intent is ``out_of_scope``
    or ``security_breach``.
    """

    intent: Intent
    reason: str


class AgentState(TypedDict):
    """Graph state.

    A plain TypedDict for cheap dict-merge plumbing between nodes, with one
    validated Pydantic value (intent) coming from the LLM.
    """

    question: str
    intent: NotRequired[IntentResult]
    query_selection: NotRequired[QuerySelection]
    sql_result: NotRequired[SqlQueryResult]
    document_matches: NotRequired[list[ReportMatch]]
    answer: NotRequired[str]
    thinking: Annotated[list[str], operator.add]
    retry_count: NotRequired[int]

StateUpdate = dict[str, Any]
