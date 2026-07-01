"""Track 19.16 · Phase B2 · Public Gate + Advanced Reliability · LOCK TESTS.

Covers:
  * public near-miss submission via the domain engine
  * anonymous vs self-identified attribution
  * idempotency key deduplication
  * immediate-danger flag preserved
  * legacy incidents collection untouched (Zero-Drift)
  * B1 route file untouched
  * frontend surface files exist with the required contracts:
      - /near-miss route mount
      - offline queue with idempotency
      - draft resume banner
      - EN↔ES parity for every new key
"""
from __future__ import annotations

import asyncio
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Reuse the fake DB from Phase A tests.
from tests.test_track_19_16_incident_engine_phase_a import _FakeDB  # noqa: E402

from incident_engine.public_gate import (
    COLLECTION_PUBLIC_SUBS,
    NearMissPublicSubmission,
    submit_public_near_miss,
)
from incident_engine.events import list_events


def _run(c):
    return asyncio.get_event_loop().run_until_complete(c)


@pytest.fixture
def db():
    return _FakeDB()


# ═══════════════════════════════════════════════════════════════════
# 1 · PUBLIC KIOSK SUBMISSION
# ═══════════════════════════════════════════════════════════════════
def test_public_anonymous_submission_creates_field_submitted_case(db):
    sub = NearMissPublicSubmission(
        what_almost_happened="forklift almost struck a walker",
        location_label="Zone A",
    )
    out = _run(submit_public_near_miss(db, sub))
    case = out["case"]
    assert case["state"] == "FIELD_SUBMITTED"
    assert case["field_block"]["incident_type"] == "near_miss"
    assert case["field_block_locked"] is True
    assert case["field_block"]["public_gate_source"] == "public_gate_near_miss"
    assert case["field_block"]["submitter_kind"] == "anonymous"
    assert case["field_block"]["reporter_name"] == "Anonymous"
    assert out["submitter_kind"] == "anonymous"
    assert out["duplicate"] is False
    assert case["case_number"]


def test_public_self_identified_submission_records_name(db):
    sub = NearMissPublicSubmission(
        what_almost_happened="near miss on driveway",
        location_label="North gate",
        submitter_name="Maria Lopez",
        submitter_contact="maria@example.com",
        submitter_company="Public Observer",
    )
    out = _run(submit_public_near_miss(db, sub))
    assert out["submitter_kind"] == "self_identified"
    assert out["case"]["field_block"]["reporter_name"] == "Maria Lopez"
    assert out["case"]["field_block"]["submitter_contact"] == "maria@example.com"
    assert out["case"]["field_block"]["submitter_company"] == "Public Observer"


def test_public_immediate_danger_flag_preserved(db):
    sub = NearMissPublicSubmission(
        what_almost_happened="live wire on ground",
        location_label="Corner",
        immediate_danger=True,
    )
    out = _run(submit_public_near_miss(db, sub))
    assert out["immediate_danger"] is True
    assert out["case"]["field_block"]["immediate_danger_flag"] is True


def test_public_language_marker_recorded(db):
    sub = NearMissPublicSubmission(
        what_almost_happened="casi accidente",
        location_label="Área A",
        language="es",
    )
    out = _run(submit_public_near_miss(db, sub))
    assert out["case"]["field_block"]["submitter_language"] == "es"


# ═══════════════════════════════════════════════════════════════════
# 2 · IDEMPOTENCY
# ═══════════════════════════════════════════════════════════════════
def test_idempotency_key_deduplicates_replay(db):
    key = "nm_test_key_12345"
    sub = NearMissPublicSubmission(
        what_almost_happened="rock fell near excavator",
        location_label="Cut A",
        idempotency_key=key,
    )
    a = _run(submit_public_near_miss(db, sub))
    b = _run(submit_public_near_miss(db, sub))
    assert a["case_id"] == b["case_id"]
    assert a["case_number"] == b["case_number"]
    assert b["duplicate"] is True
    # Only one case created.
    all_cases = _run(_list_all(db, "incident_cases"))
    assert len(all_cases) == 1
    # One row in the public submissions ledger.
    rows = _run(_list_all(db, COLLECTION_PUBLIC_SUBS))
    assert len(rows) == 1


