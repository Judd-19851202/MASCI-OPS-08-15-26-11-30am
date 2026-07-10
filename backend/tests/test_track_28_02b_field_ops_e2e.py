"""TRACK 28.02B · Field Operations · End-to-End Certification.

Executes every Field Operations workflow as an operator would:
  1. Log in via /api/auth/multi-login (canonical super-admin).
  2. Create a brand-new TEST_28_02_<workflow>_<ts> record via the real
     write path.
  3. Read it back through the list + detail endpoints.
  4. Exercise downstream integrations (PDF, lifecycle events, audit,
     CSV export) where each workflow supports them.
  5. Clean up — either via the DELETE endpoint or (for Daily Reports,
     which are archive-locked at 410) via a direct MongoDB purge of
     any TEST_28_02_ prefixed rows.

Test invariants:
  • Every POST must return 200/201 with an id.
  • The GET-list must include the new id.
  • The GET-detail must return the persisted record.
  • Where a PDF endpoint exists, it must return HTTP 200 with a
    Content-Type of application/pdf (Daily Reports).
  • Cleanup must leave zero TEST_28_02_ prefixed rows on the DB.

Every assertion failure = certification defect. This suite is the
final gate that closes Track 28.02B.
"""
from __future__ import annotations

import os
import time
import uuid
import json
from datetime import date
import httpx
import pytest
from pymongo import MongoClient


