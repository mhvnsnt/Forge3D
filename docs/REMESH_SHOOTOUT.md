# REMESH_SHOOTOUT.md — remesh contender results (2026-10-07)

Input: `docs/stage-evidence/trellis2-full/trellis2-concept2-high.glb`
(raw trellis-2-high: 59,766 verts / 93,234 faces / NOT watertight /
24,012 boundary edges / 1 degenerate face / tri aspect p99 3.44 /
~28k non-6-valence poles of 59k verts — typical generated-mesh topology).

Harness: `forge3d/pipelines/remesh.py` (`--mode voxel|cleanup`) +
`forge3d/pipelines/quadremesh.py` (`quad_remesh_glb`). Full numbers:
`docs/stage-evidence/remesh/shootout-report.json`.

## Contenders

| | bmesh cleanup | voxel remesh | Quadriflow |
|---|---|---|---|
| Time | 23 s | 11 s | 25 s (refused) |
| Faces | 93,137 (preserved) | 8,032 (destroyed detail) | n/a |
| Watertight | **No** (25,749 boundary edges — worse) | No (16,064 boundary; UVs destroyed) | n/a |
| Degenerate faces | 1 → **0** | 0 | n/a |
| Tri aspect p99 | 3.44 → 3.44 (mean fixed: slivers dissolved) | 4.78 | n/a |
| UVs/materials | preserved | **destroyed** | n/a |

### Bugs found and fixed during the shootout
- `remesh.py` used Blender 4.2 enum `'VOXELS'` — correct enum is `'VOXEL'`
  (crashed with `enum "VOXELS" not found`). Fixed.
- `quadremesh.py` verification gate works: raises
  `ProviderError: quadremesh: output only 0.0% quads — remesh did not take`
  instead of shipping the un-remeshed mesh. Good.

## Verdict

**No single winner — the shootout revealed a pipeline ORDER, not a champion:**

1. **bmesh cleanup** = the default *repair* stage. It preserves the surface,
   kills degenerates, keeps UVs/materials. It does NOT close holes
   (boundary edges went 24,012 → 25,749 — merging can expose new boundaries).
2. **voxel remesh** = wrong tool for hero meshes at this scale. At
   voxel_size 0.015 on a ~1-unit character it collapses to 8k faces, destroys
   UVs, and still isn't watertight. Only useful as a last-resort watertight
   rebuild at fine voxel sizes — not the default path.
3. **Quadriflow** = the animation-topology winner, but it **silently refuses
   non-manifold input** (Blender's `quadriflow_remesh` returns CANCELLED
   without raising on 24k-boundary-edge soup). It needs a watertight mesh
   FIRST.

**Wired order:** `cleanup` (repair) → `watertight` (hole-fill, new
`--mode watertight` in `remesh.py`) → `quadriflow` (animation-ready quads,
only after watertight verifies True). The pipeline fails LOUDLY if
watertight isn't achieved — never silently ships triangle soup as "clean".

## Open work
- Quadriflow-on-watertight proof is pending the `watertight` stage landing
  (this doc updates when it does).
- Voxel at fine sizes (0.005–0.008) untested as an alternative hole-closer;
  deprioritized (destroys UVs — unacceptable for textured hero meshes).