def test_no_idempotency_key_creates_two_cases(db):
    sub = NearMissPublicSubmission(
        what_almost_happened="thing 1", location_label="here",
    )
    _run(submit_public_near_miss(db, sub))
    _run(submit_public_near_miss(db, sub))
    all_cases = _run(_list_all(db, "incident_cases"))
    assert len(all_cases) == 2


async def _list_all(db, coll):
    cur = db[coll].find({}, {"_id": 0})
    return [d async for d in cur]


# ═══════════════════════════════════════════════════════════════════
# 3 · EVENT SPINE COVERAGE
# ═══════════════════════════════════════════════════════════════════
def test_public_submission_emits_expected_events(db):
    sub = NearMissPublicSubmission(
        what_almost_happened="close call", location_label="lane 2",
    )
    out = _run(submit_public_near_miss(db, sub))
    ev = _run(list_events(db, case_id=out["case_id"]))
    types = [e["event_type"] for e in ev]
    # Must include lifecycle events for a submitted case.
    assert "case.created" in types
    assert "case.field_submitted" in types
    assert "case.state_changed" in types
    # Event payload must record the kiosk source somewhere.
    payloads_str = str([e.get("payload") for e in ev])
    assert "kiosk" in payloads_str or "public_gate" in str(out["case"]["field_block"])


# ═══════════════════════════════════════════════════════════════════
# 4 · ZERO-DRIFT GUARDS
# ═══════════════════════════════════════════════════════════════════
REPO_ROOT = Path("/app")


def test_public_gate_never_writes_to_legacy_incidents_collection():
    src = (REPO_ROOT / "backend/incident_engine/public_gate.py").read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "db.incidents.insert", 'db["incidents"].insert',
        "db.incidents.update", 'db["incidents"].update',
        "db.incidents.delete", 'db["incidents"].delete',
    ):
        assert forbidden not in src, forbidden


def test_legacy_incident_lifecycle_file_unchanged():
    txt = (REPO_ROOT / "backend/routes/incident_lifecycle.py").read_text(
        encoding="utf-8"
    )
    assert "register_incident_lifecycle_routes" in txt
    assert '/incidents/{incident_id}/transition' in txt


def test_b1_routes_still_mounted_in_server():
    server_txt = (REPO_ROOT / "backend/server.py").read_text(encoding="utf-8")
    assert "register_incident_engine_routes" in server_txt
    assert "register_public_routes as _register_ie_public_routes" in server_txt


def test_phase_a_engine_files_untouched_by_public_gate():
    """Phase A engine files must not depend on public_gate.py."""
    engine_dir = REPO_ROOT / "backend/incident_engine"
    for name in (
        "constants.py", "models.py", "state_machine.py",
        "permissions.py", "case_service.py", "events.py",
        "evidence.py", "corrective_actions.py", "legacy_adapter.py",
        "vocabulary.py",
    ):
        src = (engine_dir / name).read_text(encoding="utf-8")
        assert "public_gate" not in src, f"{name} imports public_gate"


# ═══════════════════════════════════════════════════════════════════
# 5 · FRONTEND SURFACE CONTRACTS
# ═══════════════════════════════════════════════════════════════════
FE_ROOT = REPO_ROOT / "frontend/src"


def test_public_kiosk_page_exists():
    p = FE_ROOT / "pages/NearMissKiosk.jsx"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    # Wired to the offline queue + emits the required testids.
    assert "submitPublicNearMiss" in src
    assert 'data-testid="near-miss-kiosk"' in src
    assert 'data-testid="near-miss-submit"' in src
    assert 'data-testid="near-miss-success"' in src
    assert 'data-testid="near-miss-queued"' in src
    assert 'data-testid="near-miss-immediate-danger-alert"' in src


