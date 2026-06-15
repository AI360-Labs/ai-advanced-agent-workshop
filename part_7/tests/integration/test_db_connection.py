import asyncio
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import text

from config import get_config

load_dotenv(Path(__file__).resolve().parents[2] / "settings" / ".env")
from db.session import get_session  # noqa: E402

# Mark as integration test
pytestmark = pytest.mark.integration


def test_sqlalchemy_db_connection() -> None:
    """Verify that we can connect to the database directly via SQLAlchemy using DATABASE_URL."""
    cfg = get_config()
    db_url = cfg.database_url.get_secret_value()

    async def run_query():
        async for session in get_session():
            res = await session.execute(text("SELECT 1"))
            return res.scalar()

    try:
        val = asyncio.run(run_query())
        assert val == 1
    except Exception as e:
        err = str(e)
        if "localhost" in db_url or "127.0.0.1" in db_url:
            pytest.skip(
                f"Local database not running (DATABASE_URL points to localhost). Error: {e}"
            )
        elif "Network is unreachable" in err or "Cannot connect to host" in err:
            pytest.skip(f"Database host unreachable from this environment. Error: {e}")
        else:
            pytest.fail(f"SQLAlchemy direct database connection failed: {e}")
