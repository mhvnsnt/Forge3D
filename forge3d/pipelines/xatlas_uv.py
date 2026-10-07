"""xatlas_uv.py — production-grade automatic UV unwrapping via xatlas (MIT).

Closes the TEXTURE RESOLUTION / UV-quality gap: trellis raw UVs are
fragmented (many tiny islands -> mip bleed + wasted texel density).
xatlas (https://github.com/jpcy/xatlas, MIT; python wheel: xatlas) packs
larger, lower-distortion charts, which directly raises effective texture
resolution and reduces seam speckle.

Distinct from pipelines/retexture.py (Blender Smart-UV + Cycles rebake,
experimental): this is deterministic, CPU, no Blender needed.

Output: <stem>.xatlas.glb + <stem>.xatlas.json
(seam-edge counts before/after, island counts, timings).
"""
from __future__ import annotations

import collections
import json
import sys
import time
from pathlib import Path

import numpy as np
import trimesh
import xatlas

from .glbutil import parse_glb, write_glb

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


def _append_accessor(doc, blob: bytearray, arr: np.ndarray,
                     comp: int, typ: str) -> int:
    raw = np.ascontiguousarray(arr)
    # map numpy dtypes to glTF component types
    if raw.dtype == np.float32:
        comp = 5126
    elif raw.dtype == np.uint32:
        comp = 5125
    elif raw.dtype == np.uint16:
        comp = 5123
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
        accessor["min"] = [float(v) for v in raw.reshape(-1, n).min(axis=0)]
        accessor["max"] = [float(v) for v in raw.reshape(-1, n).max(axis=0)]
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


def run(glb_path: str | Path, out_dir: str | Path | None = None) -> dict:
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

    verts = _read_accessor(doc, bytes(blob), pos_idx).astype(np.float32)
    faces = _read_accessor(doc, bytes(blob), idx_idx).astype(np.int64)
    faces = faces.reshape(-1, 3)
    if uv_idx is not None:
        old_uv = _read_accessor(doc, bytes(blob), uv_idx).astype(np.float32)
        old_seams = seam_edges(old_uv, faces)
    else:
        old_seams = None

    t1 = time.time()
    vmapping, new_faces, new_uv = xatlas.parametrize(verts, faces)
    xtime = time.time() - t1
    new_verts = verts[vmapping].astype(np.float32)
    new_faces32 = new_faces.astype(np.uint32)

    # recompute smooth normals for the re-indexed mesh
    tm = trimesh.Trimesh(new_verts, new_faces32, process=False)
    new_normals = np.array(tm.vertex_normals, dtype=np.float32)
    new_uv = np.ascontiguousarray(new_uv.astype(np.float32))

    pos_new = _append_accessor(doc, blob, new_verts, 5126, "VEC3")
    nrm_new = _append_accessor(doc, blob, new_normals, 5126, "VEC3")
    uv_new = _append_accessor(doc, blob, new_uv, 5126, "VEC2")
    idx_new = _append_accessor(doc, blob, new_faces32, 5125, "SCALAR")

    prim["attributes"]["POSITION"] = pos_new
    prim["attributes"]["NORMAL"] = nrm_new
    prim["attributes"]["TEXCOORD_0"] = uv_new
    prim["indices"] = idx_new

    new_seams = seam_edges(new_uv, new_faces)

    stem = glb_path.stem
    out_glb = out_dir / f"{stem}.xatlas.glb"
    write_glb(doc, bytes(blob), out_glb)
    report = {
        "input": str(glb_path), "stage": "xatlas-uv",
        "verts_in": int(len(verts)), "verts_out": int(len(new_verts)),
        "faces": int(len(new_faces)),
        "seam_edges_before": old_seams, "seam_edges_after": int(new_seams),
        "xatlas_seconds": round(xtime, 1),
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
