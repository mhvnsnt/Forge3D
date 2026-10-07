"""materials.py — CC0 PBR material library stage.

Applies a CC0 PBR texture set (from forge3d/assets/cc0/, e.g. Poly Haven)
onto a GLB's materials so the texture stage can draw on real-world
roughness/normal/albedo data instead of inventing it.

Modes:
  pbr-overlay (default): keep the GLB's own albedo, attach the library's
      roughness + normal maps (OpenGL normal) to every PBR material.
  full: also swap the albedo for the library's diffuse (useful for
      re-surfacing; recorded honestly in the report).

The library is curated CC0 only — see docs/CC0_ASSETS.md for the catalog
with source URLs, md5s and license verification dates. No NC/SA/unclear
sources are ever pulled.

Output: <stem>.mat-<setname>-<mode>.glb + report dict.
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

from PIL import Image

from ..providers.base import ProviderError
from .glbutil import append_images, parse_glb, write_glb

ASSET_ROOT = (Path(__file__).resolve().parent.parent.parent
              / "assets" / "cc0")


def list_library() -> dict:
    """Return {set_name: {map: filename}} for the local CC0 library."""
    lib = {}
    if not ASSET_ROOT.exists():
        return lib
    for d in sorted(ASSET_ROOT.iterdir()):
        if not d.is_dir():
            continue
        files = sorted(p.name for p in d.glob("*") if p.suffix.lower()
                       in (".jpg", ".jpeg", ".png"))
        if files:
            lib[d.name] = files
    return lib


def _map_kind(filename: str) -> str:
    n = filename.lower()
    if "diff" in n or "albedo" in n or "color" in n:
        return "albedo"
    if "rough" in n:
        return "roughness"
    if "nor" in n or "normal" in n:
        return "normal"
    if "metal" in n:
        return "metallic"
    if "ao" in n:
        return "ao"
    return "unknown"


def apply_material(glb: Path, out_dir: Path, set_name: str,
                   mode: str = "pbr-overlay") -> tuple[Path, dict]:
    """Apply a CC0 PBR set to a GLB's materials. Returns (glb_path, report)."""
    if mode not in ("pbr-overlay", "full"):
        raise ProviderError(f"unknown materials mode: {mode}")
    set_dir = ASSET_ROOT / set_name
    if not set_dir.is_dir():
        raise ProviderError(
            f"materials: CC0 set '{set_name}' not in library "
            f"({ASSET_ROOT}); available: {list(list_library())}")

    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    maps: dict[str, bytes] = {}
    for p in sorted(set_dir.iterdir()):
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        kind = _map_kind(p.name)
        if kind == "unknown":
            continue
        img = Image.open(p).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        maps[kind] = buf.getvalue()

    doc, blob = parse_glb(glb)
    materials = doc.get("materials", [])
    if not materials:
        raise ProviderError(
            f"materials: no materials in {glb.name}; refusing to fake it")

    payloads = []
    order = []
    want_kinds = (["albedo", "roughness", "normal", "metallic", "ao"]
                  if mode == "full"
                  else ["roughness", "normal", "metallic", "ao"])
    for kind in want_kinds:
        if kind in maps:
            payloads.append((maps[kind], "image/png"))
            order.append(kind)
    doc, new_blob, img_indices = append_images(doc, blob, payloads)
    kind_to_img = dict(zip(order, img_indices))

    if "textures" not in doc:
        doc["textures"] = []
    kind_to_tex = {}
    for kind, img_idx in kind_to_img.items():
        doc["textures"].append(
            {"source": img_idx, "name": f"cc0_{set_name}_{kind}"})
        kind_to_tex[kind] = len(doc["textures"]) - 1

    for mat in materials:
        pbr = mat.setdefault("pbrMetallicRoughness", {})
        if mode == "full" and "albedo" in kind_to_tex:
            pbr["baseColorTexture"] = {"index": kind_to_tex["albedo"],
                                       "texCoord": 0}
        if "roughness" in kind_to_tex:
            pbr["roughnessFactor"] = 1.0
            pbr["metallicFactor"] = 0.0
            pbr["roughnessTexture"] = {"index": kind_to_tex["roughness"],
                                       "texCoord": 0}
        if "normal" in kind_to_tex:
            mat["normalTexture"] = {"index": kind_to_tex["normal"],
                                    "texCoord": 0, "scale": 1.0}

    out = out_dir / f"{glb.stem}.mat-{set_name}-{mode}.glb"
    write_glb(doc, new_blob, out)
    report = {"set": set_name, "mode": mode, "maps_applied": order,
              "materials_tagged": len(materials),
              "seconds": round(time.time() - t0, 1),
              "output": out.name,
              "license": "CC0 1.0 (see docs/CC0_ASSETS.md)"}
    print(f"materials: {set_name}/{mode} -> {out.name} "
          f"(maps: {','.join(order)})", file=sys.stderr)
    return out, report


def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=False, default=None)
    ap.add_argument("--outdir", required=False, default=None)
    ap.add_argument("--set", dest="set_name", required=False, default=None)
    ap.add_argument("--mode", default="pbr-overlay")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    if a.list:
        print(json.dumps(list_library(), indent=2))
        return
    if not (a.input and a.outdir and a.set_name):
        ap.error("--input, --outdir and --set are required (or use --list)")
    out, report = apply_material(Path(a.input), Path(a.outdir),
                                 a.set_name, a.mode)
    print(out)
    if a.report:
        Path(a.report).write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
