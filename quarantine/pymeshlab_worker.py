#!/usr/bin/env python3
"""Quarantined GPL worker: mesh quality via PyMeshLab (GPL-3.0).

STANDALONE — NEVER imported by forge3d/pipelines/ (repo AGENTS.md license
rule). The MIT-licensed pipeline talks to this worker only as a subprocess
with a JSON job file; all communication is via files (arm's-length
quarantine, the standard GPL boundary).

Job JSON schema:
  {"input": "mesh.obj", "output": "mesh.out.obj",
   "ops": [{"filter": "<pymeshlab filter name>", "params": {...}}, ...],
   "report": "report.json"}

Each op is validated against pymeshlab's filter list; unknown filters fail
LOUDLY (no silent no-ops). The report records per-op mesh stats
(verts/faces, degenerate faces, non-manifold edges, tri aspect p99).

Example ops for the native-detail gap:
  meshing_smooth_taubin (feature-preserving smooth),
  meshing_isotropic_explicit_remeshing (even triangle redistribution),
  meshing_remove_degenerate_faces, meshing_remove_duplicate_vertices.
"""
import json
import sys
import time
from pathlib import Path


def _stats(ms) -> dict:
    m = ms.current_mesh()
    geo = None
    try:
        geo = ms.get_geometric_measures()
    except Exception:
        geo = {}
    return {
        "verts": int(m.vertex_number()),
        "faces": int(m.face_number()),
        "degenerate_faces": int(geo.get("degenerate_faces", -1)) if isinstance(geo, dict) else -1,
    }


def _coerce_params(params: dict) -> dict:
    """Convert JSON-safe markers to pymeshlab types (runs GPL-side only)."""
    import pymeshlab
    out = {}
    for k, v in params.items():
        if isinstance(v, dict) and set(v.keys()) == {"__pct__"}:
            out[k] = pymeshlab.PercentageValue(v["__pct__"])
        else:
            out[k] = v
    return out


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: pymeshlab_worker.py <job.json>", file=sys.stderr)
        sys.exit(2)
    import pymeshlab

    job = json.loads(Path(sys.argv[1]).read_text())
    inp, outp = Path(job["input"]), Path(job["output"])
    report_p = Path(job.get("report", inp.parent / "pymeshlab_report.json"))
    if not inp.exists():
        print(f"WORKER_FATAL: missing input {inp}", file=sys.stderr)
        sys.exit(1)

    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(inp))
    available = set(pymeshlab.filter_list())
    t0 = time.time()
    steps = []
    before = _stats(ms)
    for op in job.get("ops", []):
        name = op["filter"]
        if name not in available:
            print(f"WORKER_FATAL: unknown filter '{name}'", file=sys.stderr)
            sys.exit(1)
        raw_params = dict(op.get("params", {}))
        params = _coerce_params(raw_params)
        s = time.time()
        ms.apply_filter(name, **params)
        steps.append({"filter": name, "params": raw_params,
                      "seconds": round(time.time() - s, 1)})
    ms.save_current_mesh(str(outp))
    after = _stats(ms)
    try:
        ver = pymeshlab.__version__
    except AttributeError:
        ver = "unknown"
    report = {"input": str(inp), "output": str(outp), "before": before,
              "after": after, "steps": steps,
              "seconds": round(time.time() - t0, 1),
              "pymeshlab_version": ver}
    report_p.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
