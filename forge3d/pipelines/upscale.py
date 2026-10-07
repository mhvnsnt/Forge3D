"""upscale.py — real AI super-resolution texture stage (Real-ESRGAN 2x).

This is the deeper stage behind texture.py's honest lanczos backend:
true detail synthesis, not just resampling.

Backend "realesrgan" (default): RRDBNet x2 inference on CPU via torch,
using the vendored dependency-free arch (_vendor/realesrgan/rrdbnet_arch.py,
xinntao/BasicSR, Apache-2.0) and official RealESRGAN_x2 weights
(_vendor/realesrgan/models/RealESRGAN_x2.pth, BSD-2-Clause, downloaded from
the official v0.2.1 release). Tiled inference keeps CPU RAM bounded.
Honest scope: super-resolution synthesizes plausible detail; it cannot
invent texture content the provider never painted. Recorded as such in
run.json.

The realesrgan-ncnn-vulkan binary (~/workspace/api-wiring/bin/...) is
documented in PROVENANCE.md as the GPU path — it requires a Vulkan GPU,
which this box does not have.

Never returns the input silently claiming "upscaled": the output filename
records the backend used (e.g. .tex-esrgan2x.glb). Raises ProviderError
(loud, no silent fallback) if torch/weights are missing.
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import numpy as np

from ..providers.base import ProviderError
from .glbutil import iter_embedded_images, parse_glb, repoint_image, write_glb

VENDOR_DIR = (Path(__file__).resolve().parent.parent.parent
              / "_vendor" / "realesrgan")
WEIGHTS = VENDOR_DIR / "models" / "RealESRGAN_x2.pth"
ARCH = VENDOR_DIR / "rrdbnet_arch.py"

_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        import torch
    except ImportError:
        raise ProviderError(
            "upscale backend 'realesrgan' needs torch (CPU build is fine)")
    if not ARCH.exists() or not WEIGHTS.exists():
        raise ProviderError(
            f"upscale backend 'realesrgan' missing vendored files: "
            f"{ARCH} / {WEIGHTS}")
    sys.path.insert(0, str(VENDOR_DIR))
    from rrdbnet_arch import RRDBNet
    model = RRDBNet(num_in_ch=3, num_out_ch=3, scale=2,
                    num_feat=64, num_block=23, num_grow_ch=32)
    sd = torch.load(str(WEIGHTS), map_location="cpu", weights_only=True)
    model.load_state_dict(sd.get("params_ema", sd), strict=True)
    model.eval()
    _MODEL = (torch, model)
    return _MODEL


def esrgan2x(pil):
    """Upscale one PIL image 2x with Real-ESRGAN (tiled, CPU). Returns PIL."""
    from PIL import Image
    torch, model = _get_model()
    img = np.asarray(pil.convert("RGB")).astype(np.float32) / 255.0
    h, w, _ = img.shape
    tile, overlap, scale = 256, 16, 2
    out = np.zeros((h * scale, w * scale, 3), dtype=np.float32)
    weight = np.zeros((h * scale, w * scale, 1), dtype=np.float32)
    with torch.no_grad():
        for y0 in range(0, h, tile - overlap):
            for x0 in range(0, w, tile - overlap):
                y1 = min(y0 + tile, h)
                x1 = min(x0 + tile, w)
                patch = img[y0:y1, x0:x1]
                t = torch.from_numpy(
                    patch.transpose(2, 0, 1)[None, ...]).to(torch.float32)
                sr = model(t).clamp(0, 1)[0].numpy().transpose(1, 2, 0)
                oy0, ox0 = y0 * scale, x0 * scale
                oy1, ox1 = oy0 + sr.shape[0], ox0 + sr.shape[1]
                # feather edges to hide tile seams
                m = np.ones_like(sr[..., :1])
                fo = overlap * scale
                for ax, ln in ((0, sr.shape[0]), (1, sr.shape[1])):
                    ramp = np.minimum(np.arange(ln),
                                      np.arange(ln)[::-1] + 1) / fo
                    ramp = np.clip(ramp, 0, 1)
                    shp = [1, 1, 1]
                    shp[ax] = ln
                    m = m * ramp.reshape(shp)
                out[oy0:oy1, ox0:ox1] += sr * m
                weight[oy0:oy1, ox0:ox1] += m
    out = out / np.maximum(weight, 1e-6)
    return Image.fromarray((out * 255.0 + 0.5).clip(0, 255).astype(np.uint8))


def upscale_textures(glb: Path, out_dir: Path,
                     backend: str = "realesrgan") -> tuple[Path, dict]:
    """Upscale embedded textures 2x with real AI super-resolution.

    Returns (output_glb_path, report_dict) with before/after sizes, seconds.
    """
    if backend != "realesrgan":
        raise ProviderError(f"unknown upscale backend: {backend}")

    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc, blob = parse_glb(glb)

    report = {"backend": backend, "arch": "RRDBNet-x2 (vendored BasicSR)",
              "weights": WEIGHTS.name, "textures": [], "total_seconds": 0.0}
    refined = 0
    new_blob = bytearray(blob)
    for idx, pil, mime in iter_embedded_images(doc, blob):
        before = pil.size
        t0 = time.time()
        out_img = esrgan2x(pil)
        secs = time.time() - t0
        buf = io.BytesIO()
        out_img.save(buf, format="PNG")
        new_blob = repoint_image(doc, idx, buf.getvalue(), new_blob)
        refined += 1
        report["textures"].append(
            {"image_index": idx, "before": list(before),
             "after": list(out_img.size), "seconds": round(secs, 2),
             "upscaled_png_bytes": len(buf.getvalue())})
        report["total_seconds"] += secs
        print(f"upscale: image[{idx}] {before} -> {out_img.size} "
              f"({secs:.1f}s, {backend})", file=sys.stderr)

    if refined == 0:
        raise ProviderError(
            f"upscale stage: no embedded textures found in {glb.name}; "
            "nothing to upscale (refusing to fake it)")

    report["total_seconds"] = round(report["total_seconds"], 2)
    out = out_dir / f"{glb.stem}.tex-esrgan2x.glb"
    return write_glb(doc, bytes(new_blob), out), report


def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    out, report = upscale_textures(Path(a.input), Path(a.outdir))
    print(out)
    if a.report:
        Path(a.report).write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
