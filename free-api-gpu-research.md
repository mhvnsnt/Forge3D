# Forge3D — Free 3D API Tiers & Free GPU Compute Research
Researched 2026-10-06 via live web search (official docs, pricing pages, 2026 reviews). Quotas change often — re-verify before depending on any number.

## PART A — Free 3D-generation API tiers

### 1. Meshy AI — Free tier
- **Quota:** 100 credits/month, no credit card, reset 1st of month. 10 model downloads/month on free.
- **Cost/model:** ~30 credits per textured text-to-3D → **~3 finished models/month** free.
- **Capabilities:** text-to-3D, image-to-3D, AI texturing (to 8K PBR), auto-rigging, animation (rig/animate cheap: 3–10 cr).
- **Signup:** email/Google/Discord, no card.
- **Commercial:** Free outputs under **CC BY 4.0 — commercial use OK with attribution**. Paid plans transfer ownership.
- **API access:** API/CLI/MCP only on paid plans (Pro $20/mo = 1,000 cr). Free = web UI only.
- Sources: meshy.ai/blog/best-free-3d-modeling-software; mobileappdaily.com/product-review/meshy-ai; thetoolsverse.com/tools/meshy-ai

### 2. Tripo3D (tripo3d.ai + platform.tripo3d.ai) — Free tier
- **Quota (Studio web UI):** 200 credits/month, no card (~8 models; real cost is higher per usable game asset).
- **API Platform Basic:** 300 credits/month free, 1 concurrent task (separate credit pool from Studio). Text-to-3D ~30 cr/model → **~10 models/month** via API.
- **Capabilities:** text-to-3D, image-to-3D (single-image free; multi-view is Pro), segmentation, 4K textures, auto-rigging.
- **Signup:** email/Google/Apple/Discord, no card. Key format `tsk_...`.
- **Commercial:** Free = **public models, NON-commercial (CC BY 4.0)** — nothing free-tier ships. Commercial unlocks at Pro ($19.90–20/mo).
- Sources: dev.to/titusbrett Tripo review (15 days ago); github.com/kevinten-ai/mcp-3d-gen README

### 3. Hyper3D Rodin — Free tier
- **Quota:** $0 free plan with a **small trial pool (~10 credits; 0.5 credits per confirmed result ≈ ~20 confirms)**; generate-for-free-before-confirmation workflow. Also a 7-day Creator trial for new accounts.
- **Capabilities:** text-to-3D, image-to-3D, multi-image fusion (paid), Smart Low-Poly, HD/4K textures, best-in-class topology per reviews.
- **Signup:** account + likely card for trial.
- **Commercial:** free outputs are personal/trial; full rights on paid (Creator $30/mo ~60 models; direct credits $1.50/credit).
- **API access:** only on Business ($120/mo). No free API.
- Sources: hyper3d.ai/pricing (fetched <1h ago); winningpc.com Hyper3D coupons Oct 2026; dev.to mesh vs tripo vs rodin shootout

### 4. Spline AI — Free tier: NOT a 3D-generation option
- **Free plan = core editor with NO AI 3D generation** (verified by eweek 2026). AI credits (2,000/mo) require Hobby $12/mo+ or a $5/mo add-on; GLB/USDZ export is paid-tier only.
- Capabilities where paid: text-to-3D (returns 4 variants), front-facing image-to-3D, web-embed focus — not a mesh pipeline for games anyway.
- Verdict: skip for Forge3D.
- Sources: eweek.com/artificial-intelligence/best-ai-3d-generators/; aitools.fyi/spline-ai

