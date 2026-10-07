"""tangent_space.py — MikkTSpace tangent basis for the pipeline (quality100 wave 2).

Replaces the naive UV-derivative tangent frames with the industry-standard
MikkTSpace basis (the same basis Blender, Substance, Marmoset and Unreal
use), so normal maps baked by the pipeline shade correctly in every engine.

What it does:
  1. Loads a GLB (first Trimesh geometry), smooth vertex normals.
  2. Computes NAIVE tangents (UV-derivative dP/du solve, orthogonalized —
     the same approach as pipelines/normalmap.py) as the "before".
  3. Computes MikkTSpace tangents via the vendored C driver
     (forge3d/pipelines/_vendor/mikktspace/, zlib-style license) as "after".
  4. Measures: degenerate-tangent counts, mirrored-UV vertex fraction
     (where the naive re-orthogonalized bitangent has the WRONG handedness),
     and bakes a tangent-space normal map both ways to quantify the delta.
  5. Writes <stem>.mikkt.glb with per-vertex TANGENT attributes
     (VEC4: xyz + MikkTSpace handedness sign) for downstream stages.

Output: <stem>.mikkt.glb + <stem>.mikkt.json (metrics).
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

from ..providers.base import ProviderError
from .glbutil import parse_glb, write_glb

DRIVER = Path(__file__).parent / "_vendor" / "mikktspace" / "mikkt_driver"
SIZE = 1024  # normal-map bake resolution for the before/after comparison


def _load_first_mesh(glb: Path):
    scene = trimesh.load(str(glb), force="scene")
    geoms = list(scene.geometry.values())
    if not geoms:
        raise ProviderError(f"tangent_space: no geometry in {glb}")
    m = geoms[0]
    if m.visual is None or not hasattr(m.visual, "uv") or m.visual.uv is None:
        raise ProviderError(f"tangent_space: mesh has no UVs in {glb}")
    return (np.asarray(m.vertices, dtype=np.float64),
            np.asarray(m.faces, dtype=np.int64),
            np.asarray(m.visual.uv, dtype=np.float64))


def naive_tangents(verts, faces, uvs):
    """UV-derivative tangent solve (the 'before' — same as normalmap.py)."""
    n = len(verts)
    T = np.zeros((n, 3))
    B = np.zeros((n, 3))
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    uv0, uv1, uv2 = uvs[faces[:, 0]], uvs[faces[:, 1]], uvs[faces[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    d1, d2 = uv1 - uv0, uv2 - uv0
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    valid = np.abs(det) > 1e-12
    inv = np.zeros_like(det)
    inv[valid] = 1.0 / det[valid]
    t = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * inv[:, None]
    b = (-e1 * d2[:, 0:1] + e2 * d1[:, 0:1]) * inv[:, None]
    np.add.at(T, faces[:, 0], t); np.add.at(T, faces[:, 1], t); np.add.at(T, faces[:, 2], t)
    np.add.at(B, faces[:, 0], b); np.add.at(B, faces[:, 1], b); np.add.at(B, faces[:, 2], b)
    nrm = trimesh.Trimesh(vertices=verts, faces=faces, process=False).vertex_normals
    # orthogonalize against N (sibling's approach); handedness forced to +1
    T = T - nrm * np.einsum("ij,ij->i", T, nrm)[:, None]
    tl = np.linalg.norm(T, axis=1)
    deg = tl < 1e-12
    T[~deg] /= tl[~deg, None]
    B = np.cross(nrm, T)  # forced orientation — wrong on mirrored UVs
    w = np.ones(n)
    w[deg] = 0.0
    return T, B, nrm, w, deg


def _ensure_driver():
    if DRIVER.exists():
        return
    import shutil
    gcc = shutil.which("gcc") or shutil.which("cc")
    if gcc is None:
        raise ProviderError("tangent_space: no C compiler to build mikkt_driver")
    src = DRIVER.parent
    r = subprocess.run(
        [gcc, "-O2", "-o", str(DRIVER),
         str(src / "mikkt_driver.c"), str(src / "mikktspace.c"), "-lm"],
        capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or not DRIVER.exists():
        raise ProviderError(f"tangent_space: driver build failed: {r.stderr[:500]}")


def mikkt_tangents(verts, faces, uvs, tmp: Path):
    """MikkTSpace tangents via the vendored C driver (the 'after')."""
    _ensure_driver()
    nrm = trimesh.Trimesh(vertices=verts, faces=faces, process=False).vertex_normals
    nv, nf = len(verts), len(faces)
    inp = tmp / "mikkt_in.bin"
    outp = tmp / "mikkt_out.bin"
    with open(inp, "wb") as f:
        f.write(struct.pack("<ii", nv, nf))
        f.write(np.ascontiguousarray(verts, dtype=np.float32).tobytes())
        f.write(np.ascontiguousarray(nrm, dtype=np.float32).tobytes())
        f.write(np.ascontiguousarray(uvs, dtype=np.float32).tobytes())
        f.write(np.ascontiguousarray(faces, dtype=np.int32).tobytes())
    r = subprocess.run([str(DRIVER), str(inp), str(outp)],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise ProviderError(f"tangent_space: driver failed: {r.stderr.strip()}")
    tan = np.fromfile(str(outp), dtype=np.float32).reshape(nv, 4)
    T, w = tan[:, :3], tan[:, 3]
    # MikkTSpace bitangent = w * cross(N, T)
    B = w[:, None] * np.cross(nrm, T)
    deg = ~np.isfinite(T).all(axis=1) | (np.linalg.norm(T, axis=1) < 1e-12)
    return T, B, nrm, w, deg


def mirrored_uv_fraction(faces, uvs) -> float:
    """Fraction of vertices touching a UV-mirrored (negative-determinant) face."""
    uv0, uv1, uv2 = uvs[faces[:, 0]], uvs[faces[:, 1]], uvs[faces[:, 2]]
    d1, d2 = uv1 - uv0, uv2 - uv0
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    mirrored = det < -1e-12
    touch = np.zeros(uvs.shape[0], dtype=bool)
    for k in range(3):
        touch[faces[mirrored, k]] = True
    return float(touch.mean())


def _bake_with_frames(verts, faces, uvs, T, B, N, size=SIZE):
    """Rasterize flat face normals into the given tangent frames (float32 RGB)."""
    out = np.full((size, size, 3), [0.5, 0.5, 1.0], dtype=np.float32)
    tm = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    face_nrm = tm.face_normals
    uv_px = uvs * size
    fuv = uv_px[faces]
    chunk = 8192
    for s in range(0, len(faces), chunk):
        e = min(s + chunk, len(faces))
        tri = fuv[s:e]
        x0, y0 = tri[:, 0, 0], tri[:, 0, 1]
        x1, y1 = tri[:, 1, 0], tri[:, 1, 1]
        x2, y2 = tri[:, 2, 0], tri[:, 2, 1]
        xmin = np.clip(np.floor(tri[:, :, 0].min(1)).astype(int), 0, size - 1)
        xmax = np.clip(np.ceil(tri[:, :, 0].max(1)).astype(int), 0, size - 1)
        ymin = np.clip(np.floor(tri[:, :, 1].min(1)).astype(int), 0, size - 1)
        ymax = np.clip(np.ceil(tri[:, :, 1].max(1)).astype(int), 0, size - 1)
        ok = (xmax > xmin) & (ymax > ymin)
        for j in np.nonzero(ok)[0]:
            xs = np.arange(xmin[j], xmax[j] + 1)
            ys = np.arange(ymin[j], ymax[j] + 1)
            xx, yy = np.meshgrid(xs, ys)
            xs = xx.ravel() + 0.5
            ys = yy.ravel() + 0.5
            ax, ay = x0[j], y0[j]
            d = (y1[j] - y2[j]) * (ax - x2[j]) + (x2[j] - x1[j]) * (ay - y2[j])
            if abs(d) < 1e-12:
                continue
            w0 = ((y1[j] - y2[j]) * (xs - x2[j]) + (x2[j] - x1[j]) * (ys - y2[j])) / d
            w1 = ((y2[j] - ay) * (xs - x2[j]) + (ax - x2[j]) * (ys - y2[j])) / d
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not np.any(inside):
                continue
            fi = faces[s + j]
            W = np.stack([w0[inside], w1[inside], w2[inside]], 1)
            Tp = W @ T[fi]
            Bp = W @ B[fi]
            Nv = W @ N[fi]
            fn = face_nrm[s + j]
            n_t = np.stack([fn @ Tp.T, fn @ Bp.T, fn @ Nv.T], 1)
            nl = np.linalg.norm(n_t, axis=1, keepdims=True)
            n_t = n_t / np.maximum(nl, 1e-12)
            out[ys[inside].astype(int), xs[inside].astype(int)] = n_t * 0.5 + 0.5
    return out


def _attach_tangents(doc: dict, blob: bytes, tangents: np.ndarray):
    """Append per-vertex TANGENT (VEC4) accessors matching each primitive's
    vertex count. Returns (doc, blob)."""
    data = np.ascontiguousarray(tangents, dtype=np.float32).tobytes()
    # pad blob to 4-byte alignment
    pad = (-len(blob)) % 4
    blob = blob + b"\x00" * pad
    offset = len(blob)
    blob = blob + data
    bv_idx = len(doc.get("bufferViews", []))
    doc.setdefault("bufferViews", []).append({
        "buffer": 0, "byteOffset": offset,
        "byteLength": len(data), "byteStride": 16,
    })
    acc_idx = len(doc.get("accessors", []))
    doc.setdefault("accessors", []).append({
        "bufferView": bv_idx, "componentType": 5126, "type": "VEC4",
        "count": int(tangents.shape[0]),
    })
    return doc, blob, acc_idx


def process(glb: Path, out_dir: Path, tmp: Path | None = None) -> dict:
    t0 = time.time()
    glb, out_dir = Path(glb), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tmp) if tmp else out_dir / "_mikkt_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    verts, faces, uvs = _load_first_mesh(glb)

    Tn, Bn, Nn, wn, degn = naive_tangents(verts, faces, uvs)
    t1 = time.time()
    Tm, Bm, Nm, wm, degm = mikkt_tangents(verts, faces, uvs, tmp)
    t2 = time.time()

    mirror_frac = mirrored_uv_fraction(faces, uvs)

    # bake both ways, compare angular delta per texel
    bake_n = _bake_with_frames(verts, faces, uvs, Tn, Bn, Nn)
    bake_m = _bake_with_frames(verts, faces, uvs, Tm, Bm, Nm)
    vn = bake_n * 2.0 - 1.0
    vm = bake_m * 2.0 - 1.0
    cosang = np.clip((vn * vm).sum(-1), -1.0, 1.0)
    ang = np.degrees(np.arccos(cosang))
    # only count texels the bake actually touched (non-flat)
    touched = (np.abs(vn[..., :2]).max(-1) > 1 / 255) | (np.abs(vn[..., 2] - 1.0) > 1 / 255)
    ang_t = ang[touched]

    metrics = {
        "input": str(glb),
        "verts": int(len(verts)), "faces": int(len(faces)),
        "naive_degenerate_tangents": int(degn.sum()),
        "mikkt_degenerate_tangents": int(degm.sum()),
        "mirrored_uv_vertex_fraction": round(mirror_frac, 4),
        "mikkt_negative_handedness_fraction": round(float((wm < 0).mean()), 4),
        "bake_texels_touched": int(touched.sum()),
        "bake_mean_angular_delta_deg": round(float(ang_t.mean()), 3),
        "bake_p99_angular_delta_deg": round(float(np.percentile(ang_t, 99)), 3),
        "bake_texels_gt5deg_fraction": round(float((ang_t > 5).mean()), 4),
        "naive_seconds": round(t1 - t0, 1),
        "mikkt_seconds": round(t2 - t1, 1),
    }

    # attach MikkTSpace tangents to a GLB copy (TANGENT = xyz + handedness w)
    doc, blob = parse_glb(glb)
    counted = 0
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            pos_acc = prim["attributes"]["POSITION"]
            n = doc["accessors"][pos_acc]["count"]
            if n != len(verts):
                continue  # only the geometry we measured
            tv = np.concatenate([Tm, wm[:, None]], axis=1)
            doc, blob, acc_idx = _attach_tangents(doc, blob, tv)
            prim["attributes"]["TANGENT"] = acc_idx
            counted += 1
    if counted == 0:
        raise ProviderError("tangent_space: no primitive matched measured geometry")
    out_glb = out_dir / (glb.stem + ".mikkt.glb")
    write_glb(doc, blob, out_glb)
    metrics["output"] = str(out_glb)
    metrics["primitives_tangentized"] = counted
    metrics["seconds"] = round(time.time() - t0, 1)

    out_json = out_dir / (glb.stem + ".mikkt.json")
    out_json.write_text(json.dumps(metrics, indent=2))
    return metrics


def main():
    if len(sys.argv) != 3:
        print("usage: tangent_space.py <in.glb> <out_dir>", file=sys.stderr)
        sys.exit(2)
    m = process(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
