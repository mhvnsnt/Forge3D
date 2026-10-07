"""Shared HuggingFace Spaces Gradio REST client (no gradio_client dependency).

Implements the Gradio HTTP API directly with urllib:
  1. POST /gradio_api/upload (multipart) -> server file path
  2. POST /gradio_api/call/<endpoint> {"data": [...]} -> event_id
  3. GET  /gradio_api/call/<endpoint>/<event_id> (SSE) -> result payload
  4. Download FileData results via url or /gradio_api/file=<path>

Proven pattern: AshLanev2 tools/generative/character/auto-character.py
(keyless HF Spaces REST, working 2026-10-06).

Uses urllib (not httpx) to avoid the no_proxy IPv6-literal parsing bug
documented in ~/TOOLS.md. Proxy comes from https_proxy env as usual.

NOTE (2026-10-07): on ZeroGPU-backed spaces, quota exhaustion surfaces over
raw REST as `event: error, data: null` — the human-readable message
("You have exceeded your ZeroGPU quota ... Try again in H:MM:SS") is lost.
Use the official gradio_client when you need the real error text.
"""
from __future__ import annotations

import io
import json
import mimetypes
import time
import urllib.parse
import urllib.request
from pathlib import Path


class SpaceError(RuntimeError):
    """Raised when a Space call genuinely fails. Never masked."""


def _req(url: str, data: bytes | None = None,
         headers: dict | None = None, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        raise SpaceError(f"space request failed {url}: {e}")


def upload_file(space_host: str, file_path: Path) -> str:
    """Upload a file; returns the server-side path for FileData inputs."""
    boundary = "----forge3dboundary"
    body = io.BytesIO()
    fname = file_path.name
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    body.write(f"--{boundary}\r\n".encode())
    body.write(
        f'Content-Disposition: form-data; name="files"; filename="{fname}"\r\n'.encode())
    body.write(f"Content-Type: {ctype}\r\n\r\n".encode())
    body.write(file_path.read_bytes())
    body.write(f"\r\n--{boundary}--\r\n".encode())
    raw = _req(f"https://{space_host}/gradio_api/upload",
               data=body.getvalue(),
               headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
               timeout=120)
    try:
        paths = json.loads(raw)
        return paths[0]
    except Exception as e:  # noqa: BLE001
        raise SpaceError(f"upload parse failed: {raw[:200]!r}: {e}")


def file_data(server_path: str, orig_name: str = "input.png") -> dict:
    return {"path": server_path, "orig_name": orig_name,
            "meta": {"_type": "gradio.FileData"}}


def call_endpoint(space_host: str, endpoint: str, data: list,
                  timeout_min: int = 20) -> list:
    """Call a named endpoint and block on the SSE stream until complete.

    Returns the result `data` list from the complete event.
    """
    ep = endpoint.lstrip("/")
    raw = _req(f"https://{space_host}/gradio_api/call/{ep}",
               data=json.dumps({"data": data}).encode(),
               headers={"Content-Type": "application/json"},
               timeout=60)
    try:
        event_id = json.loads(raw)["event_id"]
    except Exception as e:  # noqa: BLE001
        raise SpaceError(f"no event_id from /{ep}: {raw[:300]!r}: {e}")

    url = f"https://{space_host}/gradio_api/call/{ep}/{event_id}"
    deadline = time.time() + timeout_min * 60
    buf = b""
    # stream SSE until we see the complete event
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
    except Exception as e:  # noqa: BLE001
        raise SpaceError(f"SSE connect failed /{ep}: {e}")
    try:
        while time.time() < deadline:
            chunk = resp.read(65536)
            if not chunk:
                break
            buf += chunk
            # process complete events as they arrive
            text = buf.decode("utf-8", "replace")
            while "\n\n" in text:
                block, text = text.split("\n\n", 1)
                event_type = None
                payload = None
                for line in block.splitlines():
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        payload = line[5:].strip()
                if event_type == "complete" and payload:
                    try:
                        return json.loads(payload)
                    except Exception as e:  # noqa: BLE001
                        raise SpaceError(f"complete payload parse failed: {e}")
                if event_type == "error" and payload:
                    raise SpaceError(f"space returned error: {payload[:300]}")
            buf = text.encode("utf-8", "replace")
    finally:
        resp.close()
    raise SpaceError(f"space /{ep} timed out after {timeout_min} min")


def download_filedata(space_host: str, filedata: dict, dest: Path,
                      timeout: int = 300) -> Path:
    """Download a Gradio FileData result (Model3d etc.) to dest."""
    url = filedata.get("url")
    if url:
        if url.startswith("/"):
            url = f"https://{space_host}{url}"
    else:
        path = filedata.get("path")
        if not path:
            raise SpaceError(f"FileData has no url/path: {str(filedata)[:200]}")
        url = (f"https://{space_host}/gradio_api/file="
               f"{urllib.parse.quote(path)}")
    dest.write_bytes(_req(url, timeout=timeout))
    return dest


def find_filedata(obj):
    """Yield FileData-ish dicts (have path/url + meta._type gradio.FileData)."""
    if isinstance(obj, dict):
        meta = obj.get("meta") or {}
        if meta.get("_type") == "gradio.FileData" and (obj.get("path") or obj.get("url")):
            yield obj
        for v in obj.values():
            yield from find_filedata(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_filedata(v)
