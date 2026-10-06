"""Tripo3D API Platform provider.

API Platform Basic: 300 credits/month free, 1 concurrent task, no card.
Text-to-3D ~30 cr/model => ~10 models/month via API. Key format tsk_...
via env var FORGE3D_TRIPO_KEY only — never in the repo.

COMMERCIAL WARNING: free-tier outputs are public + NON-commercial (CC BY 4.0).
Prototyping/reference only — nothing free-tier ships in a money build.
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)


class TripoAPIProvider(ModelProvider):
    info = ProviderInfo(
        name="tripo-api",
        kind="api",
        capabilities=[Capability.TEXT_TO_3D, Capability.IMAGE_TO_3D],
        license="service-terms (free tier: CC BY 4.0, non-commercial)",
        commercial_ok=False,
        needs_gpu=False,
        needs_key=True,
        quota_note="300 credits/month free API platform; ~10 models/month",
    )

    def is_available(self) -> tuple[bool, str]:
        if not os.environ.get("FORGE3D_TRIPO_KEY"):
            return False, "FORGE3D_TRIPO_KEY not set (free at platform.tripo3d.ai)"
        return True, "key present (quota checked at request time)"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(reason)
        # REST wiring: POST platform.tripo3d.ai task, poll, download GLB.
        raise ProviderError("tripo-api REST wiring pending (see docs/INVENTORY.md)")
