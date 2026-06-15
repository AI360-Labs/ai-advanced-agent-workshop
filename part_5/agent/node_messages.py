"""Centralized copy for graph node thinking and response messages."""

# Persisted in the per-turn thinking log
THINKING_EMBED_QUERY = "Embedding the question for document search."
THINKING_SEARCH_DOCUMENTS = "Searching report documents by vector similarity."
THINKING_NO_CATALOG_MATCH = "No predefined queries suitable; generating custom query."
THINKING_GENERATING_SQL = "Generating SQL for the Northwind database."
THINKING_COMPOSE_ANSWER = "Composing the final answer from retrieved context."

# User-facing answers and review prompts
ANSWER_NO_DATA = "I could not find data to answer that question."
ANSWER_SECURITY_REFUSAL = (
    "I cannot help with that request. It looks like an attempt to bypass "
    "safety rules or access data in an unsafe way."
)
ANSWER_OUT_OF_SCOPE = (
    "That question is outside what I can answer. I only help with "
    "Northwind sales data and business report documents."
)


def thinking_refused(intent: str) -> str:
    return f"Refusing request (intent={intent})."


def thinking_selected_catalog_query(name: str) -> str:
    return f"Selected catalog query '{name}'."


def thinking_executed_catalog_query(name: str) -> str:
    return f"Executed catalog query '{name}'."


def thinking_executing_sql(sql: str) -> str:
    return f"Executing validated query: {sql}"
