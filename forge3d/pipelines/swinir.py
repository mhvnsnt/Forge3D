"""swinir.py — CPU texture super-resolution via SwinIR-S x4 (JingyunLiang/SwinIR, Apache-2.0).

Closes the TEXTURE RESOLUTION gap: 768x768 trellis textures -> 3072x3072.
Complements pipelines/upscale.py (Real-ESRGAN, ~21 min/GLB on CPU):
SwinIR-S (lightweight, ~1M params) is far faster on CPU and doubles as a
denoiser, which also helps the speckle problem.

Network: vendored forge3d/pipelines/_vendor/swinir_net.py (Apache-2.0,
https://github.com/JingyunLiang/SwinIR).
Weights: ~/.forge3d/weights/swinir/002_lightweightSR_DIV2K_s64w8_SwinIR-S_x4.pth
(16 MB, official v0.0 release).

Output: <stem>.swinir.glb + <stem>.swinir.json (per-texture metrics).
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from .glbutil import iter_embedded_images, parse_glb, repoint_image, write_glb
from ._vendor.swinir_net import SwinIR as SwinIRNet

WEIGHTS = Path.home() / ".forge3d" / "weights" / "swinir" / \
    "002_lightweightSR_DIV2K_s64w8_SwinIR-S_x4.pth"

# SwinIR-S x4 lightweight (DIV2K): embed_dim=60, pixelshuffledirect
MODEL_KWARGS = dict(
    upscale=4, in_chans=3, img_size=64, window_size=8,
    img_range=1.0, depths=[6, 6, 6, 6], embed_dim=60,
    num_heads=[6, 6, 6, 6], mlp_ratio=2.0,
    upsampler="pixelshuffledirect", resi_connection="1conv",
)

_model = None


def get_model() -> SwinIRNet:
    global _model
    if _model is None:
        if not WEIGHTS.exists():
            raise FileNotFoundError(
                f"SwinIR weights not found at {WEIGHTS}; download "
                "002_lightweightSR_DIV2K_s64w8_SwinIR-S_x4.pth from "
                "https://github.com/JingyunLiang/SwinIR/releases/tag/v0.0")
        _model = SwinIRNet(**MODEL_KWARGS)
        sd = torch.load(WEIGHTS, map_location="cpu", weights_only=True)
        if isinstance(sd, dict) and "params" in sd:
            sd = sd["params"]
        # strip common prefixes
        sd = {k.replace("module.", ""): v for k, v in sd.items()}
        _model.load_state_dict(sd, strict=True)
        _model.eval()
        for p in _model.parameters():
            p.requires_grad_(False)
    return _model


def _sr_tile(model: SwinIRNet, tile: np.ndarray) -> np.ndarray:
    """tile: HxWx3 float32 in [0,1] -> upscaled H*4 x W*4 float32."""
    with torch.no_grad():
        t = torch.from_numpy(tile).permute(2, 0, 1).unsqueeze(0).float()
        out = model(t).clamp(0, 1).squeeze(0).permute(1, 2, 0).numpy()
    return out


def super_resolve(img: Image.Image, scale: int = 4,
                  tile: int = 512, overlap: int = 32) -> Image.Image:
    """Tiled SwinIR x4 on CPU; returns upscaled PIL image."""
    model = get_model()
    arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    h, w, _ = arr.shape
    oh, ow = h * scale, w * scale
    out = np.zeros((oh, ow, 3), dtype=np.float32)
    weight = np.zeros((oh, ow, 1), dtype=np.float32)

    step = tile - overlap
    for y0 in range(0, h, step):
        for x0 in range(0, w, step):
            y1 = min(y0 + tile, h)
            x1 = min(x0 + tile, w)
            patch = arr[y0:y1, x0:x1]
            try:
                up = _sr_tile(model, patch)
            except RuntimeError:
                # OOM fallback: quarter the tile recursively
                up = _sr_tile(model, patch[: patch.shape[0] // 2,
                                           : patch.shape[1] // 2])
                up = np.repeat(np.repeat(up, 2, axis=0), 2, axis=1)
                up = up[: (y1 - y0) * scale, : (x1 - x0) * scale]
            oy0, ox0 = y0 * scale, x0 * scale
            ph, pw = up.shape[:2]
            # feathered blend on overlaps
            wy = np.ones((ph, 1), dtype=np.float32)
            wx = np.ones((1, pw), dtype=np.float32)
            f = min(overlap * scale // 2, ph // 4, pw // 4)
            if f > 0:
                ramp = np.linspace(0, 1, f, dtype=np.float32)
                if y0 > 0:
                    wy[:f, 0] = ramp
                if y1 < h:
                    wy[-f:, 0] = ramp[::-1]
                if x0 > 0:
                    wx[0, :f] = ramp
                if x1 < w:
                    wx[0, -f:] = ramp[::-1]
            m = (wy * wx)[..., None]
            out[oy0:oy0 + ph, ox0:ox0 + pw] += up * m
            weight[oy0:oy0 + ph, ox0:ox0 + pw] += m
    out /= np.maximum(weight, 1e-6)
    return Image.fromarray((out * 255.0 + 0.5).clip(0, 255).astype(np.uint8))


def run(glb_path: str | Path, out_dir: str | Path | None = None) -> dict:
    t0 = time.time()
    glb_path = Path(glb_path)
    out_dir = Path(out_dir) if out_dir else glb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    doc, blob = parse_glb(glb_path)
    blob = bytearray(blob)
    report = {"input": str(glb_path), "stage": "swinir-x4",
              "weights": WEIGHTS.name, "textures": []}
    n = 0
    for idx, pil, mime in iter_embedded_images(doc, bytes(blob)):
        t1 = time.time()
        up = super_resolve(pil)
        buf = io.BytesIO()
        up.save(buf, format="JPEG", quality=92)
        blob = repoint_image(doc, idx, buf.getvalue(), blob, "image/jpeg")
        report["textures"].append({
            "image_index": idx,
            "in": [pil.width, pil.height],
            "out": [up.width, up.height],
            "seconds": round(time.time() - t1, 1),
        })
        n += 1
    if n == 0:
        raise RuntimeError(f"no embedded images found in {glb_path}")

    stem = glb_path.stem
    out_glb = out_dir / f"{stem}.swinir.glb"
    write_glb(doc, bytes(blob), out_glb)
    report["output"] = str(out_glb)
    report["total_seconds"] = round(time.time() - t0, 1)
    rep_path = out_dir / f"{stem}.swinir.json"
    rep_path.write_text(json.dumps(report, indent=2))
    return report


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m forge3d.pipelines.swinir <in.glb> [outdir]")
        return 2
    rep = run(argv[1], argv[2] if len(argv) > 2 else None)
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
