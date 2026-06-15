from pydantic import ValidationError

from agent.node_messages import (
    THINKING_NO_CATALOG_MATCH,
    thinking_selected_catalog_query,
)
from agent.state import AgentState, StateUpdate
from db.queries import CUSTOM_QUERY_NAME, QUERY_CATALOG, catalog_descriptions
from db.schemas import QuerySelection
from prompts import load_prompt
from utils.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)

SELECTION_PROMPT = load_prompt("query_selection")
client = LLMClient(task="sql_gen")


async def select_query(state: AgentState) -> StateUpdate:
    """Pick a catalog query or signal fallback to LLM SQL generation."""

    def fallback_to_custom_query() -> StateUpdate:
        return {
            "query_selection": None,
            "thinking": [THINKING_NO_CATALOG_MATCH],
        }

    selection = await client.astructured(
        SELECTION_PROMPT,
        {
            "catalog": catalog_descriptions(),
            "question": state["question"],
        },
        QuerySelection,
    )

    if selection.query_name == CUSTOM_QUERY_NAME:
        logger.info("Query selection: custom (fallback to SQL generation)")
        return fallback_to_custom_query()

    entry = QUERY_CATALOG.get(selection.query_name)
    if entry is None:
        logger.info(f"Query selection: unknown name '{selection.query_name}'")
        return fallback_to_custom_query()

    try:
        validated = entry.param_model.model_validate(selection.params)
    except ValidationError as exc:
        logger.warning(f"Catalog params invalid for '{entry.name}': {exc}")
        return fallback_to_custom_query()

    logger.info(f"Query selection: {entry.name}")
    return {
        "query_selection": QuerySelection(
            query_name=entry.name,
            params=validated.model_dump(),
        ),
        "thinking": [thinking_selected_catalog_query(entry.name)],
    }
