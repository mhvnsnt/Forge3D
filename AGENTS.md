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

## Muse training pack
Muse/Ashes and every agent: read the [Muse training pack](https://github.com/mhvnsnt/money-machine-hq/tree/main/docs/muse-training-pack) (instructions, pre-flight checklist, real before/after examples, right-way videos) before every job.

## No-data-loss rules (MANDATORY)
Read and follow [`docs/NO-DATA-LOSS-RULES.md`](docs/NO-DATA-LOSS-RULES.md) (canonical: mhvnsnt/agent-ops). No force-push, no rebase/amend of pushed work, no history rewrite, no branch/asset deletion without backup + owner approval, PRs only, empty D-filter + gitleaks + green CI before merge, push incrementally, keep WORKLOG, back up and sha256-verify before disk cleanup, never touch other agents' or Muse's work.
## ANTI-CLOBBER LAW (owner 2026-10-17 — the DXMMII 54k-file deletion)
On 2026-10-17 an agent committed from a working tree missing 54,456 files. `git add -A` swept every missing file in as a deletion, and the commit rode into main through PR #221. The agent's real work was 105 files. Nobody checked the deletion list before committing or merging. Canonical text: mhvnsnt/agent-ops `docs/ANTI-CLOBBER-LAW.md`.
1. Read your deletions before every commit (`git status` + `git diff --cached --name-status`). Every deleted file must be something your task meant to delete. Unexplained deletions = STOP, do not commit. Assume your environment is corrupted — do not try to "fix" it by committing.
2. Never `git add -A` / `git commit -a` in a tree you didn't fully populate yourself. Verify tree completeness (file counts vs the remote branch) first.
3. Say what you deleted in the commit message (which dirs/file types, and why). Message/diff mismatch on deletions = hard failure, do not push.
4. Deletion circuit breaker: any deletion outside your task's scope blocks the commit. Stop and report instead of committing.
5. The merger reads the PR's deletion list and matches it against the task. Unexplained deletions block the merge. A giant diff's deletions are never "probably fine".
