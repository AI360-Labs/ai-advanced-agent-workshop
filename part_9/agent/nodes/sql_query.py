from sqlalchemy import text

from agent.node_messages import (
    THINKING_GENERATING_SQL,
    thinking_executing_sql,
)
from agent.state import AgentState, StateUpdate
from config import get_config
from db.schema_snippet import SCHEMA_SNIPPET
from db.schemas import SqlGeneration, SqlQueryResult
from db.session import get_session_factory
from db.validate_sql import validate_sql
from prompts import load_prompt
from utils.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)

SQL_PROMPT = load_prompt("sql_generation")
client = LLMClient(task="sql_gen")


async def run_sql_query(state: AgentState) -> StateUpdate:
    """Generate SQL, validate it, execute read-only, return structured rows."""

    question = state["question"]
    max_limit = get_config().sql_max_limit

    generation = await client.astructured(
        SQL_PROMPT,
        {
            "schema": SCHEMA_SNIPPET,
            "max_limit": max_limit,
            "question": question,
        },
        SqlGeneration,
    )
    safe_sql = validate_sql(generation.sql, max_limit=max_limit)

    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(text(safe_sql))
        rows = [dict(row) for row in result.mappings().all()]

    sql_result = SqlQueryResult(
        sql=safe_sql,
        rationale=generation.rationale,
        row_count=len(rows),
        rows=rows,
    )
    logger.info(f"SQL returned {sql_result.row_count} rows")
    return {
        "sql_result": sql_result,
        "thinking": [
            THINKING_GENERATING_SQL,
            thinking_executing_sql(safe_sql),
        ],
    }
