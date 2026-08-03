"""
test_iter140_where_used.py — Iter140 backend verification.

Covers:
  • GET /api/master-lookup/equipment/{id}/where-used   (public)
  • GET /api/master-lookup/employees/{id}/where-used   (public)
  • GET /api/admin/search?q=... with master-label enrichment fields
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")

# Known iter140 master IDs from review_request
EQUIPMENT_MASTER_ID = "10127b48-af7e-4a24-9fde-a3f14734d0cf"  # FBT-1476
EMPLOYEE_MASTER_ID = "57a7f6b5-db6b-422d-8b9c-18a721566518"   # Jaymn Judd

SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
                      timeout=30)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    # token may be under tokens.admin or similar — try common shapes
    tok = (data.get("tokens", {}) or {}).get("admin") \
        or data.get("admin_token") \
        or data.get("token") \
        or (data.get("portal_tokens", {}) or {}).get("admin")
    assert tok, f"No admin token in multi-login response keys={list(data.keys())}"
    return tok


# ───────── Equipment where-used ─────────
class TestEquipmentWhereUsed:
    def test_equipment_where_used_ok(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/{EQUIPMENT_MASTER_ID}/where-used",
            timeout=30)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        # Shape
        assert "master" in body and body["master"].get("id") == EQUIPMENT_MASTER_ID
        assert body["master"].get("unit_number"), "master.unit_number missing"
        assert "records" in body and isinstance(body["records"], dict)
        assert "totals" in body and isinstance(body["totals"], dict)
        assert "total" in body and isinstance(body["total"], int)
        # Has expected collection keys
        for key in ("equipment_inspections", "fire_extinguishers", "incidents", "corrective_actions"):
            assert key in body["records"], f"missing records.{key}"
        # Total should be >0 since FBT-1476 was tied to iter139 incident
        assert body["total"] >= 1, f"expected >=1 linked record, got {body['total']}"

    def test_equipment_where_used_404(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment/does-not-exist-xxxxx/where-used",
            timeout=30)
        assert r.status_code == 404


# ───────── Employee where-used ─────────
class TestEmployeeWhereUsed:
    def test_employee_where_used_ok(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/employees/{EMPLOYEE_MASTER_ID}/where-used",
            timeout=30)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert body.get("master", {}).get("id") == EMPLOYEE_MASTER_ID
        assert "records" in body and isinstance(body["records"], dict)
        assert "totals" in body
        assert "total" in body
        for key in ("incidents", "corrective_actions", "safety_training_records"):
            assert key in body["records"], f"missing records.{key}"
        assert body["total"] >= 1, f"expected >=1 linked record, got {body['total']}"

    def test_employee_where_used_404(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/employees/does-not-exist-xxxxx/where-used",
            timeout=30)
        assert r.status_code == 404


# ───────── Admin global search enrichment ─────────
class TestAdminSearchEnrichment:
    def _hdr(self, tok):
        # Try Authorization Bearer first (most common)
        return {"Authorization": f"Bearer {tok}", "X-Admin-Token": tok}

    def test_search_iter139_returns_groups(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/search",
                         params={"q": "iter139", "limit": 6},
                         headers=self._hdr(admin_token),
                         timeout=30)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert "groups" in body and isinstance(body["groups"], list)
        assert body.get("total", 0) >= 1, f"expected matches for iter139, got {body}"

    def test_search_iter139_has_linked_labels(self, admin_token):
        """Incidents tagged iter139 should expose linked_equipment_label/linked_employee_label."""
        r = requests.get(f"{BASE_URL}/api/admin/search",
                         params={"q": "iter139", "limit": 6},
                         headers=self._hdr(admin_token),
                         timeout=30)
        assert r.status_code == 200
        body = r.json()
        all_rows = [row for g in body.get("groups", []) for row in g.get("rows", [])]
        assert all_rows, "No rows at all for iter139"
        has_eq = any(r.get("linked_equipment_label") for r in all_rows)
        has_emp = any(r.get("linked_employee_label") for r in all_rows)
        assert has_eq or has_emp, (
            f"Expected at least one row with linked_equipment_label or linked_employee_label. "
            f"Rows: {[{k: v for k, v in r.items() if k in ('title','linked_equipment_label','linked_employee_label')} for r in all_rows]}"
        )

    def test_search_iter138_corrective_action_enrichment(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/search",
                         params={"q": "iter138", "limit": 6},
                         headers=self._hdr(admin_token),
                         timeout=30)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        all_rows = [row for g in body.get("groups", []) for row in g.get("rows", [])]
        # iter138-bind-test CA should appear and carry employee/equipment label
        assert all_rows, "No rows for iter138"
        any_enriched = any(r.get("linked_equipment_label") or r.get("linked_employee_label") for r in all_rows)
        assert any_enriched, f"No iter138 row had linked_*_label fields. rows={all_rows}"

    def test_search_strips_internal_master_keys(self, admin_token):
        """Internal _equipment_master_id / _employee_master_id must be popped before return."""
        r = requests.get(f"{BASE_URL}/api/admin/search",
                         params={"q": "iter139", "limit": 6},
                         headers=self._hdr(admin_token),
                         timeout=30)
        body = r.json()
        for g in body.get("groups", []):
            for row in g.get("rows", []):
                assert "_equipment_master_id" not in row, f"internal key leaked: {row}"
                assert "_employee_master_id" not in row, f"internal key leaked: {row}"
