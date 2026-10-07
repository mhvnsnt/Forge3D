"""Pollinations.ai 3D provider — trellis-2 / sf3d / triposr via API.

Verified working pattern (2026-10-07, trellis-first run):
  GET https://gen.pollinations.ai/3d/{prompt}?model=trellis-2-low&image=IMAGE_URL
  with `Authorization: Bearer <key>` -> GLB bytes in the response body.

The old POST /3d/generations job payload is WRONG for the current API
version (`prompt` is an unrecognized key, `image` must be a URL, not a
local path) — replaced 2026-10-07.

Local images are uploaded to a free file host (tmpfiles.org, verified
2026-10-07) to obtain the public IMAGE_URL the API requires.

3D costs Pollen ($1 ~= 1 Pollen; trellis-2-low = 0.24/gen). Balance 0
-> HTTP 402 INSUFFICIENT_BALANCE: raised loudly as ProviderError, never
masked. Quest grinding is the owner's decision — not started.

Key via env var FORGE3D_POLLINATIONS_KEY or ~/.config/forge3d/api_keys.env
(docs/ACCOUNTS.md) — never in the repo.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)
from .keys import get_key, key_source

MODEL_PRICES = {
    "trellis-2-low": 0.24,
    "trellis-2-medium": 0.29,
    "trellis-2-high": 0.35,
    "sf3d": 0.02,
    "triposr": 0.02,
}

# Free file hosts for turning a local image into the public URL the 3D API
# requires. Tried in order; first success wins. Verified 2026-10-07.
_UPLOAD_HOSTS = ("tmpfiles.org", "catbox.moe", "file.io")


def _upload_to_tmpfiles_org(image: Path) -> str:
    import io
    boundary = "----forge3dupload"
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(
        f'Content-Disposition: form-data; name="file"; '
        f'filename="{image.name}"\r\n'.encode())
    body.write(b"Content-Type: image/jpeg\r\n\r\n")
    body.write(image.read_bytes())
    body.write(f"\r\n--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        "https://tmpfiles.org/api/v1/upload", data=body.getvalue(),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    url = (data.get("data") or {}).get("url", "")
    if not url:
        raise ProviderError(f"tmpfiles.org upload failed: {str(data)[:200]}")
    # API returns the page URL; the direct file URL uses /dl/
    return url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)


def _upload_to_catbox(image: Path) -> str:
    import io
    boundary = "----forge3dupload"
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="reqtype"\r\n\r\nfileupload\r\n')
    body.write(f"--{boundary}\r\n".encode())
    body.write(
        f'Content-Disposition: form-data; name="fileToUpload"; '
        f'filename="{image.name}"\r\n'.encode())
    body.write(b"Content-Type: image/jpeg\r\n\r\n")
    body.write(image.read_bytes())
    body.write(f"\r\n--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        "https://catbox.moe/user/api.php", data=body.getvalue(),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        url = r.read().decode().strip()
    if not url.startswith("http"):
        raise ProviderError(f"catbox upload failed: {url[:200]}")
    return url


def _upload_to_fileio(image: Path) -> str:
    import io
    boundary = "----forge3dupload"
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(
        f'Content-Disposition: form-data; name="file"; '
        f'filename="{image.name}"\r\n'.encode())
    body.write(b"Content-Type: image/jpeg\r\n\r\n")
    body.write(image.read_bytes())
    body.write(f"\r\n--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        "https://file.io", data=body.getvalue(),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    url = data.get("link", "")
    if not url:
        raise ProviderError(f"file.io upload failed: {str(data)[:200]}")
    return url


def _public_image_url(image: Path | str) -> str:
    """Return a public https URL for a local image path or URL string."""
    s = str(image)
    if s.startswith(("http://", "https://")):
        return s
    path = Path(s)
    if not path.exists():
        raise ProviderError(f"image not found: {s}")
    uploaders = {
        "tmpfiles.org": _upload_to_tmpfiles_org,
        "catbox.moe": _upload_to_catbox,
        "file.io": _upload_to_fileio,
    }
    errors = []
    for host in _UPLOAD_HOSTS:
        try:
            return uploaders[host](path)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{host}: {e}")
    raise ProviderError(
        "no free image host reachable for concept upload: " + "; ".join(errors))


class Pollinations3DProvider(ModelProvider):
    info = ProviderInfo(
        name="pollinations-3d",
        kind="api",
        capabilities=[Capability.IMAGE_TO_3D],  # trellis-2 ignores text prompts
        license="service-terms",
        commercial_ok=False,  # Quest Pollen outputs: check terms before shipping
        needs_gpu=False,
        needs_key=True,
        quota_note="key free; 3D costs Pollen (trellis-2-low $0.24/gen, Quest Pollen earnable free)",
    )

    API = "https://gen.pollinations.ai/3d"

    def _key(self) -> str:
        # Env first, then ~/.config/forge3d/api_keys.env (docs/ACCOUNTS.md).
        # Never in the repo.
        key = get_key("FORGE3D_POLLINATIONS_KEY")
        if not key:
            raise ProviderError("set FORGE3D_POLLINATIONS_KEY (free at enter.pollinations.ai/keys)")
        return key

    def is_available(self) -> tuple[bool, str]:
        src = key_source("FORGE3D_POLLINATIONS_KEY")
        if src == "missing":
            return False, "FORGE3D_POLLINATIONS_KEY not set"
        return True, f"key present via {src} (pollen balance checked at request time)"

    def generate(self, *, prompt: str | None = None, image=None,
                 out_dir: Path, model: str = "trellis-2-low",
                 **kwargs) -> GenerateResult:
        key = self._key()
        if model not in MODEL_PRICES:
            raise ProviderError(f"unknown model {model}; pick from {list(MODEL_PRICES)}")
        image_url = _public_image_url(image) if image else None
        # Prompt goes in the URL path (URL-encoded). For pure image-to-3D the
        # API ignores it, but the path segment is required.
        path_prompt = urllib.parse.quote(prompt or "3d-model", safe="")
        query = {"model": model}
        if image_url:
            query["image"] = image_url
        url = f"{self.API}/{path_prompt}?{urllib.parse.urlencode(query)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                glb_bytes = r.read()
        except urllib.error.HTTPError as e:
            body = e.read()[:500].decode("utf-8", "replace")
            if e.code == 402:
                raise ProviderError(
                    "pollinations 3d: INSUFFICIENT_BALANCE (HTTP 402) — "
                    f"{body} Top up at https://enter.pollinations.ai/top-up "
                    "or earn Quest Pollen (owner decision).") from e
            raise ProviderError(
                f"pollinations 3d request failed: HTTP {e.code}: {body}") from e
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"pollinations 3d request failed: {e}") from e
        if len(glb_bytes) < 1024 or glb_bytes[:4] != b"glTF":
            raise ProviderError(
                f"pollinations 3d: response is not a GLB ({len(glb_bytes)} bytes): "
                f"{glb_bytes[:200]!r}")
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        out_path = out / f"pollinations-{model}.glb"
        out_path.write_bytes(glb_bytes)
        return GenerateResult(
            glb_path=out_path, provider=f"pollinations-3d:{model}",
            meta={"model": model, "pollen_cost": MODEL_PRICES[model],
                  "image_url": image_url})
