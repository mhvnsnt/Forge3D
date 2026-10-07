"""glbutil.py — shared GLB parse/append/write helpers for Forge3D stages.

Extracted so that texture.py, upscale.py, lod.py and normalmap.py all share
one GLB round-trip implementation (extend, never duplicate).
"""
from __future__ import annotations

import io
import json
import struct
from pathlib import Path

from PIL import Image


def parse_glb(path: Path) -> tuple[dict, bytes]:
    """Return (glTF JSON dict, BIN chunk bytes) for a .glb file."""
    data = Path(path).read_bytes()
    if data[:4] != b"glTF":
        raise ValueError(f"not a GLB: {path}")
    jlen = struct.unpack("<I", data[12:16])[0]
    doc = json.loads(data[20:20 + jlen])
    binoff = 20 + jlen
    blen = struct.unpack("<I", data[binoff:binoff + 4])[0]
    blob = data[binoff + 8:binoff + 8 + blen]
    return doc, blob


def iter_embedded_images(doc: dict, bin_blob: bytes):
    """Yield (image_index, PIL.Image, mime) for embedded buffer-view images."""
    images = doc.get("images", [])
    buffer_views = doc.get("bufferViews", [])
    for idx, img in enumerate(images):
        bv = img.get("bufferView")
        if bv is None:
            continue
        view = buffer_views[bv]
        start = view.get("byteOffset", 0)
        end = start + view["byteLength"]
        try:
            pil = Image.open(io.BytesIO(bin_blob[start:end])).convert("RGB")
        except Exception:
            continue
        yield idx, pil, img.get("mimeType", "image/png")


def append_images(doc: dict, blob: bytes,
                 payloads: list[tuple[bytes, str]]) -> tuple[dict, bytes, list[int]]:
    """Append PNG/JPG payloads to the BIN chunk; register bufferViews+images.

    Returns (doc, new_blob, new_image_indices).
    """
    if "bufferViews" not in doc:
        doc["bufferViews"] = []
    if "images" not in doc:
        doc["images"] = []
    if "buffers" not in doc:
        doc["buffers"] = [{"byteLength": len(blob)}]
    new_blob = bytearray(blob)
    indices = []
    for payload, mime in payloads:
        pad = (-len(new_blob)) % 4
        new_blob.extend(b"\x00" * pad)
        off = len(new_blob)
        new_blob.extend(payload)
        doc["bufferViews"].append(
            {"buffer": 0, "byteOffset": off, "byteLength": len(payload)})
        doc["images"].append(
            {"bufferView": len(doc["bufferViews"]) - 1,
             "mimeType": mime, "name": f"forge3d_stage_{len(doc['images'])}"})
        indices.append(len(doc["images"]) - 1)
    doc["buffers"][0]["byteLength"] = len(new_blob)
    return doc, bytes(new_blob), indices


def repoint_image(doc: dict, image_index: int, payload: bytes,
                  blob: bytearray, mime: str = "image/png") -> bytearray:
    """Replace an existing image's buffer-view contents in place (append).

    The old bytes are left orphaned in the blob (harmless); the image's
    bufferView is repointed at the new payload.
    """
    views = doc["bufferViews"]
    images = doc["images"]
    pad = (-len(blob)) % 4
    blob.extend(b"\x00" * pad)
    off = len(blob)
    blob.extend(payload)
    bv = images[image_index]["bufferView"]
    views[bv]["byteOffset"] = off
    views[bv]["byteLength"] = len(payload)
    images[image_index]["mimeType"] = mime
    return blob


def write_glb(doc: dict, blob: bytes, out_path: Path) -> Path:
    """Write a GLB from a glTF JSON dict + BIN bytes. Returns out_path."""
    new_doc = json.dumps(doc, separators=(",", ":")).encode()
    pad = (-len(new_doc)) % 4
    new_doc += b" " * pad  # space-pad per glTF spec
    blob = bytes(blob)
    bpad = (-len(blob)) % 4
    blob = blob + b"\x00" * bpad
    total = 12 + 8 + len(new_doc) + 8 + len(blob)
    header = struct.pack("<III", 0x46546C67, 2, total)
    jchunk = struct.pack("<II", len(new_doc), 0x4E4F534A) + new_doc
    bchunk = struct.pack("<II", len(blob), 0x004E4942) + blob
    out_path = Path(out_path)
    out_path.write_bytes(header + jchunk + bchunk)
    return out_path
