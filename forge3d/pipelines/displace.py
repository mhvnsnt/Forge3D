"""displace.py — bump-to-geometry: convert texture detail into real mesh relief.

Closes the NATIVE DETAIL gap geometrically: samples the albedo's
high-frequency luminance at each vertex UV and displaces along the vertex
normal, turning painted detail (fabric weave, muscle striation, hair
strands) into actual surface relief. Displacement field is Laplacian-
smoothed to avoid spikes; amplitude is conservative (fraction of the
bounding-box diagonal).

Same topology, only POSITION changes (normals recomputed). Pure
numpy/trimesh — no Blender needed.

Output: <stem>.displace.glb + <stem>.displace.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageFilter

from .glbutil import parse_glb, write_glb
from .xatlas_uv import _append_accessor, _read_accessor


def _smooth_field(faces: np.ndarray, field: np.ndarray, iters: int = 3) -> np.ndarray:
    """Laplacian smoothing of a per-vertex scalar field (vectorized)."""
    n = len(field)
    # build adjacency via face edges
    rows = np.concatenate([faces[:, 0], faces[:, 1], faces[:, 2],
                           faces[:, 1], faces[:, 2], faces[:, 0]])
    cols = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 0],
                           faces[:, 0], faces[:, 1], faces[:, 2]])
    deg = np.bincount(rows, minlength=n).astype(np.float32)
    for _ in range(iters):
        agg = np.bincount(rows, weights=field[cols], minlength=n)
        field = np.where(deg > 0, agg / np.maximum(deg, 1), field)
    return field


def run(glb_path: str | Path, out_dir: str | Path | None = None,
        amplitude: float = 0.004, smooth_iters: int = 3) -> dict:
    t0 = time.time()
    glb_path = Path(glb_path)
    out_dir = Path(out_dir) if out_dir else glb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    doc, blob = parse_glb(glb_path)
    blob = bytearray(blob)
    prim = doc["meshes"][0]["primitives"][0]
    verts = _read_accessor(doc, bytes(blob),
                           prim["attributes"]["POSITION"]).astype(np.float64)
    faces = _read_accessor(doc, bytes(blob), prim["indices"]).astype(np.int64)
    faces = faces.reshape(-1, 3)
    uv_idx = prim["attributes"].get("TEXCOORD_0")
    if uv_idx is None:
        raise RuntimeError("displace needs TEXCOORD_0")

    # albedo luminance
    from .glbutil import iter_embedded_images
    albedo = None
    for _i, pil, _m in iter_embedded_images(doc, bytes(blob)):
        albedo = pil
        break
    if albedo is None:
        raise RuntimeError("no embedded albedo texture")

    lum = np.asarray(albedo.convert("L"), dtype=np.float32)
    # high-frequency only: subtract blurred version
    blur = np.asarray(albedo.convert("L").filter(
        ImageFilter.GaussianBlur(3)), dtype=np.float32)
    hf = lum - blur

    uvs = _read_accessor(doc, bytes(blob), uv_idx).astype(np.float64)
    h, w = hf.shape
    px = np.clip((uvs[:, 0] * w).astype(int), 0, w - 1)
    py = np.clip((uvs[:, 1] * h).astype(int), 0, h - 1)
    per_vert = hf[py, px]

    per_vert = _smooth_field(faces, per_vert, smooth_iters)

    tm = trimesh.Trimesh(verts, faces, process=False)
    normals = np.array(tm.vertex_normals)

    diag = float(np.linalg.norm(verts.max(axis=0) - verts.min(axis=0)))
    amp = amplitude * diag
    # normalize hf to [-1, 1]-ish by its robust range
    scale = float(np.percentile(np.abs(per_vert), 99)) or 1.0
    disp = np.clip(per_vert / scale, -1.0, 1.0) * amp
    new_verts = (verts + normals * disp[:, None]).astype(np.float32)
    new_normals = np.array(
        trimesh.Trimesh(new_verts, faces, process=False).vertex_normals,
        dtype=np.float32)

    pos_new = _append_accessor(doc, blob, new_verts, 5126, "VEC3")
    prim["attributes"]["POSITION"] = pos_new
    if "NORMAL" in prim["attributes"]:
        nrm_new = _append_accessor(doc, blob, new_normals, 5126, "VEC3")
        prim["attributes"]["NORMAL"] = nrm_new

    stem = glb_path.stem
    out_glb = out_dir / f"{stem}.displace.glb"
    write_glb(doc, bytes(blob), out_glb)
    report = {"input": str(glb_path), "stage": "displace",
              "amplitude_frac": amplitude, "amplitude_world": round(amp, 5),
              "smooth_iters": smooth_iters,
              "mean_abs_disp": round(float(np.abs(disp).mean()), 5),
              "max_abs_disp": round(float(np.abs(disp).max()), 5),
              "total_seconds": round(time.time() - t0, 1),
              "output": str(out_glb)}
    (out_dir / f"{stem}.displace.json").write_text(json.dumps(report, indent=2))
    return report


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m forge3d.pipelines.displace <in.glb> [outdir]")
        return 2
    print(json.dumps(run(argv[1], argv[2] if len(argv) > 2 else None),
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
