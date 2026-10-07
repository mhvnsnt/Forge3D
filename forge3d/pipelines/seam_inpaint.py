"""seam_inpaint.py — LaMa content-aware texture completion (quality100 wave 2).

Closes the TEXTURE RESOLUTION gap from the repair side: when bakes leave
genuine holes (missing UV coverage, black bake regions, damaged islands),
dilation (speckle.py) can only smear nearby texels. LaMa synthesizes
plausible content inside masked regions with Fourier convolutions that see
the whole texture at once.

Vendored lean inference from advimman/lama (Apache-2.0; LICENSE in
_vendor/lama/). Weights: big-lama (downloaded once to
~/.forge3d/weights/lama/, gitignored — never in the repo).

Usage: inpaint(image_png, mask_png, out_png) where mask white = fill.
Proof mode: --holes benchmark punches synthetic blob holes into a real
texture, inpaints, and reports PSNR on the held-out pixels.

Output: <stem>.inpainted.png + <stem>.seam_inpaint.json.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

VENDOR = Path(__file__).parent / "_vendor" / "lama"
WEIGHTS = Path.home() / ".forge3d" / "weights" / "lama" / "big-lama" / "models" / "best.ckpt"

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    if not WEIGHTS.exists():
        from ..providers.base import ProviderError
        raise ProviderError(
            f"seam_inpaint: missing weights {WEIGHTS} "
            "(download https://huggingface.co/smartywu/big-lama/resolve/main/big-lama.zip)")
    sys.path.insert(0, str(VENDOR))
    import torch
    from saicinpainting.training.modules.ffc import FFCResNetGenerator

    gen = FFCResNetGenerator(
        input_nc=4, output_nc=3, ngf=64, n_downsampling=3, n_blocks=18,
        add_out_act="sigmoid",
        init_conv_kwargs={"ratio_gin": 0, "ratio_gout": 0, "enable_lfu": False},
        downsample_conv_kwargs={"ratio_gin": 0, "ratio_gout": 0, "enable_lfu": False},
        resnet_conv_kwargs={"ratio_gin": 0.75, "ratio_gout": 0.75, "enable_lfu": False},
    )
    ckpt = torch.load(str(WEIGHTS), map_location="cpu", weights_only=False)
    sd = None
    if isinstance(ckpt, dict):
        if "state_dict" in ckpt and isinstance(ckpt["state_dict"], dict):
            raw = ckpt["state_dict"]
            gen_keys = {k[len("generator."):]: v for k, v in raw.items()
                        if k.startswith("generator.")}
            sd = gen_keys or raw
        elif "generator" in ckpt:
            g = ckpt["generator"]
            sd = g.state_dict() if hasattr(g, "state_dict") else g
    if sd is None:
        raise RuntimeError("seam_inpaint: unrecognized checkpoint layout")
    missing, unexpected = gen.load_state_dict(sd, strict=False), None
    gen.eval()
    _model = gen
    return gen


def _pad8(a: np.ndarray):
    h, w = a.shape[:2]
    ph, pw = (-h) % 8, (-w) % 8
    if ph == 0 and pw == 0:
        return a, (h, w)
    pad = ((0, ph), (0, pw)) + ((0, 0),) * (a.ndim - 2)
    return np.pad(a, pad, mode="reflect"), (h, w)


def inpaint(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """image: HxWx3 float32 [0,1]; mask: HxW float32 {0,1}, 1 = fill."""
    import torch
    model = _load_model()
    img = np.ascontiguousarray(image, dtype=np.float32)
    msk = np.ascontiguousarray((mask > 0.5).astype(np.float32))
    masked = img * (1.0 - msk[..., None])
    inp = np.concatenate([masked, msk[..., None]], axis=2)  # HxWx4
    inp, (h, w) = _pad8(inp)
    t = torch.from_numpy(inp.transpose(2, 0, 1)).unsqueeze(0)
    with torch.no_grad():
        out = model(t).squeeze(0).numpy().transpose(1, 2, 0)
    out = out[:h, :w]
    result = out * msk[..., None] + img * (1.0 - msk[..., None])
    return np.clip(result, 0, 1)


def _blob_holes(rng, h, w, n=12, rmin=12, rmax=48):
    mask = np.zeros((h, w), dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(n):
        cx, cy = rng.integers(0, w), rng.integers(0, h)
        r = rng.integers(rmin, rmax)
        mask[((xx - cx) ** 2 + (yy - cy) ** 2) < r * r] = 1.0
    return mask


def benchmark(texture_png: Path, out_dir: Path, size: int = 512,
              n_holes: int = 12, seed: int = 7) -> dict:
    """Synthetic-hole proof: punch blobs, inpaint, PSNR vs original."""
    t0 = time.time()
    img = np.asarray(Image.open(texture_png).convert("RGB").resize((size, size)),
                     dtype=np.float32) / 255.0
    rng = np.random.default_rng(seed)
    mask = _blob_holes(rng, size, size, n=n_holes)
    holed = img.copy()
    holed[mask > 0.5] = 0.0
    restored = inpaint(img * (1 - mask[..., None]), mask)
    hole = mask > 0.5
    mse = float(np.mean((restored[hole] - img[hole]) ** 2))
    psnr = 10 * math.log10(1.0 / max(mse, 1e-12))
    base_mse = float(np.mean((holed[hole] - img[hole]) ** 2))
    base_psnr = 10 * math.log10(1.0 / max(base_mse, 1e-12))
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(texture_png).stem
    Image.fromarray((holed * 255).astype(np.uint8)).save(out_dir / f"{stem}.holes.png")
    Image.fromarray((restored * 255).astype(np.uint8)).save(out_dir / f"{stem}.inpainted.png")
    Image.fromarray((mask * 255).astype(np.uint8)).save(out_dir / f"{stem}.holes.mask.png")
    metrics = {
        "input": str(texture_png), "size": size, "n_holes": n_holes,
        "hole_pixel_fraction": round(float(hole.mean()), 4),
        "hole_psnr_before_db": round(base_psnr, 2),
        "hole_psnr_after_db": round(psnr, 2),
        "psnr_gain_db": round(psnr - base_psnr, 2),
        "seconds": round(time.time() - t0, 1),
    }
    (out_dir / f"{stem}.seam_inpaint.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def run(image_png: str | Path, mask_png: str | Path,
        out_png: str | Path | None = None) -> Path:
    img = np.asarray(Image.open(image_png).convert("RGB"), dtype=np.float32) / 255.0
    mask = np.asarray(Image.open(mask_png).convert("L"), dtype=np.float32) / 255.0
    if mask.shape[:2] != img.shape[:2]:
        mask = np.asarray(Image.open(mask_png).convert("L").resize(
            (img.shape[1], img.shape[0])), dtype=np.float32) / 255.0
    out = inpaint(img, mask)
    out_png = Path(out_png) if out_png else Path(image_png).parent / (
        Path(image_png).stem + ".inpainted.png")
    Image.fromarray((out * 255).astype(np.uint8)).save(out_png)
    return out_png


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--holes":
        print(json.dumps(benchmark(sys.argv[2], Path(sys.argv[3])), indent=2))
    elif len(sys.argv) in (3, 4):
        out = run(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else None)
        print(str(out))
    else:
        print("usage: seam_inpaint.py <image> <mask> [out] | "
              "seam_inpaint.py --holes <texture> <out_dir>", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
