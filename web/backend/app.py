"""Forge3D web backend — FastAPI over the existing forge3d pipeline.

Endpoints:
  POST /api/upload            image file -> {upload_id}
  POST /api/generate          {prompt?, upload_id?, provider, texture, densify, rig} -> {job_id}
  GET  /api/job/{id}          status + previews + model stats
  GET  /api/download/{id}     GLB download (?format=glb|usdz — usdz best-effort)
  GET  /api/providers         provider availability for the picker
  /                           the frontend (static)

Generation runs in a background thread on the REAL pipeline
(forge3d.pipelines.pipeline.Pipeline) — no reimplementation, no fake meshes.
"""
from __future__ import annotations

import shutil
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from forge3d.pipelines.measure import measure_glb  # noqa: E402
from forge3d.pipelines.pipeline import Pipeline, ProviderError  # noqa: E402
from forge3d.providers.registry import discover  # noqa: E402

DATA = REPO / "web" / "data"
UPLOADS = DATA / "uploads"
JOBS = DATA / "jobs"
for d in (UPLOADS, JOBS):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Forge3D")
pool = ThreadPoolExecutor(max_workers=1)  # 1 concurrent gen (free-tier honesty)
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


class GenerateRequest(BaseModel):
    prompt: str | None = None
    upload_id: str | None = None
    provider: str = "auto"
    texture: str | None = "lanczos"
    densify: bool = True
    rig: bool = False


def _render_previews(glb: Path, out_dir: Path) -> list[str]:
    """Render 4-angle shaded thumbnails of the real geometry (matplotlib Agg)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import trimesh

    scene = trimesh.load(glb, force="scene")
    geoms = [g for g in scene.dump()] if hasattr(scene, "dump") else [scene]
    mesh = max((g for g in geoms if hasattr(g, "vertices")),
               key=lambda g: len(g.faces))
    v = np.asarray(mesh.vertices, dtype=float)
    f = np.asarray(mesh.faces)
    # decimate for plotting speed
    if len(f) > 60000:
        idx = np.random.RandomState(0).choice(len(f), 60000, replace=False)
        f = f[idx]
    from matplotlib.colors import LightSource
    ls = LightSource(azdeg=315, altdeg=45)
    urls = []
    for i, (elev, azim) in enumerate([(15, -60), (15, 60), (10, 180), (25, 300)]):
        fig = plt.figure(figsize=(4, 4), dpi=100)
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_trisurf(v[:, 0], v[:, 1], f, v[:, 2],
                        cmap="plasma", lightsource=ls, shade=True,
                        linewidth=0, antialiased=False)
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        fig.patch.set_facecolor("white")
        p = out_dir / f"preview_{i}.png"
        fig.savefig(p, bbox_inches="tight", pad_inches=0.1,
                    facecolor="white")
        plt.close(fig)
        urls.append(f"/api/jobfile/{out_dir.name}/{p.name}")
    return urls


def _run_job(job_id: str, req: GenerateRequest):
    job_dir = JOBS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = 5
    try:
        from forge3d.providers.registry import available
        providers = discover()
        if req.provider == "auto":
            pool_ = available()
            if not pool_:
                raise ProviderError("no provider available")
            def rank(p):
                return (0 if p.info.kind == "api" else 1,
                        0 if not p.info.needs_gpu else 1)
            name, prov = sorted(pool_.items(), key=lambda kv: rank(kv[1]))[0]
        else:
            prov = providers.get(req.provider)
            name = req.provider
            if prov is None:
                raise ProviderError(f"unknown provider {name}")
        with jobs_lock:
            jobs[job_id]["provider"] = name
            jobs[job_id]["progress"] = 15
        image = None
        if req.upload_id:
            up = UPLOADS / req.upload_id
            if not up.is_dir():
                raise ProviderError("upload not found")
            files = list(up.glob("*"))
            if not files:
                raise ProviderError("upload empty")
            image = files[0]
        result = Pipeline(prov, job_dir).run(
            prompt=req.prompt, image=image,
            texture=None if req.texture == "none" else req.texture,
            densify=req.densify, rig=req.rig)
        with jobs_lock:
            jobs[job_id]["progress"] = 80
        previews = _render_previews(result.glb_path, job_dir)
        stats = measure_glb(result.glb_path)
        with jobs_lock:
            jobs[job_id].update(
                status="done", progress=100, previews=previews,
                glb=str(result.glb_path),
                stats={k: stats.get(k) for k in
                       ("faces", "vertices", "bones", "texture_images",
                        "watertight", "height_m", "face_ratio_vs_tripo",
                        "vert_ratio_vs_tripo")},
                stages=result.stages)
    except Exception as e:  # noqa: BLE001
        with jobs_lock:
            jobs[job_id].update(status="failed", progress=0,
                                error=f"{type(e).__name__}: {e}")


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex[:12]
    d = UPLOADS / uid
    d.mkdir(parents=True, exist_ok=True)
    dest = d / Path(file.filename or "upload.png").name
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"upload_id": uid, "filename": dest.name,
            "url": f"/api/jobfile/../uploads/{uid}/{dest.name}"}


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    if not req.prompt and not req.upload_id:
        raise HTTPException(400, "prompt or upload_id required")
    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {"status": "queued", "progress": 0,
                        "prompt": req.prompt, "provider": req.provider}
    pool.submit(_run_job, job_id, req)
    return {"job_id": job_id}


@app.get("/api/job/{job_id}")
async def job_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        # also allow resuming from disk
        d = JOBS / job_id
        if d.is_dir():
            return {"job_id": job_id, "status": "unknown",
                    "note": "server restarted; job dir exists on disk"}
        raise HTTPException(404, "job not found")
    out = dict(job)
    out["job_id"] = job_id
    return JSONResponse(out)


@app.get("/api/jobfile/{job_id}/{name}")
async def job_file(job_id: str, name: str):
    p = (JOBS / job_id / Path(name).name)
    if not p.is_file():
        raise HTTPException(404, "file not found")
    return FileResponse(p)


@app.get("/api/download/{job_id}")
async def download(job_id: str, format: str = "glb"):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        raise HTTPException(404, "finished job not found")
    glb = Path(job["glb"])
    if format == "glb":
        return FileResponse(glb, filename=f"forge3d-{job_id}.glb")
    if format == "usdz":
        # best-effort via trimesh USD export; honest 501 when unavailable
        try:
            import trimesh
            scene = trimesh.load(glb, force="scene")
            usd = glb.with_suffix(".usd")
            scene.export(usd)
            return FileResponse(usd, filename=f"forge3d-{job_id}.usd")
        except Exception as e:  # noqa: BLE001
            raise HTTPException(501, f"USD export unavailable: {e}")
    if format == "fbx":
        raise HTTPException(501, "FBX export needs a DCC converter (Blender) — not on this host")
    raise HTTPException(400, "format must be glb|usdz|fbx")


@app.get("/api/providers")
async def providers():
    out = []
    for name, p in sorted(discover().items()):
        ok, reason = p.is_available()
        out.append({"name": name, "kind": p.info.kind, "available": ok,
                    "reason": "" if ok else reason,
                    "license": p.info.license,
                    "capabilities": [c.value for c in p.info.capabilities]})
    return {"providers": out}


FRONTEND = REPO / "web" / "frontend"
if FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
