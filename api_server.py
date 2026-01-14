from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
from pydantic import BaseModel
from typing import Dict
from log_file import LogFile
from user_analytics import UserAnalytics

logger = logging.getLogger(__name__)

app = FastAPI(title="Log Uploader")


MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_CONTENT_TYPES = {"text/plain"}


class UploadResponse(BaseModel):
    filename: str
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

    # Try to determine size without fully loading into memory
    fileobj = file.file
    size = None
    try:
        fileobj.seek(0, os.SEEK_END)
        size = fileobj.tell()
        fileobj.seek(0)
    except Exception:
        # Fall back to async read if seek not supported
        contents = await file.read()
        size = len(contents)
        from io import BytesIO

        fileobj = BytesIO(contents)

    if size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if size > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Uploaded file is too large")

    # Parse using LogFile which now accepts file-like objects
    try:
        lf = LogFile(fileobj)
        lf.parse_records()
    except Exception as exc:
        logger.exception("Failed to parse uploaded log: %s", getattr(file, "filename", "<unknown>"))
        raise HTTPException(status_code=400, detail=f"Failed to parse log file: {str(exc)}")

    try:
        ua = UserAnalytics(lf.logs)
        stats = ua.calculate_stats()
        module_counts = ua.calculate_module_stats()
        levels_per_module = ua.calculate_levels_per_module()

        safe_name = os.path.basename(file.filename) if file.filename else "uploaded"
        resp = UploadResponse(
            filename=safe_name,
            records=len(lf.logs.get("LEVEL", [])),
            levels=stats,
            modules=module_counts,
            levels_per_module=levels_per_module,
        )
        return resp
    except Exception:
        logger.exception("Failed to compute analytics for %r", file.filename)
        raise HTTPException(status_code=500, detail="Internal error computing analytics")


if __name__ == "__main__":
    # Run with: python api_server.py  (requires uvicorn to be installed)
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000)
