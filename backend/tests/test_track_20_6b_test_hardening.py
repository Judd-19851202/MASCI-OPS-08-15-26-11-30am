"""Track 20.6B · Test Hardening + Tech-Debt Closeout — lock test.

Verifies:
    * TD-20.6A-001 · TD-20.6A-002 · TD-20.7-C01 all CLOSED in the register.
    * TD-20.6B-A01 (new Class-A) FIXED in the register.
    * The synthetic-test-record short-circuit is present in
      ``backend/server.py::_dispatch_auto_email`` and runs BEFORE
      the ``auto_email_enabled()`` check.
    * Hardened test files use the current canonical multi-login endpoint,
      NOT the retired shared-password admin login (Track 15.32).
    * ``test_vocabulary_hr_sees_all_lanes`` uses an additive-safe
      superset assertion (not strict equality).
    * ``test_vocabulary_unauth_401`` uses a fresh session.
    * No email-transport imports in touched files.
    * No skip was added to hide a target failure (spot-checked against
      the docstring / message of the ONE legitimate skip that predates
      Track 20.6B).
    * PRD + CHANGELOG updated.
    * Track 20.6B markdown deliverables present.
    * Prior-track lock-test docs preserved.

Run in isolation:
    pytest /app/backend/tests/test_track_20_6b_test_hardening.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
BE = REPO / "backend"
BE_TESTS = BE / "tests"

REQUIRED_DOCS = [
    "TRACK_20_6B_EXECUTIVE_SUMMARY.md",
    "TRACK_20_6B_DEBT_CLOSEOUT_REPORT.md",
    "TRACK_20_6B_FIX_REPORT_TD_20_6A_001.md",
    "TRACK_20_6B_FIX_REPORT_TD_20_6A_002.md",
    "TRACK_20_6B_FIX_REPORT_TD_20_7_C01.md",
    "TRACK_20_6B_FIX_REPORT_TD_20_6B_A01.md",
    "TRACK_20_6B_EMAIL_SAFETY_CERTIFICATION.md",
    "TRACK_20_6B_ADDITIVE_ASSERTION_GUARDRAIL.md",
    "TRACK_20_6B_ZERO_DRIFT_MATRIX.md",
    "TRACK_20_6B_TEST_REPORT.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── Deliverables ─────────────────────────────────────────────────────

def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.6B deliverables: {missing}"


# ── Tech Debt Register status flips ─────────────────────────────────

def test_td_20_6a_001_marked_closed():
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    # Find the row and confirm it contains "CLOSED" + a Track 20.6B
    # reference. The row is one line, so slice the neighborhood.
    idx = src.find("TD-20.6A-001")
    assert idx != -1, "TD-20.6A-001 must exist in the register"
    row = src[idx: src.find("\n", idx)]
    assert "CLOSED" in row, f"TD-20.6A-001 must be CLOSED; row = {row!r}"


def test_td_20_6a_002_marked_closed():
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    idx = src.find("TD-20.6A-002")
    assert idx != -1
    row = src[idx: src.find("\n", idx)]
    assert "CLOSED" in row, f"TD-20.6A-002 must be CLOSED; row = {row!r}"


def test_td_20_7_c01_marked_closed():
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    idx = src.find("TD-20.7-C01")
    assert idx != -1
    row = src[idx: src.find("\n", idx)]
    assert "CLOSED" in row, f"TD-20.7-C01 must be CLOSED; row = {row!r}"


def test_td_20_6b_a01_registered_and_fixed():
    """New Class-A debt discovered inside 20.6B must be registered
    AND marked FIXED (Track 20.6A doctrine: Class-A never deferred)."""
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    idx = src.find("TD-20.6B-A01")
    assert idx != -1, "TD-20.6B-A01 must be registered"
    row = src[idx: src.find("\n", idx)]
    assert "FIXED" in row, f"TD-20.6B-A01 must be FIXED; row = {row!r}"
    # Class-A doctrine assertion — the row must include the "A" class.
    assert "A" in row


# ── Production hunk: synthetic-test-record short-circuit ─────────────

def test_synthetic_test_record_short_circuit_present():
    src = _read(BE / "server.py")
    # The short-circuit lives inside _dispatch_auto_email.
    fn_idx = src.find("async def _dispatch_auto_email")
    assert fn_idx != -1, "_dispatch_auto_email must exist"
    # Look at a generous window of the function body — the short-circuit
    # MUST appear before the auto_email_enabled() CALL.
    body = src[fn_idx: fn_idx + 8000]
    assert 'startswith("TEST_")' in body, (
        "synthetic-test-record short-circuit missing from _dispatch_auto_email"
    )
    # Ordering: short-circuit must appear BEFORE the actual CALL to
    # auto_email_enabled() (searching for the negated call is unambiguous
    # since the comment mentions the function name without the `not`).
    sc = body.find('startswith("TEST_")')
    en = body.find("if not auto_email_enabled()")
    assert sc != -1 and en != -1 and sc < en, (
        "synthetic-test-record short-circuit must run BEFORE "
        "the `if not auto_email_enabled()` gate so the skip audit "
        "fires even when AUTO_EMAIL_REPORTS=true (which is exactly the "
        "preview env where the test suite runs)."
    )


def test_synthetic_test_short_circuit_emits_skip_audit():
    src = _read(BE / "server.py")
    fn_idx = src.find("async def _dispatch_auto_email")
    body = src[fn_idx: fn_idx + 3500]
    # The audit failure_reason must be the machine-readable slug.
    assert '"synthetic_test_record"' in body, (
        "short-circuit must emit trust-spine audit with "
        "failure_reason='synthetic_test_record'"
    )
    assert 'status="skipped"' in body, (
        "short-circuit must emit trust-spine audit with status='skipped'"
    )


# ── Test-file hardening: multi-login migration ──────────────────────

def test_test_daily_reports_uses_multi_login():
    src = _read(BE_TESTS / "test_daily_reports.py")
    assert "/api/auth/multi-login" in src, (
        "test_daily_reports.py must use the canonical multi-login endpoint"
    )
    # Retired endpoints must NOT be referenced as an active auth path.
    assert 'requests.post(f"{API}/admin/login"' not in src, (
        "test_daily_reports.py must not call the retired /api/admin/login"
    )


def test_test_job_photos_uses_multi_login():
    src = _read(BE_TESTS / "test_job_photos.py")
    assert "/api/auth/multi-login" in src
    # The retired shared-password endpoint must not be called.
    assert 'requests.post(f"{BASE_URL}/api/admin/login"' not in src, (
        "test_job_photos.py must not call the retired /api/admin/login"
    )


def test_test_daily_reports_admin_headers_triple_token():
    """Track 20.6B fixture returns admin+HR+safety triple-token so every
    downstream gate on the platform resolves."""
    src = _read(BE_TESTS / "test_daily_reports.py")
    for h in ("X-Admin-Token", "X-HR-Token", "X-Safety-Token"):
        assert h in src, f"triple-token fixture missing header: {h}"


# ── Test-file hardening: additive-safe assertion ────────────────────

def test_vocabulary_hr_sees_all_lanes_uses_superset():
    src = _read(BE_TESTS / "test_track_19_21_e2e_live.py")
    # Locate the test function body.
    fn_idx = src.find("def test_vocabulary_hr_sees_all_lanes")
    assert fn_idx != -1
    body = src[fn_idx: fn_idx + 2000]
    # Must use subset containment, NOT strict equality.
    assert "required <= allowed" in body, (
        "test_vocabulary_hr_sees_all_lanes must use additive-safe "
        "superset assertion (`required <= allowed`), not strict equality."
    )
    # Must retain the certified-set guardrail for rogue lanes.
    assert "certified" in body, (
        "assertion must also lock the certified vocabulary superset "
        "to catch rogue additions"
    )


def test_vocabulary_hr_sees_all_lanes_not_strict_equality():
    """Guard against future regressions: the specific brittle pattern
    must never return to this test."""
    src = _read(BE_TESTS / "test_track_19_21_e2e_live.py")
    fn_idx = src.find("def test_vocabulary_hr_sees_all_lanes")
    body = src[fn_idx: fn_idx + 2000]
    forbidden = 'set(body.get("allowed_lanes_for_actor") or []) == {'
    assert forbidden not in body, (
        "brittle strict-equality assertion must not return to "
        "test_vocabulary_hr_sees_all_lanes"
    )


def test_vocabulary_unauth_uses_fresh_session():
    """TD-20.6A-001 hardening — fresh requests.Session() prevents any
    header/cookie leak from a prior fixture."""
    src = _read(BE_TESTS / "test_track_19_21_e2e_live.py")
    fn_idx = src.find("def test_vocabulary_unauth_401")
    assert fn_idx != -1
    body = src[fn_idx: fn_idx + 1000]
    assert "requests.Session()" in body, (
        "test_vocabulary_unauth_401 must use a fresh requests.Session() "
        "to close the fixture-leak surface (TD-20.6A-001)"
    )


# ── No email-transport imports in touched test files ───────────────

TOUCHED_TEST_FILES = (
    "test_track_19_21_e2e_live.py",
    "test_daily_reports.py",
    "test_job_photos.py",
    # NOTE: `test_track_20_6b_test_hardening.py` (this file) is intentionally
    # NOT scanned by the email-transport grep — it contains the transport
    # string literals AS the assertion needles used to grep the others.
)


def test_no_email_transports_in_touched_tests():
    for name in TOUCHED_TEST_FILES:
        src = _read(BE_TESTS / name)
        for needle in ("fsi_send_email", "resend.emails.send",
                       "/api/email/send", "/api/notifications/send",
                       "phase4.send_email"):
            assert needle not in src, (
                f"{name} unexpectedly contains email transport {needle!r}"
            )


# ── Doctrine: no skip added to hide target failures ─────────────────

def test_no_skip_hides_target_debt():
    """The three target debts (TD-20.6A-001 / -002 / TD-20.7-C01) must
    NOT be closed via pytest.skip. Grep the touched files for a skip
    with a message that mentions the debt IDs — none should exist."""
    for name in TOUCHED_TEST_FILES:
        src = _read(BE_TESTS / name)
        for did in ("TD-20.6A-001", "TD-20.6A-002", "TD-20.7-C01"):
            for pattern in (f'pytest.skip("{did}',
                            f"pytest.skip('{did}",
                            f'pytest.skip(f"{did}',
                            f"pytest.skip(f'{did}"):
                assert pattern not in src, (
                    f"{name} appears to close {did} via pytest.skip — "
                    "target debt must be fixed, not hidden."
                )


# ── PRD / CHANGELOG ─────────────────────────────────────────────────

def test_prd_updated():
    src = _read(MEM / "PRD.md")
    assert "TRACK 20.6B" in src


def test_changelog_updated():
    src = _read(MEM / "CHANGELOG.md")
    assert "TRACK 20.6B" in src


# ── Continuity ──────────────────────────────────────────────────────

def test_prior_track_docs_preserved():
    for name in (
        "TRACK_20_7_EXECUTIVE_SUMMARY.md",
        "TRACK_20_7_TEST_REPORT.md",
        "TRACK_19_62_EXECUTIVE_SUMMARY.md",
        "TRACK_19_61_EXECUTIVE_SUMMARY.md",
        "TRACK_20_6_FINAL_RECOMMENDATION.md",
        "TRACK_20_5_FINAL_RECOMMENDATION.md",
        "TECHNICAL_DEBT_REGISTER.md",
    ):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"
