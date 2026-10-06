"""Hi3DGen provider (Stable-X) — geometry-quality option for GPU runners.

Single image -> normal-map intermediate -> high-detail mesh. Geometry only
(no integrated texture); rated best geometric detail in 2026 roundups.
~16-19GB VRAM, CUDA + spconv + xformers.

LICENSE: MIT per upstream README (TRELLIS-MIT provenance, NVIDIA-only libs
removed) — VERIFY the LICENSE file at pull time before shipping anything.

Install (GPU runner): git clone --recursive https://github.com/Stable-X/Hi3DGen
+ pip install torch spconv-cu121 xformers + pip install -r requirements.txt
+ weights Stable-X/trellis-normal-v0-1, Stable-X/yoso-normal-v1-8-1,
  ZhengPeng7/BiRefNet (~5.4GB) -> $FORGE3D_WEIGHTS/hi3dgen
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)

WEIGHTS = Path(os.environ.get("FORGE3D_WEIGHTS", "~/.forge3d/weights")).expanduser() / "hi3dgen"

INSTALL = ("Hi3DGen not ready: need CUDA GPU (16-19GB), "
           "git clone --recursive https://github.com/Stable-X/Hi3DGen, "
           "pip install torch spconv-cu121 xformers, weights -> $FORGE3D_WEIGHTS/hi3dgen; "
           "verify LICENSE file at pull time")


class Hi3DGenProvider(ModelProvider):
    info = ProviderInfo(
        name="hi3dgen",
        kind="local",
        capabilities=[Capability.IMAGE_TO_3D],
        license="MIT (per upstream README — verify LICENSE at pull time)",
        commercial_ok=True,
        needs_gpu=True,
        quota_note="",
    )

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # type: ignore
            if not torch.cuda.is_available():
                return False, "no CUDA GPU (Hi3DGen needs 16-19GB VRAM)"
        except ImportError:
            return False, "torch not installed"
        if not WEIGHTS.exists():
            return False, f"weights missing at {WEIGHTS}"
        return True, "ready (wiring to repo API pending first GPU run)"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(f"hi3dgen unavailable: {reason}. {INSTALL}")
        raise ProviderError(
            "hi3dgen: repo API wiring pending first GPU-runner verification "
            "(weights + CUDA present; confirm MIT LICENSE at pull time)")
