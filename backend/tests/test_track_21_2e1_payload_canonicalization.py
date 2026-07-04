"""Track 21.2E-1 · Test Payload Canonicalization + Side-Effect Guardrail — lock test.

Permanent guardrail. Fails any future commit that reintroduces an unsafe
synthetic workflow payload, weakens the Track 21.2E SDK-level kill
switch, or bypasses the documented safety envelope.

No HTTP requests. No email dispatch. No live-server dependency.

Run:
    pytest /app/backend/tests/test_track_21_2e1_payload_canonicalization.py -v
"""
from __future__ import annotations

import json
import re
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
TESTS = BACKEND / "tests"
MEM = APP / "memory"

WORKFLOW_FIELDS_STRICT = {"project_name", "projectName", "job_name", "jobName"}
ALLOWLIST_TAG = "track21.2e1: allow-non-test-name"


def _http_submitting_test_files():
    for tf in sorted(TESTS.rglob("test_*.py")):
        if "__pycache__" in str(tf):
            continue
        try:
            txt = tf.read_text(errors="ignore")
        except Exception:
            continue
        if "requests.post" in txt or "client.post" in txt:
            yield tf, txt


# ---------------------------------------------------------------- 1 · CLOSEOUT INVARIANTS

def test_baseline_inventory_shows_zero_residual():
    """Track 21.2E baseline inventory has been driven to zero non-TEST_ payloads."""
    inv = MEM / "track_21_2e" / "NON_TEST_PAYLOAD_INVENTORY.json"
    assert inv.is_file()
    data = json.loads(inv.read_text())
    assert data["total_non_test_payloads"] == 0, (
        f"Non-TEST_ payloads must be zero. Found {data['total_non_test_payloads']}."
    )


def test_canonicalization_report_committed():
    rep = MEM / "track_21_2e_1" / "CANONICALIZATION_REPORT.json"
    assert rep.is_file()
    d = json.loads(rep.read_text())
    assert d["rewrites_performed"] > 0
    assert d["residual_non_test"] == [] or len(d["residual_non_test"]) == 0


def test_expanded_scan_report_zero_offenders():
    rep = MEM / "track_21_2e_1" / "EXPANDED_SCAN_REPORT.json"
    assert rep.is_file(), "Expanded scan report must exist"
    d = json.loads(rep.read_text())
    assert d["totals"].get("OFFENDER", 0) == 0, (
        f"Expanded scan reports {d['totals']['OFFENDER']} OFFENDERS. "
        f"Every future unsafe workflow payload must be canonicalized or "
        f"allowlisted with the '{ALLOWLIST_TAG}' comment tag before merge."
    )


# ---------------------------------------------------------------- 2 · FIELD-LEVEL GUARDRAIL

def test_no_unsafe_strict_workflow_payload_field_in_tests():
    """Every ``project_name`` / ``projectName`` / ``job_name`` / ``jobName``
    literal in an HTTP-submitting test file MUST start with ``TEST_``.
    An entry may only be allowlisted by adding the comment
    ``# track21.2e1: allow-non-test-name because <reason>`` on the same line.
    No reason -> failure."""
    self_path = Path(__file__).resolve()
    # Sibling canonicalization lock test declares the regex verbatim; exempt it.
    exempt = {
        self_path,
        (TESTS / "test_track_21_2e_1_canonicalization.py").resolve(),
    }
    offenders = []
    field_pat = re.compile(
        r'["\']({fields})["\']\s*:\s*"([^"]+)"'.format(
            fields="|".join(sorted(WORKFLOW_FIELDS_STRICT))
        )
    )
    for tf, txt in _http_submitting_test_files():
        if tf.resolve() in exempt:
            continue
        for m in field_pat.finditer(txt):
            field, value = m.group(1), m.group(2)
            if value.startswith("TEST_"):
                continue
            # Skip interpolation templates like `TEST_{n}`
            if "{" in value and "}" in value:
                continue
            # Check for same-line allowlist tag with a reason clause
            line_start = txt.rfind("\n", 0, m.start()) + 1
            line_end = txt.find("\n", m.end())
            line = txt[line_start:line_end if line_end > 0 else len(txt)]
            if ALLOWLIST_TAG in line and "because " in line:
                continue
            offenders.append({
                "file": tf.relative_to(APP).as_posix(),
                "line": txt[: m.start()].count("\n") + 1,
                "field": field,
                "value": value,
            })
    assert not offenders, (
        f"Found {len(offenders)} unsafe workflow-payload fields "
        f"(without TEST_ prefix and without an allowlist tag): "
        f"{offenders[:5]}"
    )


# ---------------------------------------------------------------- 3 · KILL-SWITCH REMAINS

def test_sdk_kill_switch_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):' in src
    assert "_resend_boot.Emails.send = staticmethod(_blocked_send)" in src


