"""Pollinations.ai image provider — keyless free text-to-image (Flux/Turbo).

Feeds the concept-image stage: text prompt -> reference image -> image-to-3D.
No signup, no key, no quota published. Honest failure on network errors.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)


class PollinationsImageProvider(ModelProvider):
    info = ProviderInfo(
        name="pollinations-image",
        kind="api",
        capabilities=[],  # concept-image stage, not 3D — registered for discovery
        license="service-terms",
        commercial_ok=False,  # check enter.pollinations.ai terms before shipping
        needs_gpu=False,
        needs_key=False,
        quota_note="free/keyless public endpoint (image); 3D endpoint needs key",
    )

    ENDPOINT = "https://image.pollinations.ai/prompt/"

    def is_available(self) -> tuple[bool, str]:
        return True, "keyless endpoint (network required)"

    def fetch_image(self, prompt: str, out_path: Path,
                    width: int = 1024, height: int = 1024,
                    seed: int = 42, retries: int = 5) -> Path:
        url = (self.ENDPOINT + urllib.parse.quote(prompt)
               + f"?width={width}&height={height}&seed={seed}&nologo=true&model=flux")
        import time
        last_err: Exception | None = None
        for attempt in range(max(1, retries)):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Forge3D/0.1"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = r.read()
                if len(data) < 10_000:
                    raise ProviderError("pollinations returned suspiciously small payload")
                out_path.write_bytes(data)
                return out_path
            except ProviderError:
                raise  # honest failure, not transient
            except Exception as e:  # noqa: BLE001 — transient network drops
                last_err = e
                time.sleep(4 * (attempt + 1))
        raise ProviderError(f"pollinations image fetch failed after {retries} attempts: {last_err}")

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        raise ProviderError(
            "pollinations-image is a concept stage, not a 3D provider; "
            "use fetch_image() then run an image-to-3D provider")
