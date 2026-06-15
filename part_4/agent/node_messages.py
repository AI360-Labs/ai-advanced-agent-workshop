"""Centralized copy for graph node thinking and response messages."""

# Persisted in the per-turn thinking log
THINKING_EMBED_QUERY = "Embedding the question for document search."
THINKING_SEARCH_DOCUMENTS = "Searching report documents by vector similarity."
THINKING_NO_CATALOG_MATCH = "No predefined queries suitable; generating custom query."
THINKING_GENERATING_SQL = "Generating SQL for the Northwind database."

# User-facing answers and review prompts


def thinking_selected_catalog_query(name: str) -> str:
    return f"Selected catalog query '{name}'."


def thinking_executed_catalog_query(name: str) -> str:
    return f"Executed catalog query '{name}'."


def thinking_executing_sql(sql: str) -> str:
    return f"Executing validated query: {sql}"
