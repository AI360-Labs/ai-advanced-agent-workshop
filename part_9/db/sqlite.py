from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_config
from db.persistence_models import PersistenceBase

engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None
initialized: bool = False


def sqlite_database_url(path: str) -> str:
    """Build a SQLite URL that works with absolute Windows paths."""
    db_path = Path(path).expanduser()
    if not db_path.is_absolute():
        db_path = (Path.cwd() / db_path).resolve()
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


def get_sqlite_engine() -> AsyncEngine:
    global engine
    if engine is None:
        engine = create_async_engine(
            sqlite_database_url(get_config().sqlite_path),
            echo=False,
        )
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
        await conn.run_sync(PersistenceBase.metadata.create_all)
    initialized = True
