from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_config
from db.persistence_models import Base

engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None
initialized: bool = False


def get_sqlite_engine() -> AsyncEngine:
    global engine
    if engine is None:
        path = get_config().sqlite_path
        engine = create_async_engine(f"sqlite+aiosqlite:///{path}", echo=False)
    return engine


def get_sqlite_session_factory() -> async_sessionmaker[AsyncSession]:
    global session_factory
    if session_factory is None:
        session_factory = async_sessionmaker(
            get_sqlite_engine(), expire_on_commit=False
        )
    return session_factory


async def init_db() -> None:
    """Create tables if they don't exist. Idempotent — safe to call on every turn."""
    global initialized
    if initialized:
        return
    async with get_sqlite_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    initialized = True
