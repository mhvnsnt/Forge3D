"""GNM head stage — Google's Generative aNthropometric Model (Apache 2.0).

Resolved 2026-10-06: the owner's "GNM parametric head" = google/GNM
(github.com/google/GNM), a parametric 3D statistical human-head model with
disentangled identity (253 components) / expression (383 blendshapes) /
pose control, incl. eyes, teeth, tongue. License: Apache 2.0 — commercial-safe.

This module wraps the NumPy math directly (no torch needed):
    verts = template + identity_basis @ id_params + expression_basis @ ex_params

Facial rig = expression blendshape deltas baked as morph targets / shape keys.
Facial morphs = identity parameter vectors. Model weights download once from
public HuggingFace (google/gnm-3) into the repo-local cache — never committed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
GNM_REPO = REPO / "_vendor" / "gnm"
GNM_CACHE = REPO / "_vendor" / "gnm_models"

_model = None


def _ensure_path():
    if str(GNM_REPO) not in sys.path:
        sys.path.insert(0, str(GNM_REPO))


def load():
    """Load (and cache) the GNM v3.0 head model dict."""
    global _model
    if _model is not None:
        return _model
    _ensure_path()
    import os
    os.environ.setdefault("GNM_CACHE_DIR", str(GNM_CACHE))
    from gnm.shape.oss_data_loaders import oss_data_loaders
    from gnm.shape.data.versions import gnm_specs
    _model = oss_data_loaders.load_model_from_remote(
        gnm_specs.GNMMajorVersion.V3, gnm_specs.GNMVariant.HEAD)
    return _model


def generate(identity=None, expression=None, seed: int = 0):
    """Generate head vertices.

    identity: None (template) | int seed -> random | (253,) array
    expression: None | dict {blendshape_index: weight} | (383,) array
    Returns (verts (17821,3) float64, faces (35324,3), uvs (35324,3,2)).
    """
    m = load()
    template = np.asarray(m["template_vertex_positions"], dtype=np.float64)
    id_basis = np.asarray(m["vertex_identity_basis"], dtype=np.float64)   # (253,V,3)
    ex_basis = np.asarray(m["expression_basis"], dtype=np.float64)         # (383,V,3)

    if identity is None:
        id_p = np.zeros(id_basis.shape[0])
    elif isinstance(identity, (int, np.integer)):
        rng = np.random.default_rng(int(identity) + seed)
        id_p = rng.normal(0, 0.6, id_basis.shape[0])
    else:
        id_p = np.asarray(identity, dtype=np.float64)
    verts = template + np.einsum("i,ijk->jk", id_p, id_basis)

    if expression is not None:
        if isinstance(expression, dict):
            ex_p = np.zeros(ex_basis.shape[0])
            for k, v in expression.items():
                ex_p[int(k)] = float(v)
        else:
            ex_p = np.asarray(expression, dtype=np.float64)
        verts = verts + np.einsum("e,ejk->jk", ex_p, ex_basis)

    faces = np.asarray(m["triangles"], dtype=np.int64)
    uvs = np.asarray(m["triangle_uvs"], dtype=np.float64)
    return verts, faces, uvs


def find_blendshapes(*keywords):
    """Return blendshape indices whose names contain any keyword."""
    m = load()
    names = [str(n) for n in m["expression_names"]]
    out = [i for i, n in enumerate(names)
           if any(k in n for k in keywords)]
    return out, names


# Expression presets: keyword -> activation weight. Blendshape names are
# region_indexed (e.g. 'lower_face_region_003'), so presets activate the whole region.
PRESETS = {
    "jaw_open": (("lower_face_region",), 1.2),
    "smile": (("lower_face_region",), 0.9),
    "blink": (("left_eye_region", "right_eye_region"), 0.8),
}


def _discover_preset(region_kw: str, vgroup: str, direction, top_k: int = 3,
                     weight: float = 1.0):
    """Data-driven preset: pick the blendshapes in a region whose displacement
    of a vertex group best matches `direction` (a function of (dx,dy,dz,x,y,z)).

    Honest because it measures the basis instead of guessing semantics.
    The basis is linear: displacement scales with weight, so weights are
    calibrated to visible magnitudes (head height ~= 0.34 units).
    """
    m = load()
    names = [str(n) for n in m["expression_names"]]
    vgroups = [str(n) for n in m["vertex_group_names"]]
    ex = np.asarray(m["expression_basis"], dtype=np.float64)  # (383,V,3)
    try:
        gi = vgroups.index(vgroup)
    except ValueError:
        return {}
    vg = np.asarray(m["vertex_groups"], dtype=np.float64)[gi]  # (V,)
    idx = [i for i, n in enumerate(names) if region_kw in n]
    scores = []
    V = ex.shape[1]
    w = np.clip(vg, 0, 1)
    for i in idx:
        d = ex[i]  # (V,3)
        s = float(np.sum(w * direction(d)))
        scores.append((s, i))
    scores.sort(reverse=True)
    return {i: weight for _, i in scores[:top_k]}


def preset_expression(name: str):
    if name == "jaw_open":
        # lower lip moves down; calibrated: ~0.006 @ w=1 -> w=5 ~= 0.03 drop
        return _discover_preset("lower_face_region", "lower_lip",
                                lambda d: -d[:, 1], weight=5.0)
    if name == "smile":
        # mouth corners move up and out; calibrated w=2.5 ~= 0.02
        return _discover_preset("lower_face_region", "mouth_sock",
                                lambda d: d[:, 1] + np.abs(d[:, 0]),
                                weight=2.5)
    if name == "blink":
        # upper eyelids move down; eye-region basis is subtle -> w=6
        p = _discover_preset("left_eye_region", "skin",
                             lambda d: -d[:, 1], top_k=3, weight=6.0)
        p.update(_discover_preset("right_eye_region", "skin",
                                  lambda d: -d[:, 1], top_k=3, weight=6.0))
        return p
    raise KeyError(f"unknown preset '{name}' (known: jaw_open, smile, blink)")


def export_obj(path: Path, verts, faces, uvs=None):
    path = Path(path)
    with open(path, "w") as f:
        f.write(f"# GNM head export ({len(verts)} verts)\n")
        for v in verts:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        if uvs is not None:
            # per-face uvs -> per-wedge; write unique wedge uvs
            seen, wuv, widx = {}, [], []
            for fi in range(len(faces)):
                for c in range(3):
                    key = (int(faces[fi, c]), round(float(uvs[fi, c, 0]), 5),
                           round(float(uvs[fi, c, 1]), 5))
                    if key not in seen:
                        seen[key] = len(wuv)
                        wuv.append((key[1], key[2]))
                    widx.append(seen[key])
            for u, v in wuv:
                f.write(f"vt {u:.6f} {v:.6f}\n")
            widx = np.array(widx).reshape(-1, 3)
            for fi in range(len(faces)):
                f.write("f " + " ".join(
                    f"{int(faces[fi, c])+1}/{int(widx[fi, c])+1}"
                    for c in range(3)) + "\n")
        else:
            for fa in faces:
                f.write(f"f {int(fa[0])+1} {int(fa[1])+1} {int(fa[2])+1}\n")
    return path


def export_glb(path: Path, verts, faces, uvs=None):
    """Export head as GLB via trimesh (for the preview renderer)."""
    import trimesh
    path = Path(path)
    visual = None
    if uvs is not None:
        # average per-face uvs to per-vertex
        uv = np.zeros((len(verts), 2))
        cnt = np.zeros(len(verts))
        for fi in range(len(faces)):
            for c in range(3):
                uv[faces[fi, c]] += uvs[fi, c]
                cnt[faces[fi, c]] += 1
        uv = uv / np.maximum(cnt[:, None], 1)
        visual = trimesh.visual.TextureVisuals(uv=uv)
    mesh = trimesh.Trimesh(vertices=np.asarray(verts, dtype=np.float64),
                           faces=np.asarray(faces, dtype=np.int64),
                           visual=visual, process=True)
    mesh.export(path)
    return path


def main():
    import argparse
    ap = argparse.ArgumentParser(description="GNM parametric head generator")
    ap.add_argument("--out", required=True)
    ap.add_argument("--identity-seed", type=int, default=None)
    ap.add_argument("--expressions", default="neutral,smile,jaw_open")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    jobs = []
    ident = args.identity_seed
    for expr_name in [e.strip() for e in args.expressions.split(",")]:
        expr = None if expr_name == "neutral" else preset_expression(expr_name)
        v, f, uv = generate(identity=ident, expression=expr)
        tag = f"id{ident if ident is not None else 'template'}_{expr_name}"
        p = out / f"gnm_head_{tag}.glb"
        export_glb(p, v, f, uv)
        jobs.append((tag, p, len(v), len(f)))
        print(f"gnm_head: {tag}: verts={len(v)} tris={len(f)} -> {p.name}")
    # identity variants
    for s in (7, 21):
        v, f, uv = generate(identity=s)
        p = out / f"gnm_head_id{s}_neutral.glb"
        export_glb(p, v, f, uv)
        jobs.append((f"id{s}_neutral", p, len(v), len(f)))
        print(f"gnm_head: id{s}_neutral: verts={len(v)} tris={len(f)} -> {p.name}")
    return jobs


if __name__ == "__main__":
    main()
