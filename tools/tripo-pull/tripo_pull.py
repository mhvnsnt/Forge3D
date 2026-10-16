#!/usr/bin/env python3
"""
tripo_pull.py — Recover 3D models from Tripo Studio public share links.

Tripo locked free exports, but models shared via public links
(https://studio.tripo3d.ai/3d-model/<uuid>) expose their files through
Tripo's public project-detail API. This tool resolves each link to the
direct PBR GLB download URL and pulls the file, no sign-in needed.

Usage:
    python tripo_pull.py <share-url-or-uuid> [more ...] [-o OUTDIR] [--all]

Examples:
    python tripo_pull.py https://studio.tripo3d.ai/3d-model/bfd5233e-4451-4494-8643-fdceceb2e184
    python tripo_pull.py bfd5233e-4451-4494-8643-fdceceb2e184 0309c453-c6df-4077-87b6-346d14cad382 -o ./models
    python tripo_pull.py <uuid> --all        # also pull point-cloud GLB + preview images

Output per model:
    <outdir>/<slug>.glb            the PBR textured model (meshopt-compressed GLB)
    <outdir>/<slug>.manifest.json  metadata: urls, sizes, verification, source link

Exit codes: 0 = all pulled+verified, 1 = one or more failed.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

API = "https://api.tripo3d.ai/v2/studio/project/detail/v3/{}"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def extract_uuid(token):
    m = UUID_RE.search(token)
    if not m:
        raise ValueError(f"no Tripo project UUID found in: {token}")
    return m.group(0).lower()


def slugify(name, fallback):
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s or fallback.replace("-", "")[:12]


def api_get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def download(url, dest, timeout=300):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    return os.path.getsize(dest)


def verify_glb(path):
    """Returns dict with structural info; raises on invalid file."""
    with open(path, "rb") as f:
        magic = f.read(4)
    if magic != b"glTF":
        raise ValueError(f"{path}: bad magic {magic!r}, not a GLB")
    info = {"magic": "glTF", "bytes": os.path.getsize(path)}
    try:
        from pygltflib import GLTF2
        g = GLTF2().load(path)
        info.update({
            "meshes": len(g.meshes),
            "primitives": sum(len(m.primitives) for m in g.meshes),
            "materials": len(g.materials),
            "textures": len(g.textures),
            "images": [i.mimeType for i in g.images],
            "extensionsRequired": list(g.extensionsRequired or []),
        })
    except ImportError:
        info["structure"] = "unchecked (pygltflib not installed)"
    return info


def pull_one(token, outdir, pull_all=False):
    uuid = extract_uuid(token)
    share_url = f"https://studio.tripo3d.ai/3d-model/{uuid}"
    resp = api_get(API.format(uuid))
    if resp.get("code") != 0:
        raise RuntimeError(f"API error for {uuid}: {resp.get('message')}")
    data = resp["data"]
    slug = slugify(data.get("project_name", ""), uuid)
    model_url = data.get("model_url")
    if not model_url:
        raise RuntimeError(f"no model_url in API response for {uuid}")

    os.makedirs(outdir, exist_ok=True)
    glb_path = os.path.join(outdir, f"{slug}.glb")
    print(f"[{slug}] downloading PBR model...", flush=True)
    download(model_url, glb_path)
    verification = verify_glb(glb_path)
    print(f"[{slug}] {verification['bytes']} bytes, "
          f"{verification.get('meshes', '?')} mesh(es), "
          f"{verification.get('textures', '?')} texture(s) — OK", flush=True)

    extras = {}
    if pull_all:
        for key, suffix in (("point_cloud_model_url", "pointcloud"),
                            ("rendered_image", "preview")):
            url = data.get(key)
            if not url:
                continue
            ext = ".glb" if key.endswith("model_url") else ".jpg"
            dest = os.path.join(outdir, f"{slug}.{suffix}{ext}")
            print(f"[{slug}] downloading {suffix}...", flush=True)
            extras[suffix] = {"path": dest, "bytes": download(url, dest)}

    manifest = {
        "slug": slug,
        "project_uuid": uuid,
        "project_name": data.get("project_name"),
        "share_url": share_url,
        "owner": data.get("owner_name"),
        "published": data.get("created_at") or data.get("publish_time"),
        "model_url": model_url,
        "glb_path": glb_path,
        "verification": verification,
        "extras": extras,
    }
    mpath = os.path.join(outdir, f"{slug}.manifest.json")
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[{slug}] manifest -> {mpath}", flush=True)
    return manifest


def main():
    ap = argparse.ArgumentParser(description="Pull 3D models from Tripo Studio public share links.")
    ap.add_argument("inputs", nargs="+", help="share URL(s) or project UUID(s)")
    ap.add_argument("-o", "--outdir", default="tripo_models", help="output directory")
    ap.add_argument("--all", action="store_true", help="also pull point-cloud model + preview image")
    args = ap.parse_args()

    ok, failed = 0, []
    for token in args.inputs:
        try:
            pull_one(token, args.outdir, pull_all=args.all)
            ok += 1
        except Exception as e:
            print(f"[FAIL] {token}: {e}", file=sys.stderr, flush=True)
            failed.append(token)
    print(f"\ndone: {ok} pulled, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
