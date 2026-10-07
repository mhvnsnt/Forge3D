"""mesh_quality.py — MIT-side shim for the quarantined PyMeshLab worker.

The GPL-3.0 mesh-quality code lives in quarantine/pymeshlab_worker.py and is
NEVER imported here (repo AGENTS.md license rule). This module only shells
out to it as a subprocess with a JSON job file — arm's-length quarantine.

Pipeline: GLB -> (trimesh) OBJ -> [quarantine worker: Taubin smooth +
isotropic remesh + degenerate cleanup] -> OBJ -> GLB.

Proof metrics: triangle aspect-ratio p99, non-6-valence pole count,
degenerate face count, before/after.

Output: <stem>.mq.glb + <stem>.mesh_quality.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

from ..providers.base import ProviderError

WORKER = Path(__file__).parent.parent.parent / "quarantine" / "pymeshlab_worker.py"
VENV_PY = Path.home() / "workspace" / "forge3d-venv" / "bin" / "python"

def _adaptive_remesh_ops(mesh: trimesh.Trimesh) -> list:
    """Build the op list with isotropic-remesh targetlen matched to the
    input's mean edge length (preserves resolution; only improves shape).

    NOTE: the {"__pct__": x} marker is converted to pymeshlab.PercentageValue
    inside the quarantined worker — this MIT-side module never imports
    pymeshlab (license boundary)."""
    v = mesh.vertices[mesh.faces]
    e = np.stack([np.linalg.norm(v[:, 1] - v[:, 0], axis=1),
                  np.linalg.norm(v[:, 2] - v[:, 1], axis=1),
                  np.linalg.norm(v[:, 0] - v[:, 2], axis=1)], axis=1)
    mean_edge = float(e.mean())
    diag = float(np.linalg.norm(mesh.bounds[1] - mesh.bounds[0]))
    pct = max(mean_edge / max(diag, 1e-9) * 100.0, 0.05)
    return [
        {"filter": "meshing_remove_null_faces", "params": {}},
        {"filter": "meshing_remove_duplicate_vertices", "params": {}},
        {"filter": "apply_coord_taubin_smoothing",
         "params": {"lambda_": 0.5, "mu": -0.53, "stepsmoothnum": 5}},
        {"filter": "meshing_isotropic_explicit_remeshing",
         "params": {"iterations": 3, "targetlen": {"__pct__": round(pct, 3)}}},
        {"filter": "meshing_remove_unreferenced_vertices", "params": {}},
    ]


def _load_indexed_obj(path: Path) -> trimesh.Trimesh:
    """Parse an OBJ preserving its TRUE index structure (trimesh's loader
    splits vertices at UV seams, inflating counts). Per-vertex UV = first
    referencing corner (documented approximation; the xatlas_uv stage
    re-unwraps downstream anyway)."""
    verts, uvs, faces, face_uvs = [], [], [], []
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                verts.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("vt "):
                uvs.append([float(x) for x in line.split()[1:3]])
            elif line.startswith("f "):
                fv, ft = [], []
                for p in line.split()[1:]:
                    parts = p.split("/")
                    fv.append(int(parts[0]) - 1)
                    ft.append(int(parts[1]) - 1 if len(parts) > 1 and parts[1] else -1)
                faces.append(fv)
                face_uvs.append(ft)
    verts = np.array(verts, dtype=np.float64)
    faces = np.array(faces, dtype=np.int64)
    vuv = np.zeros((len(verts), 2))
    seen = np.zeros(len(verts), bool)
    uvs_a = np.array(uvs, dtype=np.float64) if uvs else np.zeros((0, 2))
    for fv, ft in zip(faces, face_uvs):
        for vi, ti in zip(fv, ft):
            if not seen[vi] and ti >= 0 and ti < len(uvs_a):
                vuv[vi] = uvs_a[ti]
                seen[vi] = True
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    mesh.visual = trimesh.visual.TextureVisuals(uv=vuv)
    return mesh


def _mesh_metrics(mesh: trimesh.Trimesh) -> dict:
    # triangle aspect ratio via edge lengths
    v = mesh.vertices[mesh.faces]
    e = np.stack([np.linalg.norm(v[:, 1] - v[:, 0], axis=1),
                  np.linalg.norm(v[:, 2] - v[:, 1], axis=1),
                  np.linalg.norm(v[:, 0] - v[:, 2], axis=1)], axis=1)
    aspect = e.max(axis=1) / np.maximum(e.min(axis=1), 1e-12)
    valence = np.bincount(mesh.faces.ravel(), minlength=len(mesh.vertices))
    poles = int(((valence != 6) & (valence > 0)).sum())
    return {"verts": int(len(mesh.vertices)), "faces": int(len(mesh.faces)),
            "tri_aspect_p99": round(float(np.percentile(aspect, 99)), 3),
            "tri_aspect_mean": round(float(aspect.mean()), 3),
            "non6_poles": poles}


def run(glb_path: str | Path, out_dir: str | Path | None = None,
        ops: list | None = None) -> dict:
    t0 = time.time()
    glb_path = Path(glb_path)
    out_dir = Path(out_dir) if out_dir else glb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    if not WORKER.exists():
        raise ProviderError(f"mesh_quality: quarantine worker missing at {WORKER}")
    py = str(VENV_PY) if VENV_PY.exists() else sys.executable

    scene = trimesh.load(str(glb_path), force="scene")
    mesh = list(scene.geometry.values())[0]
    before = _mesh_metrics(mesh)

    obj_in = out_dir / f"{glb_path.stem}.mq_in.obj"
    obj_out = out_dir / f"{glb_path.stem}.mq_out.obj"
    job_p = out_dir / f"{glb_path.stem}.mq_job.json"
    mesh.export(str(obj_in))  # trimesh OBJ keeps UVs

    job = {"input": str(obj_in), "output": str(obj_out),
           "ops": ops or _adaptive_remesh_ops(mesh),
           "report": str(out_dir / f"{glb_path.stem}.mq_worker.json")}
    job_p.write_text(json.dumps(job, indent=2))
    r = subprocess.run([py, str(WORKER), str(job_p)],
                       capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise ProviderError(f"mesh_quality: worker failed: {r.stderr[-2000:]}")
    worker_report = json.loads((out_dir / f"{glb_path.stem}.mq_worker.json").read_text())

    out_mesh = _load_indexed_obj(obj_out)  # true index structure, not seam-split
    after = _mesh_metrics(out_mesh)
    out_glb = out_dir / f"{glb_path.stem}.mq.glb"
    # keep original materials/UVs where possible: export processed mesh
    out_mesh.export(str(out_glb))

    metrics = {"input": str(glb_path), "before": before, "after": after,
               "worker": worker_report,
               "output": str(out_glb),
               "seconds": round(time.time() - t0, 1)}
    (out_dir / f"{glb_path.stem}.mesh_quality.json").write_text(
        json.dumps(metrics, indent=2))
    return metrics


def main():
    if len(sys.argv) != 3:
        print("usage: mesh_quality.py <in.glb> <out_dir>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(run(sys.argv[1], sys.argv[2]), indent=2))


if __name__ == "__main__":
    main()
