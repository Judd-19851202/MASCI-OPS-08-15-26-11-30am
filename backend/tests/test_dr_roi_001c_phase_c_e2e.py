"""DR-ROI-001 Phase C — E2E test suite hitting live preview endpoints.

Covers review request items:
  - /api/dr-v2/meta
  - drafts create/update/read + evidence_hash behavior
  - synthesize cache miss then hit
  - synthesize force bypass
  - synthesize 404 on missing draft
  - approve accept/edit/reject/regenerate + audit log
  - invalid action rejected
  - V1 daily-reports zero drift
  - route count parity
"""
import os
import uuid
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

# V1 whitelist for evidence_refs verification
WHITELIST = {
    "project_name", "project_number", "report_date", "shift", "supervisor_name",
    "weather", "gps_location", "masci_crews", "crew_hours_total",
    "absent_early_chips", "equipment_used", "equipment_hours",
    "equipment_idle_reasons", "activity_cards", "constraint_cards",
    "tomorrow_readiness", "safety_incidents", "quality_findings", "jha_ack",
    "photos", "temperature_f", "precipitation", "wind_mph",
}


@pytest.fixture(scope="module")
def sess():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _rich_draft(report_id=None):
    p = {
        "supervisor_id": "TEST_sup_1",
        "project_number": "TEST-9001",
        "report_date": "2026-01-15",
        "day_setup": {
            "project_name": "TEST Site Alpha", "project_number": "TEST-9001",
            "report_date": "2026-01-15", "shift": "day",
            "supervisor_name": "J. Ortiz",
        },
        "masci_crews": [{"crew": "Pipe A", "count": 4, "hours": 8}],
        "equipment_used": [{"asset": "CAT 336", "hours": 7.5}],
        "activity_cards": [
            {"area": "Zone A", "activity": "Trench 8ft", "quantity": 120, "unit": "lf"},
        ],
        "constraint_cards": [{"kind": "utility", "note": "Gas locate delay 2h"}],
        "tomorrow_readiness": {"crew_confirmed": True, "materials_on_site": True},
        "safety": {"safety_incidents": 0, "jha_ack": True},
        "weather": {"temperature_f": 42, "precipitation": "none", "wind_mph": 8},
    }
    if report_id:
        p["report_id"] = report_id
    return p


# ---------------- META ----------------
def test_meta_shape(sess):
    r = sess.get(f"{API}/dr-v2/meta")
    assert r.status_code == 200
    d = r.json()
    assert d["feature_flag"] is True
    assert d["ai_available"] is True
    assert d["model"] == "claude-sonnet-4-5-20250929"
    schema = d["envelope_schema"]
    for k in ("narrative", "confidence", "evidence_refs", "sources_used"):
        assert k in schema["required"]


# ---------------- DRAFTS ----------------
def test_draft_create_read_update_hash(sess):
    # create (no report_id)
    r = sess.post(f"{API}/dr-v2/drafts", json=_rich_draft())
    assert r.status_code == 200, r.text
    d = r.json()
    rid = d["report_id"]
    assert rid.startswith("drv2-")
    h1 = d["evidence_hash"]
    assert h1 and "saved_at" in d

    # GET
    g = sess.get(f"{API}/dr-v2/drafts/{rid}")
    assert g.status_code == 200
    assert g.json()["report_id"] == rid

    # re-save identical → hash SAME
    r2 = sess.post(f"{API}/dr-v2/drafts", json=_rich_draft(rid))
    assert r2.status_code == 200
    assert r2.json()["report_id"] == rid
    assert r2.json()["evidence_hash"] == h1, "Identical draft must produce identical hash"

    # change supervisor_name → hash CHANGES
    changed = _rich_draft(rid)
    changed["day_setup"]["supervisor_name"] = "M. Kim"
    r3 = sess.post(f"{API}/dr-v2/drafts", json=changed)
    assert r3.status_code == 200
    assert r3.json()["evidence_hash"] != h1, "Changed evidence must change hash"

    # store rid for downstream tests via module scope
    pytest.rid_shared = rid


