import subprocess
import time
import socket
import requests
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UVICORN_CMD = [sys.executable, "-m", "uvicorn", "api_server:app", "--host", "127.0.0.1", "--port"]


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    addr, port = s.getsockname()
    s.close()
    return port


def wait_for(url, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url)
            return r
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("Server did not become ready in time")


def test_uvicorn_subprocess(tmp_path):
    port = find_free_port()
    cmd = UVICORN_CMD + [str(port)]
    # Start uvicorn as a subprocess
    proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        # Wait until server is ready (GET /docs is a lightweight endpoint)
        base = f"http://127.0.0.1:{port}"
        wait_for(base + "/docs")

        # POST to /upload with a small sample
        sample = b"2023-01-01T00:00:00 INFO mod A message\n"
        files = {"file": ("sample.txt", sample, "text/plain")}
        try:
            r = requests.post(base + "/upload", files=files, timeout=10)
            assert r.status_code == 200
            j = r.json()
            assert "file_id" in j
        except Exception as exc:
            # On failure, capture server stderr for debugging
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
            err = proc.stderr.read().decode(errors="replace")
            proc.stderr.close()
            raise AssertionError(f"Request failed: {exc}\nServer stderr:\n{err}") from exc
    finally:
        # If the process died earlier, surface stderr for debugging
        if proc.poll() is not None:
                try:
                    err = proc.stderr.read().decode(errors="replace")
                    proc.stderr.close()
                except Exception:
                    err = "<could not read stderr>"
                raise AssertionError(f"uvicorn process terminated early:\n{err}")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
