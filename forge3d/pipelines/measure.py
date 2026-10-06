"""Measurement harness: score a GLB against the Tripo baseline.

Owner-supplied Tripo bar (docs/tripo-baseline/, Tripo Studio screenshots):
  topology=Triangle, faces ~= 1.9M, verts ~= 1.0M, T-pose/A-pose, full PBR textures.

Every metric here is computed from the actual file — no estimates, no fakes.
Used by docs/TRIPO_BASELINE.md to report the honest delta.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path


def _parse_glb(path: Path):
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise ValueError(f"not a GLB: {path}")
    jlen = struct.unpack("<I", data[12:16])[0]
    doc = json.loads(data[20:20 + jlen])
    binoff = 20 + jlen
    blen = struct.unpack("<I", data[binoff:binoff + 4])[0]
    blob = data[binoff + 8:binoff + 8 + blen]
    return doc, blob


def _accessor_count(doc, blob, idx: int) -> int:
    acc = doc["accessors"][idx]
    return acc["count"]


def _image_sizes(doc, blob):
    """Return [(w, h)] for embedded buffer-view images (header parse only)."""
    out = []
    views = doc.get("bufferViews", [])
    for img in doc.get("images", []):
        bv = img.get("bufferView")
        if bv is None:
            continue
        v = views[bv]
        start = v.get("byteOffset", 0)
        chunk = blob[start:start + 64]
        # PNG: width/height at bytes 16..24 of the file
        if chunk[:8] == b"\x89PNG\r\n\x1a\n":
            w = struct.unpack(">I", chunk[16:20])[0]
            h = struct.unpack(">I", chunk[20:24])[0]
            out.append((w, h))
        elif chunk[:2] == b"\xff\xd8":
            out.append(("jpeg", "jpeg"))
    return out


def measure_glb(path: Path) -> dict:
    """Compute the full metric dict for a GLB file."""
    import trimesh

    path = Path(path)
    m: dict = {"file": path.name, "bytes": path.stat().st_size}
    doc, blob = _parse_glb(path)

    # bones (rig-readiness)
    m["bones"] = sum(len(s.get("joints", [])) for s in doc.get("skins", []))

    # textures
    m["texture_images"] = _image_sizes(doc, blob)
    m["pbr_materials"] = len(doc.get("materials", []))

    # geometry via trimesh
    try:
        scene = trimesh.load(path, force="scene")
        geoms = list(scene.dump()) if hasattr(scene, "dump") else [scene]
    except Exception as e:  # noqa: BLE001
        m["parse_error"] = str(e)
        return m

    verts = faces = 0
    watertight = True
    for g in geoms:
        if not hasattr(g, "vertices"):
            continue
        verts += len(g.vertices)
        faces += len(g.faces)
        try:
            watertight = watertight and bool(g.is_watertight)
        except Exception:  # noqa: BLE001
            watertight = False
    m["vertices"] = verts
    m["faces"] = faces
    m["watertight"] = watertight
    try:
        bounds = scene.bounds
        m["bounds"] = [[float(x) for x in bounds[0]], [float(x) for x in bounds[1]]]
        m["height_m"] = float(bounds[1][1] - bounds[0][1])
    except Exception:  # noqa: BLE001
        pass
    return m


TRIPO_BAR = {
    "topology": "Triangle",
    "faces": 1_931_958,      # median of owner's 4 Tripo Studio screenshots
    "vertices": 1_001_425,
    "pose": "T-pose/A-pose",
    "textures": "full PBR color",
}


def compare(path: Path) -> dict:
    """Measure a GLB and report the delta vs the Tripo bar."""
    m = measure_glb(path)
    if "faces" in m and TRIPO_BAR["faces"]:
        m["face_ratio_vs_tripo"] = round(m["faces"] / TRIPO_BAR["faces"], 4)
    if "vertices" in m and TRIPO_BAR["vertices"]:
        m["vert_ratio_vs_tripo"] = round(m["vertices"] / TRIPO_BAR["vertices"], 4)
    m["tripo_bar"] = dict(TRIPO_BAR)
    return m


if __name__ == "__main__":
    import sys
    print(json.dumps(compare(Path(sys.argv[1])), indent=2))
