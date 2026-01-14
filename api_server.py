from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import os
import logging
from contextvars import ContextVar
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from log_file import LogFile
from user_analytics import UserAnalytics
import io
import ingest as ingest_mod

logger = logging.getLogger(__name__)

# Context var for request id so log records can include it
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get() or "-"
        return True


# Configure basic structured logging (include request_id in format)
root_logger = logging.getLogger()
# Ensure every LogRecord has a `request_id` attribute to avoid
# Formatter errors from third-party libraries that log before our
# middleware sets the ContextVar.
_old_factory = logging.getLogRecordFactory()

def _record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    if not hasattr(record, "request_id"):
        record.request_id = request_id_var.get() or "-"
    return record

logging.setLogRecordFactory(_record_factory)
if not any(isinstance(f, RequestIDFilter) for f in root_logger.filters):
    root_logger.addFilter(RequestIDFilter())
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s [%(request_id)s]: %(message)s",
)

app = FastAPI(title="Log Uploader")


MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_CONTENT_TYPES = {"text/plain"}


class UploadResponse(BaseModel):
    file_id: str
    records: int
    levels: Dict[str, int]
    modules: Dict[str, int]
    levels_per_module: Dict[str, Dict[str, int]]


@app.post("/upload", response_model=UploadResponse)
async def upload_log(file: UploadFile = File(...)) -> UploadResponse:
    """Accept a log file upload, parse it, and return analytics as JSON.

    Expects a text file matching the project's log format. Returns overall level
    counts, per-module call counts, and a levels-per-module breakdown.
    """
    # Basic content-type check (lenient if client doesn't set it)
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {file.content_type}")

    # Read the uploaded file into memory (bounded by MAX_UPLOAD_SIZE)
    try:
        contents = await file.read()
    except Exception as exc:
        logger.exception("Failed to read uploaded file: %r", getattr(file, "filename", None))
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    size = len(contents) if contents is not None else 0
    if size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if size > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Uploaded file is too large")

    # Parse using LogFile which accepts raw bytes
    try:
        lf = LogFile(contents)
        lf.parse_records()
    except Exception as exc:
        logger.exception("Failed to parse uploaded log: %s", getattr(file, "filename", "<unknown>"))
        raise HTTPException(status_code=400, detail=f"Failed to parse log file: {str(exc)}")

    try:
        ua = UserAnalytics(lf.logs)
        stats = ua.calculate_stats()
        module_counts = ua.calculate_module_stats()
        levels_per_module = ua.calculate_levels_per_module()

        # Generate a server-side id for the uploaded file; do not echo back
        # the client's filename to avoid leaking client paths or sensitive info.
        file_id = uuid4().hex
        # Log the (sanitized) original filename for observability only
        try:
            orig_name = os.path.basename(file.filename) if file.filename else None
            logger.info("Upload received: file_id=%s filename=%s size=%s", file_id, orig_name, size)
        except Exception:
            orig_name = None
            logger.info("Upload received: file_id=%s", file_id)

        # Persist ingest to DB (best-effort). Failures here should not
        # prevent returning analytics to the client, but they will be logged.
        try:
            # Pass a fresh BytesIO so the ingest reader can consume it.
            bio = io.BytesIO(contents)
            ingest_result = await ingest_mod.ingest_file_like(bio, filename=orig_name)
            logger.info("Ingest result: %s", ingest_result)
        except Exception:
            logger.exception("Failed to persist ingest for file_id=%s", file_id)

        resp = UploadResponse(
            file_id=file_id,
            records=len(lf.logs.get("LEVEL", [])),
            levels=stats,
            modules=module_counts,
            levels_per_module=levels_per_module,
        )
        return resp
    except Exception:
        logger.exception("Failed to compute analytics for %r", file.filename)
        raise HTTPException(status_code=500, detail="Internal error computing analytics")


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Attach a request id to the request context and response headers.

    The request id is stored in a ContextVar so the logging filter can
    automatically inject it into log records created while processing the
    request.
    """
    rid = uuid4().hex
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        # restore previous context
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    return response


if __name__ == "__main__":
    # Run with: python api_server.py  
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000)
