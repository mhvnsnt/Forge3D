"""MV-Adapter provider (ICCV 2025) — Apache-2.0, commercial-safe multi-view.

Text or image (+ optional depth/normal) -> 6 consistent multi-view images
(768^2 via SDXL). The legal multi-view backbone for the texture-baking path
(replaces CC-BY-NC Zero123++ for anything commercial).

Caveat: needs SD2.1/SDXL base = CreativeML Open RAIL++-M (commercial OK with
ethical-use restrictions; propagate Attachment-A notice).

Install (GPU runner): git clone https://github.com/huanngzh/MV-Adapter
+ pip install -r requirements.txt + weights: huggingface-cli download
huanngzh/mv-adapter -> $FORGE3D_WEIGHTS/mv-adapter (+ SDXL base ~6.9GB fp16)
~14GB VRAM (less with CPU offload).
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)

WEIGHTS = Path(os.environ.get("FORGE3D_WEIGHTS", "~/.forge3d/weights")).expanduser() / "mv-adapter"

INSTALL = ("MV-Adapter not ready: need CUDA GPU (~14GB), "
           "git clone https://github.com/huanngzh/MV-Adapter, "
           "pip install -r requirements.txt, "
           "huggingface-cli download huanngzh/mv-adapter -> $FORGE3D_WEIGHTS/mv-adapter")


class MVAdapterProvider(ModelProvider):
    info = ProviderInfo(
        name="mv-adapter",
        kind="local",
        capabilities=[Capability.MULTIVIEW, Capability.TEXT_TO_3D],
        license="Apache-2.0 (adapter); SDXL base: Open RAIL++-M",
        commercial_ok=True,
        needs_gpu=True,
        quota_note="",
    )

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # type: ignore
            if not torch.cuda.is_available():
                return False, "no CUDA GPU (MV-Adapter needs ~14GB VRAM)"
        except ImportError:
            return False, "torch not installed"
        if not WEIGHTS.exists():
            return False, f"weights missing at {WEIGHTS}"
        return True, "ready (wiring to repo API pending first GPU run)"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(f"mv-adapter unavailable: {reason}. {INSTALL}")
        # Multi-view image generation; meshing happens downstream (TripoSG etc.)
        # Full repo-API wiring lands on the first GPU runner run — until then,
        # loud failure rather than a fake mesh.
        raise ProviderError(
            "mv-adapter: repo API wiring pending first GPU-runner verification "
            "(weights + CUDA present; see MV-Adapter README ig2mv pipeline)")
