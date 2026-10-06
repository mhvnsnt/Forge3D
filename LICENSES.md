# LICENSES.md — license manifest

Every pulled tool, model, and API dependency used by Forge3D. Updated whenever a
provider is added. Owner rule: GPL/AGPL-viral code is quarantined out of the
shipped tree; pre-ship license audit is mandatory.

| Component | License | Commercial use | Notes |
|---|---|---|---|
| Forge3D own code (`forge3d/`, docs, configs) | MIT (TBD — owner picks at ship) | yes | prototype stage |
| TripoSR (Stability AI) | MIT | yes | local provider |
| _TBD — filled by Phase 0 inventory_ | | | |

## Quarantine policy
- `quarantine/` holds any GPL/AGPL-licensed code. NOTHING in `forge3d/` may import from it.
- Non-commercial-licensed models (e.g. anything CC-BY-NC / Stability non-commercial) are research-only providers, clearly marked, never in the default `auto` path for money work.
