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

## NO-SWEEP-INFLIGHT LAW (owner 2026-10-16)
NEVER delete, move, or "clean up" anything that is downloading, uploading, rendering, extracting, or otherwise in-flight — no matter how full the disk gets. Download folders, staging dirs, partial files (.part, .kaggle-partial, .aria2, split chunks), and anything an active lane is writing to are SACRED. The disk-space-guardian, watchdog, and every agent must treat in-flight work as untouchable. If disk is critical: pause NEW downloads, surface the alert to the owner, NEVER sweep in-flight work. A deleted partial can destroy unrecoverable progress (mirrors die, sessions expire, quota burns).

## NEVER-DELETE-GAME-FILES LAW — AMENDMENT (owner 2026-10-16)
Game files (ISOs, ROMs, game archives, teardown sources) are NEVER auto-deleted. They stay until verified on TERABOX and the owner confirms. AMENDMENT: when a game file IS verified on BOTH TeraBox and GitHub, proactively surface it to the owner with the verification evidence (exact TeraBox folder + piece count, exact GitHub release/repo) and ask "verified on both stores — can I delete the local copy?" He decides per file. The law is NOT relaxed — default is still never delete — but verified files must be brought to him instead of sitting silently on disk.

**ESCALATION (owner 2026-10-16):** First time a game file is verified on both stores: surface it with evidence, ask "can I delete this?", wait for his okay. If he does not answer and it keeps getting surfaced as verified (2nd or 3rd time) with thorough re-verification — delete it, do not ask forever. Silence after repeated asks is the go-ahead.

**RELAXATION (owner 2026-10-16 — supersedes the amendment/escalation):** When a game files FULL working folder is verified BYTE-IDENTICAL on BOTH GitHub and TeraBox, it MAY be deleted from local disk without asking. Conditions: (1) byte-identical full folder on both stores, hash/size verified; (2) NO teardown/decoding/decryption actively in progress on it right now; (3) if teardown is not 100% per the TEARDOWN-COMPLETION LAW, log it on ~/workspace/agent-ops/TEARDOWN-IDLE-QUEUE.md first — idle-time work, thread never lost; (4) log every deletion + backup locations.

## GOOGLE SIGN-IN BLANKET PERMISSION (owner 2026-10-15, reaffirmed 2026-10-16)
The owner said: "Use the Google sign in to sign into anything you need to." STANDING blanket authorization — account fmmg.mars@gmail.com. Sign in with his Google account without asking when a service needs it (TeraBox, Kaggle, Colab, anything). Only ask him if Google demands his phone 2FA. Never let a sign-in wall stall work.

## TERABOX SESSION KEEPER (owner 2026-10-16 — "fix this thing that keeps signing me out")
TeraBox web auth rides on the `ndus` cookie — LONG-LIVED, does not expire on its own (only an explicit Sign Out kills it). Sign-outs on our side come from the leased Chromium profile being reset on runtime restarts, NOT natural expiry. The fix: (1) API upload path `~/workspace/tools/terabox-uploader/tbupload.py` (4MB chunks, auto-verify, no 225MB cap) replaces browser-task uploads — one-time cookie setup via browser task → setup_creds.py → .creds.json (chmod 600, gitignored, never logged/committed); (2) `terabox-session-keeper` cron every 6h: `tbupload.py resolve` → healthy = quiet, dead = browser task re-verifies terabox.com (re-sign via Google per blanket permission above), grabs fresh cookies, rewrites creds, verifies; (3) never trust the watchdog's read-only terabox.com probe — TRY-BEFORE-YOU-FLAG LAW: only a failed REAL attempt counts as logged out. Full design: ~/workspace/agent-ops/TERABOX-SESSION-KEEPER.md.

## CONTINUOUS RESEARCH + PULL-IN LAW (owner 2026-10-16 ~12:36 EDT)
Keep doing deep research on EVERYTHING related to all our work, and keep pulling in what you find — open source, experimental, new, old, legacy, production-grade, 2026 cutting-edge. Keep branching vertically and horizontally and expanding everything.
1. RESEARCH FIRST, real research (GitHub trending, 2026 roundups, HN, papers) — never guess from training data.
2. Pull in open source first. For non-open-source: document the license status honestly; do NOT crack commercial software or bypass paywalls. Some things get documented but NOT pulled (non-commercial / region-excluded licenses).
3. Wire it up: install, test, document. Push via branch → PR → merge, ONLY when green and non-destructive. NEVER clobber anyone's work — conflicts keep both sides, red CI stays open with a comment naming the blocker.
4. PULL-STRAIGHT-TO-STORE: clone into repo checkouts, wire up there, push. No local disk hoarding.
5. Log everything pulled: what, where from, license, where it landed.
This is standing and continuous — highest-value gaps first, then keep branching outward. Workflow: ~/workspace/agent-ops/CONTINUOUS-RESEARCH-PULLIN-WORKFLOW.md.
