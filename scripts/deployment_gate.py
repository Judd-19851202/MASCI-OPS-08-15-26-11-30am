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
    # TRACK 15.79B · Daily Report delivery forensics (read-only proof
    # that ``schedule_auto_email`` is reaching the dispatcher).
    "/app/backend/tests/test_track_15_79b_dr_forensics.py",
    # TRACK 15.79C · schedule_auto_email task retention (the
    # asyncio.create_task weak-reference fix that closed the
    # "saved DR · no email · no audit row" silent failure).
    "/app/backend/tests/test_track_15_79c_dispatch_task_retention.py",
    # TRACK 15.79E · continuous production certification — per-workflow
    # VERIFIED / FAILED / NOT_YET_EXERCISED state derived from
    # trust_spine_events. Locks the "never auto-clear RED" rule.
    "/app/backend/tests/test_track_15_79e_production_certification.py",
    # TRACK 15.80 · permanent secret-exposure regression — scans every
    # tracked file for high-entropy secret literals and fails the
    # build if any are found. Locks the historical
    # ``PRODUCTION_SECRETS_SEALED.env.template`` leak class out of
    # the repo forever.
    "/app/backend/tests/test_track_15_80_no_secrets_in_repo.py",
    # TRACK 15.81 · Dispatch Map Portal Access Failure regression —
    # static guards prove no Dispatch component links to the admin-
    # only ``/operations-map`` URL, and live guards prove the Dispatch
    # token is accepted on ``/api/operations-map/*`` so the Dispatch-
    # owned ``/dispatch-portal/map`` page actually loads its data.
    "/app/backend/tests/test_track_15_81_dispatch_map_portal.py",
    # TRACK 15.82 · Dispatch Portal Layout + Roll-Off Operations —
    # static + unit guards covering the Dispatch-themed map breadcrumb
    # (Back to Dispatch Hub) and the Roll-Off taxonomy / alias / fleet-
    # family / marker classification.
    "/app/backend/tests/test_track_15_82_dispatch_layout_rolloff.py",
    # TRACK 15.82B · Dispatch landing-page Roll-Off Action Button —
    # closes the visible-UI gap left by 15.82 (taxonomy was added but
    # the dispatch home Issue Work card never rendered a Roll-Off tile).
    "/app/backend/tests/test_track_15_82b_dispatch_landing_rolloff_action.py",
    # TRACK 15.83 · Production Excellence Lockup — Project Intelligence
    # responsive guardrails (iPad/tablet bleed cure) + operator-visible
    # transfer filter (audit/validation/AUDIT-2 row suppression on the
    # dispatch operator surface). Does NOT delete production data; the
    # full unfiltered list is still reachable at /asset-transfers.
    "/app/backend/tests/test_track_15_83_production_excellence_lockup.py",
    # TRACK 15.83B · Production Excellence Completion Sweep — backend
    # canonical operator transfer-visibility helper + `?audience=
    # operator` opt-in on /api/operations/transfers and
    # /api/asset-transfers, stale dispatch-banner copy removed, preview/
    # demo route hardening, parity regressions for 15.81 / 15.82B /
    # 15.83.
    "/app/backend/tests/test_track_15_83b_production_excellence_sweep.py",
    # TRACK 15.84 · ForgedOps Production Excellence Certification —
    # static guardrails preventing rendered iter### labels on
    # production-facing pages (AdminLegacyImports, AdminGuide, broad
    # pages/*.jsx sweep) and preserving every 15.81 / 15.82B / 15.83 /
    # 15.83B parity. Honest scope: cross-portal six-pillar deep audit
    # deferred (documented in track cert) — this file locks the
    # discipline against regression.
    "/app/backend/tests/test_track_15_84_forgedops_production_excellence_certification.py",
    # TRACK 15.85 · Mandatory Full-Platform Production Excellence
    # Certification Program — PERSISTENT, multi-execution. Each
    # execution adds tests for the portals it actually browser-
    # verified at 3-breakpoint minimum. Execution #1: Safety Portal +
    # Trench Safety certified. Remaining portals tracked in
    # `memory/TRACK_15_85_MANDATORY_FULL_PLATFORM_PRODUCTION_EXCELLENCE_CERTIFICATION.md`.
    "/app/backend/tests/test_track_15_85_mandatory_full_platform_certification.py",
    # TRACK 15.86 · Continuous Browser Smoke Regression Gate — STATIC
    # meta-gate locking the shape of the headless Playwright runner at
    # ``backend/tests/browser_smoke/run_browser_smoke.py``. The runner
    # itself (real browser) is opt-in via MASCI_SMOKE_BROWSER=1 and
    # invoked separately by the nightly tier — the meta-gate locks the
    # canonical route list, breakpoints, every required assertion,
    # RBAC preservation, and the forbidden-strings + hydration
    # detector needles so the gate cannot silently weaken.
    "/app/backend/tests/test_track_15_86_browser_smoke_gate.py",
    # TRACK 15.87 · Multi-Portal Access Authority Fix — P0 trust/auth
    # defect. Before this track, Admin → People & Access could grant
    # `pm` / `shop` / `hr` / `safety` / `dispatch` to a user but the
    # corresponding legacy login endpoint (`POST /api/{portal}/login`)
    # only checked the dedicated legacy collection plus an admin-only
    # directory fallback, so a directory-granted user without a row
    # in the legacy collection was denied with 401. This file locks
    # the new canonical helper at `lib/directory_portal_login.py` and
    # the wiring across all five portal-login endpoints + their
    # routers, plus the RBAC invariant that granting one portal does
    # NOT unlock another. Static-only (no DB writes), <100 ms.
    "/app/backend/tests/test_track_15_87_multi_portal_access_authority.py",
    # TRACK 15.88 · People & Access Credential Usability Clarity —
    # surfaces backend-derived `credential_state` / `usable_now` /
    # `blocked_reason` on every Admin People & Access row so admins
    # can tell at a glance which users can actually sign in vs which
    # ones are blocked and why (never_issued · change_required ·
    # disabled · no_portal_access). Static-only, <100 ms.
    "/app/backend/tests/test_track_15_88_people_access_credential_usability_clarity.py",
    # TRACK 15.93 · Zero-Touch Production Deployment Hardening —
    # eliminates the manual seed dependency. On every startup the
    # canonical bootstrap (`lib/system_bootstrap.py`) guarantees
    # required system records exist (today: email_routes catalog)
    # before the readiness flag flips. Idempotent. Admin-safe (never
    # overwrites `source=admin` rows). Never deletes. Critical-route
    # safety enforced. Persists to `system_bootstrap_status` +
    # `system_bootstrap_history`. Readiness gate blocks deploy when
    # bootstrap incomplete.
    "/app/backend/tests/test_track_15_93_zero_touch_bootstrap.py",
    # TRACK 15.95 · Operations Map phone-overflow fix — closes
    # PROD-15.94-BS01. Locks the .ops-map-banner mobile rule to use
    # `repeat(3, minmax(0, 1fr))` and adds a <=480px 2-column
    # collapse so the top stat banner cannot push past a phone-390
    # viewport. Also asserts the Track 15.83 iPad bleed fix + 15.86
    # smoke gate + 15.93 bootstrap remain intact (no weakening).
    "/app/backend/tests/test_track_15_95_operations_map_phone_overflow.py",
    # TRACK 15.97 · GitHub Actions production-health-probe repair —
    # consolidates the dual-workflow (real + PR noop) into one file,
    # removes the job-level `if:` guard that produced the canonical
    # GitHub "this check has no steps" empty-job failure, and locks
    # step-level gating + secret-handling invariants.
    "/app/backend/tests/test_track_15_97_github_actions_health_probe.py",
    # TRACK 16.00 · GitHub Repository Lifecycle Hardening — replaces
    # the consolidated 15.97 workflow with a self-silencing pattern
    # gated by the `vars.ACTIVE_PRODUCTION_SOURCE` GitHub variable.
    # Repository variables are NOT copied to snapshots/forks so every
    # future Emergent snapshot becomes operationally silent from
    # creation, with zero customer cleanup ever required. Also locks
    # the lifecycle-manager CLI contract (env-only token, no active-
    # repo mutation, snapshot-only targeting).
    "/app/backend/tests/test_track_16_00_github_lifecycle_hardening.py",
    # TRACK 16.04 · MASCI Transportation Foundation Phase 1 — locks the
    # carriers / transport_persons / transport_trucks / eligibility
    # skeleton data model, identity dedup, audit, and RBAC posture.
    "/app/backend/tests/test_track_16_04_transportation_foundation.py",
    # TRACK 16.05 · Transportation Onboarding & Compliance Center (Phase 2)
    # — rate schedules, carrier+driver documents (R2), packet workflow,
    # MASCI Hauler Truck Readiness Inspection, eligibility integration.
    "/app/backend/tests/test_track_16_05_transportation_onboarding_compliance_center.py",
    # TRACK 16.06 · Transportation Experience Layer — Compliance Center UI
    # router, dashboard/document/inspection/audit aggregation endpoints,
    # carrier/driver/truck workspaces, no duplicate identity/storage/audit.
    "/app/backend/tests/test_track_16_06_transportation_experience_layer.py",
    # TRACK 16.07 · Transportation Workflow Activation — inline Readiness
    # Inspection wizard, drag-and-drop document upload, signature pad,
    # rate-create dialog, per-entity compliance timeline, packet checklist.
    "/app/backend/tests/test_track_16_07_transportation_workflow_activation.py",
    "/app/backend/tests/test_track_16_08_transportation_orientation.py",
    "/app/backend/tests/test_track_16_09_transportation_dispatch_gate_email_pilot.py",
    "/app/backend/tests/test_track_16_10_transportation_automation_engine.py",
    "/app/backend/tests/test_track_16_10a_transport_command_digest.py",
    "/app/backend/tests/test_track_16_11_transport_hr_lifecycle_integration.py",
    "/app/backend/tests/test_track_16_11A_transport_sync_monitor.py",
    "/app/backend/tests/test_track_16_12_transport_operations_intelligence.py",
    "/app/backend/tests/test_track_16_13_dispatch_decision_surface.py",
    "/app/backend/tests/test_track_16_14_dispatcher_learning_loop.py",
    "/app/backend/tests/test_track_16_15_operational_cleanup_companion.py",
    "/app/backend/tests/test_track_16_15a_dashboard_cleanup_signal_mirror.py",
    "/app/backend/tests/test_track_16_16_operations_transportation_integration.py",
    "/app/backend/tests/test_track_17_00_transportation_audit_artifacts.py",
    "/app/backend/tests/test_track_18_00_phase_a_universal_shell.py",
    "/app/backend/tests/test_track_18_00_phase_b_mission_control.py",
    "/app/backend/tests/test_track_18_00_phase_c_universal_search.py",
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


