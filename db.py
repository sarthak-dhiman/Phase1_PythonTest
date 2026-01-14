import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Default DATABASE_URL for local development. Override with env var in production.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://root:root@localhost:5432/chicmic",
)

# Create SQLAlchemy `Base`. Defer engine creation to runtime only when an
# async driver is requested. This prevents Alembic (which uses a sync driver)
# from triggering an async engine creation error at import time.
Base = declarative_base()
engine = None
AsyncSessionLocal = None
DB_AVAILABLE = False

# Only create an async engine when the DATABASE_URL explicitly requests
# an asyncpg driver. For Alembic runs the URL will typically be a sync
# driver (psycopg2) and we must avoid calling create_async_engine.
if "+asyncpg" in (DATABASE_URL or ""):
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        DB_AVAILABLE = True
    except ModuleNotFoundError:
        engine = None
        AsyncSessionLocal = None
        DB_AVAILABLE = False


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if not DB_AVAILABLE or AsyncSessionLocal is None:
        raise RuntimeError("Database not available in current environment")
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create DB tables from models. Call in startup scripts or tests as needed.

    Raises RuntimeError if DB is not available (e.g. missing asyncpg).
    """
    if not DB_AVAILABLE or engine is None:
        raise RuntimeError("Database is not available in this environment")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
