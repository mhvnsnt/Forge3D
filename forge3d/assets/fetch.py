"""CC0 asset fetcher with provenance recording.

Every download records {file, source, source_url, license, downloaded_at,
sha256} into cc0_manifest.json next to the files — so any asset's origin
and license can be audited later. Only blanket-CC0 sources (see
cc0_sources.blanket_cc0()) are auto-fetchable; per-asset sites require an
explicit verified URL + license note.

No secrets, no keys: all endpoints used here are keyless.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path
from zipfile import ZipFile

from .cc0_sources import CC0Source, blanket_cc0, get

UA = {"User-Agent": "Forge3D/0.1 (CC0 asset research; contact via repo)"}
MANIFEST = "cc0_manifest.json"


class FetchError(RuntimeError):
    """Raised when a fetch genuinely fails. Never masked."""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dest: Path, timeout: int = 300) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:  # noqa: BLE001
        raise FetchError(f"download failed {url}: {e}")
    if dest.stat().st_size < 64:
        raise FetchError(f"download suspiciously small: {url}")
    return dest


def _manifest_entry(out_dir: Path, rel: str, source: CC0Source,
                    source_url: str) -> dict:
    p = out_dir / rel
    return {
        "file": rel,
        "source": source.id,
        "source_name": source.name,
        "source_url": source_url,
        "license": source.license,
        "license_verified": source.verified,
        "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "sha256": _sha256(p),
        "bytes": p.stat().st_size,
    }


def _record(out_dir: Path, entries: list[dict]) -> Path:
    out_dir = Path(out_dir)
    mp = out_dir / MANIFEST
    existing = json.loads(mp.read_text()) if mp.exists() else []
    existing.extend(entries)
    mp.write_text(json.dumps(existing, indent=2))
    return mp


def fetch_ambientcg(asset_id: str, out_dir: str | Path,
                    res: str = "1K", kind: str = "JPG") -> Path:
    """Download an ambientCG PBR material zip and extract it.

    e.g. asset_id="Wood096" -> Wood096_1K-JPG.zip (Color/Normal/Roughness/...)
    """
    source = get("ambientcg")
    out_dir = Path(out_dir)
    fname = f"{asset_id}_{res}-{kind}.zip"
    url = f"https://ambientcg.com/get?file={fname}"
    dest = out_dir / asset_id / fname
    _download(url, dest)
    entries = [_manifest_entry(out_dir, f"{asset_id}/{fname}", source,
                               f"https://ambientcg.com/a/{asset_id}")]
    with ZipFile(dest) as z:
        z.extractall(out_dir / asset_id)
        for name in z.namelist():
            if name.endswith("/"):
                continue
            entries.append(_manifest_entry(out_dir, f"{asset_id}/{name}",
                                           source,
                                           f"https://ambientcg.com/a/{asset_id}"))
    _record(out_dir, entries)
    return out_dir / asset_id


def fetch_polyhaven_file(asset_id: str, out_dir: str | Path,
                         variant: str = "hdri", res: str = "1k",
                         fmt: str = "hdr") -> Path:
    """Download one Poly Haven file via the keyless file API.

    e.g. fetch_polyhaven_file("studio_small_09") -> 1k HDR.
    Direct dl.polyhaven.org download (not the live API) per their ToS note.
    """
    source = get("polyhaven")
    out_dir = Path(out_dir)
    api_url = f"https://api.polyhaven.org/files/{asset_id}"
    info = None
    last_err: Exception | None = None
    for _ in range(3):  # api.polyhaven.org is intermittently 522
        req = urllib.request.Request(api_url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                info = json.loads(r.read())
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            import time as _t
            _t.sleep(10)
    if info is None:
        raise FetchError(
            f"polyhaven file API failed for {asset_id} (3 tries): {last_err}")
    try:
        entry = info[variant][res][fmt]
    except KeyError:
        avail = {k: list(v) for k, v in info.items() if isinstance(v, dict)}
        raise FetchError(
            f"polyhaven {asset_id}: no {variant}/{res}/{fmt}; have {avail}")
    url, md5 = entry["url"], entry.get("md5", "")
    fname = url.rsplit("/", 1)[-1].split("?")[0]
    fname = urllib.request.unquote(fname)
    dest = out_dir / asset_id / fname
    _download(url, dest, timeout=600)
    if md5:
        import hashlib as _hl
        got = _hl.md5(dest.read_bytes()).hexdigest()
        if got != md5:
            raise FetchError(f"polyhaven {asset_id}: md5 mismatch")
    _record(out_dir, [_manifest_entry(out_dir, f"{asset_id}/{fname}", source,
                                      f"https://polyhaven.com/a/{asset_id}")])
    return dest


def fetch_kenney_pack(pack_slug: str, out_dir: str | Path) -> Path:
    """Download a Kenney pack zip by scraping the asset page for the zip URL.

    e.g. pack_slug="city-kit-commercial". Raises FetchError if no zip found.
    """
    import re
    source = get("kenney")
    out_dir = Path(out_dir)
    page_url = f"https://kenney.nl/assets/{pack_slug}"
    req = urllib.request.Request(page_url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        raise FetchError(f"kenney page fetch failed {page_url}: {e}")
    zips = re.findall(r'https://kenney\.nl/media/pages/assets/[^"\s]+\.zip', html)
    if not zips:
        raise FetchError(f"kenney {pack_slug}: no zip URL found on page")
    url = zips[0]
    fname = url.rsplit("/", 1)[-1]
    dest = out_dir / pack_slug / fname
    _download(url, dest, timeout=600)
    entries = [_manifest_entry(out_dir, f"{pack_slug}/{fname}", source, page_url)]
    with ZipFile(dest) as z:
        z.extractall(out_dir / pack_slug)
        for name in z.namelist():
            if not name.endswith("/"):
                entries.append(_manifest_entry(out_dir, f"{pack_slug}/{name}",
                                               source, page_url))
    _record(out_dir, entries)
    return out_dir / pack_slug


def list_sources() -> list[dict]:
    """Machine-readable registry (for docs/tooling)."""
    return [
        {"id": s.id, "name": s.name, "url": s.url, "license": s.license,
         "commercial_ok": s.commercial_ok, "content": s.content,
         "verified": s.verified}
        for s in blanket_cc0()
    ]