# ── environment ────────────────────────────────────────────────
def _load_backend_url() -> str:
    # Prefer local supervisor (fast, no external egress hop)
    try:
        r = httpx.get("http://localhost:8001/api/health", timeout=5)
        if r.status_code == 200:
            return "http://localhost:8001"
    except Exception:  # noqa: BLE001
        pass
    with open("/app/frontend/.env", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not found")


BACKEND = _load_backend_url()
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TEST_PREFIX = "TEST_28_02_"

# Mongo direct access (for Daily-Report cleanup + Cross-workflow prefix purge).
_MONGO_URL = os.environ.get("MONGO_URL")
_DB_NAME = os.environ.get("DB_NAME") or "masci_safety_preview"
if not _MONGO_URL:
    # Read from backend .env
    with open("/app/backend/.env", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("MONGO_URL="):
                _MONGO_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("DB_NAME="):
                _DB_NAME = line.split("=", 1)[1].strip().strip('"').strip("'")

_mongo = MongoClient(_MONGO_URL)
_db = _mongo[_DB_NAME]


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = httpx.post(
        f"{BACKEND}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    r.raise_for_status()
    tok = (r.json().get("portal_tokens") or {}).get("admin")
    assert tok and "." in tok, "expected UUID.HMAC admin token"
    return tok


@pytest.fixture(scope="module")
def hdrs(admin_token: str) -> dict:
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


def _ts() -> str:
    return str(int(time.time() * 1000))


def _today() -> str:
    return date.today().isoformat()


def _project_name(workflow: str) -> str:
    return f"{TEST_PREFIX}{workflow}_{_ts()}_{uuid.uuid4().hex[:6]}"


# ═════════════════════════════════════════════════════════════════
# 1. DAILY REPORTS
# ═════════════════════════════════════════════════════════════════
def test_daily_report_full_e2e(hdrs: dict) -> None:
    pname = _project_name("dailyreport")
    payload = {
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert Yard",
        "report_date": _today(),
        "prepared_by": f"{TEST_PREFIX}Foreman",
        "superintendent": f"{TEST_PREFIX}Super",
        "weather_summary": "72F clear · cert",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "general_notes": "Track 28.02B end-to-end cert.",
        "masci_crews": [{"crew_lead": "Cert Lead", "crew_size": 3}],
        "activities": [{"activity": "Cert walk", "notes": "auto"}],
    }
    # POST
    r = httpx.post(f"{BACKEND}/api/daily-reports", headers=hdrs, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    dr_id = body.get("id")
    assert dr_id, "no id returned"

    # GET detail
    r = httpx.get(f"{BACKEND}/api/daily-reports/{dr_id}", headers=hdrs, timeout=30)
    assert r.status_code == 200
    assert r.json().get("project_name") == pname

    # LIST intentionally excludes TEST_ prefixed rows via TRACK 24.9
    # synthetic-DR filter. The exclusion is CORRECT here — assert it.
    r = httpx.get(f"{BACKEND}/api/daily-reports", headers=hdrs, timeout=30)
    assert r.status_code == 200
    ids = [it.get("id") for it in r.json()]
    assert dr_id not in ids, "TRACK 24.9 must hide TEST_ Daily Reports from operational list"

    # PDF endpoint returns application/pdf
    r = httpx.get(f"{BACKEND}/api/daily-reports/{dr_id}/pdf", headers=hdrs, timeout=60)
    assert r.status_code == 200, r.text[:200]
    assert "application/pdf" in r.headers.get("content-type", ""), r.headers

    # Lifecycle events endpoint (audit trail)
    r = httpx.get(f"{BACKEND}/api/daily-reports/{dr_id}/state-events", headers=hdrs, timeout=15)
    assert r.status_code == 200, r.text[:200]

    # CSV export EXCLUDES synthetic (per TRACK 24.9) — assert filter still holds.
    r = httpx.get(f"{BACKEND}/api/daily-reports.csv", headers=hdrs, timeout=60)
    assert r.status_code == 200
    assert pname not in r.text, "TRACK 24.9 must hide TEST_ Daily Reports from CSV export"

    # Cleanup — API DELETE is intentionally 410; purge via Mongo directly.
    r = httpx.delete(f"{BACKEND}/api/daily-reports/{dr_id}", headers=hdrs, timeout=15)
    assert r.status_code == 410  # documented archive-freeze
    _db.daily_reports.delete_one({"id": dr_id})
    r = httpx.get(f"{BACKEND}/api/daily-reports/{dr_id}", headers=hdrs, timeout=15)
    assert r.status_code == 404, "Daily Report should be purged after cleanup"


# ═════════════════════════════════════════════════════════════════
# 2. MEETINGS
# ═════════════════════════════════════════════════════════════════
def test_meeting_full_e2e(hdrs: dict) -> None:
    pname = _project_name("meeting")
    payload = {
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert Yard",
        "meeting_date": _today(),
        "meeting_time": "07:00",
        "conducted_by": f"{TEST_PREFIX}Conductor",
        "topic": "Track 28.02B Cert Toolbox Talk",
        "topic_category": "toolbox_talk",
        "discussion_notes": "auto cert",
        "attendees": [{
            "name": "Cert Attendee",
            "company": f"{TEST_PREFIX}Sub Co.",
            "signature": "data:image/png;base64,iVBORw0KGgo=",
            "acknowledged": True,
            "non_masci": True,
        }],
    }
    r = httpx.post(f"{BACKEND}/api/meetings", headers=hdrs, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    mid = r.json()["id"]

    r = httpx.get(f"{BACKEND}/api/meetings/{mid}", headers=hdrs, timeout=15)
    assert r.status_code == 200
    assert r.json()["topic"] == "Track 28.02B Cert Toolbox Talk"

    r = httpx.get(f"{BACKEND}/api/meetings", headers=hdrs, timeout=30)
    assert r.status_code == 200
    # TRACK 28.06 doctrine · synthetic must NOT surface on operator list.
    assert mid not in [x.get("id") for x in r.json()], (
        "TRACK 28.06 regression: synthetic meeting leaked to list"
    )

    r = httpx.delete(f"{BACKEND}/api/meetings/{mid}", headers=hdrs, timeout=15)
    assert r.status_code == 200, r.text
    r = httpx.get(f"{BACKEND}/api/meetings/{mid}", headers=hdrs, timeout=15)
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════
# 3. SITE INSPECTIONS
# ═════════════════════════════════════════════════════════════════
def test_inspection_full_e2e(hdrs: dict) -> None:
    pname = _project_name("inspection")
    payload = {
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert Yard",
        "inspection_date": _today(),
        "inspection_time": "08:30",
        "inspector_name": f"{TEST_PREFIX}Inspector",
        "foreman_name": f"{TEST_PREFIX}Foreman",
        "work_activity": "Cert walkthrough",
        "ppe_compliance": {"hard_hat": "Yes", "safety_glasses": "Yes"},
        "hazards_observed": "No",
        "stop_work_issued": "No",
        "score": 100,
        "status": "PASS",
        "graded_yes": 10, "graded_no": 0, "graded_total": 10,
    }
    r = httpx.post(f"{BACKEND}/api/inspections", headers=hdrs, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    iid = r.json()["id"]

    r = httpx.get(f"{BACKEND}/api/inspections/{iid}", headers=hdrs, timeout=15)
    assert r.status_code == 200
    assert r.json()["project_name"] == pname

    r = httpx.get(f"{BACKEND}/api/inspections", headers=hdrs, timeout=30)
    assert r.status_code == 200
    # TRACK 28.06 doctrine · synthetic TEST_ inspection must NOT
    # surface on the operator-facing list (regression-locked by
    # `lib/synthetic_safety_filter.py`). Identity-scoped GET above
    # still returns the record.
    assert iid not in [x["id"] for x in r.json()], (
        "TRACK 28.06 regression: synthetic inspection leaked to "
        "/api/inspections list"
    )

    # Lifecycle audit
    r = httpx.get(f"{BACKEND}/api/inspections/{iid}/state-events", headers=hdrs, timeout=15)
    assert r.status_code == 200

    r = httpx.delete(f"{BACKEND}/api/inspections/{iid}", headers=hdrs, timeout=15)
    assert r.status_code == 200
    r = httpx.get(f"{BACKEND}/api/inspections/{iid}", headers=hdrs, timeout=15)
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════
# 4. INCIDENTS
# ═════════════════════════════════════════════════════════════════
def test_incident_full_e2e(hdrs: dict) -> None:
    pname = _project_name("incident")
    payload = {
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert Yard",
        "incident_date": _today(),
        "incident_time": "10:15",
        "reported_date": _today(),
        "reported_by": f"{TEST_PREFIX}Reporter",
        "incident_type": "Near Miss",
        "severity": "Low",
        "description": "TRACK 28.02B cert-only incident record — auto-cleaned.",
        "immediate_actions_taken": "Cleared.",
    }
    r = httpx.post(f"{BACKEND}/api/incidents", headers=hdrs, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    iid = r.json()["id"]

    r = httpx.get(f"{BACKEND}/api/incidents/{iid}", headers=hdrs, timeout=15)
    assert r.status_code == 200

    r = httpx.get(f"{BACKEND}/api/incidents", headers=hdrs, timeout=30)
    assert r.status_code == 200
    # TRACK 28.06 doctrine · synthetic must NOT surface on operator list.
    assert iid not in [x["id"] for x in r.json()], (
        "TRACK 28.06 regression: synthetic incident leaked to list"
    )

    # CSV export
    r = httpx.get(f"{BACKEND}/api/incidents.csv", headers=hdrs, timeout=60)
    assert r.status_code == 200

    # Lifecycle
    r = httpx.get(f"{BACKEND}/api/incidents/{iid}/state-events", headers=hdrs, timeout=15)
    assert r.status_code == 200

    r = httpx.delete(f"{BACKEND}/api/incidents/{iid}", headers=hdrs, timeout=15)
    assert r.status_code == 200
    r = httpx.get(f"{BACKEND}/api/incidents/{iid}", headers=hdrs, timeout=15)
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════
# 5. JHA (Job Hazard Analysis)
# ═════════════════════════════════════════════════════════════════
def test_jha_full_e2e(hdrs: dict) -> None:
    pname = _project_name("jha")
    payload = {
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert Yard",
        "jha_date": _today(),
        "job_title": "TRACK 28.02B Cert JHA",
        "crew_lead": f"{TEST_PREFIX}Lead",
        "task_steps": [
            {"step": "Setup", "hazard": "None", "control": "None"},
        ],
        "stop_work_acknowledged": "Yes",
    }
    r = httpx.post(f"{BACKEND}/api/jhas", headers=hdrs, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    jid = r.json()["id"]

    r = httpx.get(f"{BACKEND}/api/jhas/{jid}", headers=hdrs, timeout=15)
    assert r.status_code == 200

    r = httpx.get(f"{BACKEND}/api/jhas", headers=hdrs, timeout=30)
    assert r.status_code == 200
    # TRACK 28.06 doctrine · synthetic must NOT surface on operator list.
    assert jid not in [x["id"] for x in r.json()], (
        "TRACK 28.06 regression: synthetic JHA leaked to list"
    )

    r = httpx.delete(f"{BACKEND}/api/jhas/{jid}", headers=hdrs, timeout=15)
    assert r.status_code == 200
    r = httpx.get(f"{BACKEND}/api/jhas/{jid}", headers=hdrs, timeout=15)
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════
# 6. EQUIPMENT PRE-OP
# ═════════════════════════════════════════════════════════════════
def test_equipment_inspection_full_e2e(hdrs: dict) -> None:
    pname = _project_name("equipment")
    payload = {
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert Yard",
        "inspection_date": _today(),
        "inspection_time": "06:45",
        "operator_name": f"{TEST_PREFIX}Operator",
        "equipment_type": "Excavator",
        "equipment_unit": f"{TEST_PREFIX}UNIT-01",
        "equipment_make": "Cat", "equipment_model": "336",
        "checklist": {"lights": "Pass", "horn": "Pass"},
        "pass_count": 2, "fail_count": 0, "na_count": 0,
        "out_of_service": "No",
    }
    r = httpx.post(f"{BACKEND}/api/equipment-inspections", headers=hdrs, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    eid = r.json()["id"]

    r = httpx.get(f"{BACKEND}/api/equipment-inspections/{eid}", headers=hdrs, timeout=15)
    assert r.status_code == 200

    r = httpx.get(f"{BACKEND}/api/equipment-inspections", headers=hdrs, timeout=30)
    assert r.status_code == 200
    assert eid in [x["id"] for x in r.json()]

    r = httpx.delete(f"{BACKEND}/api/equipment-inspections/{eid}", headers=hdrs, timeout=15)
    assert r.status_code == 200
    r = httpx.get(f"{BACKEND}/api/equipment-inspections/{eid}", headers=hdrs, timeout=15)
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════
# 7. QA / QC
# ═════════════════════════════════════════════════════════════════
def test_qaqc_inspection_full_e2e(hdrs: dict) -> None:
    pname = _project_name("qaqc")
    payload = {
        "inspection_kind": "concrete_form",
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert Yard",
        "inspection_date": _today(),
        "inspection_time": "09:00",
        "inspector_name": f"{TEST_PREFIX}Inspector",
        "work_area": "Pad 1",
        "checklist": [
            {"key": "form_alignment", "label": "Form Alignment", "result": "pass", "note": "cert"},
        ],
        "pass_count": 1, "fail_count": 0, "na_count": 0,
    }
    r = httpx.post(f"{BACKEND}/api/qaqc-inspections", headers=hdrs, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    qid = r.json()["id"]

    r = httpx.get(f"{BACKEND}/api/qaqc-inspections/{qid}", headers=hdrs, timeout=15)
    assert r.status_code == 200

    r = httpx.get(f"{BACKEND}/api/qaqc-inspections", headers=hdrs, timeout=30)
    assert r.status_code == 200
    assert qid in [x["id"] for x in r.json()]

    # Admin CSV export
    r = httpx.get(f"{BACKEND}/api/admin/qaqc-inspections/export.csv", headers=hdrs, timeout=60)
    assert r.status_code == 200

    r = httpx.delete(f"{BACKEND}/api/qaqc-inspections/{qid}", headers=hdrs, timeout=15)
    assert r.status_code == 200
    r = httpx.get(f"{BACKEND}/api/qaqc-inspections/{qid}", headers=hdrs, timeout=15)
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════
# 7b. JOB HAZARD PLAN — Admin upload / GET / DELETE (per-project PDF).
# ═════════════════════════════════════════════════════════════════
def test_job_hazard_plan_upload_e2e(hdrs: dict) -> None:
    """Admin uploads a per-project JHP PDF; verify GET + DELETE.

    Uses a synthetic project_number prefixed TEST_28_02 so cleanup is
    unambiguous. This validates the /api/job-hazard-plans upsert path
    (used by admin JHP uploads) + the file endpoint that serves the
    PDF back to crews.
    """
    pn = f"TEST_28_02_JHP_{int(time.time() * 1000)}"
    # Minimal valid PDF header — the backend's _validate_pdf_or_400
    # only enforces the %PDF- magic bytes.
    pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
    import base64 as _b64
    file_data = "data:application/pdf;base64," + _b64.b64encode(pdf_bytes).decode()
    payload = {
        "project_number": pn,
        "project_name": f"{TEST_PREFIX}JHP_Project",
        "location": "TEST · Cert Yard",
        "filename": f"{pn}.pdf",
        "content_type": "application/pdf",
        "file_data": file_data,
        "uploaded_by": "TEST_28_02_Admin",
    }
    r = httpx.post(f"{BACKEND}/api/job-hazard-plans", headers=hdrs, json=payload, timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert body.get("project_number") == pn
    assert body.get("file_size", 0) > 0

    # File endpoint returns application/pdf
    r = httpx.get(f"{BACKEND}/api/job-hazard-plans/{pn}/file", headers=hdrs, timeout=30)
    assert r.status_code == 200
    assert "application/pdf" in r.headers.get("content-type", ""), r.headers

    # List includes the record
    r = httpx.get(f"{BACKEND}/api/job-hazard-plans", headers=hdrs, timeout=30)
    assert r.status_code == 200
    pns = [x.get("project_number") for x in r.json()]
    assert pn in pns

    # DELETE
    r = httpx.delete(f"{BACKEND}/api/job-hazard-plans/{pn}", headers=hdrs, timeout=30)
    assert r.status_code == 200
    r = httpx.get(f"{BACKEND}/api/job-hazard-plans/{pn}/file", headers=hdrs, timeout=30)
    assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════
# 8. FINAL SWEEP — no TEST_28_02_ residue may remain anywhere.
# ═════════════════════════════════════════════════════════════════
def test_no_test_prefix_residue_left_behind() -> None:
    """Belt-and-suspenders: after every workflow test cleans itself,
    no `TEST_28_02_` row must survive in any Field-Ops collection.
    """
    fields = {
        "daily_reports": "project_name",
        "meetings": "project_name",
        "inspections": "project_name",
        "incidents": "project_name",
        "job_hazard_plans": "project_number",
        "equipment_inspections": "project_name",
        "qaqc_inspections": "project_name",
    }
    residue = {}
    for coll, key in fields.items():
        n = _db[coll].count_documents({key: {"$regex": f"^{TEST_PREFIX}"}})
        if n:
            # Auto-purge anything left over — do not leak certification
            # artefacts into production.
            _db[coll].delete_many({key: {"$regex": f"^{TEST_PREFIX}"}})
            residue[coll] = n
    assert not residue, f"Residue purged (would have leaked): {json.dumps(residue)}"
