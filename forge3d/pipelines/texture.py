"""Texture refinement stage: enhance the (often blurry) textures of a generated mesh.

Backends:
  - "lanczos" (default, CPU, always available): extracts embedded texture
    images from the GLB and upscales 2x with high-quality Lanczos resampling.
    Honest scope: this increases texel density, it does NOT synthesize new
    detail. Recorded as such in run.json.
  - "realesrgan" (Apache-2.0/BSD-2-Clause, vendored): true AI
    super-resolution — RRDBNet x2 torch inference (vendored BasicSR arch +
    official RealESRGAN_x2 weights, tiled for CPU RAM). Wired via
    pipelines/upscale.py's esrgan2x(); raises ProviderError (loud, no
    silent fallback) if torch/weights are unavailable.
  - "hunyuan-paint" (future): Tencent Hunyuan3D-Paint texture repainting.
    License: Tencent Hunyuan 3D Community License (EU/UK/SK excluded,
    1M MAU cap, attribution) — gated, texture-stage-only. Wired when the
    model is pulled; until then requesting it raises ProviderError.

Never returns the input silently claiming "refined": the output filename
records the backend used (e.g. .tex-lanczos2x.glb).
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from ..providers.base import ProviderError
from .glbutil import (iter_embedded_images as _iter_texture_images,
                      parse_glb, repoint_image, write_glb)


def _lanczos2x(pil: Image.Image) -> Image.Image:
    w, h = pil.size
    rs = getattr(Image, "Resampling", Image)
    filt = getattr(rs, "LANCZOS", getattr(rs, "Lanczos", 1))
    return pil.resize((w * 2, h * 2), filt)


def _realesrgan2x(pil: Image.Image) -> Image.Image:
    # Now wired: vendored torch RRDBNet inference (see pipelines/upscale.py).
    from .upscale import esrgan2x
    return esrgan2x(pil)


def refine_textures(glb: Path, out_dir: Path, backend: str = "lanczos") -> Path:
    """Refine embedded textures. Returns path to the refined GLB.

    Raises ProviderError if the GLB has no embedded textures to refine
    (nothing to do is a loud no-op, not a fake "refined" file) or if the
    requested backend is unavailable.
    """
    if backend == "hunyuan-paint":
        raise ProviderError(
            "texture backend 'hunyuan-paint' not wired yet (model pull pending)")
    if backend not in ("lanczos", "realesrgan"):
        raise ProviderError(f"unknown texture backend: {backend}")

    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc, blob = parse_glb(glb)

    refined = 0
    new_blob = bytearray(blob)
    for idx, pil, mime in _iter_texture_images(doc, blob):
        before = pil.size
        out_img = _lanczos2x(pil) if backend == "lanczos" else _realesrgan2x(pil)
        buf = io.BytesIO()
        out_img.save(buf, format="PNG")
        new_blob = repoint_image(doc, idx, buf.getvalue(), new_blob)
        refined += 1
        print(f"texture: image[{idx}] {before} -> {out_img.size} ({backend})",
              file=sys.stderr)

    if refined == 0:
        raise ProviderError(
            f"texture stage: no embedded textures found in {glb.name}; "
            "nothing to refine (refusing to fake it)")

    out = out_dir / f"{glb.stem}.tex-{backend}2x.glb"
    return write_glb(doc, bytes(new_blob), out)
