# HARDWARE_MATRIX.md — what runs where (honest, measured)

The sandbox VM has NO GPU. The pipeline runs where the owner has hardware.
This matrix is the truth, not a wishlist.

## Backends

| Backend | Free Colab T4 (16 GB) | Kaggle T4x2 (2×16 GB) | Lightning AI / A100 (40/80 GB) | This sandbox (CPU) |
|---|---|---|---|---|
| **TripoSR** (MIT) | ✅ YES — the primary free path. ~6 GB VRAM, seconds/image | ✅ YES | ✅ YES | ✅ YES — slow (2–10 min/image), proven 2026-10-07 |
| **TRELLIS.2** (MIT) | ⚠️ EXPERIMENTAL — official need is 24 GB; community fp16 path *may* fit 16 GB. Not guaranteed. | ⚠️ MAYBE — 2×T4 doesn't pool VRAM; single 16 GB card same as Colab | ✅ YES — the intended home (verified by MS on A100/H100) | ❌ NO — needs CUDA + custom ops |
| Hunyuan3D 2.1 | ❌ NO (needs ~21–29 GB for full pipeline; license-excluded anyway) | ❌ NO | ⚠️ shape-only ~10 GB possible; full needs 48 GB class | ❌ NO |

## Recommended paths

1. **Iterate free (today):** Colab free T4 + TripoSR → textured GLB in seconds.
   Notebook: `notebooks/Forge3D_Free_Pipeline.ipynb`.
2. **Quality pass:** Kaggle (30 GPU hrs/week, T4x2) or Lightning AI credits for
   TRELLIS.2 → native PBR GLB.
3. **Flagship (owner decision):** Hunyuan3D 2.1 full pipeline wants a 48 GB
   card (A100/A6000) AND a license decision (Tencent community license —
   see docs/WEIGHTS.md). Not in the pipeline until the owner approves.

## Pipeline stages (all CPU-capable)

| Stage | CPU sandbox | Notes |
|---|---|---|
| PBR texturing (vertex-color bake) | ✅ Blender headless | local Blender 4.0.2 via `FORGE3D_BLENDER_BIN` |
| Quad remesh | ✅ Instant Meshes binary / Blender fallback | `forge3d/pipelines/quadremesh.py` |
| Auto-rig (Blender auto-skin) | ✅ Blender headless | `forge3d/blender/stage.py::auto_skin` → `retarget_58` to the 58-bone WH skeleton |
| Auto-rig (instance-rig) | ⚠️ needs its venv + system GL libs | fails loudly without them |
| Export GLB/OBJ | ✅ trimesh | headless |
| Export FBX | ✅ Blender headless | no FBX SDK needed |

## Reality checks (measured, not claimed)

- TripoSR CPU: ~45 s/mesh (2-core VM, May-2026 test) to 2–10 min depending on
  RAM pressure; needs ~2.5 GB free RAM (`--wait-for-ram` gate exists).
- TRELLIS.2 inference on H100: ~3 s at 512³, ~17 s at 1024³, ~60 s at 1536³
  (upstream numbers).
- No stage in this repo phones home, needs an API key, or costs money.
  $0 forever is structural, not promotional.
