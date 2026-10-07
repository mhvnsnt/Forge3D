"""Automated ANATOMICAL defect gates for generated character models.

Why this exists: grunt_onyx shipped to the owner with a horse-shaped lower
leg and was presented as a roster candidate. Owner verdict: TRASH.
Generation is frozen until the pipeline is 400% better — these gates are
part of that bar. A horse-legged model must NEVER reach the owner again.

What it checks (all measurable, deterministic, CPU-only):
  - leg_segment_ratio: calf/thigh thickness per leg in human range.
    A horse-like lower leg is a uniform thin tube (calf ~= thigh,
    no calf bulge, no knee dip) — this is the primary horse-leg detector.
  - thigh_absolute: thigh thickness as a fraction of height (sanity floor).
  - knee_articulation: the thickness profile must dip at the knee
    (>=8% below the calf bulge) inside the anatomical knee band.
  - leg_symmetry: left/right thigh+calf within tolerance.
  - leg_axis: centroid path hip->ankle must not kink (digitigrade kink).
  - head_presence / feet_grounded: head exists on top, feet touch ground.
  - rig_bone_ratios: when the GLB carries a skin, bone-length ratios
    (thigh/shin, upper-arm/forearm) must be human.
  - preview_pose (optional, needs preview PNG + mediapipe bundle):
    MediaPipe pose second opinion — landmark presence, joint y-order,
    generous joint-angle sanity.

Conventions match pipelines/gates.py: PASS / FLAG / FAIL, GateResult,
GateReport. FAIL = quarantine the GLB, raise loudly, never present it.

Assumptions (documented): character stands upright, feet at the bottom,
roughly A-pose. Sitting/creature models will fail by design.

Anthropometric basis (adult human, fractions of stature H):
  knee height ~0.285H | thigh/shin length ratio ~0.9-1.1 |
  calf max width ~0.60-0.75x thigh max width.
Thresholds below are widened for stylized game characters.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh

from .gates import FAIL, FLAG, PASS, GateReport, GateResult

# ---------------------------------------------------------------- thresholds
# (owner-tunable; validated against the proof corpus — see docs/ANATOMY_GATES.md)
CALF_THIGH_MIN = 0.50   # calf max thickness / thigh max thickness
CALF_THIGH_MAX = 0.88
THIGH_MIN_FRAC = 0.085  # thigh max thickness as fraction of height
KNEE_BAND = (0.18, 0.38)          # where the knee dip must live (frac of H)
KNEE_DIP_MIN = 0.08               # profile must narrow >=8% at the knee
LEG_SYMM_TOL = 0.30               # L/R relative difference tolerance
LEG_KINK_MAX = 0.06               # max centroid-path deviation (frac of H)
HEAD_TOP_FRAC = 0.12              # top slice examined for the head
HEAD_W_MIN, HEAD_W_MAX = 0.08, 0.30  # head width as fraction of H
FEET_GROUND_TOL = 0.02
# rig-bone ratios (when a skin is present)
THIGH_SHIN_MIN, THIGH_SHIN_MAX = 0.85, 1.15
UPPER_FORE_MIN, UPPER_FORE_MAX = 0.60, 0.95
# mediapipe pose sanity (generous — stances bend joints)
MP_KNEE_MIN, MP_KNEE_MAX = 135.0, 205.0
MP_MIN_VIS = 0.5
MP_BUNDLE_ENV = "FORGE3D_MEDIAPIPE_BUNDLE"
MP_BUNDLE_DEFAULT = Path.home() / ".forge3d/weights/mediapipe/pose_landmarker_full.task"

_LEG_LM = {"l_hip": 23, "r_hip": 24, "l_knee": 25, "r_knee": 26,
           "l_ank": 27, "r_ank": 28, "l_heel": 29, "r_heel": 30}
_ARM_LM = {"l_sh": 11, "r_sh": 12, "l_elb": 13, "r_elb": 14,
           "l_wr": 15, "r_wr": 16}


# ------------------------------------------------------------------ geometry
def _load_vertices(glb_path: Path):
    """Combined vertices, normalized: feet at y=0, height=1. Returns (v, H) or (None, err)."""
    try:
        scene = trimesh.load(str(glb_path), force="scene")
        if isinstance(scene, trimesh.Scene):
            geoms = [g for g in scene.geometry.values()
                     if isinstance(g, trimesh.Trimesh) and len(g.vertices)]
        elif isinstance(scene, trimesh.Trimesh):
            geoms = [scene]
        else:
            return None, "no trimesh geometry"
        if not geoms:
            return None, "empty geometry"
        v = trimesh.util.concatenate(geoms).vertices.copy()
    except Exception as e:  # noqa: BLE001
        return None, f"load failed: {e}"
    v[:, 1] -= v[:, 1].min()
    H = float(v[:, 1].max())
    if H <= 0:
        return None, "zero height"
    v[:, 1] /= H
    return v, H


def _x_clusters(v: np.ndarray, y0: float, band: float = 0.012,
                gap_frac: float = 0.035) -> list[np.ndarray]:
    """1-D x-clustering of a horizontal vertex band. Returns 1 or 2 clusters."""
    sel = v[np.abs(v[:, 1] - y0) < band]
    if len(sel) < 20:
        return []
    xs = np.sort(sel[:, 0])
    gaps = np.diff(xs)
    if len(gaps) == 0:
        return [xs]
    i = int(np.argmax(gaps))
    if gaps[i] > gap_frac:
        return [xs[: i + 1], xs[i + 1:]]
    return [xs]


def _find_crotch(v: np.ndarray):
    """Highest y below mid-body where the slice splits into two leg clusters
    (split must persist over 3 consecutive slices)."""
    cands = []
    for y0 in np.arange(0.55, 0.05, -0.01):
        cl = _x_clusters(v, y0)
        if len(cl) == 2 and len(cl[0]) > 15 and len(cl[1]) > 15:
            cands.append(round(float(y0), 2))
    # longest persistent run -> its top
    best, run = None, []
    for c in cands:
        if run and abs(c - run[-1]) > 0.015:
            if best is None or len(run) > len(best):
                best = run
            run = [c]
        else:
            run.append(c)
    if best is None or len(run) > len(best):
        best = run
    if not best or len(best) < 3:
        return None
    return max(best)


def _leg_profiles(v: np.ndarray, crotch: float):
    """Per-leg thickness profile + centroid path. Returns dict L/R ->
    {ys, thick, cx, cz} with np.nan where the split is unclear."""
    ys = np.arange(0.01, crotch, 0.01)
    out = {}
    for key in ("L", "R"):
        out[key] = {"ys": ys, "thick": [], "cx": [], "cz": []}
    for y0 in ys:
        cl = _x_clusters(v, y0)
        if len(cl) != 2 or len(cl[0]) < 10 or len(cl[1]) < 10:
            for key in ("L", "R"):
                out[key]["thick"].append(np.nan)
                out[key]["cx"].append(np.nan)
                out[key]["cz"].append(np.nan)
            continue
        for key, xs in zip(("L", "R"), cl):  # L = smaller x
            sel = v[(np.abs(v[:, 1] - y0) < 0.012)
                    & (v[:, 0] >= xs.min() - 1e-9)
                    & (v[:, 0] <= xs.max() + 1e-9)]
            w = float(xs.max() - xs.min())
            d = float(sel[:, 2].max() - sel[:, 2].min()) if len(sel) else 0.0
            out[key]["thick"].append(max(w, d))
            out[key]["cx"].append(float(np.median(sel[:, 0])) if len(sel) else np.nan)
            out[key]["cz"].append(float(np.median(sel[:, 2])) if len(sel) else np.nan)
    for key in ("L", "R"):
        for f in ("thick", "cx", "cz"):
            out[key][f] = np.array(out[key][f])
    return out


def _leg_metrics(prof: dict, crotch: float) -> dict:
    """thigh/calf thickness, knee dip, axis kink for one leg profile."""
    ys, t = prof["ys"], prof["thick"]
    valid = ~np.isnan(t)
    m = {"samples": int(valid.sum()), "thigh": np.nan, "calf": np.nan,
         "knee_y": np.nan, "knee_dip": 0.0, "kink": np.nan}
    if valid.sum() < 5:
        return m
    yy, pp = ys[valid], t[valid]
    up = pp[yy > crotch * 0.55]
    lo = pp[(yy > 0.06) & (yy < crotch * 0.55)]
    m["thigh"] = float(up.max()) if len(up) else np.nan
    m["calf"] = float(lo.max()) if len(lo) else np.nan
    # knee: deepest local minimum of the smoothed profile inside the band
    band = (yy > KNEE_BAND[0]) & (yy < KNEE_BAND[1])
    if band.sum() >= 5:
        yb, pb = yy[band], pp[band]
        sm = np.convolve(pb, np.ones(3) / 3, mode="same")
        best, best_dip = None, 0.0
        for i in range(1, len(sm) - 1):
            if sm[i] < sm[i - 1] and sm[i] < sm[i + 1]:
                dip = (max(sm[max(0, i - 3):i].max(initial=0),
                           sm[i + 1:i + 4].max(initial=0)) - sm[i]) \
                    / max(sm[i], 1e-9)
                if dip > best_dip:
                    best_dip, best = dip, yb[i]
        if best is not None:
            m["knee_y"], m["knee_dip"] = float(best), float(best_dip)
    # axis kink: max deviation of centroid path from hip->ankle line
    cx, cz = prof["cx"], prof["cz"]
    ok = valid & ~np.isnan(cx) & ~np.isnan(cz)
    if ok.sum() > 5:
        p0 = np.array([cx[ok][0], cz[ok][0]])
        p1 = np.array([cx[ok][-1], cz[ok][-1]])
        d = p1 - p0
        L = float(np.hypot(*d))
        if L > 1e-9:
            dev = np.abs((cx[ok] - p0[0]) * d[1] - (cz[ok] - p0[1]) * d[0]) / L
            m["kink"] = float(dev.max())
    return m


# --------------------------------------------------------------------- gates
def gate_leg_segment_ratio(metrics: dict) -> GateResult:
    bad = {}
    for leg in ("L", "R"):
        r = metrics[leg]["calf"] / max(metrics[leg]["thigh"], 1e-9)
        if np.isnan(r) or not (CALF_THIGH_MIN <= r <= CALF_THIGH_MAX):
            bad[leg] = None if np.isnan(r) else round(float(r), 3)
    meas = {f"{l}_calf_thigh": (None if np.isnan(metrics[l]['calf'] / max(metrics[l]['thigh'], 1e-9))
                               else round(float(metrics[l]['calf'] / max(metrics[l]['thigh'], 1e-9)), 3))
            for l in ("L", "R")}
    if bad:
        return GateResult(
            "leg_segment_ratio", FAIL,
            "horse-like lower leg on " + ", ".join(f"{l} (calf/thigh={v})" for l, v in bad.items())
            + f" — human range [{CALF_THIGH_MIN}, {CALF_THIGH_MAX}]; "
              "uniform thin tube, no calf bulge",
            meas)
    return GateResult("leg_segment_ratio", PASS,
                      f"calf/thigh ratios human: {meas}", meas)


def gate_thigh_absolute(metrics: dict) -> GateResult:
    bad = {l: round(float(metrics[l]["thigh"]), 3) for l in ("L", "R")
           if np.isnan(metrics[l]["thigh"]) or metrics[l]["thigh"] < THIGH_MIN_FRAC}
    meas = {f"{l}_thigh_frac": round(float(metrics[l]["thigh"]), 3) for l in ("L", "R")}
    if bad:
        return GateResult(
            "thigh_absolute", FAIL,
            "thigh too thin on " + ", ".join(f"{l} ({v} of height)" for l, v in bad.items())
            + f" — floor is {THIGH_MIN_FRAC}; spindly/animal-like legs",
            meas)
    return GateResult("thigh_absolute", PASS, f"thigh thickness sane: {meas}", meas)


def gate_knee_articulation(metrics: dict) -> GateResult:
    bad = {}
    for leg in ("L", "R"):
        d = metrics[leg]["knee_dip"]
        if np.isnan(metrics[leg]["knee_y"]) or d < KNEE_DIP_MIN:
            bad[leg] = round(float(d), 3)
    meas = {}
    for l in ("L", "R"):
        meas[f"{l}_knee_y"] = (None if np.isnan(metrics[l]["knee_y"])
                               else round(float(metrics[l]["knee_y"]), 3))
        meas[f"{l}_knee_dip"] = round(float(metrics[l]["knee_dip"]), 3)
    if bad:
        return GateResult(
            "knee_articulation", FAIL,
            "no knee articulation on " + ", ".join(f"{l} (dip={v})" for l, v in bad.items())
            + f" — profile must narrow >={KNEE_DIP_MIN:.0%} in {KNEE_BAND}; "
              "straight tube = animal-like leg",
            meas)
    return GateResult("knee_articulation", PASS,
                      f"knee dips detected: {meas}", meas)


def gate_leg_symmetry(metrics: dict) -> GateResult:
    def rel(a, b):
        return abs(a - b) / max((a + b) / 2, 1e-9)
    td = rel(metrics["L"]["thigh"], metrics["R"]["thigh"])
    cd = rel(metrics["L"]["calf"], metrics["R"]["calf"])
    meas = {"thigh_LR_diff": round(float(td), 3), "calf_LR_diff": round(float(cd), 3)}
    if td > LEG_SYMM_TOL or cd > LEG_SYMM_TOL:
        return GateResult("leg_symmetry", FAIL,
                          f"L/R leg mismatch: thigh diff {td:.0%}, calf diff {cd:.0%} "
                          f"(tol {LEG_SYMM_TOL:.0%}) — one leg deformed",
                          meas)
    return GateResult("leg_symmetry", PASS, f"legs symmetric: {meas}", meas)


def gate_leg_axis(metrics: dict) -> GateResult:
    worst = max(metrics["L"]["kink"], metrics["R"]["kink"])
    meas = {f"{l}_kink": (None if np.isnan(metrics[l]["kink"]) else round(float(metrics[l]["kink"]), 3))
            for l in ("L", "R")}
    if np.isnan(worst):
        return GateResult("leg_axis", FLAG, "could not trace leg axis", meas)
    if worst > LEG_KINK_MAX:
        return GateResult("leg_axis", FLAG,
                          f"leg axis kinks {worst:.3f} of height (> {LEG_KINK_MAX}) — "
                          "possible digitigrade/reverse joint; inspect",
                          meas)
    return GateResult("leg_axis", PASS, f"leg axes straight: {meas}", meas)


def gate_head_presence(v: np.ndarray) -> GateResult:
    top = v[v[:, 1] > 1.0 - HEAD_TOP_FRAC]
    if len(top) < 20:
        return GateResult("head_presence", FAIL, "no geometry in head band", {})
    xs = np.sort(top[:, 0])
    gaps = np.diff(xs)
    n_splits = int(np.sum(gaps > 0.05)) if len(gaps) else 0
    w = float(xs.max() - xs.min())
    meas = {"head_width_frac": round(w, 3), "splits": n_splits}
    if n_splits > 0:
        return GateResult("head_presence", FAIL,
                          f"head band split into pieces ({n_splits}) — detached/floating head",
                          meas)
    if not (HEAD_W_MIN <= w <= HEAD_W_MAX):
        return GateResult("head_presence", FAIL,
                          f"head width {w:.3f} of height outside "
                          f"[{HEAD_W_MIN}, {HEAD_W_MAX}] — missing or giant head",
                          meas)
    return GateResult("head_presence", PASS, f"head present, width {w:.3f} of height", meas)


def gate_feet_grounded(v: np.ndarray, crotch: float) -> GateResult:
    gmin = float(v[:, 1].min())
    lows = []
    for y0 in (0.005, 0.015):
        cl = _x_clusters(v, y0)
        lows.append(len(cl))
    meas = {"global_min_y": round(gmin, 4), "clusters_at_ground": lows}
    if gmin > FEET_GROUND_TOL:
        return GateResult("feet_grounded", FLAG,
                          f"feet float {gmin:.3f} above ground — normalize or check",
                          meas)
    return GateResult("feet_grounded", PASS, "feet at ground plane", meas)


def _skinned_joints(glb_path: Path):
    """Joint rest positions from a skinned GLB, else None."""
    import struct as _st
    try:
        data = glb_path.read_bytes()
        if data[:4] != b"glTF":
            return None
        jlen = _st.unpack("<I", data[12:16])[0]
        doc = json.loads(data[20:20 + jlen])
        skins = doc.get("skins", [])
        if not skins:
            return None
        joints = skins[0].get("joints", [])
        nodes = doc.get("nodes", [])
        pos = {}
        for j in joints:
            n = nodes[j]
            t = n.get("translation", [0, 0, 0])
            pos[n.get("name", f"j{j}")] = np.array(t, dtype=float)
        return pos
    except Exception:  # noqa: BLE001
        return None


def gate_rig_bone_ratios(glb_path: Path) -> GateResult:
    joints = _skinned_joints(glb_path)
    if not joints:
        # Unrigged generator output: the geometric leg gates above are the
        # verification. PASS (not FLAG) so clean unrigged models ship.
        return GateResult("rig_bone_ratios", PASS,
                          "GLB unrigged — bone-ratio check not applicable; "
                          "geometric leg gates applied instead",
                          {"skinned": False})

    def seg(*name_frags):
        """Find a joint by name fragments, return its position."""
        for nm, p in joints.items():
            if all(f.lower() in nm.lower() for f in name_frags):
                return p
        return None

    meas, problems = {}, []
    pairs = [(("thigh", "shin"), ("LeftUpLeg", "LeftLeg"), ("RightUpLeg", "RightLeg"),
              THIGH_SHIN_MIN, THIGH_SHIN_MAX, "thigh/shin"),
             (("upperarm", "forearm"), ("LeftArm", "LeftForeArm"), ("RightArm", "RightForeArm"),
              UPPER_FORE_MIN, UPPER_FORE_MAX, "upperarm/forearm")]
    # generic fallback: any joint names containing 'thigh'/'shin' etc.
    for (up_f, lo_f), left_names, right_names, lo, hi, label in pairs:
        for side, names in (("L", left_names), ("R", right_names)):
            up = seg(*names[:1]) or seg(up_f)
            lo_j = seg(*names[1:]) or seg(lo_f)
            end = None
            if lo_j is not None:
                # end joint: lowest joint below the lower segment
                # (foot for legs, hand for arms), by name when possible
                cands = [(nm, p) for nm, p in joints.items()
                         if p[1] < lo_j[1] - 1e-6]
                want = "foot" if "shin" in lo_f else "hand"
                named = [p for nm, p in cands if want in nm.lower()]
                if named:
                    end = min(named, key=lambda p: p[1])
                elif cands:
                    end = min(cands, key=lambda t: t[1])[1]
            if up is None or lo_j is None or end is None:
                continue
            r = float(np.linalg.norm(up - lo_j) / max(np.linalg.norm(lo_j - end), 1e-9))
            meas[f"{side}_{label}"] = round(r, 3)
            if not (lo <= r <= hi):
                problems.append(f"{side} {label}={r:.2f} outside [{lo}, {hi}]")
    if not meas:
        return GateResult("rig_bone_ratios", FLAG,
                          "skinned but joint names unrecognized — check manually",
                          {"skinned": True})
    if problems:
        return GateResult("rig_bone_ratios", FAIL,
                          "bone ratios inhuman: " + "; ".join(problems), meas)
    return GateResult("rig_bone_ratios", PASS, f"bone ratios human: {meas}", meas)


# ------------------------------------------------------- mediapipe preview
def _mp_bundle() -> Path | None:
    p = Path(os.environ.get(MP_BUNDLE_ENV, str(MP_BUNDLE_DEFAULT)))
    return p if p.is_file() else None


def gate_preview_pose(preview_path: Path | None) -> GateResult:
    """MediaPipe pose second opinion on the 4-angle preview (front panel)."""
    if preview_path is None or not Path(preview_path).is_file():
        return GateResult("preview_pose", FLAG, "no preview supplied — pose check skipped", {})
    bundle = _mp_bundle()
    if bundle is None:
        return GateResult("preview_pose", FLAG,
                          "mediapipe bundle missing — pose check skipped", {})
    try:
        import mediapipe as mp
        from PIL import Image
        img = Image.open(preview_path).convert("RGB")
        w = img.size[0]
        front = img.crop((0, 0, w // 4, img.size[1]))
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB,
                          data=np.asarray(front))
        opts = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(bundle)),
            running_mode=mp.tasks.vision.RunningMode.IMAGE)
        with mp.tasks.vision.PoseLandmarker.create_from_options(opts) as lm:
            res = lm.detect(mp_img)
    except Exception as e:  # noqa: BLE001
        return GateResult("preview_pose", FLAG, f"pose detection errored: {e}", {})
    if not res.pose_landmarks:
        return GateResult("preview_pose", FLAG, "no pose detected in front view", {})
    pts = res.pose_landmarks[0]
    missing = [n for n, i in _LEG_LM.items()
               if pts[i].visibility < MP_MIN_VIS or pts[i].presence < MP_MIN_VIS]
    if missing:
        return GateResult("preview_pose", FAIL,
                          "pose landmarks missing/low-confidence: "
                          + ", ".join(missing) + " — limb may be absent/deformed",
                          {"missing": missing})
    problems, meas = [], {}
    for side in ("l", "r"):
        hip_i = _LEG_LM[side + "_hip"]
        knee_i = _LEG_LM[side + "_knee"]
        ank_i = _LEG_LM[side + "_ank"]
        hy, ky, ay = pts[hip_i].y, pts[knee_i].y, pts[ank_i].y
        meas[side + "_y_order"] = [round(hy, 3), round(ky, 3), round(ay, 3)]
        if not (hy < ky < ay):
            problems.append(side + " leg joint y-order wrong "
                            f"(hip {hy:.2f} knee {ky:.2f} ankle {ay:.2f})")
        ka = _angle(pts, hip_i, knee_i, ank_i)
        meas[side + "_knee_deg"] = round(ka, 1)
        if not (MP_KNEE_MIN <= ka <= MP_KNEE_MAX):
            problems.append(side + f" knee angle {ka:.0f} deg outside "
                            f"[{MP_KNEE_MIN:.0f}, {MP_KNEE_MAX:.0f}]")
    # arm landmarks present?
    for n, i in _ARM_LM.items():
        if pts[i].visibility < MP_MIN_VIS:
            problems.append(f"arm landmark {n} missing")
    if problems:
        return GateResult("preview_pose", FAIL, "; ".join(problems), meas)
    return GateResult("preview_pose", PASS, f"pose sane: {meas}", meas)


def _angle(pts, a, b, c) -> float:
    a = np.array([pts[a].x, pts[a].y]); b = np.array([pts[b].x, pts[b].y])
    c = np.array([pts[c].x, pts[c].y])
    v1, v2 = a - b, c - b
    cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cosang, -1, 1))))


# ------------------------------------------------------------------ runner
def run_anatomy_gates(glb_path: Path | str,
                      preview_path: Path | str | None = None) -> GateReport:
    """Run all anatomical gates on a GLB (+ optional preview PNG). Never raises."""
    rep = GateReport()
    glb_path = Path(glb_path)
    v, err = _load_vertices(glb_path)
    if v is None:
        rep.results.append(GateResult("load", FAIL, f"cannot analyze: {err}", {}))
        return rep
    crotch = _find_crotch(v)
    if crotch is None:
        rep.results.append(GateResult(
            "leg_split", FAIL,
            "no leg split found below mid-body — legs fused/absent (mermaid/blob?)",
            {}))
        return rep
    rep.results.append(GateResult("leg_split", PASS,
                                  f"legs split at {crotch:.2f} of height",
                                  {"crotch_frac": round(crotch, 3)}))
    profs = _leg_profiles(v, crotch)
    metrics = {leg: _leg_metrics(profs[leg], crotch) for leg in ("L", "R")}
    rep.results.append(gate_leg_segment_ratio(metrics))
    rep.results.append(gate_thigh_absolute(metrics))
    rep.results.append(gate_knee_articulation(metrics))
    rep.results.append(gate_leg_symmetry(metrics))
    rep.results.append(gate_leg_axis(metrics))
    rep.results.append(gate_head_presence(v))
    rep.results.append(gate_feet_grounded(v, crotch))
    rep.results.append(gate_rig_bone_ratios(glb_path))
    rep.results.append(gate_preview_pose(preview_path))
    return rep


def quarantine_failed(glb_path: Path | str, out_dir: Path | str,
                      report: GateReport) -> Path:
    """Copy a failed GLB into quarantine with its gate report. Never presents it."""
    out_dir = Path(out_dir)
    qdir = out_dir / "quarantine"
    qdir.mkdir(parents=True, exist_ok=True)
    glb_path = Path(glb_path)
    dest = qdir / glb_path.name
    shutil.copy2(glb_path, dest)
    (qdir / (glb_path.stem + ".anatomy_gates.json")).write_text(
        json.dumps(report.to_dict(), indent=1))
    return dest


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Forge3D anatomical defect gates")
    ap.add_argument("glb", help="model GLB to check")
    ap.add_argument("preview", nargs="?", default=None, help="4-angle preview PNG")
    ap.add_argument("--quarantine", default=None,
                    help="quarantine dir for failed models")
    args = ap.parse_args(argv)
    rep = run_anatomy_gates(args.glb, args.preview)
    print(json.dumps(rep.to_dict(), indent=1))
    if rep.verdict == FAIL and args.quarantine:
        q = quarantine_failed(args.glb, args.quarantine, rep)
        print(f"quarantined: {q}", file=sys.stderr)
    return 0 if rep.verdict == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
