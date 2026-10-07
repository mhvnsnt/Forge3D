"""normalmap.py — generate a tangent-space normal map from mesh geometry.

Bakes per-texel geometric normals into tangent space (derived from the
mesh's own UV layout) and attaches the result as the material's
normalTexture on a copy of the input GLB.

Method (trimesh + numpy, CPU):
  1. Load mesh (first Trimesh geometry), smooth vertex normals.
  2. Per-vertex tangent frame from UV derivatives (standard
     dP/du,dP/dv solve), orthogonalized against the normal.
  3. Rasterize every triangle into UV space (default 1024): barycentric
     interpolation of the T/B/N frames; the FLAT geometric face normal is
     transformed into tangent space per texel (n_t = (n·T, n·B, n·N)).
     This captures the faceting that smooth shading hides — genuine
     high-frequency surface detail already in the mesh.
  4. Encode to PNG, append as a new GLB image + texture, wire
     materials[*].normalTexture.

Honest scope: this captures the geometric high-frequency detail already
in the mesh (creases, faceting hidden by smooth shading) — it cannot
invent surface detail that isn't there. Untouched UV islands keep the
flat (128,128,255) normal.

Output: <stem>.normalmap.glb
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

from ..providers.base import ProviderError
from .glbutil import append_images, parse_glb, write_glb


def _tangent_frames(verts: np.ndarray, faces: np.ndarray,
                    uvs: np.ndarray):
    """Per-vertex (T, B, N) frames. N = smooth vertex normals."""
    n_verts = len(verts)
    T = np.zeros((n_verts, 3))
    B = np.zeros((n_verts, 3))
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    uv0, uv1, uv2 = uvs[faces[:, 0]], uvs[faces[:, 1]], uvs[faces[:, 2]]
    e1 = v1 - v0
    e2 = v2 - v0
    d1 = uv1 - uv0
    d2 = uv2 - uv0
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    valid = np.abs(det) > 1e-12
    inv = np.zeros_like(det)
    inv[valid] = 1.0 / det[valid]
    t = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * inv[:, None]
    b = (-e1 * d2[:, 0:1] + e2 * d1[:, 0:1]) * inv[:, None]
    np.add.at(T, faces[:, 0], t)
    np.add.at(T, faces[:, 1], t)
    np.add.at(T, faces[:, 2], t)
    np.add.at(B, faces[:, 0], b)
    np.add.at(B, faces[:, 1], b)
    np.add.at(B, faces[:, 2], b)
    return T, B


def _bake(verts, faces, uvs, size: int = 1024) -> np.ndarray:
    tm = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    nrm = tm.vertex_normals          # smooth (for the tangent frame)
    face_nrm = tm.face_normals       # flat geometric (what we bake)
    T, B = _tangent_frames(verts, faces, uvs)
    # orthogonalize T against N
    T = T - nrm * (np.einsum("ij,ij->i", T, nrm))[:, None]
    tl = np.linalg.norm(T, axis=1)
    fallback = tl < 1e-12
    T[~fallback] /= tl[~fallback, None]
    # re-orthogonalized bitangent keeps handedness
    B = np.cross(nrm, T)

    out = np.full((size, size, 3), [0.5, 0.5, 1.0], dtype=np.float32)
    uv_px = uvs * size
    fuv = uv_px[faces]
    # process faces in chunks to bound memory
    chunk = 8192
    yy, xx = np.mgrid[0:size, 0:size]
    for s in range(0, len(faces), chunk):
        e = min(s + chunk, len(faces))
        tri = fuv[s:e]
        x0, y0 = tri[:, 0, 0], tri[:, 0, 1]
        x1, y1 = tri[:, 1, 0], tri[:, 1, 1]
        x2, y2 = tri[:, 2, 0], tri[:, 2, 1]
        xmin = np.clip(np.floor(np.min(tri[:, :, 0], 1)).astype(int), 0, size - 1)
        xmax = np.clip(np.ceil(np.max(tri[:, :, 0], 1)).astype(int), 0, size - 1)
        ymin = np.clip(np.floor(np.min(tri[:, :, 1], 1)).astype(int), 0, size - 1)
        ymax = np.clip(np.ceil(np.max(tri[:, :, 1], 1)).astype(int), 0, size - 1)
        ok_box = (xmax > xmin) & (ymax > ymin)
        idx = np.nonzero(ok_box)[0]
        for j in idx:
            xs = xx[ymin[j]:ymax[j] + 1, xmin[j]:xmax[j] + 1].ravel() + 0.5
            ys = yy[ymin[j]:ymax[j] + 1, xmin[j]:xmax[j] + 1].ravel() + 0.5
            ax, ay = x0[j], y0[j]
            d = ((y1[j] - y2[j]) * (ax - x2[j]) +
                 (x2[j] - x1[j]) * (ay - y2[j]))
            if abs(d) < 1e-12:
                continue
            w0 = ((y1[j] - y2[j]) * (xs - x2[j]) +
                  (x2[j] - x1[j]) * (ys - y2[j])) / d
            w1 = ((y2[j] - ay) * (xs - x2[j]) +
                  (ax - x2[j]) * (ys - y2[j])) / d
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not np.any(inside):
                continue
            fi = faces[s + j]
            W = np.stack([w0[inside], w1[inside], w2[inside]], 1)
            Tp = W @ T[fi]
            Bp = W @ B[fi]
            Nv = W @ nrm[fi]
            # bake the FLAT geometric face normal into tangent space —
            # this is the high-frequency detail smooth shading hides
            Nf = np.broadcast_to(face_nrm[s + j], Tp.shape)
            nt = np.stack([np.einsum("ij,ij->i", Nf, Tp),
                           np.einsum("ij,ij->i", Nf, Bp),
                           np.einsum("ij,ij->i", Nf, Nv)], 1)
            nl2 = np.linalg.norm(nt, axis=1, keepdims=True)
            nt = nt / np.maximum(nl2, 1e-12)
            px = (xs[inside] - 0.5).astype(int)
            py = (ys[inside] - 0.5).astype(int)
            out[py, px] = nt * 0.5 + 0.5
    return (out * 255.0 + 0.5).clip(0, 255).astype(np.uint8)


def bake_normal_map(glb: Path, out_dir: Path,
                    size: int = 1024) -> tuple[Path, dict]:
    """Bake + attach a tangent-space normal map. Returns (glb_path, report)."""
    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    scene = trimesh.load(str(glb), force="scene")
    mesh = None
    for geom in scene.geometry.values():
        if isinstance(geom, trimesh.Trimesh):
            mesh = geom
            break
    if mesh is None:
        raise ProviderError(f"normalmap: no mesh geometry in {glb.name}")
    if not hasattr(mesh.visual, "uv") or mesh.visual.uv is None:
        raise ProviderError(
            f"normalmap: mesh has no UVs in {glb.name}; refusing to fake it")

    t0 = time.time()
    verts = np.asarray(mesh.vertices, dtype=np.float64)
    faces = np.asarray(mesh.faces)
    uvs = np.asarray(mesh.visual.uv, dtype=np.float64)
    uvs[:, 1] = 1.0 - uvs[:, 1]  # glTF UV origin is top-left for baking
    nrm_png = _bake(verts, faces, uvs, size=size)
    bake_secs = time.time() - t0
    from PIL import Image
    buf = io.BytesIO()
    Image.fromarray(nrm_png).save(buf, format="PNG")
    png_bytes = buf.getvalue()

    doc, blob = parse_glb(glb)
    doc, new_blob, (img_idx,) = append_images(
        doc, blob, [(png_bytes, "image/png")])
    if "textures" not in doc:
        doc["textures"] = []
    doc["textures"].append({"source": img_idx, "name": "forge3d_normal"})
    tex_idx = len(doc["textures"]) - 1
    for mat in doc.get("materials", []):
        mat["normalTexture"] = {"index": tex_idx, "texCoord": 0, "scale": 1.0}

    out = out_dir / f"{glb.stem}.normalmap.glb"
    write_glb(doc, new_blob, out)
    report = {"faces": len(faces), "verts": len(verts),
              "normal_map": f"{size}x{size}",
              "normal_png_bytes": len(png_bytes),
              "bake_seconds": round(bake_secs, 1),
              "materials_tagged": len(doc.get("materials", [])),
              "output": out.name}
    print(f"normalmap: {len(faces)}f baked to {size}x{size} "
          f"in {bake_secs:.1f}s -> {out.name}", file=sys.stderr)
    return out, report


def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    out, report = bake_normal_map(Path(a.input), Path(a.outdir), a.size)
    print(out)
    if a.report:
        Path(a.report).write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
