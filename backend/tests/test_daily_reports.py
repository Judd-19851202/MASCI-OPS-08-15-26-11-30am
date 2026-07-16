"""Daily Job Report endpoint tests for /api/daily-reports CRUD + validation + regression.

Track 20.6B · TD-20.7-C01 hardening
────────────────────────────────────
- Auth: uses the current canonical `POST /api/auth/multi-login` endpoint
  (the pre-15.32 shared-password admin login is retired).
- Email safety: relies on the Track 20.6B `_dispatch_auto_email` gate
  which short-circuits when ``project_name.startswith("TEST_")``. Every
  synthetic record created here uses that prefix, so no live email fires
  even in the preview environment with `AUTO_EMAIL_REPORTS=true`.
"""
import os
import pytest
import requests

BASE_URL = "http://127.0.0.1:8001"
API = f"{BASE_URL}/api"

SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASS = "Maddix123!"


@pytest.fixture(scope="module")
def admin_headers():
    """Track 20.6B · TD-20.7-C01 hardening — use the canonical multi-login
    endpoint (replaces the retired shared-password admin login from
    Track 15.32). Returns X-Admin-Token · X-HR-Token · X-Safety-Token
    together so every downstream gate resolves — the `require_admin`
    gate accepts directory admin tokens, `require_admin_pm_or_hr_read`
    resolves via HR, and `require_safety_or_admin` (used by inspection
    / meeting / jha / incident LIST endpoints) resolves via Safety."""
    r = requests.post(
        f"{API}/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASS},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login unavailable: {r.status_code} {r.text[:200]}")
    tokens = (r.json() or {}).get("portal_tokens") or {}
    missing = [k for k in ("admin", "hr", "safety") if not tokens.get(k)]
    if missing:
        pytest.skip(f"multi-login response missing portal tokens: {missing}")
    return {
        "X-Admin-Token": tokens["admin"],
        "X-HR-Token": tokens["hr"],
        "X-Safety-Token": tokens["safety"],
    }


def _full_payload(prefix="TEST_DR"):
    gps_lat = 29.1383
    gps_lng = -80.9956
    return {
        "project_name": f"{prefix}_Project A1A",
        "project_number": "TEST-25-23",
        "location": "Port Orange, FL",
        "location_source": "manual",
        "gps_lat": gps_lat,
        "gps_lng": gps_lng,
        "report_date": "2026-01-15",
        "report_number": "DR-001",
        "prepared_by": "Test Foreman",
        "superintendent": "Test Super",
        "weather_summary": "75°F / Sunny",
        "weather_snapshot_meta": {
            "provider": "open-meteo",
            "gps_lat": gps_lat,
            "gps_lng": gps_lng,
            "observation_timestamp": "2026-01-15T12:00:00Z",
            "location_source": "manual",
            "weather_coordinates_match_report": True,
        },
        "weather_snapshots": [
            {"time": "06:00", "condition": "Clear", "temp_f": 65, "precip_in": 0, "humidity_pct": 70, "wind_mph": 4},
            {"time": "12:00", "condition": "Sunny", "temp_f": 80, "precip_in": 0, "humidity_pct": 55, "wind_mph": 8},
            {"time": "18:00", "condition": "Sunny", "temp_f": 78, "precip_in": 0, "humidity_pct": 60, "wind_mph": 6},
        ],
        "schedule_delays": "No",
        "weather_impact": "No",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "incident_notes": "",
        "general_notes": "Smooth day.",
        "masci_crews": [
            {"trade": "Earthwork", "foreman": "Joe", "count": "5", "hours": "8", "work_performed": "Grading"},
            {"trade": "Concrete", "foreman": "Mike", "count": "3", "hours": "8", "work_performed": "Pour curb"},
        ],
        "subcontractors": [
            {"company": "ABC Striping", "trade": "Striping", "foreman": "L. Lopez", "count": "2", "hours": "6", "work_performed": "Lane lines"},
        ],
        "visitors": [
            {"name": "Bob Inspector", "company": "FDOT", "time_in": "10:00", "time_out": "11:30", "purpose": "QA visit"},
        ],
        "equipment": [
            {"description": "CAT 320 Excavator", "hours_used": "6", "time_delivered": "07:00", "time_removed": "", "notes": ""},
        ],
        "materials": [
            {"description": "Crushed Aggregate", "quantity": "40", "unit": "ton", "supplier": "Vulcan", "ticket_number": "T-9911", "notes": ""},
        ],
        "activities": [
            {"activity": "Curb pour", "percent_complete": "60", "station_from": "10+00", "station_to": "12+00", "notes": ""},
        ],
        "photos": [f"data:image/png;base64,FAKE{i}" for i in range(6)],
        "prepared_by_signature": "data:image/png;base64,SIGFAKE",
        "superintendent_signature": "",
        "ai_accepted_summary": "Accepted executive summary: test daily report ready for submission.",
        "ai_accepted_summary_meta": {"source": "ai", "approved_by": "Test Foreman", "accepted_at": "2026-01-15T19:00:00Z"},
    }


