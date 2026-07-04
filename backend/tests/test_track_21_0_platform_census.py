"""Track 21.0 · Complete Platform Census + Forensic Quality Audit — lock test.

Zero runtime touched. Pure structural + manifest assertions.

Run:
    pytest /app/backend/tests/test_track_21_0_platform_census.py -v
"""
import json
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"

REQUIRED_DOCS = [
    "PLATFORM_MANIFEST.json",
    "PLATFORM_MANIFEST_SUMMARY.md",
    "ROUTE_CENSUS.md",
    "API_CENSUS.md",
    "FRONTEND_CENSUS.md",
    "COMPONENT_CENSUS.md",
    "BUTTON_FORM_INPUT_CENSUS.md",
    "PERMISSION_CENSUS.md",
    "DATABASE_CENSUS.md",
    "WORKFLOW_CENSUS.md",
    "EMAIL_NOTIFICATION_CENSUS.md",
    "FILE_UPLOAD_CENSUS.md",
    "PDF_EXPORT_CENSUS.md",
    "TEST_CENSUS.md",
    "SECURITY_CENSUS.md",
    "PERFORMANCE_CENSUS.md",
    "UX_NOISE_AUDIT.md",
    "TECHNICAL_DEBT_REGISTER_UPDATE.md",
    "SIX_PILLAR_PLATFORM_SCORECARD.md",
    "DELETE_RETIRE_MERGE_CANDIDATES.md",
    "TRACK_21_0_FINAL_REPORT.md",
]


def _read(p): return p.read_text(encoding="utf-8")


def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 21.0 deliverables: {missing}"


def test_manifest_is_valid_json():
    p = MEM / "PLATFORM_MANIFEST.json"
    assert p.exists()
    m = json.loads(p.read_text())
    assert m["track"] == "21.0"
    assert "counts" in m
    # Non-zero sanity floors for every count category
    c = m["counts"]
    for k, floor in [("backend_endpoints", 200),
                     ("frontend_routes", 200),
                     ("mongo_collections_unique", 100),
                     ("test_files", 300),
                     ("frontend_pages", 200),
                     ("frontend_components", 200)]:
        assert c[k] >= floor, f"census count too low: {k} = {c[k]}"


def test_manifest_lists_endpoints_and_routes_and_collections():
    m = json.loads((MEM / "PLATFORM_MANIFEST.json").read_text())
    assert m["endpoints_total"] >= 200
    assert m["routes_total"] >= 200
    assert len(m["collections"]) >= 100
    # Each collection has an ID
    for c in m["collections"][:5]:
        assert c["id"].startswith("COLL-")


def test_new_class_c_debt_registered():
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    for did in ("TD-21.0-C01", "TD-21.0-C02", "TD-21.0-C03", "TD-21.0-C04",
                "TD-21.0-C05", "TD-21.0-C06", "TD-21.0-C07", "TD-21.0-C08"):
        assert did in src, f"Track 21.0 debt entry missing: {did}"


def test_zero_open_class_a_or_b_at_gate():
    """No Class-A or Class-B entry may be OPEN at deployment gate."""
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    # Every Class-A/B row must end with FIXED/CLOSED/False Positive.
    for line in src.splitlines():
        if line.startswith("| TD-") and (" **A** " in line or " **B** " in line):
            assert any(s in line for s in ("FIXED", "CLOSED", "False Positive")), (
                f"OPEN Class-A or Class-B at deployment gate: {line[:120]}..."
            )


def test_track_20_6b_email_gate_untouched():
    src = _read(REPO / "backend/server.py")
    fn = src.find("async def _dispatch_auto_email")
    body = src[fn: fn + 8000]
    assert 'startswith("TEST_")' in body
    assert '"synthetic_test_record"' in body


def test_prd_and_changelog_updated():
    assert "TRACK 21.0" in _read(MEM / "PRD.md")
    assert "TRACK 21.0" in _read(MEM / "CHANGELOG.md")


def test_prior_release_gate_docs_preserved():
    for name in ("TRACK_20_9_EXECUTIVE_SUMMARY.md",
                 "TRACK_20_8_EXECUTIVE_DEPLOYMENT_REPORT.md",
                 "TRACK_20_7_EXECUTIVE_SUMMARY.md",
                 "TRACK_20_6B_EXECUTIVE_SUMMARY.md",
                 "TECHNICAL_DEBT_REGISTER.md"):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"


def test_final_report_declares_go():
    src = _read(MEM / "TRACK_21_0_FINAL_REPORT.md")
    assert "🟢" in src and "GO" in src
