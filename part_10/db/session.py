from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_config

engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global engine
    if engine is None:
        url = get_config().database_url.get_secret_value()
        engine = create_async_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"server_settings": {"search_path": "northwind,public,rag"}},
        )
    return engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global session_factory
    if session_factory is None:
        session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session
