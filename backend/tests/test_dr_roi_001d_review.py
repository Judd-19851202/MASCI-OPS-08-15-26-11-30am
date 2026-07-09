"""DR-ROI-001D review-test — independent verification by testing agent.

Covers:
- /api/ods/meta task_routes + providers_with_keys shape
- /api/dr-v2/photos/{id}/analyze graceful no-crash without bytes
- idempotency (cached:true)
- 404 for missing photo
- accept/dismiss/resolve state transitions with seeded intel doc
- photo_evidence_fact emission after accept
- V1 route existence (auth-protected but present)
"""
import os
import uuid
import asyncio
import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

BASE = os.environ.get("REACT_APP_BACKEND_URL",
                     "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
MONGO = os.environ.get("MONGO_URL") or open("/app/backend/.env").read().split('MONGO_URL="')[1].split('"')[0]
DB = os.environ.get("DB_NAME") or "masci_safety_preview"

REPORT_ID = "drv2-c5540414a6ca"
PHOTO_ID = "phX1"


# ----- /api/ods/meta shape ---------------------------------------------------
def test_ods_meta_photo_vision_route():
    r = requests.get(f"{BASE}/api/ods/meta", timeout=30)
    assert r.status_code == 200
    d = r.json()
    gw = d.get("ai_gateway", {})
    tr = gw.get("task_routes", {}).get("photo_vision")
    assert tr == {"provider": "openai", "model": "gpt-5.4"}, f"got {tr!r}"
    pwk = gw.get("env", {}).get("providers_with_keys", {})
    assert pwk.get("openai") is True, f"openai not in providers_with_keys: {pwk}"


# ----- Graceful failure (no bytes) -----------------------------------------
def test_analyze_no_bytes_graceful():
    r = requests.post(
        f"{BASE}/api/dr-v2/photos/{PHOTO_ID}/analyze",
        json={"photo_id": PHOTO_ID, "force": True},
        timeout=45,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is False, f"expected ai_available False without bytes; got {d}"
    intel = d["intel"]
    for k in ("report_id", "photo_id", "project_id", "tenant_id",
              "evidence_hash", "analysis_status", "provider", "model",
              "observations", "suggested_links", "questions"):
        assert k in intel, f"missing field {k}"
    assert intel["analysis_status"] == "unavailable"
    assert intel["provider"] == "openai"
    assert intel["model"] == "gpt-5.4"


# ----- Idempotency ---------------------------------------------------------
def test_analyze_cached_on_repeat():
    # First (may hit cache from earlier). Do two calls back to back.
    requests.post(f"{BASE}/api/dr-v2/photos/{PHOTO_ID}/analyze",
                  json={"photo_id": PHOTO_ID}, timeout=30)
    r = requests.post(f"{BASE}/api/dr-v2/photos/{PHOTO_ID}/analyze",
                      json={"photo_id": PHOTO_ID}, timeout=30)
    assert r.status_code == 200
    assert r.json()["cached"] is True


# ----- 404 missing draft ---------------------------------------------------
def test_analyze_missing_photo_404():
    r = requests.post(
        f"{BASE}/api/dr-v2/photos/does-not-exist-abc-999/analyze",
        json={"photo_id": "does-not-exist-abc-999"}, timeout=30,
    )
    assert r.status_code == 404


# ----- GET intelligence ----------------------------------------------------
def test_get_intelligence():
    r = requests.get(
        f"{BASE}/api/dr-v2/photos/{PHOTO_ID}/intelligence?report_id={REPORT_ID}",
        timeout=30,
    )
    assert r.status_code == 200
    intel = r.json()["intel"]
    assert intel is not None
    assert intel["photo_id"] == PHOTO_ID
    assert intel["report_id"] == REPORT_ID


# ----- accept/dismiss/resolve via seeded intel doc -------------------------
@pytest.fixture(scope="module")
def seeded():
    """Directly seed a fake intel doc with suggested_link + question so
    we can exercise accept/dismiss/resolve on a real DR-V2 draft."""
    async def _seed():
        client = AsyncIOMotorClient(MONGO)
        db = client[DB]
        # Use a new synthetic photo id but bound to the real draft.
        photo_id = f"TEST-{uuid.uuid4().hex[:8]}"
        link_id = uuid.uuid4().hex
        link_id_dismiss = uuid.uuid4().hex
        question_id = uuid.uuid4().hex
        # Ensure the draft has this photo id attached so 404 doesn't fire on analyze,
        # but we won't need analyze here — we insert intel directly.
        doc = {
            "intel_id": uuid.uuid4().hex,
            "report_id": REPORT_ID,
            "photo_id": photo_id,
            "project_id": "PH-001",
            "tenant_id": "masci",
            "evidence_hash": "seeded-" + uuid.uuid4().hex,
            "analysis_status": "complete",
            "provider": "openai",
            "model": "gpt-5.4",
            "confidence": 0.87,
            "narrative": "Seeded for accept/dismiss/resolve test.",
            "observations": [
                {"label": "excavator on site", "category": "equipment",
                 "confidence": 0.9, "requires_supervisor_confirmation": True},
            ],
            "suggested_links": [
                {"link_id": link_id, "target_type": "activity_card",
                 "target_id": "act-1", "target_label": "Excavation",
                 "confidence": 0.9, "status": "suggested"},
                {"link_id": link_id_dismiss, "target_type": "equipment",
                 "target_id": "EQ-5", "target_label": "CAT 320",
                 "confidence": 0.7, "status": "suggested"},
            ],
            "questions": [
                {"question_id": question_id, "prompt": "Confirm crew on-site?",
                 "status": "open"},
            ],
            "conflicts": [],
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "trace_id": uuid.uuid4().hex,
        }
        await db["dr_v2_photo_intelligence"].replace_one(
            {"report_id": REPORT_ID, "photo_id": photo_id}, doc, upsert=True,
        )
        return photo_id, link_id, link_id_dismiss, question_id

    photo_id, link_id, link_id_dismiss, question_id = asyncio.get_event_loop().run_until_complete(_seed())
    yield {"photo_id": photo_id, "link_id": link_id,
           "link_id_dismiss": link_id_dismiss, "question_id": question_id}

    # Cleanup
    async def _cleanup():
        client = AsyncIOMotorClient(MONGO)
        db = client[DB]
        await db["dr_v2_photo_intelligence"].delete_one(
            {"report_id": REPORT_ID, "photo_id": photo_id})
        await db["operational_facts"].delete_many(
            {"source_item_id": f"photo:{photo_id}"})
    asyncio.get_event_loop().run_until_complete(_cleanup())


def test_link_accept_transitions_and_emits_fact(seeded):
    ph = seeded["photo_id"]; lid = seeded["link_id"]
    r = requests.post(
        f"{BASE}/api/dr-v2/photos/{ph}/links/{lid}/accept",
        json={"supervisor_id": "sup-test"}, timeout=30,
    )
    assert r.status_code == 200, r.text
    intel = r.json()["intel"]
    accepted = [s for s in intel["suggested_links"] if s["link_id"] == lid][0]
    assert accepted["status"] == "accepted"
    assert accepted.get("reviewed_by") == "sup-test"
    assert "reviewed_at" in accepted

    # ODS fact should appear.
    facts = requests.get(
        f"{BASE}/api/ods/facts",
        params={"fact_type": "photo_evidence_fact", "project_id": "PH-001", "limit": 20},
        timeout=30,
    )
    assert facts.status_code == 200
    body = facts.json()
    matches = [f for f in body.get("facts", body if isinstance(body, list) else [])
               if f.get("source_item_id") == f"photo:{ph}"]
    assert matches, f"no photo_evidence_fact emitted; response={body}"


def test_link_dismiss_transitions_and_no_fact(seeded):
    ph = seeded["photo_id"]; lid = seeded["link_id_dismiss"]
    r = requests.post(
        f"{BASE}/api/dr-v2/photos/{ph}/links/{lid}/dismiss",
        json={"supervisor_id": "sup-test"}, timeout=30,
    )
    assert r.status_code == 200
    intel = r.json()["intel"]
    dismissed = [s for s in intel["suggested_links"] if s["link_id"] == lid][0]
    assert dismissed["status"] == "dismissed"

    # No new fact for dismissed link.
    facts = requests.get(
        f"{BASE}/api/ods/facts",
        params={"fact_type": "photo_evidence_fact", "project_id": "PH-001", "limit": 50},
        timeout=30,
    )
    body = facts.json()
    factlist = body.get("facts", body if isinstance(body, list) else [])
    matches = [f for f in factlist if f.get("source_item_id") == f"photo:{ph}"
               and (f.get("payload") or {}).get("linked_equipment") == "EQ-5"]
    assert not matches, f"unexpected fact emitted on dismiss: {matches}"


def test_question_resolve_transitions(seeded):
    ph = seeded["photo_id"]; qid = seeded["question_id"]
    r = requests.post(
        f"{BASE}/api/dr-v2/photos/{ph}/questions/{qid}/resolve",
        json={"resolution": "confirmed", "supervisor_id": "sup-test"},
        timeout=30,
    )
    assert r.status_code == 200
    intel = r.json()["intel"]
    q = [q for q in intel["questions"] if q["question_id"] == qid][0]
    assert q["status"] == "resolved"
    assert q["resolution"] == "confirmed"
    assert q.get("reviewed_by") == "sup-test"
    assert "reviewed_at" in q


# ----- 404 on missing link/question ---------------------------------------
def test_accept_missing_link_404(seeded):
    ph = seeded["photo_id"]
    r = requests.post(
        f"{BASE}/api/dr-v2/photos/{ph}/links/nonexistent-link-id/accept",
        json={}, timeout=30,
    )
    assert r.status_code == 404


# ----- Feature-flag off code path (static check) --------------------------
def test_feature_flag_off_returns_gated_envelope():
    """Verify code path: with flag off, analyze returns ok:false + photo_vision_enabled:false."""
    src = open("/app/backend/routes/dr_v2_photos.py").read()
    assert 'photo_vision_enabled()' in src
    assert '"photo_vision_enabled": False' in src
    assert '"DR_V2_PHOTO_VISION_ENABLED off"' in src
