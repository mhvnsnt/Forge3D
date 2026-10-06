"""Hunyuan3D-Paint provider (Tencent) — the texture-refinement gap-closer.

Untextured mesh + reference image -> textured mesh with PBR maps
(albedo/normal/metallic/roughness), GLB out.

LICENSE: Tencent Hunyuan 3D 2.0 Community License (NOT Apache). Commercial
OK with conditions: territory EXCLUDES EU/UK/South Korea; >1M MAU needs
Tencent written approval; outputs cannot train competing models. Tracked in
LICENSES.md. 16GB VRAM for shape+texture (turbo variant lower).

Install (GPU runner): git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2
+ pip install -r requirements.txt && pip install -e . (compiles CUDA
rasterizers) + huggingface-cli download tencent/Hunyuan3D-2
-> $FORGE3D_WEIGHTS/hunyuan3d-2
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)

WEIGHTS = Path(os.environ.get("FORGE3D_WEIGHTS", "~/.forge3d/weights")).expanduser() / "hunyuan3d-2"

INSTALL = ("Hunyuan3D-Paint not ready: need CUDA GPU (16GB), "
           "git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2, "
           "pip install -r requirements.txt && pip install -e ., "
           "huggingface-cli download tencent/Hunyuan3D-2 -> $FORGE3D_WEIGHTS/hunyuan3d-2")


class HunyuanPaintProvider(ModelProvider):
    info = ProviderInfo(
        name="hunyuan-paint",
        kind="local",
        capabilities=[Capability.TEXTURE],
        license="Tencent Hunyuan 3D 2.0 Community License (conditional commercial)",
        commercial_ok=True,  # conditional: no EU/UK/SK, <1M MAU — see LICENSES.md
        needs_gpu=True,
        quota_note="",
    )

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # type: ignore
            if not torch.cuda.is_available():
                return False, "no CUDA GPU (Paint needs ~16GB VRAM)"
        except ImportError:
            return False, "torch not installed"
        if not WEIGHTS.exists():
            return False, f"weights missing at {WEIGHTS}"
        if importlib.util.find_spec("hy3dgen") is None:
            return False, "hy3dgen package not installed (Hunyuan3D-2 repo)"
        return True, "ready"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 mesh: Path | None = None, **kwargs) -> GenerateResult:
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(f"hunyuan-paint unavailable: {reason}. {INSTALL}")
        if mesh is None or image is None:
            raise ProviderError("hunyuan-paint needs mesh= + image= (untextured mesh + reference)")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            from hy3dgen.texgen import Hunyuan3DPaintPipeline  # type: ignore
            pipe = Hunyuan3DPaintPipeline.from_pretrained(str(WEIGHTS))
            out_mesh = pipe(mesh_path=str(mesh), image_path=str(image))
            glb = out_dir / "painted.glb"
            out_mesh.export(str(glb))
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"hunyuan-paint failed: {e}")
        return GenerateResult(glb_path=glb, provider="hunyuan-paint",
                              meta={"note": "Tencent license conditions apply"})
