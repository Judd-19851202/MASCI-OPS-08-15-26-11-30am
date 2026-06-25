#!/usr/bin/env python3
"""TRACK 15.78 · Deployment Trust Gate · CLI enforcement entry point.

This is the **canonical script** every production deployment must
run. Exits with status code 0 on PASS, non-zero on FAIL. CI/CD
pipelines should wire this in as a pre-deploy step:

    $ python3 scripts/deployment_gate.py
      [ ... runs the 69-gate pytest suite ... ]
      [ ... fetches /api/admin/deployment-readiness ... ]
      [ ... prints PASS/FAIL with evidence ... ]

Two enforcement layers:

  1. **Regression layer** — runs every Track 15.7x regression file
     (the permanent gate list). Any failure = deploy blocked.
  2. **Runtime layer** — calls the live ``/api/admin/deployment-
     readiness`` endpoint. Any ``blocking_gates`` entry = deploy
     blocked.

Operator data issues (no PM assigned, etc.) are **surfaced** but
**never block** — they are not platform code defects. The endpoint
classifies findings into ``blocking_gates`` vs ``advisory_findings``
so the gate decision is unambiguous.

Usage:
  python3 scripts/deployment_gate.py
  python3 scripts/deployment_gate.py --no-regression   # runtime only
  python3 scripts/deployment_gate.py --no-runtime      # regression only
  python3 scripts/deployment_gate.py --json            # JSON output
  python3 scripts/deployment_gate.py --base-url URL    # override

Exit codes:
  0  ALL GATES PASS — deploy permitted.
  1  Regression failure — at least one test gate failed.
  2  Runtime failure — at least one blocking_gates entry on the
     live endpoint.
  3  Unable to reach the live endpoint (config / network).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List


REGRESSION_FILES = [
    "/app/backend/tests/test_track_15_76_trust_spine.py",
    "/app/backend/tests/test_track_15_76_trust_spine_extended.py",
    "/app/backend/tests/test_track_15_76_email_render_wl_regression.py",
    "/app/backend/tests/test_track_15_76a_operations_trust_center.py",
    "/app/backend/tests/test_track_15_76b_finalization.py",
    "/app/backend/tests/test_track_15_77_production_lock.py",
    "/app/backend/tests/test_track_15_78_deployment_gate.py",
]

DEFAULT_BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or "http://localhost:8001"
)


def run_regression() -> Dict[str, Any]:
    """Run the permanent regression suite. Returns ``{passed, output}``."""
    cmd = ["python", "-m", "pytest", "-q", "--timeout", "30"] + [
        p for p in REGRESSION_FILES if os.path.exists(p)
    ]
    proc = subprocess.run(
        cmd,
        cwd="/app/backend",
        capture_output=True,
        text=True,
        timeout=600,
    )
    return {
        "passed": proc.returncode == 0,
        "returncode": proc.returncode,
        "tail": (proc.stdout + proc.stderr)[-2000:],
    }


def fetch_runtime(base_url: str, admin_token: str | None) -> Dict[str, Any]:
    """Fetch the live deployment-readiness payload. Returns the parsed
    JSON or raises."""
    req = urllib.request.Request(
        f"{base_url}/api/admin/deployment-readiness",
        headers={
            "X-Admin-Token": admin_token or "",
            "User-Agent": "deployment-gate/15.78",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def resolve_admin_token(base_url: str) -> str | None:
    """Best-effort admin token: try OPS_ADMIN_TOKEN env, then a super-
    admin multi-login if OPS_ADMIN_EMAIL/PASSWORD are available."""
    tok = os.environ.get("OPS_ADMIN_TOKEN")
    if tok:
        return tok
    email = os.environ.get("OPS_ADMIN_EMAIL")
    password = os.environ.get("OPS_ADMIN_PASSWORD")
    if not (email and password):
        return None
    req = urllib.request.Request(
        f"{base_url}/api/auth/multi-login",
        data=json.dumps({"email": email, "password": password}).encode(),
        headers={
            "Content-Type": "application/json",
            # Some preview deployments require a non-empty UA.
            "User-Agent": "deployment-gate/15.78",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.load(resp)
        return (body.get("portal_tokens") or {}).get("admin")
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-regression", action="store_true")
    parser.add_argument("--no-runtime", action="store_true")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--json", dest="emit_json", action="store_true")
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "decision": "pass",
        "regression": None,
        "runtime": None,
        "exit_code": 0,
    }

    # ── Regression layer ────────────────────────────────────────────
    if not args.no_regression:
        reg = run_regression()
        report["regression"] = reg
        if not reg["passed"]:
            report["decision"] = "fail"
            report["exit_code"] = 1

    # ── Runtime layer ───────────────────────────────────────────────
    if not args.no_runtime and report["exit_code"] == 0:
        try:
            tok = resolve_admin_token(args.base_url)
            payload = fetch_runtime(args.base_url, tok)
            report["runtime"] = payload
            if payload.get("decision") != "pass":
                report["decision"] = "fail"
                report["exit_code"] = 2
        except urllib.error.HTTPError as exc:
            report["runtime_error"] = (
                f"HTTPError {exc.code} on /api/admin/deployment-readiness"
            )
            report["decision"] = "fail"
            report["exit_code"] = 3
        except Exception as exc:  # noqa: BLE001
            report["runtime_error"] = str(exc)
            report["decision"] = "fail"
            report["exit_code"] = 3

    if args.emit_json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_human(report)
    return report["exit_code"]


def _print_human(report: Dict[str, Any]) -> None:
    decision = report.get("decision", "fail").upper()
    bar = "═" * 60
    print(bar)
    print(f"  MASCI · DEPLOYMENT TRUST GATE · TRACK 15.78")
    print(f"  DECISION: {decision}")
    print(bar)
    reg = report.get("regression")
    if reg:
        print(
            f"  Regression suite:  "
            f"{'PASS' if reg['passed'] else 'FAIL'} "
            f"(exit={reg.get('returncode')})"
        )
        if not reg["passed"]:
            print(reg["tail"])
    rt = report.get("runtime")
    if rt:
        b = rt.get("blocking_gates") or []
        a = rt.get("advisory_findings") or []
        print(
            f"  Runtime gates:     "
            f"{'PASS' if rt.get('decision') == 'pass' else 'FAIL'} "
            f"(blocking={len(b)}, advisory={len(a)})"
        )
        for g in b:
            print(f"    ✖ [{g.get('category'):14s}] {g.get('summary')}")
            print(f"        → {g.get('remediation')}")
        if a:
            print(f"  Advisory (does NOT block deploy):")
            for g in a[:8]:
                print(f"    ! [{g.get('category'):14s}] {g.get('summary')}")
        print(
            f"  Trust score: {rt.get('trust_score')} · "
            f"band: {rt.get('trust_band')} · "
            f"regression gates: {rt.get('regression_gate_count')}"
        )
    err = report.get("runtime_error")
    if err:
        print(f"  Runtime error:     {err}")
    print(bar)
    if decision == "PASS":
        print("  ✅ All deployment gates satisfied — deploy permitted.")
    else:
        print("  ❌ Deployment blocked. Fix the issues above and re-run.")
    print(bar)


if __name__ == "__main__":
    sys.exit(main())
