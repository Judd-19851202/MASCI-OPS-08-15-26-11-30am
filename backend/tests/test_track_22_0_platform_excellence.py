"""Track 22.0 · Platform Excellence Program — permanent lock test.

Locks the 13 deliverables, the deferrals for Track 22.1 (server.py) and
Track 22.2 (App.js), the Six Pillars floor of 9.7, and the fact that no
prior email-safety / CORS / auth guardrail regressed.

No HTTP calls. No email dispatched. No live-server dependency.
"""
from __future__ import annotations

import re
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"

TRACK_22_0_DELIVERABLES = [
    "TRACK_22_0_EXECUTIVE_SUMMARY.md",
    "TRACK_22_0_PLATFORM_VALUE_MATRIX.md",
    "TRACK_22_0_ARCHITECTURE_REPORT.md",
    "TRACK_22_0_UI_UX_VALUE_REPORT.md",
    "TRACK_22_0_PERMISSION_SECURITY_REPORT.md",
    "TRACK_22_0_DATA_COLLECTION_REPORT.md",
    "TRACK_22_0_EMAIL_SIDE_EFFECT_REPORT.md",
    "TRACK_22_0_PERFORMANCE_DURABILITY_REPORT.md",
    "TRACK_22_0_TEST_CI_GUARDRAIL_REPORT.md",
    "TRACK_22_0_KEEP_IMPROVE_MERGE_RETIRE_MATRIX.md",
    "TRACK_22_0_MANIFEST_DIFF_REPORT.md",
    "TRACK_22_0_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_0_TEST_REPORT.md",
]

PRIOR_TRACK_LOCK_TESTS = [
    "test_track_21_0_platform_census.py",
    "test_track_21_1_remediation.py",
    "test_track_21_2e_email_safety.py",
    "test_track_21_2e_1_canonicalization.py",
    "test_track_21_2e1_payload_canonicalization.py",
    "test_track_21_3_remaining_debt_remediation.py",
]


# ---------------------------------------------------------------- Assertion 1
def test_all_track_22_0_deliverables_committed_and_non_empty():
    missing = []
    empty = []
    for name in TRACK_22_0_DELIVERABLES:
        p = MEM / name
        if not p.is_file():
            missing.append(name)
        elif p.stat().st_size < 200:  # non-trivial content required
            empty.append(name)
    assert not missing, f"Missing Track 22.0 deliverables: {missing}"
    assert not empty, f"Empty Track 22.0 deliverables: {empty}"


# ---------------------------------------------------------------- Assertion 2
def test_platform_manifest_present():
    p = MEM / "PLATFORM_MANIFEST.json"
    assert p.is_file(), "PLATFORM_MANIFEST.json missing from /app/memory/"
    assert p.stat().st_size > 200, "PLATFORM_MANIFEST.json is suspiciously small"


# ---------------------------------------------------------------- Assertion 3
def test_executive_summary_records_six_pillars_floor():
    body = (MEM / "TRACK_22_0_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    assert "Six Pillars" in body
    # Extract the platform average (e.g. "9.79 / 10").
    m = re.search(r"Platform average[^\d]*(\d+\.\d+)\s*/\s*10", body)
    assert m, "Executive summary must record platform average score."
    avg = float(m.group(1))
    assert avg >= 9.7, f"Platform average {avg} is below the 9.7 floor."


# ---------------------------------------------------------------- Assertion 4
def test_executive_summary_defers_server_py_to_22_1():
    body = (MEM / "TRACK_22_0_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    assert "Track 22.1" in body
    assert "server.py" in body
    assert "parity" in body.lower()
    assert "Backend team" in body or "Backend" in body


# ---------------------------------------------------------------- Assertion 5
def test_executive_summary_defers_app_js_to_22_2():
    body = (MEM / "TRACK_22_0_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    assert "Track 22.2" in body
    assert "App.js" in body
    assert "parity" in body.lower()
    assert "Frontend team" in body or "Frontend" in body


# ---------------------------------------------------------------- Assertion 6
def test_debt_register_records_track_22_deferrals():
    body = (MEM / "TECHNICAL_DEBT_REGISTER.md").read_text(encoding="utf-8")
    assert "TD-22.1" in body, "Debt register must record server.py deferral (TD-22.1-*)."
    assert "TD-22.2" in body, "Debt register must record App.js deferral (TD-22.2-*)."


# ---------------------------------------------------------------- Assertion 7
def test_prd_records_track_22_0():
    body = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 22.0" in body or "Track 22.0" in body


# ---------------------------------------------------------------- Assertion 8
def test_changelog_records_track_22_0():
    body = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 22.0" in body or "Track 22.0" in body


# ---------------------------------------------------------------- Assertion 9
def test_preview_env_still_strict():
    body = (BACKEND / ".env").read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", body, re.MULTILINE)


# ---------------------------------------------------------------- Assertion 10
def test_resend_sdk_kill_switch_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):' in src, (
        "Resend SDK kill switch was removed — Track 21.2E regression."
    )


# ---------------------------------------------------------------- Assertion 11
def test_dispatcher_strict_gate_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    # Track 20.6B/21.2E gate: strict-mode short-circuit and TEST_ prefix branch.
    assert 'TEST_' in src
    assert '_dispatch_auto_email' in src


# ---------------------------------------------------------------- Assertion 12
def test_cors_explicit_allow_lists_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'allow_methods=["*"]' not in src, "CORS allow_methods reverted to wildcard."
    assert 'allow_headers=["*"]' not in src, "CORS allow_headers reverted to wildcard."
    assert '"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"' in src
    assert '"X-Admin-Token"' in src
    assert '"X-Portal-Token"' in src


# ---------------------------------------------------------------- Assertion 13
def test_prior_track_lock_test_files_still_committed():
    tests_dir = BACKEND / "tests"
    missing = [name for name in PRIOR_TRACK_LOCK_TESTS if not (tests_dir / name).is_file()]
    assert not missing, f"Prior-track lock-test files went missing: {missing}"
