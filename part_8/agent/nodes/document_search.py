from agent.node_messages import (
    THINKING_EMBED_QUERY,
    THINKING_SEARCH_DOCUMENTS,
)
from uuid import UUID

from sqlalchemy import Float, cast, literal, select

from agent.state import AgentState, StateUpdate
from config.settings import get_config
from utils.llm_client import LLMClient
from db.models import Report
from db.schemas import ReportMatch
from db.session import get_session_factory
from utils.logger import get_logger

logger = get_logger(__name__)


async def search_documents(state: AgentState) -> StateUpdate:
    """Semantic search over rag.documents using pgvector."""
    question = state["question"]

    vector = await LLMClient.aembed(question)
    logger.info(f"Embedded query ({len(vector)} dimensions)")
    vector_literal = "[" + ",".join(str(v) for v in vector) + "]"

    distance = Report.embedding.op("<=>", return_type=Float)(
        cast(literal(vector_literal), Report.embedding.type)
    ).label("distance")
    stmt = (
        select(Report.id, Report.source, Report.content, distance)
        .order_by(distance)
        .limit(get_config().search_limit)
    )

    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(stmt)
        rows = result.mappings().all()

    matches = [
        ReportMatch(
            id=UUID(str(row["id"])),
            source=row["source"],
            content=row["content"],
            distance=float(row["distance"]),
        )
        for row in rows
    ]
    logger.info(f"Document search returned {len(matches)} matches")
    return {
        "document_matches": matches,
        "thinking": [
            THINKING_EMBED_QUERY,
            THINKING_SEARCH_DOCUMENTS,
        ],
    }
