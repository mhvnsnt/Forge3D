"""Stable Fast 3D (SF3D) local provider — Stability AI.

Stability AI Community License: free for research, non-commercial AND
commercial use under $1M annual revenue. Gated HF checkpoint (accept license).
~7-9 GB VRAM, 0.5s on A100-class. Outputs UV-unwrapped GLB with de-lit
albedo + normal + metallic-roughness. Best quality-per-VRAM textured model
that fits free-tier GPUs (Colab T4 16GB).
"""
from __future__ import annotations

from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)


class SF3DProvider(ModelProvider):
    info = ProviderInfo(
        name="sf3d",
        kind="local",
        capabilities=[Capability.IMAGE_TO_3D],
        license="Stability-AI-Community (free <$1M revenue)",
        commercial_ok=True,  # safe for us: well under $1M
        needs_gpu=True,
        needs_key=False,
        quota_note="unlimited (your hardware); HF gated checkpoint, accept license once",
    )

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # noqa
        except ImportError:
            return False, "torch not installed (pip install -r requirements-local.txt)"
        vendor = Path(__file__).parent / "_vendor" / "stable-fast-3d"
        if not (vendor / "run.py").exists():
            return False, "SF3D repo not vendored (see docs/FREE_RUNNER_GUIDE.md)"
        return True, "ok"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        if image is None:
            raise ProviderError("sf3d needs --image (image-to-3D only)")
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(reason)
        raise ProviderError("sf3d run wiring pending (see docs/INVENTORY.md)")
