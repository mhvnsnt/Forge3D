"""TripoSG provider (VAST AI Research) — MIT, commercial-safe.

Low-VRAM watertight geometry workhorse (8-12GB CUDA). Rectified-flow DiT
image->3D; GEOMETRY ONLY (no texture) — pair with the texture stage
(Hunyuan3D-Paint) for full PBR output.

Install (GPU runner): git clone https://github.com/VAST-AI-Research/TripoSG
+ pip install -r requirements.txt + weights: huggingface-cli download
VAST-AI/TripoSG (~6GB) -> $FORGE3D_WEIGHTS/triposg
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)

WEIGHTS = Path(os.environ.get("FORGE3D_WEIGHTS", "~/.forge3d/weights")).expanduser() / "triposg"

INSTALL = ("TripoSG not ready: need CUDA GPU (8GB+), "
           "git clone https://github.com/VAST-AI-Research/TripoSG, "
           "pip install -r requirements.txt, "
           "huggingface-cli download VAST-AI/TripoSG -> $FORGE3D_WEIGHTS/triposg")


class TripoSGProvider(ModelProvider):
    info = ProviderInfo(
        name="triposg",
        kind="local",
        capabilities=[Capability.IMAGE_TO_3D],
        license="MIT (code + weights)",
        commercial_ok=True,
        needs_gpu=True,
        quota_note="",
    )

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # type: ignore
            if not torch.cuda.is_available():
                return False, "no CUDA GPU (TripoSG needs 8GB+ VRAM)"
        except ImportError:
            return False, "torch not installed"
        if not WEIGHTS.exists():
            return False, f"weights missing at {WEIGHTS}"
        if importlib.util.find_spec("triposg") is None:
            return False, "triposg package not installed (git clone + pip install)"
        return True, "ready"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(f"triposg unavailable: {reason}. {INSTALL}")
        if not image:
            raise ProviderError("triposg is image-to-3D: --image required")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            # official inference entrypoint (see TripoSG README); any API
            # drift surfaces here as a loud ProviderError, never a fake mesh
            from triposg.pipelines import TripoSGPipeline  # type: ignore
            import torch  # type: ignore
            pipe = TripoSGPipeline.from_pretrained(str(WEIGHTS)).to("cuda")
            mesh = pipe(str(image))  # RGBA, background-removed input
            glb = out_dir / "triposg.glb"
            mesh.export(str(glb))
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"triposg inference failed: {e}")
        return GenerateResult(glb_path=glb, provider="triposg",
                              meta={"note": "geometry-only; run texture stage next"})
