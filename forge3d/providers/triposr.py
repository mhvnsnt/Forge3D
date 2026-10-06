"""TripoSR local provider (Stability AI, MIT license).

Fast single-image -> textured mesh. Runs on GPU; CPU fallback is slow
(2-10 min/image) but functional. Model weights downloaded on first use
from the official repo (stabilityai/TripoSR).
"""
from __future__ import annotations

from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)


class TripoSRProvider(ModelProvider):
    info = ProviderInfo(
        name="triposr",
        kind="local",
        capabilities=[Capability.IMAGE_TO_3D],
        license="MIT",
        commercial_ok=True,
        needs_gpu=True,  # works on CPU, painfully slow
        needs_key=False,
        quota_note="unlimited (your hardware)",
    )

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # noqa
        except ImportError:
            return False, "torch not installed (pip install -r requirements-local.txt)"
        # TripoSR source checkout expected at providers/_vendor/triposr
        vendor = Path(__file__).parent / "_vendor" / "triposr"
        if not (vendor / "run.py").exists():
            return False, "TripoSR repo not vendored (see docs/FREE_RUNNER_GUIDE.md)"
        return True, "ok"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        if image is None:
            raise ProviderError("triposr needs --image (image-to-3D only)")
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(reason)
        # Real implementation shells to vendored TripoSR; wired during port step.
        raise ProviderError("triposr run wiring pending (see docs/INVENTORY.md)")