@pytest.fixture(scope="module")
def created_id(admin_headers):
    payload = _full_payload()
    r = requests.post(f"{API}/daily-reports", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    rid = body["id"]
    yield rid, body
    # cleanup: DR delete is frozen at 410 (historical-immutable). We POST
    # the cleanup attempt for parity with the historical contract; the
    # 410 is expected and does not affect subsequent tests. No email
    # fires because project_name starts with "TEST_" (Track 20.6B gate).
    requests.delete(f"{API}/daily-reports/{rid}", timeout=30)


# --- CRUD ---
class TestDailyReportCRUD:
    def test_create_returns_full_doc_and_no_id_leak(self, created_id):
        rid, body = created_id
        assert isinstance(body["id"], str) and len(body["id"]) > 0
        assert "_id" not in body
        assert body["project_name"].startswith("TEST_DR")
        assert body["report_date"] == "2026-01-15"
        assert body["prepared_by"] == "Test Foreman"
        assert len(body["masci_crews"]) == 2
        assert len(body["subcontractors"]) == 1
        assert len(body["visitors"]) == 1
        assert len(body["equipment"]) == 1
        assert len(body["materials"]) == 1
        assert len(body["activities"]) == 1
        assert len(body["photos"]) == 6
        assert len(body["weather_snapshots"]) == 3
        assert "created_at" in body

    def test_list_summary_no_id_and_counts(self, created_id, admin_headers):
        rid, created = created_id
        r = requests.get(f"{API}/daily-reports", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        items = r.json()
        match = [x for x in items if x["id"] == rid]
        assert len(match) == 0, "Synthetic TEST_ daily reports should be excluded from the list endpoint"
        assert created["project_name"].startswith("TEST_DR")
        assert created["project_number"] == "TEST-25-23"
        assert created["weather_snapshot_meta"]["gps_lat"] == 29.1383
        assert created["weather_snapshot_meta"]["gps_lng"] == -80.9956

    def test_get_full_doc_preserves_nested_arrays(self, created_id, admin_headers):
        rid, _ = created_id
        r = requests.get(f"{API}/daily-reports/{rid}", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert "_id" not in body
        assert body["id"] == rid
        assert body["masci_crews"][0]["trade"] == "Earthwork"
        assert body["masci_crews"][1]["foreman"] == "Mike"
        assert body["subcontractors"][0]["company"] == "ABC Striping"
        assert body["visitors"][0]["name"] == "Bob Inspector"
        assert body["equipment"][0]["description"] == "CAT 320 Excavator"
        assert body["materials"][0]["ticket_number"] == "T-9911"
        assert body["activities"][0]["activity"] == "Curb pour"
        assert body["weather_snapshots"][1]["temp_f"] == 80
        assert body["prepared_by_signature"].startswith("data:image/png")

    def test_get_404_for_unknown(self, admin_headers):
        r = requests.get(f"{API}/daily-reports/does-not-exist", headers=admin_headers, timeout=30)
        assert r.status_code == 404

    def test_delete_and_verify_removed(self, admin_headers):
        # DEPLOY-FIX-001 · Workstream C3 — DR delete is permanently frozen
        # at HTTP 410 Gone. Daily Reports are historical-immutable records
        # (see /app/backend/routes/daily_reports.py:580). Hard delete is
        # no longer permitted; records remain accessible via GET. The test
        # name "delete_and_verify_removed" is retained for backwards-grep,
        # but the contract it locks in is now "delete-is-gone, record-stays."
        payload = _full_payload(prefix="TEST_DR_DEL")
        r = requests.post(f"{API}/daily-reports", json=payload, timeout=30)
        assert r.status_code == 200
        rid = r.json()["id"]
        d = requests.delete(f"{API}/daily-reports/{rid}", headers=admin_headers, timeout=30)
        assert d.status_code == 410, (
            f"DR delete must return 410 Gone (historical-immutable doctrine); got {d.status_code}"
        )
        # Record must STILL be present — deletion is forbidden.
        g = requests.get(f"{API}/daily-reports/{rid}", headers=admin_headers, timeout=30)
        assert g.status_code == 200, (
            f"DR record must persist after DELETE attempt; got {g.status_code}"
        )

    def test_delete_404_for_unknown(self, admin_headers):
        # DEPLOY-FIX-001 · Workstream C3 — even for unknown ids the
        # endpoint returns 410 (the operation itself is gone, not the
        # record). 404 is no longer reachable.
        r = requests.delete(f"{API}/daily-reports/nope-{os.urandom(4).hex()}",
                            headers=admin_headers, timeout=30)
        assert r.status_code == 410, (
            f"DR delete must return 410 Gone for any id; got {r.status_code}"
        )


# --- Validation ---
class TestDailyReportValidation:
    @pytest.mark.parametrize("missing", ["project_name", "location", "prepared_by", "report_date"])
    def test_missing_required_returns_422(self, missing):
        payload = _full_payload(prefix="TEST_DR_VAL")
        payload.pop(missing, None)
        r = requests.post(f"{API}/daily-reports", json=payload, timeout=30)
        assert r.status_code == 422, f"Expected 422 when {missing} missing, got {r.status_code}: {r.text}"


# --- Regression on other modules ---
class TestRegressionOtherModules:
    def test_inspections_get_works(self, admin_headers):
        r = requests.get(f"{API}/inspections", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_meetings_get_works(self, admin_headers):
        r = requests.get(f"{API}/meetings", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_jhas_get_works(self, admin_headers):
        r = requests.get(f"{API}/jhas", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_incidents_get_works(self, admin_headers):
        r = requests.get(f"{API}/incidents", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_inspection_post_minimal(self, admin_headers):
        # existing regression; quick smoke. Uses TEST_ prefix so the
        # Track 20.6B auto-email gate short-circuits the send.
        payload = {
            "project_name": "TEST_DR_REG_INSP",
            "location": "Port Orange",
            "inspection_date": "2026-01-15",
            "inspection_time": "10:00",
            "inspector_name": "Insp",
            "foreman_name": "Fore",
            "work_activity": "General",
        }
        r = requests.post(f"{API}/inspections", json=payload, headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        # cleanup
        requests.delete(f"{API}/inspections/{rid}", headers=admin_headers, timeout=30)
