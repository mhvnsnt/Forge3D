"""Forge3D install selftest: verifies pipeline wiring WITHOUT generating.

Checks: package imports, registry discovery, base interface contract,
pipeline stage recording, CLI entry points. No network, no GPU, no keys.
"""
from __future__ import annotations

import tempfile
from pathlib import Path


def _check(name, fn) -> bool:
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {name}: {e}")
        return False
    print(f"ok   {name}")
    return True


def test_imports():
    import forge3d  # noqa
    from forge3d.providers import base, registry  # noqa
    from forge3d.pipelines import pipeline, postprocess  # noqa
    from forge3d import __main__  # noqa


def test_provider_contract():
    from forge3d.providers.base import Capability, ModelProvider, ProviderInfo

    class Dummy(ModelProvider):
        info = ProviderInfo(name="dummy-test", kind="local",
                            capabilities=[Capability.IMAGE_TO_3D])

        def is_available(self):
            return True, "test double"

        def generate(self, *, prompt=None, image=None, out_dir, **kw):
            import trimesh  # real minimal mesh so cleanup runs the true path
            glb = Path(out_dir) / "dummy.glb"
            trimesh.creation.box(extents=(1, 1, 1)).export(glb)
            from forge3d.providers.base import GenerateResult
            return GenerateResult(glb_path=glb, provider="dummy-test")

    d = Dummy()
    assert d.is_available()[0]
    assert Capability.IMAGE_TO_3D in d.info.capabilities


def test_pipeline_records_stages():
    from forge3d.providers.base import (Capability, GenerateResult,
                                        ModelProvider, ProviderInfo)
    from forge3d.pipelines.pipeline import Pipeline
    import json

    class Dummy(ModelProvider):
        info = ProviderInfo(name="dummy-pipe", kind="local",
                            capabilities=[Capability.IMAGE_TO_3D])

        def is_available(self):
            return True, "test double"

        def generate(self, *, prompt=None, image=None, out_dir, **kw):
            import trimesh  # real minimal mesh so cleanup runs the true path
            glb = Path(out_dir) / "m.glb"
            trimesh.creation.box(extents=(1, 1, 1)).export(glb)
            return GenerateResult(glb_path=glb, provider="dummy-pipe")

    with tempfile.TemporaryDirectory() as td:
        res = Pipeline(Dummy(), Path(td)).run(prompt="test orc")
        assert res.glb_path.exists()
        manifest = json.loads(res.run_manifest.read_text())
        stages = [s["stage"] for s in manifest["stages"]]
        for want in ("concept", "mesh", "cleanup", "export", "handoff"):
            assert want in stages, f"missing stage {want}: {stages}"


def test_registry_discovers():
    from forge3d.providers.registry import discover
    found = discover()
    assert isinstance(found, dict)
    # real providers register here once wired; empty is fine pre-inventory


def test_cli_parses():
    from forge3d.__main__ import main
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["providers"])
    assert rc == 0
    # new gap-closing flags parse
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            main(["generate", "--help"])
        except SystemExit as e:
            assert e.code == 0


def test_latency_ranking():
    from forge3d.pipelines import latency
    # ranked() is pure logic: measured-fast first, unmeasured next
    order = latency.ranked(["slow-p", "fast-p", "new-p"])
    assert set(order) == {"slow-p", "fast-p", "new-p"}
    # record() never raises, even with bad store
    latency.record("selftest-p", 1.23, True)
    assert latency.ema("selftest-p") is not None


def test_fanout_all_fail_loud():
    from forge3d.providers.base import (Capability, ModelProvider,
                                        ProviderError, ProviderInfo)
    from forge3d.pipelines.fanout import fanout_generate

    class Failer(ModelProvider):
        info = ProviderInfo(name="failer-test", kind="local",
                            capabilities=[Capability.IMAGE_TO_3D])

        def is_available(self):
            return True, "test double"

        def generate(self, *, prompt=None, image=None, out_dir, **kw):
            raise ProviderError("intentional test failure")

    with tempfile.TemporaryDirectory() as td:
        try:
            fanout_generate({"a": Failer(), "b": Failer()},
                            prompt="x", out_dir=Path(td), max_parallel=2)
        except ProviderError as e:
            assert "ALL" in str(e) and "intentional test failure" in str(e)
            return
        raise AssertionError("fanout should have raised when all fail")


