import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import asyncio

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
        # Likely asyncpg is not installed in this environment; log the error.
        logger = logging.getLogger(__name__)
        logger.exception("Failed to create async engine; async driver may be missing")
        engine = None
        AsyncSessionLocal = None
        DB_AVAILABLE = False


async def check_db_connection(retries: int = 5, delay: float = 1.0) -> bool:
    """Try to connect to the DB and run a simple query. Retry a few times.

    Returns True when a connection succeeds and False otherwise.
    """
    global engine, AsyncSessionLocal, DB_AVAILABLE
    if "+asyncpg" not in (DATABASE_URL or ""):
        # Not configured for asyncpg; cannot open async engine here.
        DB_AVAILABLE = False
        return False

    if engine is None:
        try:
            engine = create_async_engine(DATABASE_URL, echo=False)
            AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception("Failed to create async engine during check_db_connection")
            engine = None
            AsyncSessionLocal = None
            DB_AVAILABLE = False
            return False

    last_exc = None
    for _ in range(retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            DB_AVAILABLE = True
            return True
        except Exception as exc:
            last_exc = exc
            DB_AVAILABLE = False
            logger = logging.getLogger(__name__)
            logger.debug("DB check attempt failed: %s", repr(exc))
            # Also print to stdout to ensure visibility in ad-hoc probes
            try:
                print("db.check_db_connection attempt failed:", repr(exc))
            except Exception:
                pass
            await asyncio.sleep(delay)
    # If we reach here, provide a final logged summary with the last exception
    logger = logging.getLogger(__name__)
    if last_exc is not None:
        logger.error("DB connectivity check failed after %s attempts: %s", retries, repr(last_exc))
        try:
            print("db.check_db_connection final error:", repr(last_exc))
        except Exception:
            pass
    else:
        logger.error("DB connectivity check failed with no exception; check DATABASE_URL=%s", DATABASE_URL)
        try:
            print("db.check_db_connection failed: no exception; DATABASE_URL=", DATABASE_URL)
        except Exception:
            pass

    # Try a quick synchronous probe using psycopg2 as a fallback to distinguish
    # between async driver issues and actual network/auth problems.
    try:
        import psycopg2
        from urllib.parse import urlparse

        parsed = urlparse(DATABASE_URL)
        dsn = {
            'dbname': parsed.path.lstrip('/') or '',
            'user': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': parsed.port,
        }
        try:
            conn = psycopg2.connect(**dsn)
            conn.close()
            logger.info('Synchronous psycopg2 probe succeeded — Postgres reachable; async driver or async connect likely the issue')
            print('db.check_db_connection: psycopg2 probe succeeded — Postgres reachable')
        except Exception as sync_exc:
            logger.error('psycopg2 probe failed: %s', repr(sync_exc))
            print('db.check_db_connection: psycopg2 probe failed:', repr(sync_exc))
    except Exception as import_exc:
        logger.debug('psycopg2 not available for sync probe: %s', repr(import_exc))
        try:
            print('db.check_db_connection: psycopg2 not available for sync probe:', repr(import_exc))
        except Exception:
            pass

    return False


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    # If we haven't yet established availability, try a single quick check
    # to lazily initialize the async engine/sessionmaker. This helps when
    # the application is started but the DB becomes available shortly after.
    from asyncio import get_event_loop

    if not DB_AVAILABLE or AsyncSessionLocal is None:
        try:
            # perform a non-blocking single attempt to initialize
            loop = get_event_loop()
            if loop.is_running():
                # schedule check_db_connection with no delay and single try
                await check_db_connection(retries=1, delay=0)
            else:
                # fallback for synchronous contexts
                loop.run_until_complete(check_db_connection(retries=1, delay=0))
        except Exception:
            pass

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
