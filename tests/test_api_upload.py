import io
import pytest
from fastapi.testclient import TestClient
from api_server import app, MAX_UPLOAD_SIZE

client = TestClient(app)

SAMPLE_LOG = """2023-01-01T00:00:00 INFO moduleA Started processing
2023-01-01T00:00:01 ERROR moduleB Failed to process
2023-01-01T00:00:02 DEBUG moduleA Details
"""

MALFORMED_LOG = """this is not a valid log line
another bad line
"""


def test_upload_valid_file():
    files = {"file": ("sample.txt", io.BytesIO(SAMPLE_LOG.encode("utf-8")), "text/plain")}
    resp = client.post("/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "sample.txt"
    assert data["records"] == 3
    assert data["levels"]["INFO"] == 1
    assert data["levels"]["ERROR"] == 1
    assert data["levels"]["DEBUG"] == 1


def test_upload_empty_file():
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    resp = client.post("/upload", files=files)
    assert resp.status_code == 400
    assert "empty" in resp.json().get("detail", "").lower()


def test_upload_wrong_content_type():
    files = {"file": ("data.bin", io.BytesIO(SAMPLE_LOG.encode("utf-8")), "application/octet-stream")}
    resp = client.post("/upload", files=files)
    assert resp.status_code == 400
    assert "unsupported content type" in resp.json().get("detail", "").lower()


def test_upload_oversize_file():
    # construct a payload slightly larger than MAX_UPLOAD_SIZE
    big = b"A" * (MAX_UPLOAD_SIZE + 1)
    files = {"file": ("big.txt", io.BytesIO(big), "text/plain")}
    resp = client.post("/upload", files=files)
    assert resp.status_code == 413


def test_upload_malformed_file():
    files = {"file": ("bad.txt", io.BytesIO(MALFORMED_LOG.encode("utf-8")), "text/plain")}
    resp = client.post("/upload", files=files)
    # Parsing malformed lines should not crash; it may return 200 with zero counts
    assert resp.status_code in (200, 400)
