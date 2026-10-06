"""TRELLIS.2 provider (Microsoft) — MIT, the SOTA quality anchor.

Single image -> textured PBR GLB (basecolor/rough/metal/opacity), 512^3-1536^3.
Defaults target ~1M-tri 4K-textured raw output. Open-surface by design.

Needs 24GB VRAM (A100/H100, Linux); community FP8 variant lowers this.
Friction: DINOv3 dependency is HF-gated (login + Meta terms).

Install (GPU runner): git clone https://github.com/microsoft/TRELLIS.2
+ conda env (CUDA 12.4, flash-attn, nvdiffrast, CuMesh) +
weights microsoft/TRELLIS.2-4B (~15GB) -> $FORGE3D_WEIGHTS/trellis2
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)

WEIGHTS = Path(os.environ.get("FORGE3D_WEIGHTS", "~/.forge3d/weights")).expanduser() / "trellis2"

INSTALL = ("TRELLIS.2 not ready: need CUDA GPU (24GB), Linux, "
           "git clone https://github.com/microsoft/TRELLIS.2 + conda env, "
           "weights microsoft/TRELLIS.2-4B -> $FORGE3D_WEIGHTS/trellis2")


class Trellis2Provider(ModelProvider):
    info = ProviderInfo(
        name="trellis2",
        kind="local",
        capabilities=[Capability.IMAGE_TO_3D, Capability.TEXT_TO_3D],
        license="MIT (code + weights)",
        commercial_ok=True,
        needs_gpu=True,
        quota_note="",
    )

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # type: ignore
            if not torch.cuda.is_available():
                return False, "no CUDA GPU (TRELLIS.2 needs 24GB VRAM)"
        except ImportError:
            return False, "torch not installed"
        if not WEIGHTS.exists():
            return False, f"weights missing at {WEIGHTS}"
        return True, "ready (wiring to repo API pending first GPU run)"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(f"trellis2 unavailable: {reason}. {INSTALL}")
        raise ProviderError(
            "trellis2: repo API wiring pending first GPU-runner verification "
            "(weights + CUDA present; see TRELLIS.2 README image-to-3D pipeline)")
