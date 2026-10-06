"""Texture refinement stage: enhance the (often blurry) textures of a generated mesh.

Backends:
  - "lanczos" (default, CPU, always available): extracts embedded texture
    images from the GLB and upscales 2x with high-quality Lanczos resampling.
    Honest scope: this increases texel density, it does NOT synthesize new
    detail. Recorded as such in run.json.
  - "realesrgan" (BSD, AshLanev2 provenance): true AI super-resolution when
    the realesrgan package + weights are installed. Raises ProviderError
    (loud, no silent fallback) if requested but unavailable.
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


def _iter_texture_images(doc: dict, bin_blob: bytes):
    """Yield (image_index, PIL.Image, mime) for embedded buffer-view images."""
    images = doc.get("images", [])
    buffer_views = doc.get("bufferViews", [])
    for idx, img in enumerate(images):
        bv = img.get("bufferView")
        if bv is None:
            continue
        view = buffer_views[bv]
        start = view.get("byteOffset", 0)
        end = start + view["byteLength"]
        try:
            pil = Image.open(io.BytesIO(bin_blob[start:end])).convert("RGB")
        except Exception:
            continue
        yield idx, pil, img.get("mimeType", "image/png")


def _lanczos2x(pil: Image.Image) -> Image.Image:
    w, h = pil.size
    rs = getattr(Image, "Resampling", Image)
    filt = getattr(rs, "LANCZOS", getattr(rs, "Lanczos", 1))
    return pil.resize((w * 2, h * 2), filt)


def _realesrgan2x(pil: Image.Image) -> Image.Image:
    try:
        from realesrgan import RealESRGAN  # type: ignore
    except ImportError:
        raise ProviderError(
            "texture backend 'realesrgan' requested but not installed "
            "(pip install realesrgan + weights)")
    import torch  # type: ignore
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = RealESRGAN(device, scale=2)
    model.load_weights("weights/RealESRGAN_x2.pth", download=True)
    arr = np.array(pil)
    out, _ = model.predict(arr)
    return Image.fromarray(out)


def refine_textures(glb: Path, out_dir: Path, backend: str = "lanczos") -> Path:
    """Refine embedded textures. Returns path to the refined GLB.

    Raises ProviderError if the GLB has no embedded textures to refine
    (nothing to do is a loud no-op, not a fake "refined" file) or if the
    requested backend is unavailable.
    """
    import json as _json
    import struct as _struct

    if backend == "hunyuan-paint":
        raise ProviderError(
            "texture backend 'hunyuan-paint' not wired yet (model pull pending)")
    if backend not in ("lanczos", "realesrgan"):
        raise ProviderError(f"unknown texture backend: {backend}")

    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = glb.read_bytes()
    if data[:4] != b"glTF":
        raise ProviderError(f"not a GLB: {glb}")
    jlen = _struct.unpack("<I", data[12:16])[0]
    doc = _json.loads(data[20:20 + jlen])
    binoff = 20 + jlen
    blen = _struct.unpack("<I", data[binoff:binoff + 4])[0]
    blob = data[binoff + 8:binoff + 8 + blen]

    refined = 0
    new_blobs: dict[int, bytes] = {}
    for idx, pil, mime in _iter_texture_images(doc, blob):
        before = pil.size
        out_img = _lanczos2x(pil) if backend == "lanczos" else _realesrgan2x(pil)
        buf = io.BytesIO()
        out_img.save(buf, format="PNG")
        new_blobs[idx] = buf.getvalue()
        refined += 1
        print(f"texture: image[{idx}] {before} -> {out_img.size} ({backend})",
              file=sys.stderr)

    if refined == 0:
        raise ProviderError(
            f"texture stage: no embedded textures found in {glb.name}; "
            "nothing to refine (refusing to fake it)")

    # Rebuild the binary chunk: append new PNGs, repoint bufferViews.
    views = doc["bufferViews"]
    images = doc["images"]
    new_blob = bytearray(blob)
    for idx, png in new_blobs.items():
        bv = images[idx]["bufferView"]
        off = len(new_blob)
        # 4-byte align
        pad = (-len(new_blob)) % 4
        new_blob.extend(b"\x00" * pad)
        off = len(new_blob)
        new_blob.extend(png)
        views[bv]["byteOffset"] = off
        views[bv]["byteLength"] = len(png)
        images[idx]["mimeType"] = "image/png"

    new_doc = _json.dumps(doc, separators=(",", ":")).encode()
    # 4-byte align JSON chunk, pad with spaces per glTF spec
    pad = (-len(new_doc)) % 4
    new_doc += b" " * pad
    total = 12 + 8 + len(new_doc) + 8 + len(new_blob)
    header = _struct.pack("<III", 0x46546C67, 2, total)
    jchunk = _struct.pack("<II", len(new_doc), 0x4E4F534A) + new_doc
    bpad = (-len(new_blob)) % 4
    new_blob.extend(b"\x00" * bpad)
    bchunk = _struct.pack("<II", len(new_blob), 0x004E4942) + bytes(new_blob)

    out = out_dir / f"{glb.stem}.tex-{backend}2x.glb"
    out.write_bytes(header + jchunk + bchunk)
    return out
