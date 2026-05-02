#!/usr/bin/env python3
"""Post-deploy verification — one-command backend-vs-local drift check.

Run this after every mascidocs.com redeploy. It:
  1. Hits GET https://mascidocs.com/api/version and prints commit + hash
  2. Computes the same hash on local source (server.py + training_pdf.py + pdf_render.py)
  3. Compares → PASS (backend is current) or FAIL (backend is stale)
  4. If PASS, kicks off the full training-PDF audit against live
  5. Otherwise, tells you to redeploy before auditing

Usage:
    python3 scripts/post_deploy_check.py
    python3 scripts/post_deploy_check.py --base https://mascidocs.com
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACKED_FILES = [
    REPO_ROOT / "backend" / "server.py",
    REPO_ROOT / "backend" / "training_pdf.py",
    REPO_ROOT / "backend" / "pdf_render.py",
]


def local_source_hash() -> str:
    h = hashlib.md5()
    for p in TRACKED_FILES:
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def fetch_version(base: str) -> dict:
    req = urllib.request.Request(
        base.rstrip("/") + "/api/version",
        headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://mascidocs.com")
    args = ap.parse_args()

    print(f"Target: {args.base}")
    print("-" * 60)

    try:
        live = fetch_version(args.base)
    except Exception as e:
        print(f"FAIL — could not reach /api/version: {e}")
        print("  → backend may not have shipped the /api/version endpoint yet.")
        return 2

    local = local_source_hash()
    match = live.get("source_hash") == local

    print(f"  Live backend commit      : {live.get('commit', '?')}")
    print(f"  Live backend built_at    : {live.get('built_at', '?')}")
    print(f"  Live backend source_hash : {live.get('source_hash', '?')}")
    print(f"  Local source_hash        : {local}")
    print(f"  Live backend uptime      : {live.get('uptime_s', '?')} s")
    print("-" * 60)

    if not match:
        print("RESULT: ❌ STALE — live backend does NOT match local source.")
        print("  → Redeploy mascidocs.com to ship the current backend code.")
        return 1

    print("RESULT: ✅ FRESH — live backend source matches local.")

    # Also run the training-PDF audit when available
    audit_script = Path("/tmp/audit_live_pdfs.py")
    if audit_script.exists():
        print()
        print("=" * 60)
        print("Running training-PDF audit on live site...")
        print("=" * 60)
        r = subprocess.run(["python3", str(audit_script)])
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
