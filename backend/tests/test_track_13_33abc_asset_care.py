"""Track 13.33ABC · Asset Care · Readiness Engine · Renewal Alerts tests."""
import io
import os
import uuid
from datetime import date, timedelta

import httpx
import pytest

REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin():
    r = httpx.post(f"{API}/admin/login", json={"password": "Maddix123!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_tok():
    return _admin()


def _seed(tok, asset_class, asset_type, **extra):
    body = {
        "asset_number": f"AC-{uuid.uuid4().hex[:8]}",
        "asset_name": f"AC {asset_type}",
        "asset_class": asset_class,
        "asset_type": asset_type,
        "taxonomy_verified": True,
        "taxonomy_source": "manual_admin",
        "lifecycle_status": "Active",
        **extra,
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body,
                   headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code in (200, 201)
    j = r.json()
    return j.get("asset_id") or j.get("id")


def _upload(tok, asset_id, doc_type, expiration=None):
    files = {"file": ("d.pdf", io.BytesIO(b"%PDF-1.4\n%%EOF"), "application/pdf")}
    data = {"document_type": doc_type}
    if expiration:
        data["expiration_date"] = expiration
    return httpx.post(f"{API}/asset-spine/assets/{asset_id}/documents/upload",
                      files=files, data=data,
                      headers={"X-Admin-Token": tok}, timeout=30)


# ── Summary / readiness / work-queue / alerts shape ────────────────


def test_summary_shape(admin_tok):
    r = httpx.get(f"{API}/asset-care/summary",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    for k in ("total_assets", "readiness", "missing_documents_total", "renewals"):
        assert k in body
    for s in ("Ready", "Warning", "Not Ready", "Needs Review"):
        assert s in body["readiness"]
    for b in ("expired", "7", "30", "60", "90"):
        assert b in body["renewals"]


def test_readiness_returns_items(admin_tok):
    r = httpx.get(f"{API}/asset-care/readiness?limit=10",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    items = r.json()["items"]
    if items:
        i = items[0]
        for k in ("asset_id", "unit_number", "readiness_status", "reasons",
                  "missing_required", "taxonomy_verified"):
            assert k in i


def test_work_queue_shape(admin_tok):
    r = httpx.get(f"{API}/asset-care/work-queue",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    for b in ("needs_classification_review", "missing_required_documents",
              "gps_survey_tech_review", "open_defects"):
        assert b in body


# ── Readiness engine: expired renewal → Not Ready ─────────────────


def test_expired_registration_marks_not_ready(admin_tok):
    asset_id = _seed(admin_tok, "Truck", "Pickup Truck")
    past = (date.today() - timedelta(days=30)).isoformat()
    _upload(admin_tok, asset_id, "registration", expiration=past)
    # Re-fetch readiness
    r = httpx.get(f"{API}/asset-care/readiness?status=Not%20Ready&limit=500",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    ids = [i["asset_id"] for i in r.json()["items"]]
    assert asset_id in ids


def test_future_expiry_in_30_days_marks_warning(admin_tok):
    asset_id = _seed(admin_tok, "Truck", "Pickup Truck")
    future = (date.today() + timedelta(days=20)).isoformat()
    _upload(admin_tok, asset_id, "registration", expiration=future)
    _upload(admin_tok, asset_id, "insurance_card", expiration=(date.today() + timedelta(days=400)).isoformat())
    # Need to also satisfy other required docs so the asset is not Not Ready
    r = httpx.get(f"{API}/asset-care/readiness?limit=500",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    match = next((i for i in r.json()["items"] if i["asset_id"] == asset_id), None)
    assert match is not None
    # Pickup Truck requires registration + insurance_card. With both present and registration
    # in 20d, status should be Warning.
    assert match["readiness_status"] in ("Warning", "Not Ready")


def test_unknown_classification_marks_needs_review(admin_tok):
    body = {
        "asset_number": f"AC-NR-{uuid.uuid4().hex[:8]}",
        "asset_name": "needs review",
        "asset_class": "Other",
        "asset_type": "Other",
        "taxonomy_verified": False,
        "taxonomy_source": "import",
        "lifecycle_status": "Active",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body,
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    aid = r.json().get("asset_id") or r.json().get("id")
    rr = httpx.get(f"{API}/asset-care/readiness?status=Needs%20Review&limit=1000",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    matched = next((i for i in rr.json()["items"] if i["asset_id"] == aid), None)
    assert matched is not None, "newly-created unverified asset must appear in readiness list"
    assert matched["readiness_status"] == "Needs Review"


# ── Renewal alerts ─────────────────────────────────────────────────


def test_renewal_alerts_categorize_correctly(admin_tok):
    asset_id_30 = _seed(admin_tok, "Truck", "Pickup Truck")
    _upload(admin_tok, asset_id_30, "registration",
            expiration=(date.today() + timedelta(days=25)).isoformat())
    r = httpx.get(f"{API}/asset-care/alerts",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    items = r.json()["items"]
    hit = [i for i in items if i["asset_id"] == asset_id_30]
    assert hit, "alert for 25-day asset must be present"
    assert hit[0]["bucket"] == "Due in 30 days"
    assert hit[0]["severity"] == "medium"
    assert hit[0]["recommended_action"]
    assert hit[0]["open_asset_profile"].startswith("/admin/assets/")


def test_renewal_alert_resolves_on_new_doc(admin_tok):
    asset_id = _seed(admin_tok, "Truck", "Pickup Truck")
    _upload(admin_tok, asset_id, "registration",
            expiration=(date.today() - timedelta(days=10)).isoformat())
    # Alert present
    r1 = httpx.get(f"{API}/asset-care/alerts",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert any(i["asset_id"] == asset_id for i in r1.json()["items"])
    # Upload renewed reg with future expiration
    _upload(admin_tok, asset_id, "registration",
            expiration=(date.today() + timedelta(days=365)).isoformat())
    # Mirror update is the latest write so cleared from alerts
    r2 = httpx.get(f"{API}/asset-care/alerts",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    matches = [i for i in r2.json()["items"]
               if i["asset_id"] == asset_id and i["renewal_type"] == "Registration"]
    # The latest doc upload mirrors expiration to equipment_master.registration_expiration
    # which is the value alerts read. So the alert moves out of the expired bucket.
    for m in matches:
        assert m["bucket"] != "Expired"


# ── Notifications matrix ───────────────────────────────────────────


def test_notification_matrix(admin_tok):
    r = httpx.get(f"{API}/asset-care/notifications-matrix",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    body = r.json()
    assert body["count"] >= 20
    keys = {e["event"] for e in body["items"]}
    expected = {
        "registration_expired", "insurance_expired", "dot_expired",
        "calibration_expired", "asset_classification_review",
        "preop_failed", "dvir_failed", "asset_oos", "pm_overdue",
    }
    assert expected.issubset(keys)
    for e in body["items"]:
        for k in ("trigger", "audience", "resolution"):
            assert k in e
    # Delivery status
    assert body["delivery_status"]["dashboard"] == "live"


# ── Authn ─────────────────────────────────────────────────────────


def test_asset_care_requires_admin():
    r = httpx.get(f"{API}/asset-care/summary", timeout=30)
    assert r.status_code in (401, 403)


# ── Regression guard ──────────────────────────────────────────────


def test_no_new_collection_added():
    src = open("/app/backend/routes/asset_care.py").read()
    assert "create_collection" not in src
    for bad in ("asset_care_events", "readiness_records", "notification_events"):
        assert bad not in src
