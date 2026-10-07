"""Cloudflare Workers AI text-to-image (SDXL) — key-ready provider.

Free tier (verified 2026-10-06, free-apis.md): 10,000 Neurons/day, no
credit card. Needs a free Cloudflare account:
  1. dash.cloudflare.com -> Workers AI (free, no card)
  2. Create API token (My Profile -> API Tokens) with Workers AI Read
  3. Account ID from the dashboard sidebar
Store as FORGE3D_CLOUDFLARE_KEY and FORGE3D_CLOUDFLARE_ACCOUNT_ID
(env or ~/.config/forge3d/api_keys.env — see docs/ACCOUNTS.md).

Concept stage only (like pollinations-image / flux-space): fetch_image()
produces the concept PNG; feed it to an image-to-3D provider. generate()
raises loudly per the provider contract.

Model: @cf/stabilityai/stable-diffusion-xl-base-1.0 (SDXL license terms
apply to the model; outputs usable per Stability AI Community License).
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)
from .keys import get_key, key_source


class CloudflareWorkersAIProvider(ModelProvider):
    info = ProviderInfo(
        name="cloudflare-workers-ai",
        kind="api",
        capabilities=[Capability.TEXT_TO_IMAGE],  # concept-image stage
        license="service-terms (Cloudflare); SDXL: Stability AI Community License",
        commercial_ok=False,  # check Cloudflare + Stability terms before shipping
        needs_gpu=False,
        needs_key=True,
        quota_note="free: 10,000 Neurons/day, no card; key via free Cloudflare account",
    )

    MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"

    def _creds(self) -> tuple[str, str]:
        key = get_key("FORGE3D_CLOUDFLARE_KEY")
        acct = get_key("FORGE3D_CLOUDFLARE_ACCOUNT_ID")
        if not key or not acct:
            raise ProviderError(
                "cloudflare-workers-ai needs FORGE3D_CLOUDFLARE_KEY and "
                "FORGE3D_CLOUDFLARE_ACCOUNT_ID (free at dash.cloudflare.com, "
                "no card; see module docstring)")
        return key, acct

    def is_available(self) -> tuple[bool, str]:
        ks, asrc = key_source("FORGE3D_CLOUDFLARE_KEY"), key_source("FORGE3D_CLOUDFLARE_ACCOUNT_ID")
        if ks == "missing" or asrc == "missing":
            return False, "FORGE3D_CLOUDFLARE_KEY / _ACCOUNT_ID not set"
        return True, f"creds present (key via {ks}, account via {asrc})"

    def fetch_image(self, prompt: str, out_path: Path,
                    width: int = 1024, height: int = 1024,
                    seed: int = 42, steps: int = 20,
                    timeout: int = 300) -> Path:
        key, acct = self._creds()
        url = (f"https://api.cloudflare.com/client/v4/accounts/{acct}"
               f"/ai/run/{self.MODEL}")
        payload = json.dumps({
            "prompt": prompt, "width": width, "height": height,
            "num_steps": steps, "seed": seed,
        }).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body, ctype = r.read(), r.headers.get("Content-Type", "")
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"cloudflare-workers-ai request failed: {e}")
        if "image" not in ctype:
            raise ProviderError(
                "cloudflare-workers-ai: non-image response "
                f"({ctype}): {body[:200]!r}")
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(body)
        if out_path.stat().st_size < 1024:
            raise ProviderError("cloudflare-workers-ai: image suspiciously small")
        return out_path

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        raise ProviderError(
            "cloudflare-workers-ai is a concept stage, not a 3D provider; "
            "use fetch_image() then run an image-to-3d provider")