def append_to_ledger(
    base_url: str,
    admin_token: str | None,
    report: Dict[str, Any],
    duration_ms: int,
) -> Dict[str, Any] | None:
    """TRACK 15.79 — best-effort append to the immutable deployment
    ledger. Never raises; the ledger is a forensic side-channel and
    must not be allowed to block a passing gate from exiting cleanly."""
    if not admin_token:
        return None
    runtime = report.get("runtime") or {}
    blocking = runtime.get("blocking_gates") or []
    advisory = runtime.get("advisory_findings") or []
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd="/app", capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        commit = ""
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd="/app", capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        branch = ""
    payload = {
        "decision": report.get("decision", "fail"),
        "exit_code": int(report.get("exit_code", 1)),
        "commit": commit,
        "branch": branch,
        "environment": os.environ.get("DEPLOY_ENV", "preview"),
        "operator": (
            os.environ.get("OPS_ADMIN_EMAIL")
            or os.environ.get("DEPLOY_OPERATOR", "ci")
        ),
        "duration_ms": duration_ms,
        "trust_score": int(runtime.get("trust_score") or 0),
        "trust_band": runtime.get("trust_band") or "",
        "blocking_count": len(blocking),
        "advisory_count": len(advisory),
        "regression_count": int(runtime.get("regression_gate_count") or 0),
        "blocking_ids": [g.get("id") for g in blocking][:32],
    }
    try:
        req = urllib.request.Request(
            f"{base_url}/api/admin/deployment-readiness/snapshot",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Admin-Token": admin_token,
                "User-Agent": "deployment-gate/15.79",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except Exception:
        return None


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
    parser.add_argument(
        "--no-ledger", action="store_true",
        help="skip TRACK 15.79 append to deployment_decisions",
    )
    args = parser.parse_args()

    import time  # noqa: PLC0415
    started_at = time.time()
    report: Dict[str, Any] = {
        "decision": "pass",
        "regression": None,
        "runtime": None,
        "exit_code": 0,
    }
    admin_token: str | None = None

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
            admin_token = resolve_admin_token(args.base_url)
            payload = fetch_runtime(args.base_url, admin_token)
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

    duration_ms = int((time.time() - started_at) * 1000)
    report["duration_ms"] = duration_ms

    # ── TRACK 15.79 · Ledger append (best-effort, never blocks) ────
    if not args.no_ledger and admin_token is None:
        # If runtime layer was skipped via --no-runtime, still try to
        # resolve a token so the ledger can record the regression-only
        # invocation.
        admin_token = resolve_admin_token(args.base_url)
    if not args.no_ledger and admin_token:
        report["ledger"] = append_to_ledger(
            args.base_url, admin_token, report, duration_ms,
        )

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