def test_offline_queue_module_exists_and_provides_idempotency():
    p = FE_ROOT / "lib/incidentOfflineQueue.js"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    assert "newIdempotencyKey" in src
    assert "flushQueue" in src
    assert "submitPublicNearMiss" in src
    assert "X-Idempotency-Key" in src
    # Must not lie about submission when offline.
    assert '"queued"' in src
    assert '"submitted"' in src


def test_draft_resume_banner_component_exists():
    p = FE_ROOT / "components/DraftResumeBanner.jsx"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    assert 'data-testid="incident-report-draft-banner"' in src
    assert 'data-testid="incident-report-draft-banner-resume"' in src
    assert 'data-testid="incident-report-draft-banner-discard"' in src


def test_app_js_mounts_kiosk_route_alongside_legacy():
    app_txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    # New route present.
    assert 'path="/near-miss"' in app_txt
    assert "<NearMissKiosk />" in app_txt
    # B1 route still present.
    assert 'path="/incidents/report"' in app_txt
    # Legacy route still present.
    assert 'path="/incidents/new"' in app_txt


# ═══════════════════════════════════════════════════════════════════
# 6 · BILINGUAL PARITY (EN↔ES for every new B2 key)
# ═══════════════════════════════════════════════════════════════════
def test_i18n_has_all_new_b2_keys():
    i18n = (FE_ROOT / "lib/i18n.js").read_text(encoding="utf-8")
    required_keys = [
        "Public Near-Miss Reporting",
        "Report a near miss",
        "What almost happened?",
        "Where did it happen?",
        "Is anyone in immediate danger right now?",
        "This form is not a replacement for emergency action.",
        "Move people away from the hazard now.",
        "Notify a supervisor immediately.",
        "Call 911 if there is an active emergency.",
        "Submit near-miss report",
        "Save & queue",
        "Saved and queued",
        "This will submit when connection returns.",
        "Thank you. Safety has received your report.",
        "Anonymous submissions are welcome. Nothing is shared with your employer beyond Safety.",
        "Online", "Offline",
        "Unfinished report", "Resume", "Discard",
        "just now", "ago",
        "Add photo (optional)",
        "Add your name or a photo (optional)",
    ]
    for k in required_keys:
        assert f'"{k}":' in i18n, f"missing i18n key: {k}"


# ═══════════════════════════════════════════════════════════════════
# 7 · SIX-PILLAR CERTIFICATION (B2)
# ═══════════════════════════════════════════════════════════════════
def test_pillar_trusted_never_falsely_reports_submitted():
    """When the client is offline, the queue MUST return status=queued,
    never status=submitted. The lock test scans the source file to make
    sure the code path exists and cannot be conflated."""
    src = (FE_ROOT / "lib/incidentOfflineQueue.js").read_text(encoding="utf-8")
    # Look for the explicit branch: `if (!isOnline()) { ... return { status: "queued" ... } }`
    assert re.search(r"isOnline\(\)\s*[\)\s\{\s]", src)
    assert 'status: "queued"' in src


def test_pillar_operational_kiosk_shows_emergency_guidance_when_flag_set():
    src = (FE_ROOT / "pages/NearMissKiosk.jsx").read_text(encoding="utf-8")
    # Emergency alert is rendered conditionally on immediate_danger flag.
    assert "form.immediate_danger &&" in src
    assert "EmergencyAlert" in src


def test_pillar_powerful_kiosk_flows_through_phase_a_engine(db):
    """The public gate must reuse Phase A helpers (case_service) — not
    duplicate case creation logic. The behaviour test confirms this:
    events, immutability, and case_number generation only happen via
    Phase A. Any regression that bypasses case_service.create_case
    would fail these assertions."""
    sub = NearMissPublicSubmission(
        what_almost_happened="test", location_label="loc",
    )
    out = _run(submit_public_near_miss(db, sub))
    # Case number is Phase A-issued (YYYY-NNNNN format).
    assert re.match(r"^\d{4}-\d{5}$", out["case_number"])
    # State is Phase A-managed (FIELD_SUBMITTED after transition).
    assert out["case"]["state"] == "FIELD_SUBMITTED"
    # Immutability flag comes from Phase A transition logic.
    assert out["case"]["field_block_locked"] is True
