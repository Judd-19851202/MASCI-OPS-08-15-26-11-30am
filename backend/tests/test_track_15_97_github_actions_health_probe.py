"""TRACK 15.97 · GitHub Actions production-health-probe regression.

Locks the workflow contract so the failure mode that triggered Track
15.97 (canonical "this check has no steps" empty-job failure) cannot
recur. Static guards only — does not invoke GitHub Actions itself.
"""
from __future__ import annotations

import os
import re

import pytest

try:
    import yaml  # PyYAML — already a backend dep
except Exception:
    yaml = None  # type: ignore


WORKFLOWS_DIR = "/app/.github/workflows"
PROBE_PATH = os.path.join(WORKFLOWS_DIR, "production-health-probe.yml")


def _load_workflow() -> dict:
    if yaml is None:
        pytest.skip("PyYAML not available")
    with open(PROBE_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_workflow_file_exists():
    assert os.path.exists(PROBE_PATH), (
        f"Track 15.97: {PROBE_PATH} must exist — the production-health-"
        f"probe workflow is the live production heartbeat."
    )


def test_no_legacy_pr_noop_sibling():
    """The Track 15.56 noop sibling that shared the same workflow
    `name` caused GitHub's required-check resolution to surface the
    empty-job failure. It MUST stay removed after 15.97."""
    legacy = os.path.join(WORKFLOWS_DIR, "production-health-probe-pr-noop.yml")
    assert not os.path.exists(legacy), (
        f"Track 15.97: {legacy} must not exist — its presence collides "
        f"on workflow `name:` and re-introduces 'this check has no "
        f"steps' on pull_request."
    )


def test_workflow_yaml_parses():
    d = _load_workflow()
    assert isinstance(d, dict) and d, "workflow YAML did not parse to a dict"


def test_workflow_name_canonical():
    d = _load_workflow()
    assert d.get("name") == "production-health-probe", (
        "workflow `name:` must be exactly 'production-health-probe' so "
        "branch-protection required-check rules resolve to this file."
    )


def test_workflow_triggers_include_pr_schedule_and_dispatch():
    """All three triggers must be present:
        * schedule — periodic real probe
        * workflow_dispatch — manual run button
        * pull_request — green check for branch protection
    """
    d = _load_workflow()
    on = d.get("on") if "on" in d else d.get(True)
    assert isinstance(on, dict), f"`on:` must be a mapping, got {type(on)}"
    assert "schedule" in on, "`schedule` trigger missing"
    assert "workflow_dispatch" in on, "`workflow_dispatch` trigger missing"
    assert "pull_request" in on, (
        "`pull_request` trigger missing — without it, branch-protection "
        "required-check resolution falls into the 'no steps' failure."
    )


def test_probe_job_exists_and_has_no_job_level_if():
    """The empty-job failure was caused by a job-level `if:` that
    skipped all steps. The job-level guard MUST be absent — step-level
    `if:` is used instead."""
    d = _load_workflow()
    jobs = d.get("jobs") or {}
    assert "probe" in jobs, "job named `probe` missing"
    probe = jobs["probe"]
    assert "if" not in probe, (
        "job-level `if:` on probe must NOT exist — that is the exact "
        "trigger of GitHub Actions 'this check has no steps' failure."
    )


def test_probe_job_has_non_empty_steps():
    d = _load_workflow()
    steps = (d.get("jobs", {}).get("probe") or {}).get("steps") or []
    assert len(steps) >= 4, (
        f"probe job must have at least 4 explicit steps "
        f"(ctx, /api/health, /api/version, summary). got {len(steps)}."
    )
    for i, s in enumerate(steps):
        assert s.get("name"), f"step #{i+1} missing `name:` — required by 15.97"


def test_probe_runs_health_endpoint_check():
    d = _load_workflow()
    steps = (d.get("jobs", {}).get("probe") or {}).get("steps") or []
    assert any("/api/health" in (s.get("run") or "") for s in steps), (
        "probe must include a /api/health check step."
    )


def test_probe_runs_version_endpoint_check():
    d = _load_workflow()
    steps = (d.get("jobs", {}).get("probe") or {}).get("steps") or []
    found = False
    for s in steps:
        run = s.get("run") or ""
        if "/api/version" in run and "production" in run and "masci_safety" in run:
            found = True
            break
    assert found, (
        "probe must include a /api/version check that asserts "
        "app_env=production and db_name=masci_safety."
    )


def test_authenticated_readiness_step_gated_to_non_pr():
    """The /api/admin/deployment-readiness step MUST be guarded so it
    does not run on pull_request events (where secrets are unavailable
    or unsafe)."""
    d = _load_workflow()
    steps = (d.get("jobs", {}).get("probe") or {}).get("steps") or []
    readiness = [
        s for s in steps
        if "/api/admin/deployment-readiness" in (s.get("run") or "")
        and "curl" in (s.get("run") or "")
    ]
    assert readiness, "readiness probe step missing"
    for s in readiness:
        ifc = s.get("if") or ""
        assert "is_pr" in ifc and "false" in ifc, (
            f"readiness step must be gated to non-PR contexts; got `if: {ifc!r}`"
        )


def test_no_hardcoded_credentials_in_workflow():
    """Secrets must flow exclusively via ${{ secrets.* }}. The
    super-admin email and password must NEVER appear inline."""
    src = open(PROBE_PATH, encoding="utf-8").read()
    forbidden = [
        "jaymn.judd@mascigc.com",
        "Maddix123!",
        "Maddix123",
        "password: 'Maddix",
        'password: "Maddix',
    ]
    for needle in forbidden:
        assert needle not in src, (
            f"hard-coded credential leak detected: {needle!r} found in "
            f"production-health-probe.yml — must use ${{{{ secrets.* }}}} instead."
        )


def test_secrets_referenced_via_secrets_context_only():
    """Every secret reference must go through the secrets context."""
    src = open(PROBE_PATH, encoding="utf-8").read()
    # Each "OPS_ADMIN_EMAIL" or "OPS_ADMIN_PASSWORD" mention that's
    # NOT in a comment must be either a `secrets.` reference or
    # an env-var name (e.g. `OPS_ADMIN_EMAIL: ${{ secrets.OPS_ADMIN_EMAIL }}`).
    # The forbidden pattern is `OPS_ADMIN_PASSWORD:` immediately
    # followed by a literal string.
    bad = re.search(
        r"OPS_ADMIN_PASSWORD\s*:\s*['\"][^$]", src
    )
    assert bad is None, (
        "OPS_ADMIN_PASSWORD must only be assigned from secrets context."
    )


def test_no_continue_on_error_hiding_failures():
    """The probe must not silently swallow failures."""
    src = open(PROBE_PATH, encoding="utf-8").read()
    assert "continue-on-error: true" not in src, (
        "Track 15.97: `continue-on-error: true` not permitted — would "
        "hide a real production outage from the probe."
    )


def test_step_summary_always_published():
    """The summary step must run on success AND failure."""
    d = _load_workflow()
    steps = (d.get("jobs", {}).get("probe") or {}).get("steps") or []
    summary = [
        s for s in steps
        if "GITHUB_STEP_SUMMARY" in (s.get("run") or "")
        and s.get("if") == "always()"
    ]
    assert summary, (
        "an `if: always()` step that writes to GITHUB_STEP_SUMMARY "
        "must exist so the operator gets diagnostic output on every run."
    )


def test_deployment_gate_includes_track_15_97():
    src = open("/app/scripts/deployment_gate.py", encoding="utf-8").read()
    assert "test_track_15_97_github_actions_health_probe.py" in src, (
        "deployment_gate.py must include the 15.97 regression file."
    )
