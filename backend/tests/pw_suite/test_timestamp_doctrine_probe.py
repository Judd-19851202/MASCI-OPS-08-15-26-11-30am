"""TRUST-TIME-1B · Timestamp Doctrine Probe regression suite · 2026-05-28.

Proves the probe:
  1. passes on the clean tree (current state).
  2. catches a synthetic `.slice(0,16).replace("T"," ")` violation.
  3. catches a synthetic `new Date(x).toLocaleString()` violation.
  4. ignores the canonical helpers in `lib/dateUtils.js`.
  5. catches a synthetic `datetime.utcnow()` backend violation.
  6. honors the baseline allowlist — entries in the baseline never fail.
  7. `--gate` exits 0 when clean and 1 when dirty.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path("/app")
PROBE = REPO_ROOT / "scripts" / "timestamp_doctrine_probe.py"
BASELINE = REPO_ROOT / "scripts" / "timestamp_pattern_baseline.json"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
BACKEND_ROUTES = REPO_ROOT / "backend" / "routes"


def _run(*args: str) -> subprocess.CompletedProcess:
    """Invoke the probe and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(PROBE), *args],
        capture_output=True, text=True, timeout=30,
    )


def _scan_json() -> dict:
    proc = _run("--json")
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


# ─── Baseline state ────────────────────────────────────────────────


def test_probe_passes_on_clean_tree():
    """The committed tree has all violations baselined — probe must
    exit 0 with zero new violations."""
    report = _scan_json()
    assert report["new_violations"] == [], (
        f"unexpected new violations: {report['new_violations'][:5]}"
    )


def test_probe_gate_exits_zero_when_clean():
    proc = _run("--gate")
    assert proc.returncode == 0, (
        f"--gate failed unexpectedly · stdout={proc.stdout!r} "
        f"stderr={proc.stderr!r}"
    )


def test_probe_runs_under_two_seconds():
    """Operational doctrine: probe must stay sub-second-ish."""
    report = _scan_json()
    assert report["scan_ms"] < 2000, report["scan_ms"]


def test_probe_scans_both_languages():
    report = _scan_json()
    assert report["files_scanned"] > 100, report["files_scanned"]
    assert report["patterns"] >= 4, report["patterns"]


# ─── Synthetic violations · frontend ──────────────────────────────


def test_synthetic_slice_replace_t_violation_fails(tmp_path):
    """Drop a temp .jsx file with the exact bug pattern. Probe must
    flag it as a NEW high-severity violation."""
    bad_file = FRONTEND_SRC / "_probe_sentinel_slice_replace.jsx"
    bad_file.write_text(textwrap.dedent("""
        // SYNTHETIC · TRUST-TIME-1B probe sentinel · safe to delete.
        export function Bad({ ts }) {
          return <span>{(ts || "").slice(0, 16).replace("T", " ")}</span>;
        }
    """).lstrip())
    try:
        report = _scan_json()
        hits = [h for h in report["new_violations"]
                if h["path"].endswith("_probe_sentinel_slice_replace.jsx")]
        assert hits, f"probe missed the synthetic violation: {report['new_violations'][:3]}"
        assert hits[0]["pattern_id"] == "F1·slice16-replaceT"
        assert hits[0]["severity"] == "high"
    finally:
        bad_file.unlink(missing_ok=True)


def test_synthetic_new_date_to_locale_violation_fails(tmp_path):
    """`new Date(x).toLocaleString()` outside dateUtils.js must warn."""
    bad_file = FRONTEND_SRC / "_probe_sentinel_to_locale.jsx"
    bad_file.write_text(textwrap.dedent("""
        export function Bad({ ts }) {
          return <span>{new Date(ts).toLocaleString()}</span>;
        }
    """).lstrip())
    try:
        report = _scan_json()
        hits = [h for h in report["new_warnings"] + report["new_violations"]
                if h["path"].endswith("_probe_sentinel_to_locale.jsx")]
        assert hits, "probe missed new Date().toLocaleString() pattern"
        assert any(h["pattern_id"] == "F4·toLocaleString-bare" for h in hits)
    finally:
        bad_file.unlink(missing_ok=True)


def test_canonical_dateutils_not_flagged():
    """The probe MUST NOT flag the canonical helpers in dateUtils.js
    even though that file contains `toLocaleString` references."""
    report = _scan_json()
    bad = [h for h in report["new_violations"] + report["new_warnings"]
           if h["path"] == "lib/dateUtils.js"]
    assert bad == [], f"dateUtils.js wrongly flagged: {bad}"


# ─── Synthetic violations · backend ───────────────────────────────


def test_synthetic_utcnow_violation_fails(tmp_path):
    """`datetime.utcnow()` produces naive datetimes — probe must catch."""
    bad_file = BACKEND_ROUTES / "_probe_sentinel_utcnow.py"
    bad_file.write_text(textwrap.dedent("""
        from datetime import datetime
        def bad():
            return datetime.utcnow().isoformat()
    """).lstrip())
    try:
        report = _scan_json()
        hits = [h for h in report["new_violations"]
                if h["path"].endswith("_probe_sentinel_utcnow.py")]
        assert hits, "probe missed datetime.utcnow() pattern"
        assert hits[0]["pattern_id"] == "B1·datetime-utcnow"
        assert hits[0]["severity"] == "high"
    finally:
        bad_file.unlink(missing_ok=True)


# ─── Baseline behavior ────────────────────────────────────────────


def test_baseline_keys_persist_across_runs():
    """Confirm the baseline file is non-trivial and that EVERY hit on
    the current tree is keyed in the baseline (otherwise the gate
    would fail)."""
    data = json.loads(BASELINE.read_text())
    assert data.get("version") == "TRUST-TIME-1B/v1", data.get("version")
    entries = data.get("entries") or []
    assert len(entries) > 0, "baseline must be populated"
    # Each entry must be a `path::pattern_id::line` string.
    for e in entries:
        parts = e.split("::")
        assert len(parts) == 3, e
        assert parts[2].isdigit(), e


def test_pre_deploy_script_wires_probe():
    """The pre-deploy gate MUST run the probe as a stage."""
    script = (REPO_ROOT / "scripts" / "pre_deploy_check.sh").read_text()
    assert "stage_timestamp_doctrine" in script, (
        "stage_timestamp_doctrine function missing from pre_deploy_check.sh"
    )
    assert "timestamp_doctrine_probe.py --gate" in script, (
        "probe invocation missing from pre_deploy_check.sh"
    )
    assert 'run_stage "TRUST-TIME-1B · timestamp doctrine probe"' in script, (
        "TRUST-TIME-1B run_stage line missing"
    )
