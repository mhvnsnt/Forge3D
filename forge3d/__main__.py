"""Forge3D CLI: generate / providers / selftest."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cmd_providers(_args) -> int:
    from forge3d.providers.registry import discover
    for name, p in sorted(discover().items()):
        ok, reason = p.is_available()
        caps = ",".join(c.value for c in p.info.capabilities)
        print(f"{name:20s} [{p.info.kind:5s}] {'OK ' if ok else 'DOWN'} "
              f"caps={caps} license={p.info.license} {'' if ok else reason}")
    return 0


def cmd_generate(args) -> int:
    from forge3d.providers.registry import discover, available
    from forge3d.pipelines.pipeline import Pipeline, ProviderError
    from forge3d.pipelines import latency

    providers = discover()
    if args.provider == "auto":
        pool = available()
        if not pool:
            print("no provider available; run `providers` for reasons", file=sys.stderr)
            return 2
        # Fallback chain for image-to-3d: best quality first, local CPU last.
        # A provider that raises ProviderError is skipped; the next is tried.
        # (Owner law: failures are loud, never masked into fake output.)
        QUALITY_ORDER = ["trellis2-space", "instantmesh-space",
                         "pollinations-3d", "tripo-api",
                         "triposg", "trellis2", "hi3dgen", "sf3d", "triposr"]
        def rank(item):
            name, p = item
            try:
                q = QUALITY_ORDER.index(name)
            except ValueError:
                q = len(QUALITY_ORDER)
            return (q,)
        quality_chain = [name for name, _ in sorted(pool.items(), key=rank)]
        # Latency learning: within equal quality tiers, try historically-fastest first.
        # (Does not override quality order — it reorders unmeasured/unknown providers
        # by learned speed and pushes known-flaky ones last.)
        chain = latency.ranked(quality_chain)
    else:
        prov = providers.get(args.provider)
        name = args.provider
        if prov is None:
            print(f"unknown provider {name}", file=sys.stderr)
            return 2
        chain = [name]

    gen_kwargs = dict(
        texture=None if args.texture == "none" else args.texture,
        densify=not args.no_densify,
        quadremesh=args.quadremesh,
        quad_target=args.quad_target,
        multiview=args.multiview,
        rig=args.rig,
        gates=not args.no_gates,
    )
    image = Path(args.image) if args.image else None

    # RAM HARDENING: gate local inference on free RAM + single-flight lock.
    # Without this, parallel agents + a 2.5GB model = OOM roulette.
    # atexit releases the lock on every return path (no restructure needed).
    if args.wait_for_ram:
        import atexit
        from contextlib import ExitStack
        from forge3d.tools.ram_gate import wait_for_ram, inference_lock
        _stack = ExitStack()
        wait_for_ram(args.min_ram_gb, timeout_s=args.ram_timeout)
        _stack.enter_context(inference_lock(timeout_s=args.ram_timeout))
        atexit.register(_stack.close)

    # FAN-OUT: race N providers in parallel, take the first good mesh,
    # then run post stages once on the winner. (GAP 3 latency mitigation.)
    if args.fanout > 1 and len(chain) > 1:
        from forge3d.pipelines.fanout import fanout_generate
        racers = {n: providers[n] for n in chain[:args.fanout]}
        print(f"fan-out: racing {', '.join(racers)}", file=sys.stderr)
        try:
            winner, mesh_result = fanout_generate(
                racers, prompt=args.prompt, image=image,
                out_dir=Path(args.out), max_parallel=args.fanout)
        except ProviderError as e:
            print(f"fan-out FAILED: {e}", file=sys.stderr)
            return 1
        print(f"fan-out winner: {winner}", file=sys.stderr)
        pipe = Pipeline(providers[winner], Path(args.out))
        result = pipe.run_from_mesh(mesh_result, **gen_kwargs)
        print(f"GLB: {result.glb_path}")
        print(f"manifest: {result.run_manifest}")
        return 0

    errors = []
    for name in chain:
        prov = providers[name]
        print(f"provider: {name}")
        try:
            result = Pipeline(prov, Path(args.out)).run(
                prompt=args.prompt, image=image, **gen_kwargs)
        except ProviderError as e:
            print(f"provider {name} FAILED: {e}", file=sys.stderr)
            errors.append(f"{name}: {e}")
            continue
        print(f"GLB: {result.glb_path}")
        print(f"manifest: {result.run_manifest}")
        return 0
    print(f"ALL PROVIDERS FAILED (no fake output produced):", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    return 1


def cmd_selftest(_args) -> int:
    from forge3d.tests.selftest import run
    ok = run()
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="forge3d")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("providers")
    g = sub.add_parser("generate")
    g.add_argument("--prompt", default=None)
    g.add_argument("--image", default=None)
    g.add_argument("--provider", default="auto")
    g.add_argument("--out", default="out")
    g.add_argument("--texture", default="lanczos",
                   choices=["lanczos", "realesrgan", "hunyuan-paint", "none"],
                   help="texture refinement backend (none = skip)")
    g.add_argument("--no-densify", action="store_true",
                   help="skip geometry densification")
    g.add_argument("--quadremesh", action="store_true",
                   help="quad-remesh to animation-ready topology via Blender "
                        "Quadriflow (runs instead of densify; game characters)")
    g.add_argument("--quad-target", type=int, default=30000,
                   help="target quad count for --quadremesh (default 30000)")
    g.add_argument("--multiview", default=None,
                   choices=["zero123plus", "provider-native"],
                   help="multi-view synthesis before meshing (backs observed, "
                        "not hallucinated). zero123plus is research-only "
                        "(CC-BY-NC); provider-native is a documented no-op")
    g.add_argument("--fanout", type=int, default=1,
                   help="race N providers in parallel, take first good mesh "
                        "(latency mitigation; default 1 = sequential chain)")
    g.add_argument("--rig", action="store_true",
                   help="auto-rig the output (instance-rig, CPU)")
    g.add_argument("--no-gates", action="store_true",
                   help="skip automated quality gates (default: gates run, "
                        "FAIL aborts loudly)")
    g.add_argument("--wait-for-ram", action="store_true",
                   help="wait until enough free RAM before local inference "
                        "(default need: 2.5GB, see --min-ram-gb); holds a "
                        "single-flight lock so two local runs never OOM "
                        "each other")
    g.add_argument("--min-ram-gb", type=float, default=2.5,
                   help="GB of free RAM required with --wait-for-ram "
                        "(default 2.5)")
    g.add_argument("--ram-timeout", type=float, default=1800.0,
                   help="seconds to wait for RAM with --wait-for-ram "
                        "(default 1800)")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    # allow running from repo root without install
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    return {"providers": cmd_providers, "generate": cmd_generate,
            "selftest": cmd_selftest}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