### 5. Pollinations.ai — YES it does 3D (but no longer fully keyless for it)
- **Image generation:** still free/keyless on the public `image.pollinations.ai` endpoint (Flux/Turbo), no signup.
- **3D generation:** exists — `GET https://gen.pollinations.ai/3d/{prompt}` returns **GLB**, plus async `POST /3d/generations`. Requires an **API key** (free at enter.pollinations.ai/keys, `pk_`/`sk_`) and **Pollen** billing ($1 ≈ 1 Pollen).
- **3D models & prices:** `trellis-2-low` $0.24/gen (default, works with **Quest Pollen** — free pollen earned by completing quests), `trellis-2-medium` $0.29, `trellis-2-high` $0.35; `hyper3d/rodin-2.5` $0.40/gen (**Paid Pollen only**); tripoSR/sf3d confirmed at $0.02/gen.
- **Key detail:** Trellis 2 family **ignores text prompts — image input only** (image-to-3D). Text→3D route goes image-first.
- **Commercial terms:** Quest Pollen is earn-only (can't cash out); paid-model outputs require paid pollen. Check enter.pollinations.ai terms before shipping assets.
- Sources: github.com/pollinations/pollinations PR #12048 (3D feature); AGENTS.md forks (Billing/Pollen); samucastudent/pollinations 3d-generation.md docs

### 6. Hugging Face Inference serverless — NO 3D models served
- Free tier: **$0.10/month in auto-replenished credits**, models <10GB, shared queues, cold starts.
- **No text-to-3D/image-to-3D model is deployed on any Inference Provider** — confirmed on microsoft/TRELLIS-image-large's HF page: "This model isn't deployed by any Inference Provider."
- Workaround: **HF Spaces (ZeroGPU)** — see Part B. Not the serverless API.
- Sources: huggingface.co/microsoft/TRELLIS-image-large; awesome-free-llm-apis READMEs

### 7. fal.ai / Replicate / Stability AI
- **fal.ai:** No true free tier — prepaid credits only (one source reports ~$10 signup credit; official docs don't guarantee an amount). Sandbox gives 15 free generations/day on selected models without an account. Hosts 3D: `fal-ai/hyper3d/rodin/v2.5/fast` (the model Pollinations routes Rodin through). No card-free monthly allowance.
- **Replicate:** **No free tier, no trial credits** — pay-as-you-go from $0.000225/sec (T4-class). Not free.
- **Stability AI:** **25 one-time signup credits** (no recurring free tier; Google-login-only reported). No 3D endpoint — image/audio APIs only; Stable 3D is discontinued. Not a 3D option.
- Sources: costbench.com fal/Replicate pricing; github.com/idoy12/awesome-free-ai-apis; github.com/parthalon025/six-flags-sa free-tier catalog (2026-08-20)

### Bonus find (not requested but directly relevant)
- **SupaVoxel:** **3 models/day free, no credit card** (~90/month). Image-to-3D, GLB output, 1 credit/model. Narrowest tool (no rigging), but the cheapest free volume in the market. Cheapest commercial tier ~$25/yr.
- Source: dev.to mesh-vs-tripo-vs-hyper3d-vs-supavoxel shootout (15 days ago)

## PART B — Free GPU compute

### Kaggle — best free GPU path
- **Quota (verified 2026): 30 GPU-hours/week**, resets weekly; 20 TPU-hours/week.
- **GPUs:** dual Tesla T4 (16GB each); P100 **retired Sep 2026** (one source). TPU v5e-8 (128GB) for JAX/Keras.
- **Sessions:** up to 12h, 20-min idle while editing; "Save & Run All" runs with browser closed.
- **Signup:** Google account + **phone/SMS verification** to unlock GPU/internet. No card.
- Note: Colab Pro/Pro+ linkers get 15/30 extra GPU-h/week (paid route).
- Sources: medium.com Nehal Garg (Sep 21, 2026); github.com/shubhampandey567/ascent free-compute-apis.md (docs checked 2026-09-24); youtube.com/watch?v=Depcu3GX4-A (Oct 3, 2026 test)

### Google Colab free tier
- **GPU:** usually Tesla T4 (15GB), dynamic/unpublished availability; K80 largely phased out.
- **Limits:** ~12h max session, ~90-min idle timeout; **100 compute units/month** free; Pro ($12.67/mo) = 500 units, Pro+ ($49.99) = 1,000 units.
- **Rules:** notebooks only on free tier — no web-UI hosting, no SSH, no crypto; machines wiped on disconnect, persist to Drive.
- **Signup:** Google account, no card.
- Sources: research.google.com/colaboratory/faq.html (via spheron.network blog, Oct 2026); deploybase.ai (Mar 2026)

### Hugging Face Spaces (ZeroGPU) — verified 2026
- **Free account: 5 GPU-minutes/day** on ZeroGPU (half RTX Pro 6000 Blackwell, 48GB VRAM); PRO ($9/mo) = 40 min/day.
- **MAJOR 2026 change:** creating compute Spaces now requires a paid plan — but **free accounts in good standing (verified email, account >30 days) can host up to 2 ZeroGPU Gradio Spaces** for free.
- Agent angle: Gradio Spaces expose an HTTP API — agents can call a hosted TRELLIS/TripoSR Space from CPU VMs within the 5-min/day quota.
- Sources: huggingface hub-docs spaces-zerogpu.md (5-min table); discuss.huggingface.co forum; github.com/shubhampandey567/ascent notes

### Lightning AI
- **Free plan:** "up to 30 credits to start" (~75 T4-hours at $0.55/hr) — **reads as one-time starter grant, monthly refresh unconfirmed**. 1 free Studio 24/7 (restart every 4h), 32-core CPU studios, 50GB storage, 15 req/min model APIs.
- **Signup:** no credit card (some guides say phone verification possible).
- Real Linux dev environment (git/venv/SSH/VS Code) vs Colab/Kaggle notebook kernels — better for agent-driven workflows.
- Sources: github.com/shubhampandey567/ascent free-compute-apis.md (pricing rendered 2026-09-24); github.com/au-nlp/2026 COMPUTE_RESOURCES.md

## CPU-only reality check (this VM: 2 vCPU, 8GB RAM)
- **TripoSR "2–10 min/image on CPU" guidance is stale.** A May 2026 CPU test (2-core VM): init 5–10s, LRM forward ~14s, mesh extraction (mc-res 256) ~23s, GLB export <1s → **~45s total per mesh**. Output: watertight GLB with vertex colors, ~35k faces, back side hallucinated.
- **SF3D** (TripoSR successor): similar CPU profile, 120K-poly output.
- Shap-E on CPU = hours — skip. **TRELLIS/Hunyuan3D = GPU-only** (shape gen needs 10GB VRAM; full shape+texture 29GB).
- Genuinely CPU-usable today: TripoSR/SF3D image-to-3D base meshes, rembg background removal, trimesh decimation/repair, weight-transfer rigging, GLB manipulation.
- Sources: github.com/aliter230880/unity session-log-2026-05-13.md; github.com/safebots/infrastructure model-runners/triposr; github.com/claudao01/triposr-docker-deployment

## RANKED RECOMMENDATIONS

### Best free API for occasional character-mesh generation
1. **Pollinations 3D (trellis-2-low)** — API-first, free signup key, Quest Pollen earned free via quests at $0.24/gen, GLB output, Trellis quality tier. Best for automated pipelines. (Image-to-3D only; generate the reference image with the free keyless image endpoint.)
2. **Tripo web free tier** — 200 cr/mo (~8 models), no card, text+image-to-3D with the best all-in-one pipeline (segmentation, rigging). **Non-commercial, public models** — prototyping/reference only.
3. **Meshy free tier** — 100 cr/mo (~3 textured models), no card, **CC BY 4.0 = commercial use allowed with attribution** — the most commercially usable free tier. API paid-only.
4. **Hyper3D Rodin free trial** — ~10 trial credits, superb topology, but thin pool and API only on $120/mo Business. One-shot hero models only.
5. Bonus: **SupaVoxel** — 3 models/day (~90/mo) no card for pure volume; no rigging.
Avoid: Spline AI (no AI gen on free plan), fal.ai/Replicate/Stability AI (no genuine free tier for 3D), HF serverless API (no 3D models deployed).

### Best free GPU path for TRELLIS / Hunyuan3D
1. **Kaggle** — 30 GPU-h/week, dual T4 16GB, no card, 12h sessions. Run TRELLIS image-to-3D or Hunyuan3D shape-only; texture pass needs 21GB+ VRAM (fp8/low-res or Colab A100 alternative). Phone verification required.
2. **Google Colab free** — T4, ~100 compute units/mo, simplest for one-off runs; dynamic availability is the risk.
3. **Lightning AI** — ~30 starter credits (~75 T4-hours), persistent Linux + SSH/VS Code; best if agents need a real dev box rather than notebooks.
4. **HF ZeroGPU Spaces** — 5 min/day free (host 2 Gradio Spaces after 30-day account age); agent-callable API for single generations. Queueing is the tax.

### Genuinely usable from this CPU-only VM today
**TripoSR (MIT): ~45s per mesh on this exact class of VM** — watermark-free, no quota, no key, no card. Pipeline: rembg → TripoSR → trimesh → decimate → weight-transfer rig → game-ready GLB. This is the Forge3D v0 free pipeline. SF3D for higher-poly variants. TRELLIS/Hunyuan3D only via the free GPU paths above.
