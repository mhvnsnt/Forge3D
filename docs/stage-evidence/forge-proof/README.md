# GNM Head Attachment — Forge Proof (2026-10-07)

**Test subject:** Forge3D-generated body (NOT a Bannon asset — owner TEST-MODEL RULE).
- Source: `runs/closeout/body128/triposr-concept1.glb`
- Provider: TripoSR (local, CPU, mc_resolution=128, no bg-removal)
- Input: `runs/gen1/concept1.jpg` (hoooded street figure concept)
- Raw output: 6,634 verts / 13,444 tris, lying along X, 164 floaters
- Prepped: largest component (11,150 tris), stood up (+90° Z), floored → `body_standing.glb`

**Attach:** `forge3d/body/attach_head.py` (identity_seed=3, facing_degrees=0)
- Neck: geometric detection (deepest-significant XZ cross-section minimum, top 35%)
  - neck_y=0.857, neck_radius=0.067, neck_center=(-0.006, 0.010)
  - neck_source: geometric (generated body has no rig — head-joint fallback N/A)
- Head: GNM (Apache-2.0), scale_xz=0.853 / scale_y=0.388, seated 0.012 embed
- Seam: 1,160 head verts cosine-blended toward body neck cylinder
- Output: `body_gnm_head.glb` — 22,924 verts / 45,502 tris (5,103 body + 17,821 head)

**Files:**
- `before.png` — generated body, 4 angles (white void, full framing)
- `after.png` — body + GNM head, 4 angles
- `body_gnm_head.glb` / `.json` — merged model + stats

**Known limits:** 128³ body is blobby; TripoSR baked a ground-disc artifact at the feet;
head Y-scale compresses to fit the hood volume (non-uniform scale). Mechanics proven;
quality scales with provider resolution.
