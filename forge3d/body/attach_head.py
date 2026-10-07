"""GNM head attachment: merge a parametric GNM head onto a generated body.

Steps:
1. Load body GLB (all geometries merged to one mesh).
2. Locate the neck:
   a. HEAD-JOINT FALLBACK: if the GLB has a skin whose joint node name
      contains 'head' (case-insensitive), use that joint's world position
      as the neck anchor.
   b. GEOMETRIC (default for unrigged generator output): the neck is the
      height of minimum horizontal cross-section area in the top 35% of
      the mesh (the neck is the narrowest part above the shoulders).
3. Cut the body at neck_y (generated head/hood region removed).
4. Generate the GNM head (identity seed + expression), scale it to the
   body's neck/head proportions, orient it to the body's facing, and seat
   its base into the neck with a small embed.
5. Neck-seam blending (distance-weighted): head vertices near the seam are
   pulled toward the body's neck-ring profile with a cosine falloff, so the
   transition is smooth instead of a hard ledge.
6. Merge to one GLB (body_trimmed + head_attached) + stats JSON.

GNM faces +Z (verified against render_preview's camera convention).
Body facing is a parameter (facing_degrees, rotation about Y applied to the
head); for TripoSR-from-front-photo bodies the caller should verify with a
4-angle render and set it explicitly.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np


def _load_meshes(glb_path: Path):
    import trimesh
    scene = trimesh.load(glb_path, force="scene")
    geoms = list(scene.dump()) if hasattr(scene, "dump") else [scene]
    return geoms


def _merged_verts_faces(glb_path: Path):
    geoms = _load_meshes(glb_path)
    Vs, Fs = [], []
    vo = 0
    for g in geoms:
        V = np.asarray(g.vertices, dtype=np.float64)
        F = np.asarray(g.faces, dtype=np.int64)
        Vs.append(V)
        Fs.append(F + vo)
        vo += len(V)
    return np.vstack(Vs), np.vstack(Fs)


def _glb_json(glb_path: Path) -> dict:
    d = Path(glb_path).read_bytes()
    ln = struct.unpack("<I", d[12:16])[0]
    return json.loads(d[20:20 + ln])


def find_head_joint(glb_path: Path):
    """Return (joint_index, world_xyz) of a 'head' joint, or None.

    Explicit head-joint fallback: used when the body is already rigged.
    """
    try:
        j = _glb_json(glb_path)
    except Exception:
        return None
    skins = j.get("skins", [])
    nodes = j.get("nodes", [])
    if not skins or not nodes:
        return None
    # world transforms by walking up parents (bind pose)
    parents = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parents[c] = i

    def world_pos(idx: int) -> np.ndarray:
        p = np.zeros(3)
        cur = idx
        while cur is not None:
            t = nodes[cur].get("translation", [0, 0, 0])
            p = p + np.asarray(t, dtype=np.float64)
            cur = parents.get(cur)
        return p

    for s in skins:
        for ji in s.get("joints", []):
            name = str(nodes[ji].get("name", ""))
            if "head" in name.lower():
                return ji, world_pos(ji)
    return None


def _slab_area(V: np.ndarray, y: float, half: float) -> tuple[float, np.ndarray]:
    """Convex-hull area of the XZ cross-section at height y."""
    sel = V[np.abs(V[:, 1] - y) < half]
    if len(sel) < 4:
        return 0.0, np.zeros(2)
    pts = sel[:, [0, 2]]
    center = pts.mean(axis=0)
    try:
        from scipy.spatial import ConvexHull
        area = float(ConvexHull(pts).volume)  # volume == area in 2D
    except Exception:
        e = pts.max(axis=0) - pts.min(axis=0)
        area = float(e[0] * e[1])
    return area, center


def find_neck_geometric(V: np.ndarray, top_frac: float = 0.35,
                       levels: int = 60) -> tuple[float, np.ndarray, float]:
    """Return (neck_y, neck_center_xz, neck_radius).

    Scans horizontal slabs over the top `top_frac` of the Y range. The neck
    is the first local minimum of cross-section area when moving UP from the
    shoulders (the widest part) -- this avoids mistaking the top of the head
    cap (which is also narrow) for the neck. The top 8% (head cap) is
    excluded from the search outright.
    """
    ymin, ymax = V[:, 1].min(), V[:, 1].max()
    yr = ymax - ymin
    lo = ymax - top_frac * yr
    hi = ymax - 0.08 * yr  # exclude the head cap
    half = yr / (levels * 2.5)
    ys = np.linspace(lo, hi, levels)
    areas, centers = [], []
    for y in ys:
        a, c = _slab_area(V, y, half)
        areas.append(a)
        centers.append(c)
    areas = np.array(areas)
    # light smoothing (3-tap): convex-hull slab areas are already stable;
    # heavy smoothing smears the sharp neck dip into spurious minima
    k = np.ones(3) / 3
    sm = np.convolve(areas, k, mode="same")
    # ignore empty slabs
    valid = areas > 1e-12
    if not valid.any():
        raise ValueError("no geometry in top region -- cannot find neck")
    sm = np.where(valid, sm, np.inf)

    # neck = deepest SIGNIFICANT local minimum: a real neck is far narrower
    # than the head/shoulders around it, so shallow facet-wobble dips lose
    n = len(ys)
    local_min = [i for i in range(1, n - 1)
                 if sm[i] <= sm[i - 1] and sm[i] <= sm[i + 1]
                 and np.isfinite(sm[i])]
    wmax = float(np.max(sm[np.isfinite(sm)]))
    sig = [i for i in local_min if sm[i] < 0.7 * wmax]
    if sig:
        neck_i = int(min(sig, key=lambda i: sm[i]))
    else:
        # fallback: global minimum of the included range
        neck_i = int(np.argmin(sm))
    neck_y = float(ys[neck_i])
    neck_center = centers[neck_i]
    neck_radius = float(np.sqrt(max(areas[neck_i], 1e-12) / np.pi))
    return neck_y, neck_center, neck_radius


def _head_base_radius(head_V: np.ndarray, frac: float = 0.12) -> tuple[float, np.ndarray]:
    """Radius/center of the GNM head's base (neck) ring."""
    ymin, ymax = head_V[:, 1].min(), head_V[:, 1].max()
    sel = head_V[head_V[:, 1] < ymin + frac * (ymax - ymin)]
    pts = sel[:, [0, 2]]
    center = pts.mean(axis=0)
    r = float(np.median(np.linalg.norm(pts - center, axis=1)))
    return r, center