def test_fanout_winner():
    from forge3d.providers.base import (Capability, GenerateResult,
                                        ModelProvider, ProviderInfo)
    from forge3d.pipelines.fanout import fanout_generate

    class Winner(ModelProvider):
        info = ProviderInfo(name="winner-test", kind="local",
                            capabilities=[Capability.IMAGE_TO_3D])

        def is_available(self):
            return True, "test double"

        def generate(self, *, prompt=None, image=None, out_dir, **kw):
            import trimesh
            glb = Path(out_dir) / "w.glb"
            trimesh.creation.box(extents=(1, 1, 1)).export(glb)
            return GenerateResult(glb_path=glb, provider="winner-test")

    class Loser(ModelProvider):
        info = ProviderInfo(name="loser-test", kind="local",
                            capabilities=[Capability.IMAGE_TO_3D])

        def is_available(self):
            return True, "test double"

        def generate(self, *, prompt=None, image=None, out_dir, **kw):
            from forge3d.providers.base import ProviderError
            raise ProviderError("slow loser")

    with tempfile.TemporaryDirectory() as td:
        name, res = fanout_generate({"w": Winner(), "l": Loser()},
                                    prompt="x", out_dir=Path(td),
                                    max_parallel=2)
        assert name == "w"
        assert res.glb_path.exists()


def test_multiview_unknown_backend_loud():
    from forge3d.pipelines.multiview import generate_views, BACKEND_LICENSE
    from forge3d.providers.base import ProviderError
    with tempfile.TemporaryDirectory() as td:
        try:
            generate_views(Path("nonexistent.png"), Path(td),
                           backend="nope")
        except ProviderError:
            return
        raise AssertionError("unknown backend should raise")
    assert "zero123plus" in BACKEND_LICENSE  # license table present


def test_pipeline_run_from_mesh():
    from forge3d.providers.base import (Capability, GenerateResult,
                                        ModelProvider, ProviderInfo)
    from forge3d.pipelines.pipeline import Pipeline
    import json

    class Dummy(ModelProvider):
        info = ProviderInfo(name="dummy-mesh", kind="local",
                            capabilities=[Capability.IMAGE_TO_3D])

        def is_available(self):
            return True, "test double"

        def generate(self, *, prompt=None, image=None, out_dir, **kw):
            import trimesh
            glb = Path(out_dir) / "m.glb"
            trimesh.creation.box(extents=(1, 1, 1)).export(glb)
            return GenerateResult(glb_path=glb, provider="dummy-mesh")

    with tempfile.TemporaryDirectory() as td:
        d = Dummy()
        mesh_res = d.generate(prompt="x", out_dir=Path(td))
        # run_from_mesh: post stages on existing mesh (fan-out winner path)
        res = Pipeline(d, Path(td) / "post").run_from_mesh(
            mesh_res, texture="none", densify=False)
        assert res.glb_path.exists()
        stages = [s["stage"] for s in
                  json.loads(res.run_manifest.read_text())["stages"]]
        assert "mesh" in stages and "cleanup" in stages


def run() -> bool:
    checks = [
        ("imports", test_imports),
        ("provider-contract", test_provider_contract),
        ("pipeline-stages", test_pipeline_records_stages),
        ("registry-discovery", test_registry_discovers),
        ("cli-parses", test_cli_parses),
        ("latency-ranking", test_latency_ranking),
        ("fanout-all-fail-loud", test_fanout_all_fail_loud),
        ("fanout-winner", test_fanout_winner),
        ("multiview-unknown-loud", test_multiview_unknown_backend_loud),
        ("pipeline-run-from-mesh", test_pipeline_run_from_mesh),
    ]
    results = [_check(n, f) for n, f in checks]
    print(f"{sum(results)}/{len(results)} selftest checks passed")
    return all(results)
