"""detail.py — micro-surface detail synthesis for generated textures.

Closes the NATIVE DETAIL gap from the texture side (sibling's normalmap.py
bakes normals from GEOMETRY; this synthesizes detail-normals from the
TEXTURE's own high-frequency content, which is where trellis outputs hide
their finest detail):

1. micro-contrast: extract high-frequency luminance, re-inject amplified
   (perceptual detail lift on the albedo, no new assets needed).
2. detail normal map: Sobel gradients of the luminance -> tangent-space
   normal map, attached as the material's normalTexture (skipped when the
   material already carries one, to avoid clobbering the geometry-baked map).

Dependency-free (PIL + numpy). Output: <stem>.detail.glb + <stem>.detail.json.
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from .glbutil import (append_images, iter_embedded_images, parse_glb,
                      repoint_image, write_glb)


def micro_contrast(img: Image.Image, amount: float = 0.55,
                   radius: float = 2.0) -> Image.Image:
    """Boost high-frequency luminance (unsharp-mask style)."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    # luminance
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
    blur = np.asarray(
        Image.fromarray(lum.astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(radius)), dtype=np.float32)
    hf = lum - blur
    # keep boost conservative in dark regions to avoid noise amplification
    mask = np.clip((lum - 24.0) / 120.0, 0.0, 1.0)
    lum2 = np.clip(lum + amount * hf * mask, 0, 255)
    # re-apply luminance delta proportionally to RGB
    delta = (lum2 - lum)[..., None] / np.maximum(lum[..., None], 1.0)
    out = np.clip(a * (1.0 + 0.85 * delta), 0, 255)
    return Image.fromarray(out.astype(np.uint8))


def luminance_normal_map(img: Image.Image, strength: float = 1.6) -> Image.Image:
    """Sobel-of-luminance -> tangent-space normal map (RGB)."""
    a = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    # Sobel kernels
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    ky = kx.T
    from scipy import ndimage  # noqa
    dx = ndimage.convolve(a, kx, mode="nearest") * strength
    dy = ndimage.convolve(a, ky, mode="nearest") * strength
    n = np.stack([-dx, -dy, np.ones_like(a)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8
    rgb = ((n * 0.5 + 0.5) * 255.0).astype(np.uint8)
    # flip green for OpenGL convention used by glTF
    rgb[..., 1] = 255 - rgb[..., 1]
    return Image.fromarray(rgb)


def luminance_normal_map_numpy(img: Image.Image,
                               strength: float = 1.6) -> Image.Image:
    """Sobel-of-luminance normal map, dependency-free (no scipy)."""
    a = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    # separable Sobel via shifts
    px = np.roll(a, -1, axis=1)
    nx = np.roll(a, 1, axis=1)
    py = np.roll(a, -1, axis=0)
    ny = np.roll(a, 1, axis=0)
    pxd = np.roll(a, (-1, -1), axis=(0, 1))
    pxu = np.roll(a, (1, -1), axis=(0, 1))
    nxd = np.roll(a, (-1, 1), axis=(0, 1))
    nxu = np.roll(a, (1, 1), axis=(0, 1))
    dx = ((pxu + 2 * px + pxd) - (nxu + 2 * nx + nxd)) * strength / 4.0
    dy = ((pxd + 2 * py + nxd) - (pxu + 2 * ny + nxu)) * strength / 4.0
    n = np.stack([-dx, -dy, np.ones_like(a)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8
    rgb = ((n * 0.5 + 0.5) * 255.0).astype(np.uint8)
    rgb[..., 1] = 255 - rgb[..., 1]  # OpenGL green
    return Image.fromarray(rgb)


def run(glb_path: str | Path, out_dir: str | Path | None = None,
        micro: float = 0.55) -> dict:
    t0 = time.time()
    glb_path = Path(glb_path)
    out_dir = Path(out_dir) if out_dir else glb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    doc, blob = parse_glb(glb_path)
    blob = bytearray(blob)
    report = {"input": str(glb_path), "stage": "detail",
              "micro_contrast": micro, "textures": []}

    detail_normals: list[tuple[bytes, str]] = []
    for idx, pil, mime in iter_embedded_images(doc, bytes(blob)):
        t1 = time.time()
        sharp = micro_contrast(pil, amount=micro)
        buf = io.BytesIO()
        sharp.save(buf, format="JPEG", quality=92)
        blob = repoint_image(doc, idx, buf.getvalue(), blob, "image/jpeg")
        # detail normal from the ORIGINAL (pre-boost) texture
        nmap = luminance_normal_map_numpy(pil)
        nbuf = io.BytesIO()
        nmap.save(nbuf, format="PNG")
        detail_normals.append((nbuf.getvalue(), "image/png"))
        report["textures"].append({
            "image_index": idx,
            "in": [pil.width, pil.height],
            "seconds": round(time.time() - t1, 1),
        })

    if not report["textures"]:
        raise RuntimeError(f"no embedded images in {glb_path}")

    # attach the first detail normal map as normalTexture where missing
    doc, new_blob, (nimg_idx,) = append_images(
        doc, bytes(blob), [detail_normals[0]])
    blob = bytearray(new_blob)
    if "textures" not in doc:
        doc["textures"] = []
    doc["textures"].append({"source": nimg_idx, "name": "forge3d_detail_nrm"})
    ntex_idx = len(doc["textures"]) - 1
    attached = 0
    for mat in doc.get("materials", []):
        if "normalTexture" not in mat:
            mat["normalTexture"] = {"index": ntex_idx, "texCoord": 0,
                                    "scale": 1.0}
            attached += 1
    report["detail_normal_attached_to"] = attached

    stem = glb_path.stem
    out_glb = out_dir / f"{stem}.detail.glb"
    write_glb(doc, bytes(blob), out_glb)
    report["output"] = str(out_glb)
    report["total_seconds"] = round(time.time() - t0, 1)
    (out_dir / f"{stem}.detail.json").write_text(json.dumps(report, indent=2))
    return report


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m forge3d.pipelines.detail <in.glb> [outdir]")
        return 2
    print(json.dumps(run(argv[1], argv[2] if len(argv) > 2 else None),
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
