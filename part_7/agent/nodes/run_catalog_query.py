from agent.node_messages import (
    thinking_executed_catalog_query,
)
from agent.state import AgentState, StateUpdate
from db.queries import QUERY_CATALOG
from db.schemas import SqlQueryResult
from db.session import get_session_factory
from utils.logger import get_logger

logger = get_logger(__name__)


async def run_catalog_query(state: AgentState) -> StateUpdate:
    """Execute a pre-built ORM query from the catalog."""

    selection = state["query_selection"]
    entry = QUERY_CATALOG[selection.query_name]
    params = entry.param_model.model_validate(selection.params)

    factory = get_session_factory()
    async with factory() as session:
        rows = await entry.handler(session, params)

    sql_result = SqlQueryResult(
        sql=f"[catalog:{entry.name}]",
        rationale=entry.description,
        row_count=len(rows),
        rows=rows,
    )
    logger.info(f"Catalog query '{entry.name}' returned {sql_result.row_count} rows")
    return {
        "sql_result": sql_result,
        "thinking": [thinking_executed_catalog_query(entry.name)],
    }
