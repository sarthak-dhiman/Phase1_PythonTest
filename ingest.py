from __future__ import annotations

import hashlib
from typing import BinaryIO
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from models import Ingest, Log
from log_file import LogFile


async def ingest_bytes(session: AsyncSession, raw_bytes: bytes, filename: str | None = None) -> dict:
    """Ingest raw bytes of a log file into the DB.

    - Computes a file-level SHA256 hash to detect duplicate uploads.
    - Creates an `Ingest` row (status updated as work proceeds).
    - Parses the file using `LogFile` and bulk-inserts into `logs` using
      PostgreSQL `ON CONFLICT DO NOTHING` on the `row_hash` unique index.

    Returns a summary dict with `file_hash`, `ingest_id`, `total_rows`, `inserted_rows`.
    """
    # Compute file hash
    file_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Check for existing ingest
    existing = await session.scalar(select(Ingest).where(Ingest.file_hash == file_hash))
    if existing:
        return {
            "file_hash": file_hash,
            "ingest_id": existing.id,
            "total_rows": existing.total_rows,
            "inserted_rows": existing.inserted_rows,
            "skipped": True,
        }

    # Create ingest row
    ingest = Ingest(file_hash=file_hash, file_name=filename, status="processing")
    session.add(ingest)
    await session.flush()  # populate ingest.id

    # Parse records using LogFile (we pass raw bytes to avoid consuming streams twice)
    lf = LogFile(raw_bytes)
    parsed = lf.parse_records()

    ts_list = parsed.get("TIMESTAMP", [])
    lvl_list = parsed.get("LEVEL", [])
    mod_list = parsed.get("MODULE", [])
    msg_list = parsed.get("MESSAGE", [])

    total_rows = len(lvl_list)

    # Prepare rows for bulk insert
    rows = []
    for ts, lvl, mod, msg in zip(ts_list, lvl_list, mod_list, msg_list):
        # Compute row-level hash to deduplicate identical lines across ingests
        row_hash = hashlib.sha256("|".join([str(ts), lvl, mod, msg]).encode("utf-8")).hexdigest()
        rows.append(
            {
                "ingest_id": ingest.id,
                "timestamp": None,
                "module": mod,
                "level": lvl,
                "message": msg,
                "row_hash": row_hash,
            }
        )

    inserted_rows = 0
    if rows:
        stmt = pg_insert(Log).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["row_hash"])
        result = await session.execute(stmt)
        # `rowcount` is best-effort; reflect inserted rows conservatively
        try:
            inserted_rows = result.rowcount or 0
        except Exception:
            inserted_rows = 0

    # Update ingest record
    ingest.total_rows = total_rows
    ingest.inserted_rows = inserted_rows
    ingest.status = "complete"
    await session.commit()

    return {
        "file_hash": file_hash,
        "ingest_id": ingest.id,
        "total_rows": total_rows,
        "inserted_rows": inserted_rows,
        "skipped": False,
    }


async def ingest_file_like(file_like: BinaryIO, filename: str | None = None) -> dict:
    """Helper that reads a file-like object into bytes and calls `ingest_bytes`."""
    raw = file_like.read()
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    async with get_session() as session:
        return await ingest_bytes(session, raw, filename=filename)
