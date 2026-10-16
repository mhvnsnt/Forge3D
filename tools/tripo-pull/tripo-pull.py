#!/usr/bin/env python3
"""
tripo-pull — Download 3D models from Tripo3D Studio.

Tripo locked free exports behind a paywall / their site has Cloudflare and
auth issues, but models shared via public links expose their files through
Tripo's public project-detail API. This tool resolves each link to the
direct download URL and pulls the file. No sign-in, no browser, no credits.

Strategies (tried in order):
  1. Public project-detail API  (no auth — works for public share links)
  2. Page HTML scrape           (fallback — extracts embedded model URLs)
  3. Official Tripo API         (TRIPO_API_KEY env var — for private models)

Formats: GLB is what Tripo serves. Use --to fbx,obj,usdz to convert locally
via Blender (headless) after download.

Usage:
    python tripo-pull.py <share-url-or-uuid> [more ...] [-o OUTDIR] [--all] [--to FORMATS]

Examples:
    python tripo-pull.py https://studio.tripo3d.ai/3d-model/67a6f309-0ac2-4c56-92b8-a4ea3e72bf46
    python tripo-pull.py 67a6f309-0ac2-4c56-92b8-a4ea3e72bf46 bfd5233e-4451-4494-8643-fdceceb2e184 -o ./models
    python tripo-pull.py <uuid> --all                    # also pull point-cloud + preview
    python tripo-pull.py <uuid> --to fbx                 # convert GLB -> FBX via Blender
    python tripo-pull.py <uuid> --to fbx,obj,usdz        # convert to multiple formats

Output per model:
    <outdir>/<slug>.glb              the PBR textured model (meshopt GLB)
    <outdir>/<slug>.manifest.json    metadata: urls, sizes, verification, source link
    <outdir>/<slug>.fbx ...          converted formats (only with --to)

Exit codes: 0 = all pulled+verified, 1 = one or more failed.
Stdlib only — no pip install needed.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error

# ---------------------------------------------------------------- endpoints

PUBLIC_API = "https://api.tripo3d.ai/v2/studio/project/detail/v3/{}"
STUDIO_PAGE = "https://studio.tripo3d.ai/3d-model/{}"
OFFICIAL_API_TASK = "https://api.tripo3d.ai/v2/openapi/task/{}"

UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)

USER_AGENTS = [
    # Rotate through these on retry — Cloudflare sometimes blocks one UA
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) "
    "Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

CONVERT_FORMATS = ("fbx", "obj", "usdz", "stl", "ply", "x3d")

# ---------------------------------------------------------------- helpers


def extract_uuid(token):
    m = UUID_RE.search(token)
    if not m:
        raise ValueError(
            f"no Tripo project UUID found in: {token}\n"
            f"  expected a share link like "
            f"https://studio.tripo3d.ai/3d-model/<uuid> or a bare UUID")
    return m.group(0).lower()


def slugify(name, fallback):
    s = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")
    return s or fallback.replace("-", "")[:12]


def http_get(url, timeout=30, binary=False, _ua_idx=0):
    """GET with UA rotation on 403/blocked responses."""
    last_err = None
    for attempt in range(len(USER_AGENTS)):
        ua = USER_AGENTS[(_ua_idx + attempt) % len(USER_AGENTS)]
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (403, 429, 503):
                time.sleep(1 + attempt)  # back off, try next UA
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            time.sleep(1 + attempt)
            continue
    raise RuntimeError(
        f"GET failed after {len(USER_AGENTS)} attempts: {url}\n"
        f"  last error: {last_err}\n"
        f"  Tripo may be rate-limiting or Cloudflare-blocking this IP. "
        f"Wait a few minutes and retry.")


def api_get_json(url, timeout=30):
    raw = http_get(url, timeout=timeout)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"API returned non-JSON (site may be showing a challenge page): "
            f"{url}\n  {e}")


# ---------------------------------------------------------------- strategies

def strategy_public_api(uuid):
    """Strategy 1: public project-detail API. No auth needed."""
    resp = api_get_json(PUBLIC_API.format(uuid))
    if resp.get("code") != 0:
        raise RuntimeError(
            f"public API error for {uuid}: {resp.get('message')}\n"
            f"  (code {resp.get('code')}) — the model may be private, "
            f"deleted, or the share link may be wrong.")
    data = resp.get("data") or {}
    model_url = data.get("model_url")
    if not model_url:
        raise RuntimeError(
            f"public API returned no model_url for {uuid}.\n"
            f"  The model may not have a public share link. "
            f"In Tripo Studio, open the model and use Share to make "
            f"a public link, then retry.")
    return {
        "project_name": data.get("project_name") or data.get("model_name_user_renamed"),
        "owner": data.get("owner_name"),
        "published": data.get("created_at") or data.get("publish_time"),
        "model_url": model_url,
        "point_cloud_model_url": data.get("point_cloud_model_url"),
        "preview_image": data.get("rendered_image") or data.get("cover_image"),
        "source": "public-api",
    }


def strategy_page_scrape(uuid):
    """Strategy 2: scrape the Studio page HTML for embedded model URLs."""
    html = http_get(STUDIO_PAGE.format(uuid), timeout=30)
    # Look for direct model file URLs in page bundles / JSON blobs
    patterns = [
        r'https?://[^\s"\'<>]+\.glb[^\s"\'<>]*',
        r'"model_url"\s*:\s*"([^"]+)"',
        r'"download[^"]*"\s*:\s*"(https?://[^"]+)"',
    ]
    for pat in patterns:
        for m in re.finditer(pat, html):
            url = m.group(1) if m.lastindex else m.group(0)
            url = url.replace("\\u0026", "&").replace("\\/", "/")
            if ".glb" in url or "tripo" in url:
                # Try to pull a project name too
                nm = re.search(r'"project_name"\s*:\s*"([^"]+)"', html)
                return {
                    "project_name": nm.group(1) if nm else None,
                    "owner": None,
                    "published": None,
                    "model_url": url,
                    "point_cloud_model_url": None,
                    "preview_image": None,
                    "source": "page-scrape",
                }
    raise RuntimeError(
        f"page scrape found no model URLs for {uuid}.\n"
        f"  Tripo may have changed their page structure, or the model "
        f"page requires sign-in (Cloudflare challenge).")


def strategy_official_api(uuid):
    """Strategy 3: official Tripo API with TRIPO_API_KEY (for private models)."""
    key = os.environ.get("TRIPO_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            f"official API needs TRIPO_API_KEY env var (not set).\n"
            f"  Get a key at https://platform.tripo3d.ai/ -> API keys, then:\n"
            f"    export TRIPO_API_KEY='tsk_...'\n"
            f"  Note: the public strategies above usually work without a key "
            f"for shared models.")
    req = urllib.request.Request(
        OFFICIAL_API_TASK.format(uuid),
        headers={"User-Agent": USER_AGENTS[0], "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(
            f"official API HTTP {e.code} for {uuid}: {body}\n"
            f"  Check that TRIPO_API_KEY is valid.")
    if resp.get("code") != 0:
        raise RuntimeError(
            f"official API error: {resp.get('message')} (code {resp.get('code')})")
    data = resp.get("data") or {}
    # Official API task objects carry output model URLs under various keys
    model_url = (data.get("model_url") or data.get("pbr_model")
                 or (data.get("output") or {}).get("pbr_model"))
    if not model_url:
        raise RuntimeError(
            f"official API returned no downloadable model URL for {uuid}.")
    return {
        "project_name": None,
        "owner": None,
        "published": None,
        "model_url": model_url,
        "point_cloud_model_url": None,
        "preview_image": None,
        "source": "official-api",
    }


STRATEGIES = [
    ("public-api", strategy_public_api),
    ("page-scrape", strategy_page_scrape),
    ("official-api", strategy_official_api),
]


def resolve_model(uuid):
    """Try each strategy in order; return (info, strategy_name)."""
    errors = []
    for name, fn in STRATEGIES:
        try:
            return fn(uuid), name
        except Exception as e:
            errors.append(f"[{name}] {e}")
    raise RuntimeError(
        f"All download strategies failed for {uuid}:\n\n"
        + "\n\n".join(errors) +
        f"\n\nWhat to try:\n"
        f"  1. Open https://studio.tripo3d.ai/3d-model/{uuid} in a browser — "
        f"if you see a Cloudflare check, complete it, then re-run.\n"
        f"  2. In Tripo Studio, Share the model to get a fresh public link.\n"
        f"  3. Set TRIPO_API_KEY for the official API route.")


# ---------------------------------------------------------------- download

def download(url, dest, timeout=600):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENTS[0]})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, \
                open(dest, "wb") as f:
            total = r.getheader("Content-Length")
            total = int(total) if total else 0
            done = 0
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done * 100 // total
                    print(f"\r    {done//1024//1024}MB / "
                          f"{total//1024//1024}MB ({pct}%)",
                          end="", flush=True)
            print()
    except urllib.error.HTTPError as e:
        # Signed CloudFront URLs expire — tell the user to re-run
        if e.code in (403, 410):
            raise RuntimeError(
                f"download URL expired (HTTP {e.code}). Tripo signs URLs "
                f"with a short lifetime — just re-run tripo-pull to get "
                f"a fresh URL.")
        raise
    return os.path.getsize(dest)


def verify_glb(path):
    """Structural check. Returns info dict; raises on invalid file."""
    with open(path, "rb") as f:
        magic = f.read(4)
    if magic != b"glTF":
        raise ValueError(f"{path}: bad magic {magic!r} — not a GLB file. "
                         f"Tripo may have returned an error page instead "
                         f"of model data.")
    info = {"magic": "glTF", "bytes": os.path.getsize(path)}
    try:
        from pygltflib import GLTF2
        g = GLTF2().load(path)
        info.update({
            "meshes": len(g.meshes or []),
            "primitives": sum(len(m.primitives) for m in (g.meshes or [])),
            "materials": len(g.materials or []),
            "textures": len(g.textures or []),
        })
    except ImportError:
        info["structure"] = "unchecked (pygltflib not installed)"
    return info


# ---------------------------------------------------------------- blender

def find_blender():
    """Locate a Blender binary. Returns path or None."""
    env = os.environ.get("BLENDER_BIN", "").strip()
    if env and os.path.isfile(env) and os.access(env, os.X_OK):
        return env
    which = shutil.which("blender")
    if which:
        return which
    candidates = [
        os.path.expanduser("~/workspace/tools/blender/blender-4.0.2-linux-x64/blender"),
        os.path.expanduser("~/workspace/tools/blender/blender"),
        "/usr/bin/blender",
        "/opt/blender/blender",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def convert_with_blender(blender_bin, src_glb, out_path, fmt):
    """Convert GLB -> fmt using headless Blender. Returns True on success."""
    exporters = {
        "fbx": "bpy.ops.export_scene.fbx(filepath=r'''{o}''')",
        "obj": "bpy.ops.wm.obj_export(filepath=r'''{o}''')",
        "usdz": "bpy.ops.wm.usd_export(filepath=r'''{o}''')",
        "stl": "bpy.ops.wm.stl_export(filepath=r'''{o}''')",
        "ply": "bpy.ops.wm.ply_export(filepath=r'''{o}''')",
        "x3d": "bpy.ops.export_scene.x3d(filepath=r'''{o}''')",
    }
    if fmt not in exporters:
        print(f"    [convert] unknown format '{fmt}' — skipping", flush=True)
        return False
    py_expr = (
        "import bpy, sys; "
        "bpy.ops.wm.read_factory_settings(use_empty=True); "
        f"bpy.ops.import_scene.gltf(filepath=r'''{src_glb}'''); "
        + exporters[fmt].format(o=out_path)
    )
    cmd = [blender_bin, "-b", "--python-expr", py_expr]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print(f"    [convert] Blender timed out on {fmt}", flush=True)
        return False
    if r.returncode != 0 or not os.path.isfile(out_path):
        err = (r.stderr or "")[-500:]
        print(f"    [convert] Blender failed for {fmt}: {err}", flush=True)
        return False
    return True


# ---------------------------------------------------------------- pull

def pull_one(token, outdir, pull_all=False, to_formats=()):
    uuid = extract_uuid(token)
    share_url = STUDIO_PAGE.format(uuid)
    print(f"[{uuid}] resolving...", flush=True)
    info, used = resolve_model(uuid)
    slug = slugify(info.get("project_name"), uuid)
    print(f"[{slug}] via {used}: "
          f"{info.get('project_name') or 'unnamed model'}"
          + (f" by {info['owner']}" if info.get("owner") else ""),
          flush=True)

    os.makedirs(outdir, exist_ok=True)
    glb_path = os.path.join(outdir, f"{slug}.glb")
    print(f"[{slug}] downloading PBR model...", flush=True)
    try:
        download(info["model_url"], glb_path)
    except Exception:
        # Never leave a partial file behind
        if os.path.exists(glb_path):
            os.remove(glb_path)
        raise
    verification = verify_glb(glb_path)
    print(f"[{slug}] {verification['bytes'] // 1024 // 1024}MB, "
          f"{verification.get('meshes', '?')} mesh(es), "
          f"{verification.get('textures', '?')} texture(s) — OK", flush=True)

    extras = {}
    if pull_all:
        for key, suffix in (("point_cloud_model_url", "pointcloud"),
                            ("preview_image", "preview")):
            url = info.get(key)
            if not url:
                continue
            ext = ".glb" if key.endswith("model_url") else ".jpg"
            dest = os.path.join(outdir, f"{slug}.{suffix}{ext}")
            try:
                print(f"[{slug}] downloading {suffix}...", flush=True)
                extras[suffix] = {"path": dest, "bytes": download(url, dest)}
            except Exception as e:
                print(f"[{slug}] {suffix} failed (non-fatal): {e}",
                      flush=True)

    converted = {}
    if to_formats:
        blender_bin = find_blender()
        if not blender_bin:
            print(f"[{slug}] --to requested but no Blender found.\n"
                  f"  Install Blender 4.2+ or set BLENDER_BIN. "
                  f"Skipping conversion.", flush=True)
        else:
            print(f"[{slug}] converting via Blender: "
                  f"{', '.join(to_formats)}...", flush=True)
            for fmt in to_formats:
                out_path = os.path.join(outdir, f"{slug}.{fmt}")
                ok = convert_with_blender(blender_bin, glb_path,
                                          out_path, fmt)
                if ok:
                    converted[fmt] = {"path": out_path,
                                      "bytes": os.path.getsize(out_path)}
                    print(f"    {fmt} OK "
                          f"({converted[fmt]['bytes']//1024}KB)", flush=True)

    manifest = {
        "slug": slug,
        "project_uuid": uuid,
        "project_name": info.get("project_name"),
        "share_url": share_url,
        "owner": info.get("owner"),
        "published": info.get("published"),
        "resolved_via": used,
        "model_url": info.get("model_url"),
        "glb_path": glb_path,
        "verification": verification,
        "extras": extras,
        "converted": converted,
    }
    mpath = os.path.join(outdir, f"{slug}.manifest.json")
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[{slug}] manifest -> {mpath}", flush=True)
    return manifest


def main():
    ap = argparse.ArgumentParser(
        description="Download 3D models from Tripo3D Studio "
                    "(public share links, no sign-in needed).")
    ap.add_argument("inputs", nargs="+",
                    help="share URL(s) or project UUID(s)")
    ap.add_argument("-o", "--outdir", default="tripo_models",
                    help="output directory (default: tripo_models)")
    ap.add_argument("--all", action="store_true",
                    help="also pull point-cloud model + preview image")
    ap.add_argument("--to", default="",
                    help="convert GLB via Blender: comma-separated list "
                         f"from {', '.join(CONVERT_FORMATS)} "
                         "(e.g. --to fbx or --to fbx,obj,usdz)")
    args = ap.parse_args()

    to_formats = []
    if args.to:
        for f in args.to.split(","):
            f = f.strip().lower().lstrip(".")
            if f not in CONVERT_FORMATS:
                print(f"error: unknown format '{f}'. "
                      f"Choose from: {', '.join(CONVERT_FORMATS)}",
                      file=sys.stderr)
                return 2
            if f not in to_formats:
                to_formats.append(f)

    ok, failed = 0, []
    for token in args.inputs:
        try:
            pull_one(token, args.outdir,
                     pull_all=args.all, to_formats=to_formats)
            ok += 1
        except Exception as e:
            # Never crash — explain and move on
            print(f"\n[FAIL] {token}:\n  {e}\n", file=sys.stderr, flush=True)
            failed.append(token)
    print(f"done: {ok} pulled, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())