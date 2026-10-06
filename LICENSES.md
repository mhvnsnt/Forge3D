# LICENSES.md — license manifest

Every pulled tool, model, and API dependency used by Forge3D. Updated whenever a
provider is added. Owner rule: GPL/AGPL-viral code is quarantined out of the
shipped tree; pre-ship license audit is mandatory. All rows verified 2026-10-06
against official repos (see docs/research/).

| Component | License | Commercial use | Notes |
|---|---|---|---|
| Forge3D own code (`forge3d/`, docs, configs) | MIT (TBD — owner picks at ship) | yes | prototype stage |
| TripoSR (Stability AI × Tripo) | MIT (code + weights) | yes | CPU-capable fallback provider |
| Stable Fast 3D | Stability AI Community License | yes, <$1M annual revenue | default GPU provider; gated HF checkpoint |
| TripoSG (VAST AI) | MIT | yes | shape fallback; geometry-only |
| Unique3D | MIT | yes | hero-asset provider (16 GB) |
| TRELLIS.2 (Microsoft) | MIT (code + weights) | yes | hero provider; 24 GB VRAM |
| Hunyuan3D-Paint (Tencent) | Tencent Hunyuan 3D Community License | gated: EU/UK/SK excluded, 1M MAU cap, attribution required | texture stage only |
| Pollinations.ai (image + 3D API) | service terms | check terms before shipping | free key; 3D costs Pollen |
| Tripo3D API Platform | service terms, free tier CC BY 4.0 non-commercial | NO on free tier | prototyping/reference only |
| Meshy AI | service terms, free tier CC BY 4.0 | yes with attribution | web UI only (no free API) |

## Hard no-gos (never wired as providers)
- Zero123++ weights — CC-BY-NC 4.0 (non-commercial)
- Hunyuan3D-2/2.1 weights — territory exclusion, 1M MAU gate, no-training-use clause
- nvdiffrast-dependent TRELLIS v1 pipeline — NVIDIA non-commercial source license (use TRELLIS.2/Hi3DGen instead)

## Quarantine policy
- `quarantine/` holds any GPL/AGPL-licensed code. NOTHING in `forge3d/` may import from it.
- Non-commercial-licensed models are research-only providers, clearly marked, never in the default `auto` path for money work.
