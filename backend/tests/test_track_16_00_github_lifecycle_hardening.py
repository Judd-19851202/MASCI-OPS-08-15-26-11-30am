"""TRACK 16.00 · GitHub Repository Lifecycle Hardening regression.

Locks the permanent contract for the production-health-probe workflow
shape AND the operator-facing lifecycle CLI:

* the workflow self-silences on every repo that is NOT the active
  production source (vars.ACTIVE_PRODUCTION_SOURCE gate);
* the first step ALWAYS runs (so GitHub never renders "this check
  has no steps") and emits a clear summary;
* every subsequent step is gated by ``steps.lifecycle.outputs.is_active``
  — snapshots cannot accidentally probe production;
* authenticated readiness is double-gated to non-PR + secrets-present;
* the operator-facing lifecycle CLI exists with documented dry-run/apply
  modes and never echoes the PAT.

Static guards only — no GitHub Actions execution.
"""
from __future__ import annotations

import os
import re

import pytest

try:
    import yaml
except Exception:
    yaml = None  # type: ignore


WORKFLOW = "/app/.github/workflows/production-health-probe.yml"
CLI = "/app/scripts/github_lifecycle_manager.py"


def _wf() -> dict:
    if yaml is None:
        pytest.skip("PyYAML not available")
    return yaml.safe_load(open(WORKFLOW, encoding="utf-8"))


# ---------------------------------------------------------------------------
# Workflow shape
# ---------------------------------------------------------------------------

def test_workflow_file_exists():
    assert os.path.exists(WORKFLOW)


def test_no_legacy_pr_noop_sibling():
    legacy = "/app/.github/workflows/production-health-probe-pr-noop.yml"
    assert not os.path.exists(legacy), \
        "Track 16.00: legacy noop sibling must remain removed"


def test_workflow_name_is_canonical():
    assert _wf().get("name") == "production-health-probe"


def test_triggers_include_all_three():
    on = _wf().get("on") if "on" in _wf() else _wf().get(True)
    assert "schedule" in on and "workflow_dispatch" in on and "pull_request" in on


def test_no_job_level_if_on_probe():
    """The empty-job failure trigger MUST NOT recur."""
    job = (_wf().get("jobs") or {}).get("probe") or {}
    assert "if" not in job, \
        "Track 16.00: probe job MUST NOT have a job-level `if:` guard"


def test_first_step_always_runs():
    """The lifecycle-gate step must have no `if:` so the GitHub UI
    can never render 'this check has no steps'."""
    job = (_wf().get("jobs") or {}).get("probe") or {}
    steps = job.get("steps") or []
    assert steps, "probe job has no steps"
    first = steps[0]
    assert first.get("if") is None, \
        "Track 16.00: the first step MUST be unconditional"
    assert "lifecycle" in (first.get("id") or "").lower() or \
        "lifecycle" in (first.get("name") or "").lower(), \
        "first step must be the lifecycle-role resolver"


def test_lifecycle_gate_uses_active_production_source_variable():
    """The gate must read vars.ACTIVE_PRODUCTION_SOURCE."""
    src = open(WORKFLOW, encoding="utf-8").read()
    assert "vars.ACTIVE_PRODUCTION_SOURCE" in src or \
        "ACTIVE_PRODUCTION_SOURCE" in src, \
        "lifecycle gate must reference vars.ACTIVE_PRODUCTION_SOURCE"


def test_probe_steps_gated_by_is_active():
    """Every probe step must be step-gated on
    steps.lifecycle.outputs.is_active == 'true'."""
    job = (_wf().get("jobs") or {}).get("probe") or {}
    steps = job.get("steps") or []
    probe_step_names = ("GET /api/health", "GET /api/version",
                       "GET /api/admin/deployment-readiness",
                       "Detect admin credentials availability")
    for s in steps:
        name = s.get("name") or ""
        if name in probe_step_names:
            ifc = s.get("if") or ""
            assert "is_active" in ifc and "true" in ifc, \
                f"step {name!r} missing is_active gate (got if={ifc!r})"


