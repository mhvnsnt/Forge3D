"""xatlas_uv.py — production-grade automatic UV unwrapping via xatlas (MIT).

Closes the TEXTURE RESOLUTION / UV-quality gap: trellis raw UVs are
fragmented (many tiny islands -> mip bleed + wasted texel density).
xatlas (https://github.com/jpcy/xatlas, MIT; python wheel: xatlas) packs
larger, lower-distortion charts, which directly raises effective texture
resolution and reduces seam speckle.

Because re-unwrapping invalidates the old texture's UV mapping, this stage
also REBAKES the old texture onto the new UV layout (exact face
correspondence via xatlas's vmapping — no Blender needed).

Distinct from pipelines/retexture.py (Blender Smart-UV + Cycles rebake,
experimental): this is deterministic, CPU, no Blender needed.

Output: <stem>.xatlas.glb + <stem>.xatlas.json
(seam-edge counts before/after, island counts, timings).
"""
from __future__ import annotations

import collections
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import trimesh
import xatlas
from PIL import Image

from .glbutil import (iter_embedded_images, parse_glb, repoint_image,
                      write_glb)

_COMP = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
_TYPE_N = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def _read_accessor(doc, blob: bytes, idx: int) -> np.ndarray:
    acc = doc["accessors"][idx]
    bv = doc["bufferViews"][acc["bufferView"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    n = _TYPE_N[acc["type"]]
    dtype = np.dtype(_COMP[acc["componentType"]])
    count = acc["count"]
    arr = np.frombuffer(blob, dtype=dtype, count=count * n, offset=start)
    return np.array(arr.reshape(count, n) if n > 1 else arr)


def _append_accessor(doc, blob: bytearray, arr: np.ndarray) -> int:
    raw = np.ascontiguousarray(arr)
    comp = {np.dtype("float32"): 5126, np.dtype("uint32"): 5125,
            np.dtype("uint16"): 5123}[raw.dtype]
    typ = {1: "SCALAR", 2: "VEC2", 3: "VEC3", 4: "VEC4"}[
        raw.shape[1] if raw.ndim > 1 else 1]
    pad = (-len(blob)) % 4
    blob.extend(b"\x00" * pad)
    off = len(blob)
    blob.extend(raw.tobytes())
    doc["bufferViews"].append(
        {"buffer": 0, "byteOffset": off, "byteLength": len(raw.tobytes())})
    bv_idx = len(doc["bufferViews"]) - 1
    n = _TYPE_N[typ]
    accessor = {"bufferView": bv_idx, "byteOffset": 0,
                "componentType": comp, "count": raw.shape[0], "type": typ}
    if comp == 5126:
        flat = raw.reshape(-1, n)
        accessor["min"] = [float(v) for v in flat.min(axis=0)]
        accessor["max"] = [float(v) for v in flat.max(axis=0)]
    doc["accessors"].append(accessor)
    return len(doc["accessors"]) - 1


def seam_edges(uvs: np.ndarray, faces: np.ndarray) -> int:
    """Count UV edges used by exactly one triangle (island boundaries)."""
    ec = collections.Counter()
    for f in faces:
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            ua = tuple(np.round(uvs[a], 4))
            ub = tuple(np.round(uvs[b], 4))
            ec[tuple(sorted((ua, ub)))] += 1
    return sum(1 for c in ec.values() if c == 1)


def transfer_texture(old_uv: np.ndarray, old_tex: Image.Image,
                     new_uv: np.ndarray, new_faces: np.ndarray,
                     vmapping: np.ndarray, size: int = 1024) -> Image.Image:
    """Rebake the old texture onto the new UV layout (exact correspondence).

    new vertex i sits on old vertex vmapping[i]; new face (a,b,c) is the same
    3D triangle as old face (vmapping[a],vmapping[b],vmapping[c]). For each
    texel covered by a new-UV triangle, interpolate the old UV with identical
    barycentric coordinates and bilinear-sample the old texture.
    """
    old_arr = np.asarray(old_tex.convert("RGB"), dtype=np.float32)
    oh, ow = old_arr.shape[:2]
    new_arr = np.zeros((size, size, 3), dtype=np.float32)
    filled = np.zeros((size, size), dtype=bool)

    for nf in new_faces:
        tuv = new_uv[nf]
        of = vmapping[nf]
        ouv = old_uv[of]
        xs = (tuv[:, 0] * size).astype(int)
        ys = (tuv[:, 1] * size).astype(int)
        x0, x1 = max(xs.min(), 0), min(xs.max(), size - 1)
        y0, y1 = max(ys.min(), 0), min(ys.max(), size - 1)
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        px = (gx + 0.5) / size
        py = (gy + 0.5) / size
        ax, ay = tuv[0]
        bx, by = tuv[1]
        cx, cy = tuv[2]
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12:
            continue
        l0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d
        l1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d
        l2 = 1.0 - l0 - l1
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not inside.any():
            continue
        ou = l0 * ouv[0, 0] + l1 * ouv[1, 0] + l2 * ouv[2, 0]
        ov = l0 * ouv[0, 1] + l1 * ouv[1, 1] + l2 * ouv[2, 1]
        fx = np.clip(ou * ow - 0.5, 0, ow - 1.001)
        fy = np.clip(ov * oh - 0.5, 0, oh - 1.001)
        xA = fx.astype(int)
        yA = fy.astype(int)
        xB = np.minimum(xA + 1, ow - 1)
        yB = np.minimum(yA + 1, oh - 1)
        wx = (fx - xA)[..., None]
        wy = (fy - yA)[..., None]
        samp = (old_arr[yA, xA] * (1 - wx) * (1 - wy) +
                old_arr[yA, xB] * wx * (1 - wy) +
                old_arr[yB, xA] * (1 - wx) * wy +
                old_arr[yB, xB] * wx * wy)
        region = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        upd = inside & ~filled[region]
        new_arr[region][upd] = samp[upd]
        filled[region] |= inside
    return Image.fromarray(np.clip(new_arr, 0, 255).astype(np.uint8))


def run(glb_path: str | Path, out_dir: str | Path | None = None,
        tex_size: int = 1024) -> dict:
    t0 = time.time()
    glb_path = Path(glb_path)
    out_dir = Path(out_dir) if out_dir else glb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    doc, blob = parse_glb(glb_path)
    blob = bytearray(blob)

    prim = doc["meshes"][0]["primitives"][0]
    pos_idx = prim["attributes"]["POSITION"]
    uv_idx = prim["attributes"].get("TEXCOORD_0")
    idx_idx = prim.get("indices")
    if idx_idx is None:
        raise RuntimeError("primitive has no indices; xatlas stage needs indexed geometry")
    if uv_idx is None:
        raise RuntimeError("primitive has no TEXCOORD_0; nothing to rebake from")

    verts = _read_accessor(doc, bytes(blob), pos_idx).astype(np.float32)
    faces = _read_accessor(doc, bytes(blob), idx_idx).astype(np.int64).reshape(-1, 3)
    old_uv = _read_accessor(doc, bytes(blob), uv_idx).astype(np.float32)
    old_seams = seam_edges(old_uv, faces)

    # source albedo (first embedded image)
    old_tex = None
    old_img_idx = None
    for i, pil, _m in iter_embedded_images(doc, bytes(blob)):
        old_tex, old_img_idx = pil, i
        break
    if old_tex is None:
        raise RuntimeError("no embedded texture to rebake")

    t1 = time.time()
    vmapping, new_faces, new_uv = xatlas.parametrize(verts, faces)
    xtime = time.time() - t1
    new_verts = verts[vmapping].astype(np.float32)
    new_faces32 = new_faces.astype(np.uint32)

    tm = trimesh.Trimesh(new_verts, new_faces32, process=False)
    new_normals = np.array(tm.vertex_normals, dtype=np.float32)
    new_uv = np.ascontiguousarray(new_uv.astype(np.float32))

    t2 = time.time()
    rebaked = transfer_texture(old_uv, old_tex, new_uv, new_faces, vmapping,
                               size=tex_size)
    baketime = time.time() - t2

    pos_new = _append_accessor(doc, blob, new_verts)
    nrm_new = _append_accessor(doc, blob, new_normals)
    uv_new = _append_accessor(doc, blob, new_uv)
    idx_new = _append_accessor(doc, blob, new_faces32.reshape(-1))  # SCALAR indices
    prim["attributes"]["POSITION"] = pos_new
    prim["attributes"]["NORMAL"] = nrm_new
    prim["attributes"]["TEXCOORD_0"] = uv_new
    prim["indices"] = idx_new

    # replace the albedo with the rebaked texture
    buf = io.BytesIO()
    rebaked.save(buf, format="JPEG", quality=92)
    blob = repoint_image(doc, old_img_idx, buf.getvalue(), blob, "image/jpeg")

    new_seams = seam_edges(new_uv, new_faces)

    stem = glb_path.stem
    out_glb = out_dir / f"{stem}.xatlas.glb"
    write_glb(doc, bytes(blob), out_glb)
    report = {
        "input": str(glb_path), "stage": "xatlas-uv",
        "verts_in": int(len(verts)), "verts_out": int(len(new_verts)),
        "faces": int(len(new_faces)),
        "seam_edges_before": int(old_seams),
        "seam_edges_after": int(new_seams),
        "texture_rebaked": [tex_size, tex_size],
        "xatlas_seconds": round(xtime, 1),
        "rebake_seconds": round(baketime, 1),
        "total_seconds": round(time.time() - t0, 1),
        "output": str(out_glb),
    }
    (out_dir / f"{stem}.xatlas.json").write_text(json.dumps(report, indent=2))
    return report


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m forge3d.pipelines.xatlas_uv <in.glb> [outdir]")
        return 2
    print(json.dumps(run(argv[1], argv[2] if len(argv) > 2 else None), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
