# AGENTS.md — Forge3D

Standing rules for every agent working in this repo. These come from the owner (Real) and are non-negotiable.

## Secrets
- NEVER commit secrets to this repo. No API keys, tokens, passwords, or credentials in any file. API keys go in the Secure Vault / environment variables ONLY (`FORGE3D_<PROVIDER>_KEY`).
- If you find a secret in the working tree, delete it and rotate it — do not report the value anywhere.

## No fakes, ever
- No fake/placeholder gameplay, no mock outputs presented as real. A generated model must be a real file produced by a real provider. If a provider is stubbed, the stub must FAIL LOUDLY, not return a placeholder mesh.
- Honesty rule: anything built for money must actually work.

## Docs
- Production/development decisions get documented in-repo (owner's doc rule). Architecture and inventory notes live in `docs/`.
- Never invent canon, characters, or based-on relationships in prompts or docs.

## Licensing
- Prototype freely, but GPL/AGPL-viral code is QUARANTINED out of the shipped tree (`quarantine/`, never imported by `pipelines/`). Every pulled tool's license is recorded in `LICENSES.md`. Pre-ship license audit is mandatory.

## Checkpoints
- Long-running workers: FIRST action is writing `~/workspace/agent-ops/checkpoints/<name>.json` per the checkpoint schema, heartbeat `updated_at` every ≤10 min, commit incrementally, mark done at end.

## Verification
- A worker's "verified" is a CLAIM. Deliverable reports must include proof: which files exist, which tests ran and passed, sample outputs. No proof = not done.
