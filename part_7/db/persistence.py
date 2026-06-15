"""Persist conversations and messages to the local SQLite database."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.persistence_models import Conversation, Message
from utils.logger import get_logger

logger = get_logger(__name__)


async def get_or_create_conversation(
    session: AsyncSession, session_id: str, title: str
) -> Conversation:
    result = await session.execute(
        select(Conversation).where(Conversation.session_id == session_id).limit(1)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row

    conversation = Conversation(
        id=uuid4(),
        session_id=session_id,
        title=title[:200],
        created_at=datetime.now(UTC),
    )
    session.add(conversation)
    await session.flush()
    logger.info(f"Created conversation {conversation.id} for session {session_id}")
    return conversation


async def append_message(
    session: AsyncSession,
    conversation_id: UUID,
    role: str,
    content: str,
    steps: list | dict | None = None,
) -> Message:
    message = Message(
        id=uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        steps=steps,
        created_at=datetime.now(UTC),
    )
    session.add(message)
    await session.flush()
    return message


async def save_agent_turn(
    session: AsyncSession,
    session_id: str,
    question: str,
    answer: str,
    steps: list | dict | None,
) -> UUID:
    """Store the user question and assistant answer for one completed turn."""
    conversation = await get_or_create_conversation(session, session_id, title=question)
    await append_message(session, conversation.id, "user", question)
    await append_message(session, conversation.id, "assistant", answer, steps=steps)
    await session.commit()
    logger.info(f"Saved turn to conversation {conversation.id}")
    return conversation.id
