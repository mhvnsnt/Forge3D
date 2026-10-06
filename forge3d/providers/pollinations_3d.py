"""Pollinations.ai 3D provider — trellis-2 / sf3d / tripoSR via API.

Free signup key (enter.pollinations.ai/keys); 3D billed in Pollen
($1 ~= 1 Pollen). trellis-2-low $0.24/gen works with free Quest Pollen
(earned via quests); tripoSR/sf3d confirmed $0.02/gen.
Key via env var FORGE3D_POLLINATIONS_KEY only — never in the repo.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)

MODEL_PRICES = {
    "trellis-2-low": 0.24,
    "trellis-2-medium": 0.29,
    "trellis-2-high": 0.35,
    "sf3d": 0.02,
    "triposr": 0.02,
}


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

    API = "https://gen.pollinations.ai/3d/generations"

    def _key(self) -> str:
        key = os.environ.get("FORGE3D_POLLINATIONS_KEY", "")
        if not key:
            raise ProviderError("set FORGE3D_POLLINATIONS_KEY (free at enter.pollinations.ai/keys)")
        return key

    def is_available(self) -> tuple[bool, str]:
        if not os.environ.get("FORGE3D_POLLINATIONS_KEY"):
            return False, "FORGE3D_POLLINATIONS_KEY not set"
        return True, "key present (quota checked at request time)"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 model: str = "trellis-2-low", **kwargs) -> GenerateResult:
        key = self._key()
        if model not in MODEL_PRICES:
            raise ProviderError(f"unknown model {model}; pick from {list(MODEL_PRICES)}")
        payload = {"model": model, "prompt": prompt or "",
                   "image": str(image) if image else None}
        req = urllib.request.Request(
            self.API, data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                job = json.loads(r.read())
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"pollinations 3d submit failed: {e}")
        job_id = job.get("id") or job.get("job_id")
        if not job_id:
            raise ProviderError(f"no job id in response: {job}")
        # poll for completion
        deadline = time.time() + 1200
        status_url = f"{self.API}/{urllib.parse.quote(str(job_id))}"
        while time.time() < deadline:
            time.sleep(15)
            sreq = urllib.request.Request(
                status_url, headers={"Authorization": f"Bearer {key}"})
            try:
                with urllib.request.urlopen(sreq, timeout=30) as r:
                    st = json.loads(r.read())
            except Exception as e:  # noqa: BLE001
                raise ProviderError(f"pollinations 3d status failed: {e}")
            status = st.get("status")
            if status == "completed":
                glb_url = st.get("glb_url") or st.get("result_url")
                if not glb_url:
                    raise ProviderError(f"completed but no GLB url: {st}")
                out = Path(out_dir) / f"pollinations-{job_id}.glb"
                with urllib.request.urlopen(glb_url, timeout=300) as r:
                    out.write_bytes(r.read())
                return GenerateResult(glb_path=out, provider=f"pollinations-3d:{model}",
                                      meta={"job_id": job_id, "pollen_cost": MODEL_PRICES[model]})
            if status in ("failed", "error"):
                raise ProviderError(f"pollinations 3d job failed: {st}")
        raise ProviderError("pollinations 3d job timed out after 20 min")
