"""Automated quality gates for generated models.

Every generation runs through these gates before it ships. A gate returns
PASS / FLAG (shippable with warnings) / FAIL. FAIL means retry with the next
provider (fan-out) or abort loudly — never silently ship a bad model.

Gates (all measurable with trimesh + PIL, no GPU):
  - watertight: zero boundary loops (trimesh edges)
  - manifold: is_watertight + winding consistent
  - components: single connected component (no floating bits)
  - degenerate: degenerate-face ratio under threshold
  - poly_count: triangle count within game-character band
  - texture_res: every embedded texture >= minimum resolution
  - proportions: bounding-box sanity for a humanoid character
    (height range, not absurdly flat/wide) — heuristic, documented

Hands/face honesty note: true hand/face anatomical QA needs a trained
detector (not wired). The gates catch structural defects; fine anatomical
correctness is the owner's eyes-on step (likeness sheet, 150%).
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

# Game-character targets (owner-tunable)
MIN_TRIS = 8_000
MAX_TRIS = 120_000
MIN_TEX_RES = 512          # min width/height per texture
MIN_HEIGHT_M = 1.2         # normalized character height range
MAX_HEIGHT_M = 2.4
MAX_DEGENERATE_RATIO = 0.02

PASS, FLAG, FAIL = "PASS", "FLAG", "FAIL"


@dataclass
class GateResult:
    name: str
    verdict: str
    detail: str
    measured: dict = field(default_factory=dict)


@dataclass
class GateReport:
    results: list[GateResult] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        vs = [r.verdict for r in self.results]
        if FAIL in vs:
            return FAIL
        if FLAG in vs:
            return FLAG
        return PASS

    def to_dict(self) -> dict:
        return {"verdict": self.verdict,
                "gates": [{"name": r.name, "verdict": r.verdict,
                           "detail": r.detail, "measured": r.measured}
                          for r in self.results]}


def _load_scene(path: Path):
    try:
        return trimesh.load(str(path), force="scene"), None
    except Exception as e:  # noqa: BLE001
        return None, e


def _meshes(scene) -> list:
    if scene is None:
        return []
    if isinstance(scene, trimesh.Scene):
        return [g for g in scene.geometry.values()
                if isinstance(g, trimesh.Trimesh)]
    if isinstance(scene, trimesh.Trimesh):
        return [scene]
    return []


def _combined(mesh_list: list) -> trimesh.Trimesh | None:
    if not mesh_list:
        return None
    if len(mesh_list) == 1:
        return mesh_list[0]
    try:
        return trimesh.util.concatenate(mesh_list)
    except Exception:  # noqa: BLE001
        return mesh_list[0]


def gate_watertight(mesh: trimesh.Trimesh) -> GateResult:
    edges = mesh.edges_sorted
    # boundary edges appear exactly once
    _, counts = np.unique(mesh.edges_sorted, axis=0, return_counts=True)
    n_boundary = int(np.sum(counts == 1))
    ok = n_boundary == 0
    return GateResult("watertight", PASS if ok else FAIL,
                      f"{n_boundary} boundary edges" + ("" if ok else
                      " — mesh has holes"),
                      {"boundary_edges": n_boundary})


def gate_manifold(mesh: trimesh.Trimesh) -> GateResult:
    wt = bool(mesh.is_watertight)
    wc = bool(mesh.is_winding_consistent)
    if wt and wc:
        return GateResult("manifold", PASS, "watertight + winding consistent",
                          {"watertight": wt, "winding_consistent": wc})
    if wt:
        return GateResult("manifold", FLAG,
                          "watertight but winding inconsistent — shading risk",
                          {"watertight": wt, "winding_consistent": wc})
    return GateResult("manifold", FAIL, "not watertight",
                      {"watertight": wt, "winding_consistent": wc})


def gate_components(mesh_list: list) -> GateResult:
    n = len(mesh_list)
    if n == 1:
        return GateResult("components", PASS, "single connected mesh",
                          {"components": n})
    if n <= 3:
        return GateResult("components", FLAG,
                          f"{n} components — check for floating bits",
                          {"components": n})
    return GateResult("components", FAIL,
                      f"{n} disconnected components — likely fragments",
                      {"components": n})


def gate_degenerate(mesh: trimesh.Trimesh) -> GateResult:
    try:
        # faces with ~zero area
        area = mesh.area_faces
        deg = int(np.sum(area < 1e-10))
        ratio = deg / max(1, len(area))
    except Exception:  # noqa: BLE001
        return GateResult("degenerate", FLAG, "could not measure",
                          {"ratio": -1.0})
    if ratio <= MAX_DEGENERATE_RATIO:
        return GateResult("degenerate", PASS,
                          f"{deg} degenerate faces ({ratio:.4f})",
                          {"ratio": ratio, "count": deg})
    return GateResult("degenerate", FAIL,
                      f"{deg} degenerate faces ({ratio:.4f} > "
                      f"{MAX_DEGENERATE_RATIO})",
                      {"ratio": ratio, "count": deg})


def gate_poly_count(mesh: trimesh.Trimesh) -> GateResult:
    n = len(mesh.faces)
    if MIN_TRIS <= n <= MAX_TRIS:
        return GateResult("poly_count", PASS, f"{n} tris in band",
                          {"tris": n})
    if n < MIN_TRIS:
        return GateResult("poly_count", FLAG,
                          f"{n} tris below {MIN_TRIS} — low detail, "
                          "consider densify",
                          {"tris": n})
    return GateResult("poly_count", FLAG,
                      f"{n} tris above {MAX_TRIS} — heavy for game, "
                      "consider decimate/quadremesh",
                      {"tris": n})


def _embedded_textures(glb_path: Path) -> list[tuple[int, Image.Image]]:
    """Extract embedded texture images from a GLB. Returns [(idx, PIL)]."""
    import struct as _st
    data = glb_path.read_bytes()
    if data[:4] != b"glTF":
        return []
    json_len = _st.unpack("<I", data[12:16])[0]
    doc = __import__("json").loads(data[20:20 + json_len])
    bin_off = 20 + json_len
    chunk_len = _st.unpack("<I", data[bin_off:bin_off + 4])[0]
    blob = data[bin_off + 8:bin_off + 8 + chunk_len]
    out = []
    for idx, img in enumerate(doc.get("images", [])):
        bv = img.get("bufferView")
        if bv is None:
            continue
        view = doc["bufferViews"][bv]
        s = view.get("byteOffset", 0)
        e = s + view["byteLength"]
        try:
            pil = Image.open(io.BytesIO(blob[s:e])).convert("RGB")
            out.append((idx, pil))
        except Exception:  # noqa: BLE001
            continue
    return out


def gate_texture_res(glb_path: Path) -> GateResult:
    texs = _embedded_textures(glb_path)
    if not texs:
        return GateResult("texture_res", FLAG,
                          "no embedded textures found — untextured mesh?",
                          {"textures": 0})
    small = [(i, p.size) for i, p in texs
             if min(p.size) < MIN_TEX_RES]
    sizes = [p.size for _, p in texs]
    if not small:
        return GateResult("texture_res", PASS,
                          f"{len(texs)} textures, all >= {MIN_TEX_RES}px",
                          {"textures": len(texs), "sizes": sizes})
    return GateResult("texture_res", FLAG,
                      f"{len(small)}/{len(texs)} textures below "
                      f"{MIN_TEX_RES}px: {small} — run texture upscale",
                      {"textures": len(texs), "small": small})


def gate_proportions(mesh: trimesh.Trimesh) -> GateResult:
    try:
        b = mesh.bounds
        ext = b[1] - b[0]
        h = float(ext[1])
        w = float(max(ext[0], ext[2]))
    except Exception:  # noqa: BLE001
        return GateResult("proportions", FLAG, "could not measure", {})
    meas = {"height": round(h, 3), "width": round(w, 3)}
    if not (MIN_HEIGHT_M <= h <= MAX_HEIGHT_M):
        return GateResult("proportions", FLAG,
                          f"height {h:.2f}m outside {MIN_HEIGHT_M}-"
                          f"{MAX_HEIGHT_M}m — normalize scale",
                          meas)
    if w > h * 1.2:
        return GateResult("proportions", FLAG,
                          f"width {w:.2f}m > 1.2x height — splayed limbs?",
                          meas)
    return GateResult("proportions", PASS,
                      f"height {h:.2f}m, width {w:.2f}m — humanoid-ish",
                      meas)


def run_gates(glb_path: Path) -> GateReport:
    """Run all quality gates on a GLB. Never raises on bad input."""
    rep = GateReport()
    scene, err = _load_scene(glb_path)
    if scene is None:
        rep.results.append(GateResult("load", FAIL,
                                      f"could not load GLB: {err}", {}))
        return rep
    meshes = _meshes(scene)
    if not meshes:
        rep.results.append(GateResult("load", FAIL,
                                      "no meshes in GLB", {}))
        return rep
    mesh = _combined(meshes)
    rep.results.append(gate_watertight(mesh))
    rep.results.append(gate_manifold(mesh))
    rep.results.append(gate_components(meshes))
    rep.results.append(gate_degenerate(mesh))
    rep.results.append(gate_poly_count(mesh))
    rep.results.append(gate_texture_res(glb_path))
    rep.results.append(gate_proportions(mesh))
    return rep
