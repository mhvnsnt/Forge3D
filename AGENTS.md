# AGENTS.md — Forge3D

# ANTI-CLOBBER LAWS (owner 2026-10-17 — the DXMMII 54k-file wipe)

On 2026-10-17, commit cd3bf38 ("DXMMII limb system", PR mhvnsnt/western-heart#221) deleted 54,456 files against 105 additions. The commit message said nothing about deletions. Nobody read the deletion list before merging. The repo was 99.996% gone. These laws exist so that never happens again. Every agent, every repo, every commit, every merge.

1. DELETION CHECK — before every commit, read `git status` and the diff stat. Every deleted file in the diff must be something your task intended to delete. A deleted file your task did not delete on purpose means STOP: do not commit, do not push, report what you found. The working tree is wrong, not the task.

2. OWN THE TREE — never `git add -A` or `git commit -a` in a working tree you did not fully populate yourself. Before committing, verify the tree is complete: file counts match the remote branch you branched from (your task's own additions and changes aside). A tree missing files you didn't delete is damaged — don't sweep it into history.

3. CIRCUIT BREAKER — if a commit would delete more than a handful of files outside your task's scope, STOP and report instead of committing. A big deletion count is a hard stop, not a warning to scroll past. Committing unexplained deletions "and letting someone else figure it out" is the failure.

4. SAY THE DELETIONS — the commit message names every deletion. One deleted file gets one line; many deleted files get a count plus what category went. A commit whose message and diff disagree is a hard failure — don't push it.

5. MERGE GATE — the merger reads the PR's deletion list against the task description before merging. Unexplained deletions block the merge. "CI is green" does not excuse a deletion list the task never asked for. A red, conflicting, or lossy PR stays open with a comment naming the blocker.

(Co-authored with Aider and Copilot per the ALL-AGENTS-WORKFLOW LAW. Cline's seat stays open — its free-tier API was down during drafting.)


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
