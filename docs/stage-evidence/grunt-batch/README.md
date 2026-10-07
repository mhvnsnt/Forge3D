# Grunt Batch — AshLane low/mid-level characters (2026-10-07)

7 grunt archetypes for AshLane: 3 factionless street bodies + 4 faction-oriented
(Onyx street faction, Dynasty Authority, Kennedy corporate security, SWMG street affiliate).
Grounded Urban Reign/Def Jam street level; faction identifiers are subtle
(patches, armbands) per canon — no matching uniforms.

## Result

| Archetype | Faction | Tier | Backbone | Faces | Status |
|---|---|---|---|---|---|
| grunt_onyx — Street Faction Enforcer | Onyx street faction | mid | trellis-2-high (0.35 pollen) | 96,599 | **GOOD — roster candidate** |
| grunt_hustler — Corner Hustler | factionless | low | local TripoSR | 98,812 | RELIEF-FAILED |
| grunt_bouncer — Door Heavy | factionless | low-mid | local TripoSR | 125,450 | RELIEF-FAILED |
| grunt_alley — Alley Brawler | factionless | low | local TripoSR | 90,652 | RELIEF-FAILED |
| grunt_dynasty — Patrol Officer | Dynasty Authority | mid | local TripoSR | 92,980 | RELIEF-FAILED |
| grunt_kennedy — Corporate Security | Kennedy corpsec | mid | local TripoSR | 102,626 | RELIEF-FAILED |
| grunt_lookout — Block Lookout | SWMG affiliate | low | local TripoSR | 95,352 | RELIEF-FAILED |

Pollen: spent 0.35 / ~0.54 → ~0.19 remaining (insufficient for another gen).

## Honest finding

Local TripoSR on these concepts produces **flat bas-reliefs, not characters**
(verified on all 6 + a no-bg-removal 128³ control run — same failure).
The reliefs are documented by the preview PNGs; their GLBs were not committed.
This is a backbone limitation, not a settings issue. Grunt 3D needs API/GPU
backbones (trellis tiers) or the SF3D-space path once its REST API works.

## Files

- `<slug>.concept.jpg` — concept art (keyless Pollinations image; 3 needed
  single-view regen + left-half crop after the model emitted diptychs)
- `grunt_onyx.glb` + `grunt_onyx.preview.png` — the one good model
- `<slug>.preview.png` — 4-angle white-void previews (0/90/180/270)
- `stats.json` — measurements + statuses
- `concepts.json` — archetype/faction/tier index
