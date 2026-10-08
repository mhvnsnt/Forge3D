"""Remesh shootout driver: voxel vs bmesh-cleanup vs quadriflow on trellis2-concept2-high.

Runs sequentially (RAM-safe: one Blender at a time), measures topology quality
on raw + all three outputs, writes a JSON report. Renders are done separately.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

REPO = Path("/home/hatch/workspace/forge3d")
VENV_PY = Path("/home/hatch/workspace/forge3d-venv/bin/python")
RAW = REPO / "docs/stage-evidence/trellis2-full/trellis2-concept2-high.glb"
OUTDIR = REPO / "docs/stage-evidence/remesh"


def topology_metrics(glb_path: Path) -> dict:
    scene = trimesh.load(glb_path, force="scene")
    geoms = list(scene.geometry.values())
    out = {"file": glb_path.name, "parts": len(geoms)}
    verts = sum(len(g.vertices) for g in geoms)
    faces = sum(len(g.faces) for g in geoms)
    out["verts"] = verts
    out["faces"] = faces
    # per-part topology on the largest part
    g = max(geoms, key=lambda x: len(x.faces))
    out["watertight"] = bool(g.is_watertight)
    # edge manifoldness
    edges = g.edges_sorted
    uniq, counts = np.unique(edges, axis=0, return_counts=True)
    out["boundary_edges"] = int((counts == 1).sum())
    out["nonmanifold_edges"] = int((counts > 2).sum())
    out["total_unique_edges"] = int(len(uniq))
    # valence / poles
    valence = np.bincount(g.faces.ravel(), minlength=len(g.vertices))
    out["poles_v3"] = int((valence == 3).sum())
    out["poles_v5"] = int((valence == 5).sum())
    out["poles_v7plus"] = int((valence >= 7).sum())
    out["verts_valence6"] = int((valence == 6).sum())
    # triangle quality: mean worst aspect ratio (longest/shortest edge)
    v = g.vertices
    f = g.faces
    e01 = np.linalg.norm(v[f[:, 0]] - v[f[:, 1]], axis=1)
    e12 = np.linalg.norm(v[f[:, 1]] - v[f[:, 2]], axis=1)
    e20 = np.linalg.norm(v[f[:, 2]] - v[f[:, 0]], axis=1)
    stack = np.stack([e01, e12, e20], axis=1)
    aspect = stack.max(axis=1) / np.maximum(stack.min(axis=1), 1e-12)
    out["tri_aspect_mean"] = float(aspect.mean())
    out["tri_aspect_p99"] = float(np.percentile(aspect, 99))
    # degenerate faces
    area = 0.5 * np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]],
                                          v[f[:, 2]] - v[f[:, 0]]), axis=1)
    out["degenerate_faces"] = int((area < 1e-12).sum())
    # UV survival
    out["has_uv"] = bool(hasattr(g.visual, "uv") and g.visual.uv is not None)
    return out


def run_step(name: str, cmd: list[str]) -> tuple[float, int]:
    t0 = time.time()
    print(f"[{name}] running: {' '.join(cmd[:4])} ...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    dt = time.time() - t0
    print(f"[{name}] done in {dt:.1f}s rc={r.returncode}", flush=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], flush=True)
        print(r.stderr[-2000:], flush=True)
    return dt, r.returncode


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    report: dict = {"input": str(RAW), "steps": {}}

    report["steps"]["raw"] = {"metrics": topology_metrics(RAW), "seconds": 0.0}

    # 1. voxel remesh
    dt, rc = run_step("voxel", [
        str(VENV_PY), "-m", "forge3d.pipelines.remesh",
        "--input", str(RAW), "--outdir", str(OUTDIR),
        "--mode", "voxel", "--voxel-size", "0.02",
    ])
    vfiles = sorted(OUTDIR.glob("*.remesh-voxel.glb"))
    if rc == 0 and vfiles:
        report["steps"]["voxel"] = {"metrics": topology_metrics(vfiles[-1]),
                                    "seconds": round(dt, 1), "file": vfiles[-1].name}
    else:
        report["steps"]["voxel"] = {"error": "blender run failed", "seconds": round(dt, 1)}

    # 2. bmesh cleanup
    dt, rc = run_step("cleanup", [
        str(VENV_PY), "-m", "forge3d.pipelines.remesh",
        "--input", str(RAW), "--outdir", str(OUTDIR),
        "--mode", "cleanup",
    ])
    cfiles = sorted(OUTDIR.glob("*.remesh-cleanup.glb"))
    if rc == 0 and cfiles:
        report["steps"]["cleanup"] = {"metrics": topology_metrics(cfiles[-1]),
                                      "seconds": round(dt, 1), "file": cfiles[-1].name}
    else:
        report["steps"]["cleanup"] = {"error": "blender run failed", "seconds": round(dt, 1)}

    # 3. quadriflow
    qmod = (
        "from pathlib import Path; "
        "from forge3d.pipelines.quadremesh import quad_remesh_glb; "
        f"quad_remesh_glb(Path('{RAW}'), Path('{OUTDIR}'), target_faces=30000)"
    )
    dt, rc = run_step("quadriflow", [str(VENV_PY), "-c", qmod])
    qfiles = [p for p in OUTDIR.glob("*.glb")
              if "remesh-voxel" not in p.name and "remesh-cleanup" not in p.name]
    if rc == 0 and qfiles:
        newest = max(qfiles, key=lambda p: p.stat().st_mtime)
        report["steps"]["quadriflow"] = {"metrics": topology_metrics(newest),
                                         "seconds": round(dt, 1), "file": newest.name}
    else:
        report["steps"]["quadriflow"] = {"error": "quad remesh failed", "seconds": round(dt, 1)}

    rep_path = OUTDIR / "shootout-report.json"
    rep_path.write_text(json.dumps(report, indent=2))
    print("REPORT:", rep_path, flush=True)
    print(json.dumps({k: v.get("metrics", v) for k, v in report["steps"].items()
                      if k != "raw"}, indent=2)[:3000], flush=True)


if __name__ == "__main__":
    main()
