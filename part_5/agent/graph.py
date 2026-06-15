from langgraph.graph import END, START, StateGraph

from agent.nodes.compose_answer import compose_answer
from agent.nodes.select_query import select_query
from agent.nodes.run_catalog_query import run_catalog_query
from agent.nodes.document_search import search_documents
from agent.nodes.intent import recognize_intent
from agent.nodes.refuse import refuse
from agent.nodes.sql_query import run_sql_query
from agent.state import AgentState


def route_after_intent(state: AgentState) -> str:
    match state["intent"].intent:
        case "security_breach" | "out_of_scope":
            return "refuse"
        case "document_search":
            return "search_documents"
        case "northwind_query" | "reporting":
            return "select_query"
        case other:
            raise ValueError(f"Unhandled intent: {other}")


def route_after_selection(state: AgentState) -> str:
    if state.get("query_selection"):
        return "run_catalog_query"
    return "run_sql_query"


def build_graph():
    """Intent -> retrieval path -> compose answer -> END."""
    builder = StateGraph(AgentState)
    builder.add_node("recognize_intent", recognize_intent)
    builder.add_node("refuse", refuse)
    builder.add_node("select_query", select_query)
    builder.add_node("run_catalog_query", run_catalog_query)
    builder.add_node("run_sql_query", run_sql_query)
    builder.add_node("search_documents", search_documents)
    builder.add_node("compose_answer", compose_answer)

    builder.add_edge(START, "recognize_intent")
    builder.add_conditional_edges(
        "recognize_intent",
        route_after_intent,
        {
            "refuse": "refuse",
            "select_query": "select_query",
            "search_documents": "search_documents",
        },
    )
    builder.add_conditional_edges(
        "select_query",
        route_after_selection,
        {
            "run_catalog_query": "run_catalog_query",
            "run_sql_query": "run_sql_query",
        },
    )
    builder.add_edge("run_catalog_query", "compose_answer")
    builder.add_edge("run_sql_query", "compose_answer")
    builder.add_edge("search_documents", "compose_answer")
    builder.add_edge("refuse", END)
    builder.add_edge("compose_answer", END)
    return builder.compile()