def attach_head(body_glb: str | Path, out_glb: str | Path,
                identity_seed: int | None = 3,
                expression: str | None = None,
                facing_degrees: float = 0.0,
                embed: float = 0.02,
                blend: float = 0.035) -> dict:
    """Attach a GNM head to a generated body. Returns stats dict."""
    import trimesh
    from .gnm_head import generate, preset_expression

    body_glb = Path(body_glb)
    out_glb = Path(out_glb)
    V, F = _merged_verts_faces(body_glb)
    ymin, ymax = V[:, 1].min(), V[:, 1].max()
    body_h = ymax - ymin
    # embed/blend are tuned for a ~1.7-unit body; scale to actual height
    hscale = body_h / 1.7 if body_h > 1e-9 else 1.0
    embed = embed * hscale
    blend = blend * hscale

    # --- locate neck ---
    hj = find_head_joint(body_glb)
    if hj is not None:
        ji, jpos = hj
        neck_y = float(jpos[1])
        # geometric radius still needed: scan near the joint height
        _, neck_center, neck_radius = find_neck_geometric(V)
        neck_center = np.asarray([jpos[0], jpos[2]])
        neck_source = f"head-joint[{ji}]"
    else:
        neck_y, neck_center, neck_radius = find_neck_geometric(V)
        neck_source = "geometric"

    # --- cut body at neck ---
    keep = V[:, 1] <= neck_y
    if keep.sum() < 100:
        raise ValueError(f"neck cut kept only {keep.sum()} verts -- bad neck_y={neck_y}")
    # remap faces
    idx = np.full(len(V), -1, dtype=np.int64)
    idx[np.where(keep)[0]] = np.arange(keep.sum())
    fkeep = keep[F].all(axis=1)
    body_V = V[keep]
    body_F = idx[F[fkeep]]

    # --- generate GNM head ---
    expr = None if not expression else preset_expression(expression)
    hV, hF, _huv = generate(identity=identity_seed, expression=expr)
    hV = np.asarray(hV, dtype=np.float64)
    hF = np.asarray(hF, dtype=np.int64)

    # --- scale: match neck radius (XZ) and head height (Y) ---
    head_base_r, head_base_c = _head_base_radius(hV)
    hh = hV[:, 1].max() - hV[:, 1].min()
    body_head_h = ymax - neck_y
    s_xz = neck_radius / max(head_base_r, 1e-9)
    s_y = (body_head_h * 0.92) / max(hh, 1e-9)
    # clamp absurd scales (generated heads vary, but not 10x)
    s_xz = float(np.clip(s_xz, 0.3, 3.0))
    s_y = float(np.clip(s_y, 0.3, 3.0))
    hV[:, 0] = (hV[:, 0] - head_base_c[0]) * s_xz
    hV[:, 2] = (hV[:, 2] - head_base_c[1]) * s_xz
    hV[:, 1] = hV[:, 1] * s_y

    # --- orient: GNM faces +Z; rotate about Y by facing_degrees ---
    a = np.radians(facing_degrees)
    c, s = np.cos(a), np.sin(a)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    hV = hV @ R.T

    # --- seat: head base goes `embed` below the neck cut, centered on neck ---
    hV[:, 0] += neck_center[0] - hV[:, [0]].mean()
    hV[:, 2] += neck_center[1] - hV[:, [2]].mean()
    hV[:, 1] += (neck_y - embed) - hV[:, 1].min()

    # --- neck-seam blending (distance-weighted, cosine falloff) ---
    # head verts within `blend` of the cut get pulled toward the body neck ring
    d = hV[:, 1] - neck_y
    band_idx = np.where(np.abs(d) < blend)[0]
    if len(band_idx):
        # target: body neck cylinder of radius neck_radius around neck_center
        # (note: hV[band_idx] is a copy -- write back via np.ix_)
        off = hV[band_idx][:, [0, 2]] - neck_center
        r = np.linalg.norm(off, axis=1, keepdims=True) + 1e-12
        target = neck_center + off / r * neck_radius
        w = 0.5 * (1 + np.cos(np.pi * (d[band_idx] + blend) / (2 * blend)))
        # w=1 deep below the cut (conform to neck), 0 above (keep head)
        w = w[:, None]
        hV[np.ix_(band_idx, [0, 2])] = (
            (1 - w) * hV[band_idx][:, [0, 2]] + w * target)
        blended = int(len(band_idx))
    else:
        blended = 0

    # --- skin-tone the head from the body's neck region (visual continuity) ---
    neck_sel = body_V[np.abs(body_V[:, 1] - (neck_y - 0.01)) < 0.02]
    body_mesh = trimesh.Trimesh(vertices=body_V, faces=body_F, process=True)
    head_mesh = trimesh.Trimesh(vertices=hV, faces=hF, process=True)
    if len(neck_sel) > 0:
        # TripoSR-style bodies carry texture; approximate skin tone from the
        # body's mean vertex color if present, else neutral skin tone
        tone = np.array([0.72, 0.55, 0.45, 1.0])
        try:
            vc = getattr(body_mesh.visual, "vertex_colors", None)
            if vc is not None and len(vc) == len(body_V):
                tone = np.asarray(vc).reshape(-1, 4).mean(axis=0) / 255.0
        except Exception:
            pass
        head_mesh.visual = trimesh.visual.ColorVisuals(
            head_mesh, vertex_colors=np.tile((tone * 255).astype(np.uint8),
                                             (len(hV), 1)))

    # --- merge ---
    scene = trimesh.Scene([body_mesh, head_mesh])
    out_glb.parent.mkdir(parents=True, exist_ok=True)
    scene.export(out_glb)

    stats = {
        "body_glb": str(body_glb),
        "neck_y": neck_y,
        "neck_radius": neck_radius,
        "neck_center": [float(neck_center[0]), float(neck_center[1])],
        "neck_source": neck_source,
        "head_scale_xz": s_xz,
        "head_scale_y": s_y,
        "facing_degrees": facing_degrees,
        "embed": embed,
        "blend": blend,
        "blended_verts": blended,
        "body_verts": int(len(body_V)),
        "body_tris": int(len(body_F)),
        "head_verts": int(len(hV)),
        "head_tris": int(len(hF)),
        "out_glb": str(out_glb),
    }
    out_glb.with_suffix(".json").write_text(json.dumps(stats, indent=1))
    return stats


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Attach a GNM head to a body GLB")
    ap.add_argument("--body", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--identity-seed", type=int, default=3)
    ap.add_argument("--expression", default=None)
    ap.add_argument("--facing-degrees", type=float, default=0.0)
    args = ap.parse_args()
    stats = attach_head(args.body, args.out,
                        identity_seed=args.identity_seed,
                        expression=args.expression,
                        facing_degrees=args.facing_degrees)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
