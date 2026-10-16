"""TRELLIS.2 provider (Microsoft) — MIT, the SOTA quality anchor.

Single image -> textured PBR GLB (basecolor/rough/metal/opacity), 512^3-1536^3.
Wired against the real upstream API (verified against microsoft/TRELLIS.2
source, 2026-10-16; GPU-run verification still pending — see note below).

Upstream : https://github.com/microsoft/TRELLIS.2 (MIT)
Weights  : microsoft/TRELLIS.2-4B on Hugging Face (MIT)
VRAM     : 24GB official (A100/H100, Linux). Community fp16 path may fit 16GB
           (experimental — set FORGE3D_TRELLIS2_FP16=1).

GPU-runner note: this sandbox has no CUDA GPU, so generate() is verified
code-correct against the upstream source but NOT yet executed. First GPU run
(Kaggle/Colab/Lightning) must confirm before the stub-era warning is lifted.
It still FAILS LOUDLY when unavailable (owner law: no fake outputs).

Friction: DINOv3 dependency is HF-gated (login + Meta terms) — install docs
in docs/WEIGHTS.md.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)

WEIGHTS = Path(os.environ.get("FORGE3D_WEIGHTS", "~/.forge3d/weights")).expanduser() / "trellis2"
REPO = Path(os.environ.get("FORGE3D_TRELLIS2_REPO", "")).expanduser()  # local TRELLIS.2 checkout

INSTALL = (
    "TRELLIS.2 not ready on this host.\n"
    "GPU runner setup (Kaggle/Colab/Lightning, Linux + CUDA 12.x):\n"
    "  git clone https://github.com/microsoft/TRELLIS.2\n"
    "  cd TRELLIS.2 && bash setup.sh   # flash-attn, nvdiffrast, CuMesh, o-voxel\n"
    "  # weights (MIT): huggingface.co/microsoft/TRELLIS.2-4B -> $FORGE3D_WEIGHTS/trellis2\n"
    "  export FORGE3D_TRELLIS2_REPO=/path/to/TRELLIS.2\n"
    "Then forge3d generate --provider trellis2 --image X.png"
)


class Trellis2Provider(ModelProvider):
    info = ProviderInfo(
        name="trellis2",
        kind="local",
        capabilities=[Capability.IMAGE_TO_3D],  # v2 ships image-to-3D + texturing only
        license="MIT (code + weights)",
        commercial_ok=True,
        needs_gpu=True,
        quota_note="unlimited (your hardware)",
    )

    def _repo_on_path(self) -> Path | None:
        candidates = [REPO] if str(REPO) else []
        here = Path(__file__).resolve()
        candidates += [
            here.parent / "_vendor" / "TRELLIS.2",
            Path.home() / "workspace" / "TRELLIS.2",
        ]
        import sys
        for c in candidates:
            if c and (c / "trellis2").is_dir():
                if str(c) not in sys.path:
                    sys.path.insert(0, str(c))
                return c
        return None

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # type: ignore
        except ImportError:
            return False, "torch not installed"
        if not torch.cuda.is_available():
            return False, "no CUDA GPU (TRELLIS.2 needs ~24GB VRAM)"
        if self._repo_on_path() is None:
            return False, "TRELLIS.2 repo not found (set FORGE3D_TRELLIS2_REPO)"
        if not WEIGHTS.exists():
            return False, f"weights missing at {WEIGHTS}"
        if importlib.util.find_spec("trellis2") is None:
            return False, "trellis2 package not importable from the repo checkout"
        return True, "ok"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 seed: int = 42, texture_size: int = 2048,
                 decimation_target: int = 250000,
                 **kwargs) -> GenerateResult:
        if image is None:
            raise ProviderError("trellis2 needs --image (image-to-3D only)")
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(f"trellis2 unavailable: {reason}\n{INSTALL}")

        try:
            import torch
            from PIL import Image
            from trellis2.pipelines import Trellis2ImageTo3DPipeline
            import o_voxel
        except Exception as e:
            raise ProviderError(f"TRELLIS.2 imports failed: {e}")

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            pipeline = Trellis2ImageTo3DPipeline.from_pretrained(str(WEIGHTS))
            if os.environ.get("FORGE3D_TRELLIS2_FP16") == "1":
                pipeline = pipeline.half()
            pipeline.cuda()
            pil = Image.open(image).convert("RGB")
            with torch.no_grad():
                mesh = pipeline.run(pil, seed=seed)[0]
            mesh.simplify(16777216)  # nvdiffrast limit (upstream example.py)
            glb = o_voxel.postprocess.to_glb(
                vertices=mesh.vertices,
                faces=mesh.faces,
                attr_volume=mesh.attrs,
                coords=mesh.coords,
                attr_layout=mesh.layout,
                voxel_size=mesh.voxel_size,
                aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
                decimation_target=decimation_target,
                texture_size=texture_size,
                remesh=True,
                remesh_band=1,
                remesh_project=0,
                verbose=False,
            )
            out = out_dir / f"trellis2-{Path(image).stem}.glb"
            glb.export(str(out))
        except Exception as e:
            raise ProviderError(f"TRELLIS.2 inference failed: {e}")

        if not out.exists() or out.stat().st_size < 1000:
            raise ProviderError("TRELLIS.2 produced no usable mesh")
        return GenerateResult(
            glb_path=out, provider="trellis2",
            meta={"seed": seed, "texture_size": texture_size,
                  "decimation_target": decimation_target,
                  "gpu_verified": False})  # set True after first real GPU run
