"""Tripo3D API Platform provider (v3 REST).

Free tier: 300 credits/month, 1 concurrent task, no card. Key format tsk_...
via env var FORGE3D_TRIPO_KEY only — never in the repo.

REST spec wired from official docs (developers.tripo3d.com), verified 2026-10-06:
  base: https://openapi.tripo3d.ai/v3  (auth: Bearer <key>)
  text: POST /v3/generation/text-to-model  {"prompt","model",...} -> task_id
  image: POST /v3/files (multipart "file") -> file_token, then
         POST /v3/generation/image-to-model {"input": file_token|url, ...}
  poll: GET /v3/tasks/{task_id} -> status queued/running/success/failed/...
  result: data.output.model_url (signed, short-lived — download immediately)

COMMERCIAL WARNING: free-tier outputs are public + NON-commercial (CC BY 4.0).
Prototyping/reference/baseline only — nothing free-tier ships in a money build.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)

BASE = "https://openapi.tripo3d.ai/v3"
MODEL = "v3.1-20260211"  # latest/best per docs; fall back to v3.0-20250812


class TripoAPIProvider(ModelProvider):
    info = ProviderInfo(
        name="tripo-api",
        kind="api",
        capabilities=[Capability.TEXT_TO_3D, Capability.IMAGE_TO_3D],
        license="service-terms (free tier: CC BY 4.0, non-commercial)",
        commercial_ok=False,
        needs_gpu=False,
        needs_key=True,
        quota_note="300 credits/month free API platform; ~10 textured models/month",
    )

    def _headers(self) -> dict:
        key = os.environ.get("FORGE3D_TRIPO_KEY", "")
        if not key:
            raise ProviderError(
                "FORGE3D_TRIPO_KEY not set (free key: platform.tripo3d.ai -> API Keys)")
        return {"Authorization": f"Bearer {key}"}

    def is_available(self) -> tuple[bool, str]:
        if not os.environ.get("FORGE3D_TRIPO_KEY"):
            return False, "FORGE3D_TRIPO_KEY not set (free at platform.tripo3d.ai)"
        return True, "key present (quota checked at request time)"

    def _post(self, path: str, payload: dict) -> dict:
        r = requests.post(BASE + path, headers=self._headers(),
                          json=payload, timeout=60)
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            raise ProviderError(f"tripo-api {path}: HTTP {r.status_code} (no JSON)")
        if r.status_code == 401:
            raise ProviderError("tripo-api: bad key (401)")
        if r.status_code == 402 or data.get("code") in (1002, 2010):
            raise ProviderError("tripo-api: insufficient credits (free tier exhausted)")
        if data.get("code", 0) != 0:
            # field-name discrepancy: docs say "model", some integrations use "model_version"
            if data.get("code") == 1004 and "model" in payload and "model_version" not in payload:
                payload = dict(payload)
                payload["model_version"] = payload.pop("model")
                return self._post(path, payload)
            raise ProviderError(
                f"tripo-api {path}: code={data.get('code')} msg={data.get('message')}")
        return data["data"]

    def _upload(self, image: Path) -> str:
        with open(image, "rb") as f:
            r = requests.post(BASE + "/files", headers=self._headers(),
                              files={"file": (image.name, f)}, timeout=120)
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            raise ProviderError(f"tripo-api /files: HTTP {r.status_code} (no JSON)")
        if data.get("code", 0) != 0:
            raise ProviderError(f"tripo-api /files: {data.get('message')}")
        return data["data"]["file_token"]

    def _wait(self, task_id: str, timeout: int = 900) -> dict:
        t0 = time.time()
        while time.time() - t0 < timeout:
            r = requests.get(f"{BASE}/tasks/{task_id}",
                             headers=self._headers(), timeout=30)
            data = r.json().get("data", {})
            status = data.get("status")
            if status == "success":
                return data.get("output", {})
            if status in ("failed", "cancelled", "banned", "expired"):
                raise ProviderError(f"tripo-api task {status}: {data}")
            time.sleep(5)
        raise ProviderError(f"tripo-api task {task_id} timed out after {timeout}s")

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        body = {
            "model": MODEL,
            "texture": True,
            "pbr": True,
            "texture_quality": "detailed",
            "face_limit": 1500000,
            "auto_size": True,
        }
        if image:
            body["input"] = self._upload(Path(image))
            data = self._post("/generation/image-to-model", body)
        elif prompt:
            body["prompt"] = prompt[:1024]
            body["negative_prompt"] = "blurry, low quality, broken mesh"
            data = self._post("/generation/text-to-model", body)
        else:
            raise ProviderError("tripo-api: need prompt or image")
        task_id = data["task_id"]
        output = self._wait(task_id)
        url = (output.get("model_url") or output.get("pbr_model")
               or output.get("model") or output.get("base_model"))
        if not url:
            raise ProviderError(f"tripo-api: no model URL in output: {output}")
        # signed URL — download immediately, never store the URL
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        glb = out_dir / f"tripo-{task_id[:8]}.glb"
        glb.write_bytes(r.content)
        if glb.stat().st_size < 1024:
            raise ProviderError("tripo-api: downloaded model suspiciously small")
        return GenerateResult(glb_path=glb, provider="tripo-api",
                              meta={"task_id": task_id, "model": MODEL,
                                    "note": "free-tier baseline: CC BY 4.0 non-commercial"})
