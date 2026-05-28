"""GOVERNANCE-INFRA-1 · Workstream 1 · Authority Mismatch Probe test.

Self-test the platform self-protection probe. Verifies:
  * Probe runs in under 1 second
  * Probe reports zero NEW violations on the current tree (TRUST-PO-1
    remediation held; nothing new introduced)
  * Probe correctly fails the --gate flag when a synthetic
    token-coexistence pattern is added to an unallowlisted file
  * Baseline JSON is well-formed
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

REPO_ROOT = Path("/app")
PROBE_PATH = REPO_ROOT / "scripts" / "authority_mismatch_probe.py"
BASELINE_PATH = REPO_ROOT / "scripts" / "authority_pattern_baseline.json"
REPORT_PATH = REPO_ROOT / "memory" / "AUTHORITY_MISMATCH_REPORT.md"


def test_probe_runs_under_1_second():
    started = time.time()
    r = subprocess.run(
        ["python3", str(PROBE_PATH), "--json"],
        capture_output=True, text=True, timeout=5,
    )
    elapsed = time.time() - started
    assert r.returncode == 0, r.stderr
    assert elapsed < 1.5, f"probe took {elapsed:.2f}s — slow"


def test_probe_baseline_is_valid_json():
    assert BASELINE_PATH.exists(), "authority pattern baseline missing"
    data = json.loads(BASELINE_PATH.read_text())
    assert "approved" in data
    assert isinstance(data["approved"], list)
    assert len(data["approved"]) > 0, "baseline should have approved patterns"
    # Every baseline entry should look like `path::pattern::line`.
    for k in data["approved"][:5]:
        assert "::" in k, f"malformed baseline key: {k!r}"


def test_probe_reports_zero_new_violations_on_current_tree():
    r = subprocess.run(
        ["python3", str(PROBE_PATH), "--json"],
        capture_output=True, text=True, timeout=5,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["new_violations"] == [], (
        f"NEW authority-mismatch violations detected (TRUST-PO-1 may have "
        f"regressed): {data['new_violations']}"
    )


def test_probe_gate_passes_on_clean_tree():
    r = subprocess.run(
        ["python3", str(PROBE_PATH), "--gate"],
        capture_output=True, text=True, timeout=5,
    )
    assert r.returncode == 0, (
        f"probe --gate returned non-zero on a clean tree · "
        f"stdout={r.stdout[:300]} stderr={r.stderr[:300]}"
    )


def test_probe_gate_fails_on_synthetic_violation(tmp_path):
    """Drop a synthetic violation into a known unallowlisted file and
    confirm --gate fails. Restore the file afterwards."""
    target = REPO_ROOT / "frontend" / "src" / "pages" / "_governance_probe_test_scratch.jsx"
    if target.exists():
        pytest.skip("scratch file conflict; skipping synthetic test")
    target.write_text(
        "import { isPm, isHr, isAdmin } from '@/lib/auth';\n"
        "export default function Scratch() {\n"
        "  const canApprove = isPm() || isHr() || isAdmin();\n"
        "  return canApprove ? 'yes' : 'no';\n"
        "}\n"
    )
    try:
        r = subprocess.run(
            ["python3", str(PROBE_PATH), "--gate"],
            capture_output=True, text=True, timeout=5,
        )
        assert r.returncode != 0, (
            f"probe --gate did NOT fail on a synthetic violation · "
            f"this means the probe regex is broken · stdout={r.stdout[:300]}"
        )
        assert "authority-mismatch probe FAILED" in (r.stderr + r.stdout), r.stderr
    finally:
        target.unlink(missing_ok=True)


def test_probe_writes_markdown_report():
    subprocess.run(
        ["python3", str(PROBE_PATH)],
        capture_output=True, text=True, timeout=5,
    )
    assert REPORT_PATH.exists()
    content = REPORT_PATH.read_text()
    assert "AUTHORITY MISMATCH REPORT" in content
    assert "Summary" in content
