#!/usr/bin/env python3
"""
safe-watcher.py — Monitor-only process watcher. NEVER kills, NEVER deletes.

This is the anti-pattern to the destructive watcher that deleted system
files and killed working processes. This watcher:

  ✓ Checks if monitored processes are alive
  ✓ Checks if frame counts are increasing (render progress)
  ✓ Writes status to a JSON file for dashboards
  ✓ Logs alerts when things look wrong
  ✗ NEVER kills any process
  ✗ NEVER deletes any file
  ✗ NEVER restarts anything automatically

If something is wrong, it ALERTS (writes to alert log). A human or a
separate, explicitly-authorized remediation script decides what to do.

Usage:
    python3 safe-watcher.py --config watcher.json
    python3 safe-watcher.py --check-once  # single check, for cron

Config format (watcher.json):
{
    "processes": [
        {"name": "render-pipeline", "pattern": "pipeline.py.*stickup"}
    ],
    "progress_dirs": [
        {"name": "frames", "path": "/path/to/frames", "pattern": "*.png"}
    ],
    "status_file": "/tmp/watcher-status.json",
    "alert_log": "/tmp/watcher-alerts.log",
    "stale_threshold_minutes": 15
}
"""

import argparse
import datetime
import glob
import json
import os
import subprocess
import sys


def log(msg):
    ts = datetime.datetime.now().isoformat()
    print(f"[{ts}] {msg}", flush=True)


def alert(msg, alert_log):
    """Write an alert. This is the ONLY action this watcher takes."""
    ts = datetime.datetime.now().isoformat()
    line = f"[{ts}] ALERT: {msg}\n"
    with open(alert_log, "a") as f:
        f.write(line)
    log(f"ALERT written: {msg}")


def check_process(pattern):
    """Check if a process matching pattern is running. Read-only."""
    try:
        r = subprocess.run(
            ["pgrep", "-f", pattern],
            capture_output=True, text=True, timeout=10
        )
        pids = [p for p in r.stdout.strip().split("\n") if p]
        # Filter out our own pgrep
        return len(pids) > 0, pids
    except Exception as e:
        return False, []


def count_files(path, pattern):
    """Count files matching pattern in path. Read-only."""
    try:
        full = os.path.join(path, pattern)
        return len(glob.glob(full))
    except Exception:
        return -1


def check_once(config):
    """Run a single check cycle. Returns status dict."""
    status = {
        "timestamp": datetime.datetime.now().isoformat(),
        "processes": {},
        "progress": {},
        "alerts": [],
    }

    # Check processes (read-only)
    for proc in config.get("processes", []):
        alive, pids = check_process(proc["pattern"])
        status["processes"][proc["name"]] = {
            "alive": alive,
            "pid_count": len(pids),
        }
        if not alive:
            msg = f"Process '{proc['name']}' (pattern: {proc['pattern']}) is NOT running"
            status["alerts"].append(msg)
            alert(msg, config["alert_log"])

    # Check progress dirs (read-only)
    for pd in config.get("progress_dirs", []):
        count = count_files(pd["path"], pd.get("pattern", "*"))
        prev_key = f"_prev_{pd['name']}"
        prev = getattr(check_once, prev_key, None)
        setattr(check_once, prev_key, count)

        status["progress"][pd["name"]] = {
            "count": count,
            "path": pd["path"],
        }
        if prev is not None and count == prev and count > 0:
            # No progress since last check — might be stuck
            # But we DON'T act on it, just note it
            status["progress"][pd["name"]]["stalled"] = True

    # Write status file (for dashboards)
    with open(config["status_file"], "w") as f:
        json.dump(status, f, indent=2)

    return status


def main():
    ap = argparse.ArgumentParser(description="Safe monitor-only watcher")
    ap.add_argument("--config", required=True, help="Path to watcher.json")
    ap.add_argument("--check-once", action="store_true",
                    help="Run single check and exit (for cron)")
    ap.add_argument("--interval", type=int, default=600,
                    help="Seconds between checks in loop mode")
    pa = ap.parse_args()

    with open(pa.config) as f:
        config = json.load(f)

    # Ensure alert log exists
    open(config.get("alert_log", "/tmp/watcher-alerts.log"), "a").close()

    log("Safe watcher starting (monitor-only, will NEVER kill or delete)")

    if pa.check_once:
        status = check_once(config)
        alive = sum(1 for p in status["processes"].values() if p["alive"])
        total = len(status["processes"])
        log(f"Check complete: {alive}/{total} processes alive, "
            f"{len(status['alerts'])} alerts")
        return 0 if not status["alerts"] else 1

    import time
    while True:
        check_once(config)
        time.sleep(pa.interval)


if __name__ == "__main__":
    sys.exit(main())
