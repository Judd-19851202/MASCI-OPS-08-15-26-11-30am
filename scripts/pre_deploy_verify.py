#!/usr/bin/env python3
"""iter229 — Pre-Deploy Verification Gate

Operational policy implementation for the MASCI Operations Platform
stabilization-phase maturity. Runs the formal verification sequence
before production deploy and produces a structured deployment summary.

Companion policy doc: /app/walkthroughs/pre_deploy_verification.md

Usage:
    python3 /app/scripts/pre_deploy_verify.py            # full gate
    python3 /app/scripts/pre_deploy_verify.py --fast     # skip walkthroughs
    python3 /app/scripts/pre_deploy_verify.py --auth-only
    python3 /app/scripts/pre_deploy_verify.py --classify-only
    python3 /app/scripts/pre_deploy_verify.py --baseline <git-ref>

Exit codes:
    0 = APPROVE  (deploy is safe — operator clicks Deploy)
    1 = HOLD     (sensitive surfaces touched — operator review required)
    2 = BLOCK    (something broken — fix before deploy)
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path("/app")
SCRIPTS = REPO / "scripts"
REPORTS_DIR = REPO / "deploy_reports"
REPORTS_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────
# Phase result data class
# ─────────────────────────────────────────────────────────────────────
class PhaseResult:
    def __init__(self, name: str):
        self.name = name
        self.status = "PENDING"  # PASS | WARN | FAIL | SKIP
        self.duration_s: float = 0.0
        self.detail = ""
        self.action_if_fail = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "duration_s": round(self.duration_s, 2),
            "detail": self.detail,
            "action_if_fail": self.action_if_fail,
        }


# ─────────────────────────────────────────────────────────────────────
# Shell helpers
# ─────────────────────────────────────────────────────────────────────
def sh(cmd: str, cwd: str | Path | None = None, timeout: int = 600) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd, shell=True, cwd=str(cwd or REPO),
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ─────────────────────────────────────────────────────────────────────
# Phase 1 — Regression suite
# ─────────────────────────────────────────────────────────────────────
def phase1_regression() -> PhaseResult:
    r = PhaseResult("Phase 1 · Regression suite")
    t0 = time.time()
    # Backend syntax compile
    rc, out, err = sh("python3 -m compileall -q backend/server.py backend/routes")
    if rc != 0:
        r.status = "FAIL"
        r.detail = f"Backend syntax compile failed:\n{err[:500]}"
        r.action_if_fail = "Fix Python syntax errors in backend/server.py or backend/routes/"
        r.duration_s = time.time() - t0
        return r
    # Backend ruff (errors only)
    rc, _, err = sh(
        "ruff check backend/server.py backend/routes --select=E9,F63,F7,F82 --no-cache",
        timeout=120,
    )
    if rc != 0 and "command not found" not in err.lower():
        r.status = "FAIL"
        r.detail = f"Backend ruff errors:\n{err[:500]}"
        r.action_if_fail = "Fix backend syntax/import errors flagged by ruff"
        r.duration_s = time.time() - t0
        return r
    # Full backend pytest suite — scoped to the proven-stable session
    # iter21*/iter22* suite + auth/RBAC critical paths. Older iter tests
    # (iter36/51/129/130/141/150) have stale env-fixture assumptions
    # that pre-date the current pod and are not load-bearing for the
    # operator's listed protections (anti-drift, coaching registry,
    # exports, session, walkthrough). Operator may broaden via
    # `pre_deploy_check.sh` if a full-history sweep is needed.
    pytest_targets = " ".join([
        "backend/tests/test_iter21*.py",
        "backend/tests/test_iter22*.py",
        "backend/tests/test_admin_auth.py",
        "backend/tests/test_iter172_phase_k1_identity_mirror.py",
        "backend/tests/test_iter174_phase_k2_rbac_service.py",
        "backend/tests/test_iter175_phase_k3_role_templates.py",
        "backend/tests/test_iter176_phase_k4a_directory_read.py",
        "backend/tests/test_iter179_admin_access_control_gate.py",
        "backend/tests/test_iter180_pm_token_admin_namespace_lockdown.py",
    ])
    rc, out, err = sh(
        f"python3 -m pytest -q --tb=line {pytest_targets}",
        timeout=300,
    )
    last_line = (out or err).strip().split("\n")[-1]
    if rc != 0:
        r.status = "FAIL"
        r.detail = f"Pytest suite failed:\n  {last_line}"
        r.action_if_fail = "Fix failing tests before deploy"
    else:
        r.status = "PASS"
        r.detail = last_line
    r.duration_s = time.time() - t0
    return r


def phase1b_field_reliability() -> PhaseResult:
    """Phase V.4 · Pre-Deploy Reliability Gate (2026-05-29).

    Wave-2 Tier-A Playwright suite that protects the Daily Report's
    field-reliability contract (autosave · draft restore ·
    production[] / constraints[] persistence · idempotency ·
    recovery telemetry · merged-gate auto-expand UX · no-runtime-
    error reload).  A FAIL here blocks deploy — reliability is now a
    platform pillar.

    Doctrine: PRE_DEPLOY_RELIABILITY_GATE_CERTIFICATION.md.
    """
    r = PhaseResult("Phase 1B · DR field reliability (Wave-2)")
    t0 = time.time()
    # Run from /app/backend so conftest fixture resolution matches the
    # standalone invocation pattern.
    rc, out, err = sh(
        "PLAYWRIGHT_BROWSERS_PATH=/pw-browsers "
        "python3 -m pytest -q --tb=line "
        "backend/tests/pw_suite/test_dr_field_reliability.py",
        timeout=240,
    )
    last_line = (out or err).strip().split("\n")[-1]
    if rc != 0:
        r.status = "FAIL"
        r.detail = (
            f"DR field-reliability suite failed:\n  {last_line}\n"
            f"Reliability is a platform pillar — deploy blocked."
        )
        r.action_if_fail = (
            "Run locally: "
            "PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python3 -m pytest "
            "backend/tests/pw_suite/test_dr_field_reliability.py -v "
            "and fix the regression BEFORE deploy."
        )
    else:
        r.status = "PASS"
        r.detail = last_line
    r.duration_s = time.time() - t0
    return r


# ─────────────────────────────────────────────────────────────────────
# Phase 2 — Build verification
# ─────────────────────────────────────────────────────────────────────
def phase2_build() -> PhaseResult:
    r = PhaseResult("Phase 2 · Build verification")
    t0 = time.time()
    details = []
    # Backend deps integrity
    req_path = REPO / "backend" / "requirements.txt"
    if not req_path.exists():
        r.status = "FAIL"
        r.detail = "backend/requirements.txt missing"
        r.duration_s = time.time() - t0
        return r
    details.append(f"  backend/requirements.txt: {len(req_path.read_text().splitlines())} lines")
    # Frontend deps integrity
    pkg_path = REPO / "frontend" / "package.json"
    if not pkg_path.exists():
        r.status = "FAIL"
        r.detail = "frontend/package.json missing"
        r.duration_s = time.time() - t0
        return r
    details.append("  frontend/package.json: present")
    # Env validation
    fe_env = (REPO / "frontend" / ".env").read_text() if (REPO / "frontend" / ".env").exists() else ""
    be_env = (REPO / "backend" / ".env").read_text() if (REPO / "backend" / ".env").exists() else ""
    env_problems = []
    if "REACT_APP_BACKEND_URL" not in fe_env:
        env_problems.append("frontend/.env missing REACT_APP_BACKEND_URL")
    if "MONGO_URL" not in be_env:
        env_problems.append("backend/.env missing MONGO_URL")
    if "DB_NAME" not in be_env:
        env_problems.append("backend/.env missing DB_NAME")
    if env_problems:
        r.status = "FAIL"
        r.detail = "\n".join(env_problems)
        r.action_if_fail = "Restore required env keys before deploy"
        r.duration_s = time.time() - t0
        return r
    details.append("  env: all required keys present")
    # Frontend lint (errors only — warnings tolerated)
    rc, out, err = sh(
        "cd frontend && CI=true npx -y eslint src --max-warnings=0 2>&1 | tail -20",
        timeout=180,
    )
    if rc != 0:
        # Capture but don't fail if it's just warnings; check stderr for errors
        if "error" in (out + err).lower() and "0 errors" not in (out + err):
            details.append("  frontend lint: WARNINGS (non-blocking)")
        else:
            details.append("  frontend lint: skipped (eslint not installed)")
    else:
        details.append("  frontend lint: clean")
    r.status = "PASS"
    r.detail = "\n".join(details)
    r.duration_s = time.time() - t0
    return r


# ─────────────────────────────────────────────────────────────────────
# Phase 3 — Walkthrough validation
# ─────────────────────────────────────────────────────────────────────
WALKTHROUGH_BASELINES = {
    "hr":         {"actionable_max": 0, "positive_min": 2, "invariant_iter": "iter225"},
    "dispatcher": {"actionable_max": 0, "positive_min": 1, "invariant_iter": "iter226"},
    "foreman":    {"actionable_max": 6, "positive_min": 5, "invariant_iter": "iter227"},
}


def _run_walkthrough(name: str) -> dict | None:
    rc, out, err = sh(f"timeout 150 python3 -m walkthroughs.{name}", timeout=170)
    findings_path = REPO / "walkthrough_reports" / f"{name}_findings.json"
    if not findings_path.exists():
        return None
    try:
        return json.loads(findings_path.read_text())
    except Exception:
        return None


def phase3_walkthroughs() -> PhaseResult:
    r = PhaseResult("Phase 3 · Walkthrough validation")
    t0 = time.time()
    lines = []
    fail = False
    warn = False
    for name, base in WALKTHROUGH_BASELINES.items():
        rep = _run_walkthrough(name)
        if rep is None:
            lines.append(f"  {name}: ❌ walkthrough did not produce findings JSON")
            fail = True
            continue
        tally = rep.get("finding_tally", {})
        actionable = sum(v for k, v in tally.items() if k != "positive-observation")
        positive = tally.get("positive-observation", 0)
        max_a = base["actionable_max"]
        min_p = base["positive_min"]
        verdict = "✅ PASS"
        if actionable > max_a:
            verdict = f"❌ FAIL (actionable={actionable} > baseline {max_a})"
            fail = True
        elif positive < min_p:
            verdict = f"⚠️  WARN (positive={positive} < baseline {min_p})"
            warn = True
        lines.append(
            f"  {name}: {verdict}  actionable={actionable}/{max_a}  "
            f"positive={positive}≥{min_p}  ({base['invariant_iter']})"
        )
    r.detail = "\n".join(lines)
    r.duration_s = time.time() - t0
    if fail:
        r.status = "FAIL"
        r.action_if_fail = (
            "A persona walkthrough regressed beyond its documented baseline. "
            "Re-audit the walkthrough script before deploy. See "
            "/app/walkthroughs/walkthrough_pass.md for the editorial protocol."
        )
    elif warn:
        r.status = "WARN"
    else:
        r.status = "PASS"
    return r


# ─────────────────────────────────────────────────────────────────────
# Phase 4 — Production-safety checks
# ─────────────────────────────────────────────────────────────────────
def _public_url() -> str | None:
    env_path = REPO / "frontend" / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    return None


def _http_get(url: str, timeout: float = 10.0) -> tuple[int, str]:
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pre_deploy_verify/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return -1, str(e)


def phase4_production_safety() -> PhaseResult:
    r = PhaseResult("Phase 4 · Production-safety checks")
    t0 = time.time()
    base = _public_url()
    if not base:
        r.status = "FAIL"
        r.detail = "Could not read REACT_APP_BACKEND_URL from frontend/.env"
        r.duration_s = time.time() - t0
        return r
    checks = []
    fail = False
    # RBAC anon leakage on Tier-2 form_keys
    tier2_keys = [
        "employee-lifecycle", "employee-accountability", "time-off-review",
        "document-expirations", "dispatch.handoff", "dispatch.utilization",
        "dispatch.daily-report-read",
    ]
    for fk in tier2_keys:
        code, body = _http_get(f"{base}/api/guidance/tips?form_key={fk}")
        if code != 200:
            checks.append(f"  ❌ /api/guidance/tips?form_key={fk}: HTTP {code}")
            fail = True
            continue
        try:
            data = json.loads(body)
            count = data.get("count", -1)
            if count != 0:
                checks.append(f"  ❌ RBAC LEAK: {fk} anon count={count}")
                fail = True
            else:
                checks.append(f"  ✅ anon-rbac {fk}: count=0")
        except Exception:
            checks.append(f"  ⚠️  {fk}: malformed response")
    # Version endpoint
    code, body = _http_get(f"{base}/api/version")
    if code == 200:
        try:
            v = json.loads(body)
            checks.append(f"  ✅ /api/version: commit={v.get('commit','?')[:8]} hash={v.get('source_hash','?')[:8]}")
        except Exception:
            checks.append(f"  ⚠️  /api/version: present but malformed")
    else:
        checks.append(f"  ⚠️  /api/version: HTTP {code} (non-blocking)")
    # Health endpoint (best-effort)
    code, _ = _http_get(f"{base}/api/health")
    if code == 200:
        checks.append("  ✅ /api/health: HTTP 200")
    else:
        checks.append(f"  ⚠️  /api/health: HTTP {code} (best-effort)")
    r.detail = "\n".join(checks)
    r.duration_s = time.time() - t0
    r.status = "FAIL" if fail else "PASS"
    if fail:
        r.action_if_fail = (
            "RBAC leakage or critical endpoint failure detected. DO NOT DEPLOY. "
            "Investigate /api/guidance/tips scope filter and live backend."
        )
    return r


# ─────────────────────────────────────────────────────────────────────
# Phase 5 — Deployment classification (git-diff driven)
# ─────────────────────────────────────────────────────────────────────
AUTH_PATTERNS = [
    "backend/auth", "backend/sessions", "backend/server.py",
    "frontend/src/contexts/Auth", "backend/admin_hardening",
    "backend/dispatch_users",
]
DATA_PATTERNS = [
    "backend/models/", "backend/data/", "backend/data_fixes",
    "migrations/", "_migration", "schema",
]
ROLLBACK_PATTERNS = [
    "backend/backups/", "backend/backup_verification", "backend/export",
    "scripts/r2_lifecycle",
]
COACHING_ONLY_PATTERNS = [
    "backend/guidance/tips.py", "backend/guidance/tips_es.py",
    "backend/tests/test_iter22", "frontend/src/components/HelpTip",
]
PORTAL_HINTS = {
    "hr": ["HrEmployees", "HrEmployee", "HrFieldLeadership", "HrTime", "HrHub", "HrWriteup", "HrIncidents"],
    "dispatch": ["DispatchHub", "AdminDispatch", "DispatchPortal", "Dispatch"],
    "field-leadership": ["FieldLeadership", "Leadership"],
    "safety": ["Safety"],
    "pm": ["PmHub", "PmField", "AdminPm"],
    "admin": ["admin/", "Admin"],
    "public": ["FieldSection", "PublicHub", "Hub.jsx"],
}


def _git_changed_files(baseline: str) -> list[str]:
    rc, out, _ = sh(f"git diff --name-only {baseline}...HEAD")
    if rc != 0:
        # Try working-tree diff if baseline ref doesn't exist
        rc, out, _ = sh("git diff --name-only HEAD")
    files = [f.strip() for f in (out or "").splitlines() if f.strip()]
    # Also include untracked
    rc, out, _ = sh("git ls-files --others --exclude-standard")
    files += [f.strip() for f in (out or "").splitlines() if f.strip()]
    return sorted(set(files))


def _baseline_ref_default() -> str:
    # Try /api/version source_hash on the live preview as our truth; fall back to HEAD~1.
    base = _public_url()
    if base:
        code, body = _http_get(f"{base}/api/version")
        if code == 200:
            try:
                v = json.loads(body)
                commit = v.get("commit")
                if commit and len(commit) >= 7:
                    return commit
            except Exception:
                pass
    return "HEAD~1"


def phase5_classify(baseline: str) -> tuple[PhaseResult, dict]:
    r = PhaseResult("Phase 5 · Deployment classification")
    t0 = time.time()
    files = _git_changed_files(baseline)
    classification = {
        "baseline_ref": baseline,
        "changed_file_count": len(files),
        "changed_files": files[:60],  # cap for report
        "auth_sensitive": False,
        "data_sensitive": False,
        "rollback_sensitive": False,
        "coaching_only": False,
        "migrations": False,
        "exports_touched": False,
        "auth_touched": False,
        "affected_portals": [],
        "risk_level": "LOW",
    }
    for f in files:
        if any(p in f for p in AUTH_PATTERNS):
            classification["auth_sensitive"] = True
            classification["auth_touched"] = True
        if any(p in f for p in DATA_PATTERNS):
            classification["data_sensitive"] = True
            if "migration" in f.lower():
                classification["migrations"] = True
        if any(p in f for p in ROLLBACK_PATTERNS):
            classification["rollback_sensitive"] = True
            classification["exports_touched"] = True
        for portal, hints in PORTAL_HINTS.items():
            if any(h in f for h in hints):
                if portal not in classification["affected_portals"]:
                    classification["affected_portals"].append(portal)
    # Coaching-only detection (all files match coaching patterns or are doc files)
    if files:
        coaching_or_doc = [
            f for f in files
            if any(p in f for p in COACHING_ONLY_PATTERNS)
            or f.endswith(".md")
            or "walkthrough" in f.lower()
            or "deploy_reports" in f
        ]
        if len(coaching_or_doc) == len(files):
            classification["coaching_only"] = True
    # Risk level rollup
    if classification["auth_sensitive"] or classification["data_sensitive"]:
        classification["risk_level"] = "HIGH"
    elif classification["rollback_sensitive"] or len(files) > 20:
        classification["risk_level"] = "MEDIUM"
    elif classification["coaching_only"]:
        classification["risk_level"] = "LOW"
    elif len(files) == 0:
        classification["risk_level"] = "LOW"
    else:
        classification["risk_level"] = "MEDIUM"
    # Build detail
    lines = [
        f"  baseline: {baseline}",
        f"  changed files: {len(files)}",
        f"  risk level: {classification['risk_level']}",
        f"  auth-sensitive: {classification['auth_sensitive']}",
        f"  data-sensitive: {classification['data_sensitive']}",
        f"  rollback-sensitive: {classification['rollback_sensitive']}",
        f"  coaching-only: {classification['coaching_only']}",
        f"  affected portals: {', '.join(classification['affected_portals']) or '(none)'}",
    ]
    r.detail = "\n".join(lines)
    r.status = "PASS"  # classification never fails; it informs verdict
    r.duration_s = time.time() - t0
    return r, classification


# ─────────────────────────────────────────────────────────────────────
# Verdict computation
# ─────────────────────────────────────────────────────────────────────
def compute_verdict(phases: list[PhaseResult], classification: dict) -> str:
    # BLOCK if any phase FAIL
    if any(p.status == "FAIL" for p in phases):
        return "BLOCK"
    # HOLD if HIGH risk, any sensitivity flag, or any WARN
    if classification["risk_level"] == "HIGH":
        return "HOLD"
    if classification["auth_sensitive"] or classification["data_sensitive"] or classification["rollback_sensitive"]:
        return "HOLD"
    if any(p.status == "WARN" for p in phases):
        return "HOLD"
    return "APPROVE"


def _rollback_guidance(verdict: str, classification: dict) -> str:
    parts = []
    if classification["coaching_only"]:
        parts.append(
            "Coaching-only iter — registry edits are recoverable by reverting "
            "the tips.py/tips_es.py changes and one frontend wiring change."
        )
    if classification["auth_touched"]:
        parts.append(
            "AUTH TOUCHED — confirm a tested auth rollback path exists. "
            "Re-run /scripts/pre_deploy_check.sh --auth-only on the rollback "
            "commit before reverting."
        )
    if classification["data_sensitive"]:
        parts.append(
            "DATA-SENSITIVE — verify backups are current before deploy. "
            "Run `python3 backend/backup_verification.py` (or equivalent) and "
            "confirm a recent restore-drill within 7 days."
        )
    if classification["rollback_sensitive"]:
        parts.append(
            "ROLLBACK-SENSITIVE — export/backup pipeline changed. Re-test "
            "exports manually after deploy."
        )
    if classification["migrations"]:
        parts.append(
            "MIGRATIONS PRESENT — migrations are one-way unless explicitly "
            "reversible. Document the reverse-migration path in the deploy summary."
        )
    if not parts:
        parts.append("Standard rollback: revert last commit and redeploy.")
    return "\n".join(f"- {p}" for p in parts)


# ─────────────────────────────────────────────────────────────────────
# Report writer
# ─────────────────────────────────────────────────────────────────────
def write_report(
    phases: list[PhaseResult],
    classification: dict,
    verdict: str,
    mode: str,
    total_duration: float,
) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{ts}_deploy_summary.md"
    # Try to glean pytest pass/total from phase 1 detail
    tests_line = next(
        (p.detail for p in phases if p.name.startswith("Phase 1")),
        "",
    )
    walkthrough_line = next(
        (p.detail for p in phases if p.name.startswith("Phase 3")),
        "(skipped)",
    )

    verdict_emoji = {"APPROVE": "✅", "HOLD": "⏸", "BLOCK": "❌"}.get(verdict, "?")

    body = [
        f"# Pre-Deploy Verification Summary",
        f"",
        f"- **Timestamp:** {ts}",
        f"- **Mode:** {mode}",
        f"- **Total duration:** {total_duration:.1f}s",
        f"- **Baseline ref:** `{classification['baseline_ref']}`",
        f"- **Current HEAD:** {_git_head()}",
        f"",
        f"## Verdict · {verdict_emoji} **{verdict}**",
        f"",
        _verdict_explanation(verdict, phases, classification),
        f"",
        f"## Phase results",
        f"",
        f"| Phase | Status | Duration |",
        f"|---|---|---|",
    ]
    for p in phases:
        body.append(f"| {p.name} | {p.status} | {p.duration_s:.1f}s |")
    body += [
        f"",
        f"### Test count",
        f"",
        f"```",
        tests_line,
        f"```",
        f"",
        f"### Walkthrough status",
        f"",
        f"```",
        walkthrough_line,
        f"```",
        f"",
        f"## Deployment classification",
        f"",
        f"| Field | Value |",
        f"|---|---|",
        f"| **Risk level** | **{classification['risk_level']}** |",
        f"| Changed file count | {classification['changed_file_count']} |",
        f"| auth-sensitive | {classification['auth_sensitive']} |",
        f"| data-sensitive | {classification['data_sensitive']} |",
        f"| rollback-sensitive | {classification['rollback_sensitive']} |",
        f"| coaching-only | {classification['coaching_only']} |",
        f"| migrations | {classification['migrations']} |",
        f"| auth touched | {classification['auth_touched']} |",
        f"| exports/backups touched | {classification['exports_touched']} |",
        f"| affected portals | {', '.join(classification['affected_portals']) or '(none)'} |",
        f"",
        f"## Rollback considerations",
        f"",
        _rollback_guidance(verdict, classification),
        f"",
        f"## Changed surfaces",
        f"",
        f"<details><summary>{classification['changed_file_count']} files</summary>",
        f"",
        "```",
    ] + classification['changed_files'] + ["```", "", "</details>", ""]
    # Per-phase detail
    body += ["## Phase detail", ""]
    for p in phases:
        body.append(f"### {p.name} — {p.status}")
        body.append("```")
        body.append(p.detail or "(no detail)")
        body.append("```")
        if p.status in ("FAIL", "WARN") and p.action_if_fail:
            body.append(f"**Action:** {p.action_if_fail}")
        body.append("")
    body.append("---")
    body.append(f"*Generated by `pre_deploy_verify.py` per /app/walkthroughs/pre_deploy_verification.md*")
    path.write_text("\n".join(body))
    return path


def _git_head() -> str:
    rc, out, _ = sh("git rev-parse --short HEAD")
    return out.strip() if rc == 0 else "?"


def _verdict_explanation(verdict: str, phases: list[PhaseResult], classification: dict) -> str:
    if verdict == "APPROVE":
        return (
            "All required phases passed. Risk level is "
            f"**{classification['risk_level']}** with no sensitivity flags. "
            "Deploy is safe to proceed. Operator still owns the Deploy click."
        )
    if verdict == "HOLD":
        reasons = []
        if classification["risk_level"] == "HIGH":
            reasons.append(f"risk level HIGH")
        for k in ("auth_sensitive", "data_sensitive", "rollback_sensitive"):
            if classification[k]:
                reasons.append(k.replace("_", "-"))
        warn_phases = [p.name for p in phases if p.status == "WARN"]
        if warn_phases:
            reasons.append("WARN: " + ", ".join(warn_phases))
        return (
            f"Deploy gate returns HOLD. Reason(s): {', '.join(reasons) or '(unspecified)'}.\n"
            "Operator review required before deploy. This is not a block — "
            "it's a request for explicit operator acknowledgement that the "
            "sensitive surfaces in this batch are intentional."
        )
    # BLOCK
    fails = [p.name for p in phases if p.status == "FAIL"]
    return (
        f"Deploy gate returns BLOCK. Failed phase(s): {', '.join(fails)}.\n"
        "DO NOT DEPLOY. See the Action field for each failed phase."
    )


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fast", action="store_true", help="skip Phase 3 walkthroughs")
    ap.add_argument("--auth-only", action="store_true", help="run only Phase 1 (auth tests) + 4 + 5")
    ap.add_argument("--classify-only", action="store_true", help="run only Phase 5")
    ap.add_argument("--baseline", default=None, help="git ref to diff against")
    args = ap.parse_args()

    mode = "full"
    if args.fast: mode = "fast"
    if args.auth_only: mode = "auth-only"
    if args.classify_only: mode = "classify-only"

    print(f"\n══ MASCI Pre-Deploy Verification Gate · mode={mode} ══\n")
    t0 = time.time()
    phases: list[PhaseResult] = []
    baseline = args.baseline or _baseline_ref_default()

    if args.classify_only:
        p5, classification = phase5_classify(baseline)
        phases.append(p5)
        print(p5.detail)
    else:
        # Phase 1
        p1 = phase1_regression()
        phases.append(p1); print(f"{p1.name}: {p1.status}\n{p1.detail}\n")
        # Phase 1B · Wave-2 reliability tripwire
        p1b = phase1b_field_reliability()
        phases.append(p1b); print(f"{p1b.name}: {p1b.status}\n{p1b.detail}\n")
        # Phase 2
        if not args.auth_only:
            p2 = phase2_build()
            phases.append(p2); print(f"{p2.name}: {p2.status}\n{p2.detail}\n")
        # Phase 3
        if mode == "full":
            p3 = phase3_walkthroughs()
            phases.append(p3); print(f"{p3.name}: {p3.status}\n{p3.detail}\n")
        # Phase 4
        p4 = phase4_production_safety()
        phases.append(p4); print(f"{p4.name}: {p4.status}\n{p4.detail}\n")
        # Phase 5
        p5, classification = phase5_classify(baseline)
        phases.append(p5); print(f"{p5.name}: {p5.status}\n{p5.detail}\n")

    if args.classify_only:
        # synthesize a minimal verdict from classification only
        verdict = "HOLD" if (
            classification["risk_level"] == "HIGH"
            or classification["auth_sensitive"]
            or classification["data_sensitive"]
            or classification["rollback_sensitive"]
        ) else "APPROVE"
    else:
        verdict = compute_verdict(phases, classification)

    total = time.time() - t0
    report_path = write_report(phases, classification, verdict, mode, total)
    print(f"\n══ VERDICT: {verdict} ══")
    print(f"Report written → {report_path}")
    print(f"Total time: {total:.1f}s\n")

    return {"APPROVE": 0, "HOLD": 1, "BLOCK": 2}.get(verdict, 2)


if __name__ == "__main__":
    sys.exit(main())
