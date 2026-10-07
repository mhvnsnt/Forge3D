# CC0_SOURCES.md — public-domain/CC0 3D asset sources

Owner directive 2026-10-07: CC0 / public domain ONLY — no NC, no SA.
Every blanket-CC0 entry below was verified LIVE against the source's own
license page on 2026-10-07. Re-verify before any bulk pull; terms move.

Machine-readable registry: `forge3d/assets/cc0_sources.py`.
Fetcher with provenance manifest: `forge3d/assets/fetch.py`
(every download → `cc0_manifest.json`: file, source, source_url, license,
license_verified date, sha256).

## Blanket CC0 (safe for automated fetching)

| Source | Content | License (verified live 2026-10-07) | Fetch path |
|---|---|---|---|
| [Poly Haven](https://polyhaven.org) | PBR textures (8K+), HDRI, 3D models | **CC0-1.0** — [polyhaven.com/license](https://polyhaven.com/license): "All assets … are all licensed as CC0" | `fetch_polyhaven_file()` via `api.polyhaven.org/files/<id>` (keyless, send User-Agent) → direct `dl.polyhaven.org` download. NOTE: separate API ToS — commercial *API* use needs sponsorship; direct downloads are the automation path. API was intermittently 522 on 2026-10-07 (retries built in). |
| [ambientCG](https://ambientcg.com) | PBR materials (Color/Normal/Displacement/Roughness/AO), models, HDRIs | **CC0-1.0** — [docs.ambientcg.com/license](https://docs.ambientcg.com/license/): "All ambientCG assets are provided under CC0 1.0 … You can include the raw files in your project, for example a video game." | `fetch_ambientcg()` — `https://ambientcg.com/get?file=<ID>_1K-JPG.zip` (verified live: Wood096 → real PBR set). Catalog API: `ambientcg.com/api/v2/full_json` (keyless). |
| [Quaternius](https://quaternius.com) | stylized low-poly packs: rigged characters, 250+ animation clips (Universal Animation Library), environments, props | **CC0** — each pack page states "Free to use in personal, educational and commercial projects. (CC0 License)" (verified live on pack pages 2026-10-07) | manual / page-scrape zips (no API). 60–70% of each pack free. |
| [Kenney](https://kenney.nl/assets) | low-poly 3D kits (city, nature, dungeon, characters), 2D, UI, audio | **CC0** — asset pages carry "License: Creative Commons CC0" (verified live 2026-10-07) | `fetch_kenney_pack()` scrapes `kenney.nl/media/pages/assets/<pack>/…zip`. City kits directly serve AshLane urban-district dressing. |
| [KayKit](https://github.com/KayKit-Game-Assets) | stylized low-poly characters, dungeon/city builder bits | **CC0-1.0** per repo LICENSE (GitHub org; itch pages state CC0) | `https://codeload.github.com/KayKit-Game-Assets/<repo>/zip/refs/heads/main`. ⚠️ OWNER LAW: no KayKit chibi characters inside AshLane — prototyping/tooling only. |
| [cgbookcase](https://www.cgbookcase.com) | photoscanned PBR sets (4K/8K), decals | **CC0** per site terms (secondary-verified 2026-10-07) | manual; recheck terms page before first bulk pull. |
| [TextureCan](https://texturecan.com) | PBR textures + SBSAR procedural sources | **CC0** per terms page (secondary-verified 2026-10-07; footer "All rights reserved" is NOT the grant — the terms page is) | manual; recheck before first bulk pull. |
| [NASA 3D Resources](https://science.nasa.gov/3d-resources) | spacecraft/rover/astronaut/terrain models | **US federal public domain** | manual; skip any entry crediting contractors. |

## Per-asset license — check every item, never auto-fetch blind

| Source | License posture |
|---|---|
| [Poly Pizza](https://poly.pizza) | per-model CC0 or CC-BY — assert the `license` field per model (free API key for API v1.1) |
| [Khronos glTF-Sample-Models](https://github.com/KhronosGroup/glTF-Sample-Models) | per-model (mostly CC0, some CC-BY) — read the model's license file; best for PBR pipeline conformance tests |
| [Smithsonian Open Access 3D](https://3d.si.edu) | per-record — use ONLY CC0-designated records; third-party rights can apply elsewhere |

## Explicitly excluded (not CC0/PD)

ShareTextures ("custom CC0" banning redistribution), FreePBR (custom grant, not CC0),
Sketchfab/BlenderKit/OpenGameArt/itch.io (mixed per-asset — CC0-filtered one-offs only,
never blanket), Fab/Quixel Megascans (no redistribution), Mixamo (no raw redistribution),
textures.com/CGTrader free sections (royalty-free ≠ CC0).