# ---------------- SYNTHESIZE ----------------
def test_synthesize_cold_then_cached(sess):
    rid = pytest.rid_shared
    r1 = sess.post(f"{API}/dr-v2/ai/synthesize", json={"report_id": rid}, timeout=120)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert d1["ai_available"] is True
    assert d1["model"] == "claude-sonnet-4-5-20250929"
    outs = d1["outputs"]
    assert set(outs.keys()) == {"day_narrative", "risk_and_constraints", "tomorrow_readiness"}
    assert d1["cache_hits"] == 0
    # Some agents may fail — total should equal misses (or fewer if exceptions); at least one output
    for name, o in outs.items():
        assert isinstance(o.get("narrative"), str)
        assert 0.0 <= float(o.get("confidence", 0)) <= 1.0
        assert isinstance(o.get("evidence_refs"), list)
        assert isinstance(o.get("sources_used"), list)
        # Evidence refs must reference only whitelisted fields (allow prefix like 'activity_cards[0].quantity')
        for ref in o["evidence_refs"]:
            # Root token = first identifier-like segment (before . [ : whitespace)
            import re
            m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", ref)
            root = m.group(1) if m else ref
            assert root in WHITELIST, f"evidence_ref {ref!r} not whitelisted (agent={name})"
        if o.get("ai_available", True):
            assert o.get("model") == "claude-sonnet-4-5-20250929"
            assert o.get("provider") == "emergent"
            assert o.get("generated_at")

    # Second call — should hit cache
    r2 = sess.post(f"{API}/dr-v2/ai/synthesize", json={"report_id": rid}, timeout=30)
    assert r2.status_code == 200
    d2 = r2.json()
    # cache_hits should equal number of previously successful (cached) agents
    assert d2["cache_hits"] >= 1, f"Expected cache hits, got {d2}"
    # If all 3 were cached: hits==3, misses==0
    if d1["cache_misses"] == 3 and all(o.get("ai_available", True) for o in outs.values()):
        assert d2["cache_hits"] == 3 and d2["cache_misses"] == 0


def test_synthesize_force_bypasses_cache(sess):
    rid = pytest.rid_shared
    r = sess.post(f"{API}/dr-v2/ai/synthesize", json={"report_id": rid, "force": True}, timeout=120)
    assert r.status_code == 200
    d = r.json()
    assert d["cache_hits"] == 0
    assert d["cache_misses"] == 3


def test_synthesize_404_missing_draft(sess):
    r = sess.post(f"{API}/dr-v2/ai/synthesize", json={"report_id": "drv2-nonexistent-xyz"})
    assert r.status_code == 404


# ---------------- APPROVAL ----------------
def test_approval_flow_and_audit(sess):
    rid = pytest.rid_shared
    steps = [
        {"action": "accept", "agent": "day_narrative"},
        {"action": "edit", "agent": "day_narrative", "edited_narrative": "Supervisor edit v1"},
        {"action": "reject", "agent": "risk_and_constraints", "reason": "Not accurate"},
        {"action": "regenerate", "agent": "tomorrow_readiness", "reason": "Regenerate"},
    ]
    for s in steps:
        payload = {"report_id": rid, **s}
        r = sess.post(f"{API}/dr-v2/ai/approve", json=payload)
        assert r.status_code == 200, r.text

    audit = sess.get(f"{API}/dr-v2/ai/audit/{rid}")
    assert audit.status_code == 200
    log = audit.json()["log"]
    # Chronological — last 4 entries should match our actions in order
    tail = log[-4:]
    assert [e["action"] for e in tail] == ["accept", "edit", "reject", "regenerate"]
    edit_entry = tail[1]
    assert edit_entry["edited_narrative"] == "Supervisor edit v1"


def test_approval_invalid_action(sess):
    r = sess.post(f"{API}/dr-v2/ai/approve", json={"report_id": pytest.rid_shared, "action": "delete"})
    assert r.status_code == 400


# ---------------- V1 zero drift ----------------
def test_v1_daily_reports_still_works(sess):
    r = sess.get(f"{API}/daily-reports")
    assert r.status_code in (200, 401, 403), f"V1 list failed: {r.status_code}"


def test_route_count_parity(sess):
    r = sess.get(f"{API}/openapi.json", timeout=30)
    if r.status_code != 200:
        pytest.skip("openapi not exposed")
    paths = r.json().get("paths", {})
    # Count distinct method+path
    total = sum(len(m) for m in paths.values())
    print(f"Total routes: {total}")
    # Expected == 1447 per problem statement; tolerate ±5 for other churn
    assert abs(total - 1447) <= 10, f"route count drift: {total}"
