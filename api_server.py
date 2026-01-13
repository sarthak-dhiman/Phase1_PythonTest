from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from log_file import LogFile
from user_analytics import UserAnalytics

app = FastAPI(title="ChicMic Log Uploader")


@app.post("/upload")
async def upload_log(file: UploadFile = File(...)):
    """Accept a log file upload, parse it, and return analytics as JSON.

    Expects a text file matching the project's log format. Returns overall level
    counts, per-module call counts, and a levels-per-module breakdown.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Write uploaded bytes to a temporary file and parse with existing LogFile
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(contents)
            tmp.flush()
            tmp_path = tmp.name

        lf = LogFile(tmp_path)
        lf.parse_records()

        ua = UserAnalytics(lf.logs)
        stats = ua.calculate_stats()
        module_counts = ua.calculate_module_stats()
        levels_per_module = ua.calculate_levels_per_module()

        return JSONResponse(
            {
                "filename": file.filename,
                "records": len(lf.logs.get("LEVEL", [])),
                "levels": stats,
                "modules": module_counts,
                "levels_per_module": levels_per_module,
            }
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


if __name__ == "__main__":
    # Run with: python api_server.py  (requires uvicorn to be installed)
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000)
