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

    providers = discover()
    if args.provider == "auto":
        pool = available()
        if not pool:
            print("no provider available; run `providers` for reasons", file=sys.stderr)
            return 2
        # prefer: free API with quota > local GPU > CPU fallback
        def rank(p):
            api = 0 if p.info.kind == "api" else 1
            gpu = 0 if not p.info.needs_gpu else 1
            return (api, gpu)
        name, prov = sorted(pool.items(), key=lambda kv: rank(kv[1]))[0]
    else:
        prov = providers.get(args.provider)
        name = args.provider
        if prov is None:
            print(f"unknown provider {name}", file=sys.stderr)
            return 2
    print(f"provider: {name}")
    try:
        result = Pipeline(prov, Path(args.out)).run(
            prompt=args.prompt, image=Path(args.image) if args.image else None)
    except ProviderError as e:
        print(f"FAILED (no fake output produced): {e}", file=sys.stderr)
        return 1
    print(f"GLB: {result.glb_path}")
    print(f"manifest: {result.run_manifest}")
    return 0


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
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    # allow running from repo root without install
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    return {"providers": cmd_providers, "generate": cmd_generate,
            "selftest": cmd_selftest}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
