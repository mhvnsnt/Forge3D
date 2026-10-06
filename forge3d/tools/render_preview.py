"""Forge3D preview renderer — software rasterizer (no GPU needed).

Loads a GLB via trimesh, renders turntable/angle sheets on a WHITE VOID
background with full framing (model at 80% of frame, margins on all sides).
Prints mesh stats (verts/tris/bounds) as generation proof.

Adapted raster core from the proven bannon-v10-models/work/render2.py rig.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * (c ** (1 / 2.4)) - 0.055)


def load_glb(glb_path: Path):
    """Return (V, N, UV, F, tex_lin) merged from all GLB geometries."""
    import trimesh

    scene = trimesh.load(glb_path, force="scene")
    geoms = list(scene.dump()) if hasattr(scene, "dump") else [scene]
    Vs, Ns, UVs, Fs = [], [], [], []
    tex = None
    vo = 0
    for g in geoms:
        V = np.asarray(g.vertices, dtype=np.float64)
        F = np.asarray(g.faces, dtype=np.int64)
        N = (np.asarray(g.vertex_normals, dtype=np.float64)
             if hasattr(g, "vertex_normals") and g.vertex_normals is not None
             and len(g.vertex_normals) == len(V)
             else None)
        if N is None:
            N = np.zeros_like(V)
            v0, v1, v2 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
            fn = np.cross(v1 - v0, v2 - v0)
            np.add.at(N, F[:, 0], fn)
            np.add.at(N, F[:, 1], fn)
            np.add.at(N, F[:, 2], fn)
        nl = np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
        N = N / nl
        if tex is None:
            try:
                mat = getattr(g, "visual", None)
                mat = getattr(mat, "material", None) if mat is not None else None
                img = getattr(mat, "baseColorTexture", None) if mat is not None else None
                if img is not None:
                    pil_img = img if isinstance(img, Image.Image) else Image.open(img)
                    tex = np.array(pil_img.convert("RGB"))
            except Exception:
                pass
        if hasattr(g.visual, "uv") and g.visual.uv is not None and len(g.visual.uv) == len(V):
            UV = np.asarray(g.visual.uv, dtype=np.float64)
        else:
            UV = np.zeros((len(V), 2), dtype=np.float64)
        Vs.append(V); Ns.append(N); UVs.append(UV); Fs.append(F + vo)
        vo += len(V)
    V = np.vstack(Vs); N = np.vstack(Ns); UV = np.vstack(UVs); F = np.vstack(Fs)
    if tex is None:
        tex = np.full((4, 4, 3), 200, np.uint8)  # flat light gray, untextured
    return V, N, UV, F, srgb_to_linear(tex.astype(np.float32))


def render_view(V, N, UV, F, tex_lin, W=700, H=1000, roty=0.0, flip_v=False):
    if roty:
        a = np.radians(roty); c, s = np.cos(a), np.sin(a)
        R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        V = V @ R.T
        N = N @ R.T
    mn, mx = V.min(0), V.max(0)
    sc = min((W * 0.80) / max(mx[0] - mn[0], 1e-9),
             (H * 0.80) / max(mx[1] - mn[1], 1e-9))
    cx, cy = (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2
    sx = (V[:, 0] - cx) * sc + W / 2
    sy = (cy - V[:, 1]) * sc + H / 2
    sz = V[:, 2]
    P = np.stack([sx, sy, sz], 1)

    img = np.ones((H, W, 3), np.float32)  # WHITE VOID
    zbuf = np.full((H, W), -1e18)
    key_dir = np.array([0.45, 0.55, 0.75]); key_dir /= np.linalg.norm(key_dir)
    fill_dir = np.array([-0.6, 0.15, 0.55]); fill_dir /= np.linalg.norm(fill_dir)
    rim_dir = np.array([-0.25, 0.35, -0.9]); rim_dir /= np.linalg.norm(rim_dir)
    view_dir = np.array([0.0, 0.0, 1.0])
    hemi_sky = np.array([0.55, 0.55, 0.58]); hemi_gnd = np.array([0.18, 0.17, 0.16])

    th, tw = tex_lin.shape[:2]
    Fpos = P[F]; Fnrm = N[F]; Fuv = UV[F]
    for i in range(len(F)):
        tri = Fpos[i]
        xs = tri[:, 0]; ys = tri[:, 1]
        x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, W - 1)
        y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, H - 1)
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = ((tri[1, 1] - tri[2, 1]) * (tri[0, 0] - tri[2, 0])
             + (tri[2, 0] - tri[1, 0]) * (tri[0, 1] - tri[2, 1]))
        if abs(d) < 1e-9:
            continue
        l0 = ((tri[1, 1] - tri[2, 1]) * (gx - tri[2, 0])
              + (tri[2, 0] - tri[1, 0]) * (gy - tri[2, 1])) / d
        l1 = ((tri[2, 1] - tri[0, 1]) * (gx - tri[2, 0])
              + (tri[0, 0] - tri[2, 0]) * (gy - tri[2, 1])) / d
        l2 = 1 - l0 - l1
        mask = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
        if not mask.any():
            continue
        z = l0 * tri[0, 2] + l1 * tri[1, 2] + l2 * tri[2, 2]
        upd = mask & (z > zbuf[y0:y1 + 1, x0:x1 + 1])
        if not upd.any():
            continue
        zbuf[y0:y1 + 1, x0:x1 + 1][upd] = z[upd]
        n = (l0[..., None] * Fnrm[i, 0] + l1[..., None] * Fnrm[i, 1]
             + l2[..., None] * Fnrm[i, 2])
        n /= (np.linalg.norm(n, axis=2, keepdims=True) + 1e-12)
        tu = l0 * Fuv[i, 0, 0] + l1 * Fuv[i, 1, 0] + l2 * Fuv[i, 2, 0]
        tv = l0 * Fuv[i, 0, 1] + l1 * Fuv[i, 1, 1] + l2 * Fuv[i, 2, 1]
        txi = np.clip((tu * tw).astype(int), 0, tw - 1)
        if flip_v:
            tyi = np.clip((tv * th).astype(int), 0, th - 1)
        else:
            tyi = np.clip(((1 - tv) * th).astype(int), 0, th - 1)
        albedo = tex_lin[tyi, txi]
        ndk = np.clip((n * key_dir).sum(-1), 0, 1)
        ndf = np.clip((n * fill_dir).sum(-1), 0, 1)
        ndr = np.clip((n * rim_dir).sum(-1), 0, 1)
        hemi = (hemi_sky * (n[..., 1] * 0.5 + 0.5)[..., None]
                + hemi_gnd * (1 - (n[..., 1] * 0.5 + 0.5))[..., None])
        h = key_dir + view_dir; h /= np.linalg.norm(h)
        spec = (np.clip((n * h).sum(-1), 0, 1) ** 48) * 0.35
        light = (hemi * 0.55 + ndk[..., None] * np.array([1.15, 1.12, 1.05])
                 + ndf[..., None] * np.array([0.35, 0.38, 0.45])
                 + ndr[..., None] * np.array([0.5, 0.48, 0.45]))
        col = albedo * light + spec[..., None] * np.array([1.0, 0.98, 0.95])
        tile = img[y0:y1 + 1, x0:x1 + 1]
        tile[upd] = linear_to_srgb(col[upd])
        img[y0:y1 + 1, x0:x1 + 1] = tile
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def decimate_for_preview(V, N, UV, F, target_faces=40000):
    if len(F) <= target_faces:
        return V, N, UV, F
    import trimesh
    mesh = trimesh.Trimesh(vertices=V, faces=F, vertex_normals=N, process=False)
    try:
        r = int(len(F) / target_faces)
        mesh = mesh.simplify_quadric_decimation(max(1000, len(F) // r))
    except Exception:
        pass
    Vn = np.asarray(mesh.vertices)
    Fn = np.asarray(mesh.faces)
    Nn = (np.asarray(mesh.vertex_normals)
          if mesh.vertex_normals is not None and len(mesh.vertex_normals) == len(Vn)
          else np.tile(np.array([[0.0, 0.0, 1.0]]), (len(Vn), 1)))
    # nearest-vertex UV remap
    try:
        from scipy.spatial import cKDTree
        _, idx = cKDTree(V).query(Vn)
        UVn = UV[idx]
    except Exception:
        UVn = np.zeros((len(Vn), 2))
    return Vn, Nn, UVn, Fn


def main():
    glb = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else glb.with_suffix(".preview.png")
    angles = [float(a) for a in sys.argv[3].split(",")] if len(sys.argv) > 3 else [0, 45, 135, 225]
    flip_v = len(sys.argv) > 4 and sys.argv[4] == "flipv"

    V, N, UV, F, tex_lin = load_glb(glb)
    mn, mx = V.min(0), V.max(0)
    print(f"verts={len(V)} tris={len(F)} "
          f"bbox_min=({mn[0]:.3f},{mn[1]:.3f},{mn[2]:.3f}) "
          f"bbox_max=({mx[0]:.3f},{mx[1]:.3f},{mx[2]:.3f})")
    assert len(V) > 100 and len(F) > 100, "mesh too small — generation failed"
    assert np.all(np.isfinite(V)), "non-finite vertices"
    assert (mx - mn).max() > 1e-6, "zero-size bounds"

    Pv, Pn, Puv, Pf = decimate_for_preview(V, N, UV, F)
    print(f"preview mesh: verts={len(Pv)} tris={len(Pf)}")
    views = [render_view(Pv, Pn, Puv, Pf, tex_lin, roty=a, flip_v=flip_v) for a in angles]
    sheet = np.hstack(views)
    Image.fromarray(sheet).save(out)
    print(f"saved {out} ({sheet.shape[1]}x{sheet.shape[0]}, angles={angles})")


if __name__ == "__main__":
    main()
