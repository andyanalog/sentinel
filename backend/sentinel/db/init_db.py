"""Boot-time table creation for environments where alembic is awkward
(SQLite on ephemeral container disks). Idempotent — safe to run on every start.
"""
import asyncio

from sentinel.config import get_settings
from sentinel.db import tables  # noqa: F401  -- registers models on Base
from sentinel.db.session import Base, make_engine


async def _init() -> None:
    engine = make_engine(get_settings().database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_init())
    print("init_db: tables ensured")