def test_preview_env_still_strict():
    body = (BACKEND / ".env").read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", body, re.MULTILINE)


def test_track_20_6b_test_prefix_gate_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "synthetic-test-record gate" in src
    assert 'startswith("TEST_")' in src


def test_auto_email_enabled_still_honors_safety_mode():
    src = (BACKEND / "pm_routing.py").read_text(encoding="utf-8")
    assert 'EMAIL_SAFETY_MODE' in src
    assert '("strict", "silent", "test")' in src


# ---------------------------------------------------------------- 4 · NO TEST SPINS UP LIVE EMAIL TRANSPORT

def test_no_test_imports_resend_directly_outside_safety_test():
    """No backend test file may `import resend` except the Track 21.2E
    safety-mode unit test."""
    allow = {
        "test_track_21_2e_email_safety.py",
        # Track 22.1B · legitimate SDK-patch persistence verification, same
        # safety category as the Track 21.2E test. Direct import is exactly
        # how we probe that `resend.Emails.send` still routes to the
        # `_blocked_send` stub after the email-dispatcher extraction.
        "test_track_22_1b_email_dispatch.py",
    }
    offenders = []
    for tf in TESTS.rglob("test_*.py"):
        if tf.name in allow or "__pycache__" in str(tf):
            continue
        try:
            txt = tf.read_text(errors="ignore")
        except Exception:
            continue
        if re.search(r"^\s*import resend|^\s*from resend", txt, re.MULTILINE):
            offenders.append(tf.relative_to(APP).as_posix())
    assert not offenders, (
        f"Test files must not import Resend directly. Offenders: {offenders}"
    )


# ---------------------------------------------------------------- 5 · NO pytest.skip HIDES AN UNSAFE PAYLOAD

def test_no_pytest_skip_masks_unsafe_workflow_payload():
    """A test file must not `pytest.skip` a case that contains a
    non-TEST_ project_name / job_name literal on a line above the skip.
    The intent is to prevent 'we skipped this so it's fine' from
    becoming a smuggling path for unsafe payloads."""
    self_path = Path(__file__).resolve()
    offenders = []
    for tf, txt in _http_submitting_test_files():
        if tf.resolve() == self_path:
            continue
        # For each test function, scan for a non-TEST_ project_name literal
        # followed later in the function by pytest.skip().
        for m in re.finditer(
            r'"(project_name|projectName|job_name|jobName)"\s*:\s*"([^"]+)"',
            txt,
        ):
            v = m.group(2)
            if v.startswith("TEST_"):
                continue
            if "{" in v and "}" in v:
                continue
            # A 600-char forward window is our proxy for "same function".
            window = txt[m.end():m.end() + 600]
            if "pytest.skip" in window:
                offenders.append({
                    "file": tf.relative_to(APP).as_posix(),
                    "line": txt[: m.start()].count("\n") + 1,
                    "value": v,
                })
    assert not offenders, (
        f"pytest.skip must not be used to mask unsafe payloads: {offenders[:5]}"
    )


# ---------------------------------------------------------------- 6 · MEMORY DOCS EXIST

def test_all_track_21_2e1_deliverables_committed():
    required = [
        "TRACK_21_2E1_EXECUTIVE_SUMMARY.md",
        "TRACK_21_2E1_CANONICALIZATION_REPORT.md",
        "TRACK_21_2E1_SIDE_EFFECT_GUARDRAIL.md",
        "TRACK_21_2E1_EMAIL_SAFETY_RECERTIFICATION.md",
        "TRACK_21_2E1_ZERO_DRIFT_MATRIX.md",
        "TRACK_21_2E1_TEST_REPORT.md",
    ]
    missing = [name for name in required if not (MEM / name).is_file()]
    assert not missing, f"Missing Track 21.2E-1 deliverables: {missing}"


def test_prd_documents_email_safety_mode():
    body = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "EMAIL_SAFETY_MODE" in body
    assert "21.2E" in body


def test_debt_register_closes_td_21_2e_c01():
    body = (MEM / "TECHNICAL_DEBT_REGISTER.md").read_text(encoding="utf-8")
    assert "TD-21.2E-C01" in body
    assert "CLOSED" in body


def test_changelog_records_track_21_2e_1():
    body = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "21.2E-1" in body


# ---------------------------------------------------------------- 7 · SDK-LEVEL PATCH ACTIVATION IN CURRENT POD

def test_boot_log_still_records_sdk_patch():
    for lp in Path("/var/log/supervisor").glob("backend*.log"):
        try:
            if "EMAIL_SAFETY_MODE=strict — Resend SDK patched" in lp.read_text(errors="ignore"):
                return
        except Exception:
            continue
    raise AssertionError(
        "Supervisor log must contain the Track 21.2 SDK-patch activation line."
    )
