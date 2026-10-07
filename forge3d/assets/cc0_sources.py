"""CC0 / public-domain 3D asset source registry for Forge3D.

Every entry verified LIVE against the source's own license page on
2026-10-07 (see docs/CC0_SOURCES.md for the verification log).
LICENSE RULE (owner): CC0 / public domain ONLY — no NC, no SA, no
per-asset gambles on the blanket entries. Per-asset-license sites are
marked as such and are NOT auto-fetched.

These sources strengthen generation: PBR textures for the texture stage,
HDRI for lookdev/lighting reference, and CC0 base meshes/props for
kitbashing, retargeting practice, and scene dressing.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CC0Source:
    id: str
    name: str
    url: str
    license: str            # SPDX-ish; all CC0-1.0 or public-domain here
    commercial_ok: bool
    redistribution_ok: bool
    content: str            # what you get
    formats: tuple[str, ...] = ()
    api: str = ""           # keyless API endpoint, if any
    download_pattern: str = ""  # URL pattern for direct fetch
    notes: str = ""
    verified: str = "2026-10-07"  # date terms were read live


SOURCES: tuple[CC0Source, ...] = (
    CC0Source(
        id="polyhaven",
        name="Poly Haven",
        url="https://polyhaven.org",
        license="CC0-1.0",
        commercial_ok=True,
        redistribution_ok=True,
        content="photoscanned PBR textures (8K+), HDRI environments, 3D models",
        formats=("hdr", "exr", "jpg", "png", "blend", "gltf", "fbx"),
        api="https://api.polyhaven.org (keyless; send unique User-Agent)",
        download_pattern="https://dl.polyhaven.org/file/ph-assets/<path>",
        notes=("Blanket CC0 on ALL assets (verified at polyhaven.com/license). "
               "Separate API ToS: commercial *API* use needs sponsorship — use "
               "direct dl.polyhaven.org downloads for automation, not the live API."),
    ),
    CC0Source(
        id="ambientcg",
        name="ambientCG",
        url="https://ambientcg.com",
        license="CC0-1.0",
        commercial_ok=True,
        redistribution_ok=True,
        content="PBR materials (Color/Normal/Displacement/Roughness/AO), models, HDRIs, terrain",
        formats=("jpg", "png", "zip", "blend", "usdc"),
        api="https://ambientcg.com/api/v2/full_json (keyless)",
        download_pattern="https://ambientcg.com/get?file=<ID>_1K-JPG.zip",
        notes=("Blanket CC0 incl. preview renders (verified at "
               "docs.ambientcg.com/license). 1K-JPG zips ~5MB; PNG up to 8K. "
               "Short links: ambientcg.com/a/<ID>."),
    ),
    CC0Source(
        id="quaternius",
        name="Quaternius",
        url="https://quaternius.com",
        license="CC0-1.0",
        commercial_ok=True,
        redistribution_ok=True,
        content="stylized low-poly game packs: characters (rigged/retargetable), "
                "animations (Universal Animation Library 250+ clips), environments, props",
        formats=("glb", "gltf", "fbx", "obj", "blend"),
        notes=("Each pack page states 'Free to use in personal, educational and "
               "commercial projects. (CC0 License)' (verified live 2026-10-07). "
               "60-70% of each pack free; rest on itch/Patreon. Direct zips from "
               "pack pages; no API — manual or page-scrape fetch."),
    ),
    CC0Source(
        id="kenney",
        name="Kenney",
        url="https://kenney.nl/assets",
        license="CC0-1.0",
        commercial_ok=True,
        redistribution_ok=True,
        content="low-poly 3D kits (city, nature, characters, dungeon), 2D, UI, audio, textures",
        formats=("glb", "fbx", "obj", "png", "ogg", "wav"),
        notes=("Asset pages carry 'License: Creative Commons CC0' "
               "(verified live on kenney.nl asset page 2026-10-07). "
               "Zips at kenney.nl/media/pages/assets/<pack>/…kenney_*.zip. "
               "City kits directly serve AshLane's urban-district dressing."),
    ),
    CC0Source(
        id="kaykit",
        name="KayKit (Kay Lousberg)",
        url="https://github.com/KayKit-Game-Assets",
        license="CC0-1.0",
        commercial_ok=True,
        redistribution_ok=True,
        content="stylized low-poly characters, dungeon/city builder bits, animations",
        formats=("gltf", "fbx", "obj", "blend"),
        download_pattern="https://codeload.github.com/KayKit-Game-Assets/<repo>/zip/refs/heads/main",
        notes=("CC0-1.0 per repo LICENSE (GitHub org). NOTE: owner law bans KayKit "
               "(KK) chibi characters inside AshLane — use for prototyping/tooling "
               "only, never ship KK-derived characters in the game."),
    ),
    CC0Source(
        id="cgbookcase",
        name="cgbookcase",
        url="https://www.cgbookcase.com",
        license="CC0-1.0",
        commercial_ok=True,
        redistribution_ok=True,
        content="photoscanned PBR texture sets (4K/8K) + decals",
        formats=("jpg", "png", "zip"),
        notes="CC0 per site terms (secondary-verified 2026-10-07; recheck the terms page before first bulk pull).",
    ),
    CC0Source(
        id="texturecan",
        name="TextureCan",
        url="https://texturecan.com",
        license="CC0-1.0",
        commercial_ok=True,
        redistribution_ok=True,
        content="PBR textures incl. SBSAR procedural sources",
        formats=("sbsar", "jpg", "png", "zip"),
        notes="CC0 per terms page (secondary-verified 2026-10-07; footer says 'All rights reserved' — the terms page is the grant; recheck before first bulk pull).",
    ),
    CC0Source(
        id="nasa3d",
        name="NASA 3D Resources",
        url="https://science.nasa.gov/3d-resources",
        license="public-domain (US federal)",
        commercial_ok=True,
        redistribution_ok=True,
        content="spacecraft, rover, astronaut, terrain 3D models",
        formats=("stl", "obj", "blend", "fbx"),
        notes=("US federal work = public domain. Verify per-model: a few gallery "
               "entries credit contractors — skip those."),
    ),
)

# Sources that are USEFUL but NOT blanket-CC0: per-asset license check required.
# Listed for completeness; the fetcher refuses them unless a CC0 asset URL is
# handed to it explicitly with per-asset verification recorded.
PER_ASSET_SOURCES: tuple[CC0Source, ...] = (
    CC0Source(
        id="polypizza",
        name="Poly Pizza",
        url="https://poly.pizza",
        license="per-asset (CC0 or CC-BY)",
        commercial_ok=True,
        redistribution_ok=True,
        content="searchable low-poly model index (Google Poly rescue + community)",
        formats=("glb",),
        api="https://poly.pizza API v1.1 (free key)",
        notes="ASSERT the per-model license field before every download; CC0 ones are fine, CC-BY needs attribution.",
    ),
    CC0Source(
        id="khronos-samples",
        name="Khronos glTF-Sample-Models",
        url="https://github.com/KhronosGroup/glTF-Sample-Models",
        license="per-model (mostly CC0, some CC-BY)",
        commercial_ok=True,
        redistribution_ok=True,
        content="reference PBR glTF models — best for pipeline conformance testing",
        formats=("gltf", "glb"),
        notes="Read the per-model license file; CC0 models are safe, CC-BY needs attribution.",
    ),
    CC0Source(
        id="smithsonian",
        name="Smithsonian Open Access 3D",
        url="https://3d.si.edu",
        license="per-record (CC0-designated only)",
        commercial_ok=True,
        redistribution_ok=True,
        content="museum artifacts, specimens — reference/prop material",
        formats=("glb", "obj"),
        notes="Use ONLY records explicitly designated CC0; third-party rights can apply to other records.",
    ),
)


def get(source_id: str) -> CC0Source:
    for s in SOURCES + PER_ASSET_SOURCES:
        if s.id == source_id:
            return s
    raise KeyError(f"unknown CC0 source: {source_id}")


def blanket_cc0() -> tuple[CC0Source, ...]:
    """Sources safe for automated fetching without per-asset checks."""
    return SOURCES
