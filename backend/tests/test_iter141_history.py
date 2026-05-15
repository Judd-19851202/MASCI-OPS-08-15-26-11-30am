"""
test_iter141_history.py — Iter141 Asset/Employee History Timeline.

Covers:
  • GET /api/master-lookup/equipment/{id}/history       (JSON)
  • GET /api/master-lookup/employees/{id}/history       (JSON)
  • GET /api/master-lookup/equipment/{id}/history.csv   (CSV)
  • GET /api/master-lookup/employees/{id}/history.csv   (CSV)
  • GET /api/master-lookup/equipment/{id}/history.pdf   (PDF)
  • GET /api/master-lookup/employees/{id}/history.pdf   (PDF)
  • 404 on bogus master id
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

EQUIPMENT_MASTER_ID = "10127b48-af7e-4a24-9fde-a3f14734d0cf"  # FBT-1476
EMPLOYEE_MASTER_ID = "57a7f6b5-db6b-422d-8b9c-18a721566518"   # Jaymn Judd


# ───────── Equipment JSON ─────────
class TestEquipmentHistoryJSON:
    def test_equipment_history_shape(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/{EQUIPMENT_MASTER_ID}/history",
            timeout=30)
        assert r.status_code == 200, r.text[:300]
        b = r.json()
        for k in ("master", "events", "total", "summary", "generated_at"):
            assert k in b, f"missing {k}"
        assert b["master"].get("id") == EQUIPMENT_MASTER_ID
        assert isinstance(b["events"], list)
        assert isinstance(b["total"], int) and b["total"] == len(b["events"])
        assert isinstance(b["summary"], dict)

    def test_equipment_history_has_expected_kinds(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/{EQUIPMENT_MASTER_ID}/history",
            timeout=30)
        b = r.json()
        kinds = {e["kind"] for e in b["events"]}
        # Spec says at least 1 fire_ext_inspection, 1 ca, 1 incident
        assert "fire_ext_inspection" in kinds, f"no fire_ext_inspection in kinds={kinds}"
        assert "ca" in kinds, f"no ca in kinds={kinds}"
        assert "incident" in kinds, f"no incident in kinds={kinds}"
        assert b["total"] >= 3

    def test_equipment_history_sorted_newest_first(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/{EQUIPMENT_MASTER_ID}/history",
            timeout=30)
        events = r.json()["events"]
        ats = [e.get("at", "") for e in events]
        assert ats == sorted(ats, reverse=True), "events not newest-first"

    def test_equipment_history_event_shape(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/{EQUIPMENT_MASTER_ID}/history",
            timeout=30)
        events = r.json()["events"]
        assert events, "no events"
        e = events[0]
        for k in ("at", "kind", "title", "subtitle", "route", "record_id"):
            assert k in e, f"event missing key {k}: {e}"

    def test_equipment_history_404(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/does-not-exist/history",
            timeout=30)
        assert r.status_code == 404


# ───────── Employee JSON ─────────
class TestEmployeeHistoryJSON:
    def test_employee_history_shape(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/employees/{EMPLOYEE_MASTER_ID}/history",
            timeout=30)
        assert r.status_code == 200, r.text[:300]
        b = r.json()
        for k in ("master", "events", "total", "summary", "generated_at"):
            assert k in b
        assert b["master"].get("id") == EMPLOYEE_MASTER_ID

    def test_employee_history_has_incident_and_ca(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/employees/{EMPLOYEE_MASTER_ID}/history",
            timeout=30)
        b = r.json()
        kinds = {e["kind"] for e in b["events"]}
        assert "incident" in kinds, f"no incident in kinds={kinds}"
        assert "ca" in kinds, f"no ca in kinds={kinds}"
        assert b["total"] >= 2

    def test_employee_history_404(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/employees/does-not-exist/history",
            timeout=30)
        assert r.status_code == 404


# ───────── CSV ─────────
class TestHistoryCSV:
    def test_equipment_history_csv(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/{EQUIPMENT_MASTER_ID}/history.csv",
            timeout=30)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        body = r.text
        # Brand header rows
        assert "MASCI Operations Platform" in body
        # Column header row
        for col in ("Date", "Kind", "Title", "Subtitle", "Status", "Severity", "Record ID"):
            assert col in body, f"CSV missing column {col}"

    def test_employee_history_csv(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/employees/{EMPLOYEE_MASTER_ID}/history.csv",
            timeout=30)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        body = r.text
        assert "MASCI Operations Platform" in body
        for col in ("Date", "Kind", "Title"):
            assert col in body


# ───────── PDF ─────────
class TestHistoryPDF:
    def test_equipment_history_pdf(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/{EQUIPMENT_MASTER_ID}/history.pdf",
            timeout=60)
        assert r.status_code == 200, r.text[:300]
        assert "application/pdf" in r.headers.get("content-type", "")
        assert r.content[:5] == b"%PDF-", f"not a PDF, first bytes={r.content[:10]!r}"
        assert len(r.content) > 1000

    def test_employee_history_pdf(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/employees/{EMPLOYEE_MASTER_ID}/history.pdf",
            timeout=60)
        assert r.status_code == 200, r.text[:300]
        assert "application/pdf" in r.headers.get("content-type", "")
        assert r.content[:5] == b"%PDF-"
        assert len(r.content) > 1000