def test_authenticated_readiness_step_double_gated():
    """The readiness step must be gated on is_active AND non-PR AND
    creds-present."""
    job = (_wf().get("jobs") or {}).get("probe") or {}
    steps = job.get("steps") or []
    for s in steps:
        if s.get("name") == "GET /api/admin/deployment-readiness":
            ifc = s.get("if") or ""
            assert "is_active" in ifc and "pull_request" in ifc \
                and "creds.outputs.have" in ifc, \
                f"readiness step under-gated: if={ifc!r}"
            return
    pytest.fail("readiness step missing from workflow")


def test_no_hardcoded_credentials():
    src = open(WORKFLOW, encoding="utf-8").read()
    for needle in ("jaymn.judd@mascigc.com", "Maddix123!", "Maddix123"):
        assert needle not in src


def test_no_continue_on_error():
    src = open(WORKFLOW, encoding="utf-8").read()
    assert "continue-on-error: true" not in src


# ---------------------------------------------------------------------------
# Lifecycle CLI shape
# ---------------------------------------------------------------------------

def test_cli_script_exists_and_executable_bit():
    assert os.path.exists(CLI)
    assert os.access(CLI, os.X_OK), \
        "scripts/github_lifecycle_manager.py must be chmod +x"


def test_cli_parses_python():
    import ast
    ast.parse(open(CLI, encoding="utf-8").read())


def test_cli_supports_dry_run_and_apply_flags():
    src = open(CLI, encoding="utf-8").read()
    assert '"--dry-run"' in src and '"--apply"' in src


def test_cli_reads_token_from_env_only():
    """Token must come from GITHUB_PAT or GITHUB_TOKEN env var,
    never from a CLI flag (so it doesn't show up in process listings)."""
    src = open(CLI, encoding="utf-8").read()
    assert 'os.environ.get("GITHUB_PAT")' in src
    # Forbid any --token / --pat CLI flag definition.
    bad = re.search(r'add_argument\(\s*["\']--?(token|pat)["\']', src)
    assert bad is None, \
        "CLI must NOT expose --token/--pat — tokens belong in env only"


def test_cli_never_prints_token_payload():
    """The CLI body must not print the GITHUB_PAT value verbatim."""
    src = open(CLI, encoding="utf-8").read()
    # Look for print(token) or any echo that includes the raw value.
    assert "print(token)" not in src
    assert 'print(f"{token' not in src
    # And the Authorization header construction must use Bearer + token, fine.
    # The CLI explicitly prints "<len chars · redacted>" — verify.
    assert "redacted" in src


def test_cli_only_targets_snapshot_named_repos_by_default():
    """The SNAPSHOT_NAME_RE filter must be present so unrelated repos
    in the same account are left untouched."""
    src = open(CLI, encoding="utf-8").read()
    assert "SNAPSHOT_NAME_RE" in src
    assert "UNRELATED" in src
    assert "ACTIVE_PRODUCTION_SOURCE" in src
    assert "INACTIVE_SNAPSHOT" in src


def test_cli_does_not_modify_active_repo():
    """The CLI must classify the active repo and verify only — never
    disable workflows or delete files in it."""
    src = open(CLI, encoding="utf-8").read()
    # The branch that handles ACTIVE_PRODUCTION_SOURCE must NOT call
    # _disable_workflow or _delete_file. We grep that block.
    m = re.search(
        r'if cls == "ACTIVE_PRODUCTION_SOURCE":(.*?)continue',
        src, re.DOTALL,
    )
    assert m, "ACTIVE_PRODUCTION_SOURCE handling block not found"
    block = m.group(1)
    assert "_disable_workflow" not in block, \
        "CLI must not disable workflows in the active production repo"
    assert "_delete_file" not in block, \
        "CLI must not delete files in the active production repo"


def test_deployment_gate_includes_track_16_00():
    src = open("/app/scripts/deployment_gate.py", encoding="utf-8").read()
    assert "test_track_16_00_github_lifecycle_hardening.py" in src
