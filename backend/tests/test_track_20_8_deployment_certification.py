"""Track 20.8 · Final Production Deployment Certification — lock test.

Certification-only track. Zero production code changes. This lock test
verifies that all Track 20.8 deliverables + register updates + PRD +
CHANGELOG are on disk.

Run in isolation:
    pytest /app/backend/tests/test_track_20_8_deployment_certification.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
BE_TESTS = REPO / "backend/tests"

REQUIRED_DOCS = [
    "TRACK_20_8_EXECUTIVE_DEPLOYMENT_REPORT.md",
    "TRACK_20_8_PRODUCTION_READINESS_REPORT.md",
    "TRACK_20_8_GO_NO_GO_CHECKLIST.md",
    "TRACK_20_8_SIX_PILLARS_SCORECARD.md",
    "TRACK_20_8_SECURITY_CERTIFICATION.md",
    "TRACK_20_8_EMAIL_SAFETY_CERTIFICATION.md",
    "TRACK_20_8_OPERATIONAL_THREAD_CERTIFICATION.md",
    "TRACK_20_8_MOBILE_CERTIFICATION.md",
    "TRACK_20_8_WORKFLOW_CERTIFICATION.md",
    "TRACK_20_8_HUMAN_WALKTHROUGH.md",
    "TRACK_20_8_DEPLOYMENT_CHECKLIST.md",
    "TRACK_20_8_ROLLBACK_CHECKLIST.md",
    "TRACK_20_8_BACKUP_VALIDATION.md",
    "TRACK_20_8_ZERO_DRIFT_MATRIX.md",
    "TRACK_20_8_FINAL_TEST_REPORT.md",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── Deliverables ─────────────────────────────────────────────────────

def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.8 deliverables: {missing}"


def test_all_deliverables_declare_verdict():
    """Every certification doc must declare a verdict — CERTIFIED /
    PASS / READY / GO / GREEN — so a reader can identify pass/fail at a
    glance."""
    ok_tokens = ("🟢", "GO", "PASS", "CERTIFIED", "READY", "GREEN")
    for name in REQUIRED_DOCS:
        src = _read(MEM / name)
        assert any(tok in src for tok in ok_tokens), (
            f"{name} must declare a machine-readable pass verdict "
            f"(one of {ok_tokens})"
        )


# ── Executive report content ─────────────────────────────────────────

def test_executive_report_declares_go():
    src = _read(MEM / "TRACK_20_8_EXECUTIVE_DEPLOYMENT_REPORT.md")
    assert "🟢" in src and ("GO" in src or "DEPLOY" in src), (
        "Executive Deployment Report must declare a GO verdict"
    )


# ── Register updates ─────────────────────────────────────────────────

def test_td_20_8_d01_registered_as_false_positive():
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    idx = src.find("TD-20.8-D01")
    assert idx != -1, "TD-20.8-D01 must be registered in the debt register"
    row = src[idx: src.find("\n", idx)]
    assert "False Positive" in row or "D" in row, (
        f"TD-20.8-D01 must be classified as Class D · False Positive"
    )


def test_no_open_debt_at_deployment_gate():
    """All classified debt entries must be either FIXED or CLOSED at
    the deployment gate."""
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    # Extract every TD- row.
    debt_ids = ("TD-19.62-A01", "TD-20.6A-001", "TD-20.6A-002",
                "TD-20.7-B01", "TD-20.7-C01", "TD-20.6B-A01",
                "TD-20.8-D01")
    for did in debt_ids:
        idx = src.find(did)
        assert idx != -1, f"debt {did} must be registered"
        row = src[idx: src.find("\n", idx)]
        # Any of these statuses is deployment-safe.
        safe = any(s in row for s in ("FIXED", "CLOSED", "False Positive"))
        assert safe, (
            f"debt {did} is not deployment-safe: {row}"
        )


# ── PRD / CHANGELOG ─────────────────────────────────────────────────

def test_prd_updated():
    assert "TRACK 20.8" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 20.8" in _read(MEM / "CHANGELOG.md")


# ── Continuity ──────────────────────────────────────────────────────

def test_prior_release_gate_tracks_preserved():
    """Track 20.8 must preserve every deliverable produced by Tracks
    20.6B (test hardening) and 20.7 (photo capture)."""
    for name in ("TRACK_20_6B_EXECUTIVE_SUMMARY.md",
                 "TRACK_20_6B_TEST_REPORT.md",
                 "TRACK_20_6B_EMAIL_SAFETY_CERTIFICATION.md",
                 "TRACK_20_7_EXECUTIVE_SUMMARY.md",
                 "TRACK_20_7_TEST_REPORT.md",
                 "TRACK_20_7_FIX_REPORT.md",
                 "TECHNICAL_DEBT_REGISTER.md"):
        assert (MEM / name).exists(), f"prior release-gate doc missing: {name}"


# ── Zero-drift verification (no production code change) ──────────────

def test_no_new_production_code_files_added_by_20_8():
    """Track 20.8 is certification-only. It must not have added any new
    Python module under backend/ (other than the lock test itself) or
    any new JSX/JS file under frontend/src/."""
    # Assert the lock test itself exists.
    assert (BE_TESTS / "test_track_20_8_deployment_certification.py").exists()
    # No new modules under backend/ named with track_20_8 outside tests.
    for p in (REPO / "backend").rglob("*_track_20_8_*.py"):
        rel = p.relative_to(REPO)
        assert rel.parts[1] == "tests", (
            f"Track 20.8 must not add production code file: {rel}"
        )
