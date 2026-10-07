"""speckle.py — UV-seam speckle reduction via island color dilation (bleed fill).

Diagnosis (2026-10-07, trellis2-concept2-high.glb): the visible "speckle" on
renders is NOT noise inside the albedo — a scan found 0 near-black pixels
inside skin regions. It is UV-SEAM BLEED: mip filtering samples the black
texture background at UV island boundaries, drawing dark speckled outlines
along every seam (visible as jagged dark/tan fringes tracing island edges).

Fix: dilate each UV island's edge colors outward into the background
("bleed", standard gamedev practice) so filtered samples at seams hit
island colors instead of black. Dependency-free (PIL + numpy).

Output: <stem>.despeckle.glb + JSON report with seam-band metrics.
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

from ..providers.base import ProviderError
from .glbutil import iter_embedded_images, parse_glb, repoint_image, write_glb


def uv_coverage_mask(uvs: np.ndarray, faces: np.ndarray, size: int) -> np.ndarray:
    """Boolean mask of texels covered by any UV triangle (PIL rasterization)."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    uv_px = (uvs * size).astype(np.float32)
    fuv = uv_px[faces]
    for tri in fuv:
        # clip absurd coords; degenerate tris draw nothing
        pts = [(float(x), float(y)) for x, y in tri]
        if max(abs(x) for x, y in pts) > size * 2 or max(abs(y) for x, y in pts) > size * 2:
            continue
        draw.polygon(pts, fill=1)
    return np.array(mask, dtype=bool)


def dilate_fill(img: np.ndarray, mask: np.ndarray, iters: int = 8) -> np.ndarray:
    """Propagate edge colors into background; vectorized, no scipy needed.

    img: HxWxC float32. mask: HxW bool, True = valid texel.
    Each iteration fills background pixels touching valid ones with the mean
    of their valid 3x3 neighbors.
    """
    h, w = mask.shape
    out = img.astype(np.float32).copy()
    valid = mask.copy()
    for _ in range(iters):
        pv = np.pad(valid.astype(np.float32), 1)
        pc = np.pad(out, ((1, 1), (1, 1), (0, 0)))
        cnt = np.zeros((h, w), dtype=np.float32)
        acc = np.zeros((h, w, out.shape[2]), dtype=np.float32)
        for dy in range(3):
            for dx in range(3):
                cnt += pv[dy:dy + h, dx:dx + w]
                acc += pc[dy:dy + h, dx:dx + w]
        fill = (~valid) & (cnt > 0)
        if not fill.any():
            break
        out[fill] = acc[fill] / cnt[fill][..., None]
        valid |= fill
    return np.clip(out, 0, 255).astype(np.uint8)


def _basecolor_image_indices(doc: dict) -> list[int]:
    idx = set()
    for m in doc.get("materials", []):
        pbr = m.get("pbrMetallicRoughness", {})
        for key in ("baseColorTexture",):
            t = pbr.get(key)
            if isinstance(t, dict) and "index" in t:
                tex = doc["textures"][t["index"]]
                idx.add(tex["source"])
    return sorted(idx)


def reduce_speckle(glb: Path, out_dir: Path, bleed_px: int = 8) -> tuple[Path, dict]:
    """Dilate UV-island colors on base-color textures. Returns (glb, report)."""
    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    doc, blob = parse_glb(glb)
    scene = trimesh.load(glb, force="scene")
    geoms = [g for g in scene.geometry.values() if hasattr(g.visual, "uv")]
    if not geoms:
        raise ProviderError("reduce_speckle: no UVs on input mesh")
    g = max(geoms, key=lambda x: len(x.faces))
    uvs = np.asarray(g.visual.uv, dtype=np.float64)
    # glTF UV origin is top-left; flip V for image coords
    uvs = np.stack([uvs[:, 0], 1.0 - uvs[:, 1]], axis=1)
    faces = np.asarray(g.faces)

    targets = _basecolor_image_indices(doc)
    if not targets:
        raise ProviderError("reduce_speckle: no baseColorTexture found")

    new_blob = bytearray(blob)
    report: dict = {"bleed_px": bleed_px, "images": [], "seconds": 0.0}
    for img_idx, pil, mime in iter_embedded_images(doc, blob):
        if img_idx not in targets:
            continue
        img = pil.convert("RGB")
        size = img.size[0]
        if img.size[0] != img.size[1]:
            raise ProviderError("reduce_speckle: non-square texture unsupported")
        mask = uv_coverage_mask(uvs, faces, size)
        arr = np.array(img)
        # seam-band metric: background texels within bleed distance, before fill
        filled_mask = _filled_mask(mask, bleed_px)
        band_px = filled_mask & ~mask
        before_lum = arr[band_px].mean() if band_px.any() else 0.0
        filled = dilate_fill(arr, mask, bleed_px)
        after_lum = filled[band_px].mean() if band_px.any() else 0.0
        near_black_before = int(((arr[band_px].max(axis=1) < 40)).sum()) if band_px.any() else 0
        near_black_after = int(((filled[band_px].max(axis=1) < 40)).sum()) if band_px.any() else 0
        buf = io.BytesIO()
        Image.fromarray(filled).save(buf, format="PNG")
        new_blob = repoint_image(doc, img_idx, buf.getvalue(), new_blob, "image/png")
        report["images"].append({
            "index": img_idx, "size": size,
            "seam_band_texels": int(band_px.sum()),
            "band_luminance_before": round(float(before_lum), 1),
            "band_luminance_after": round(float(after_lum), 1),
            "near_black_band_px_before": near_black_before,
            "near_black_band_px_after": near_black_after,
        })

    out_glb = out_dir / f"{glb.stem}.despeckle.glb"
    write_glb(doc, bytes(new_blob), out_glb)
    report["seconds"] = round(time.time() - t0, 1)
    report["output"] = out_glb.name
    (out_dir / f"{glb.stem}.despeckle.json").write_text(json.dumps(report, indent=2))
    return out_glb, report


def _filled_mask(mask: np.ndarray, iters: int) -> np.ndarray:
    """Boolean dilation of mask (background reachable within `iters` px)."""
    h, w = mask.shape
    valid = mask.copy()
    for _ in range(iters):
        pv = np.pad(valid.astype(np.float32), 1)
        cnt = np.zeros((h, w), dtype=np.float32)
        for dy in range(3):
            for dx in range(3):
                cnt += pv[dy:dy + h, dx:dx + w]
        new = (~valid) & (cnt > 0)
        if not new.any():
            break
        valid |= new
    return valid


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--bleed", type=int, default=8)
    a = ap.parse_args()
    out, rep = reduce_speckle(Path(a.input), Path(a.outdir), a.bleed)
    print("WROTE:", out)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
