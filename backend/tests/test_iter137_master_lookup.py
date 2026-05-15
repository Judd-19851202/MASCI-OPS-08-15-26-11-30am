"""Iter137 — Master Lookup SOT + Iter B-continued empty/loading states.

Tests cover the master_lookup.py router endpoints:
  - GET /api/master-lookup/equipment (typeahead)
  - GET /api/master-lookup/employees (typeahead)
  - GET /api/master-lookup/audit (admin gated)
  - POST /api/master-lookup/backfill/equipment (admin, dry/real)
  - POST /api/master-lookup/backfill/employees (admin)
Plus regression: training-center portals total=18, deploy-readiness ready.
"""
from pathlib import Path

import requests


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_PW = _read_kv(Path("/app/backend/.env"), "ADMIN_PASSWORD")


# ── Typeahead: equipment ──────────────────────────────────────────
class TestEquipmentTypeahead:
    def test_equipment_typeahead_returns_results(self):
        r = requests.get(f"{BASE_URL}/api/master-lookup/equipment", params={"q": "T-1"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "items" in body
        assert isinstance(body["items"], list)
        # at least 1 T-prefix result expected (per problem statement)
        assert len(body["items"]) >= 1, f"Expected >=1 T-1 match, got {body}"
        first = body["items"][0]
        assert "id" in first and first["id"]
        assert "unit_number" in first
        # make_model is part of the projection; may be empty string but key should exist or be optional
        # (do not strictly require value, but key tolerance ok)

    def test_equipment_empty_query_returns_empty(self):
        r = requests.get(f"{BASE_URL}/api/master-lookup/equipment", params={"q": ""})
        assert r.status_code == 200
        assert r.json().get("items") == []

    def test_equipment_empty_query_with_limit_returns_empty(self):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment",
            params={"q": "", "limit": 1},
        )
        assert r.status_code == 200
        assert r.json().get("items") == []

    def test_equipment_typeahead_no_auth_required(self):
        # Bare request with no admin token
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/equipment",
            params={"q": "T"},
            headers={"X-Admin-Token": ""},
        )
        assert r.status_code == 200


# ── Typeahead: employees ──────────────────────────────────────────
class TestEmployeeTypeahead:
    def test_employee_typeahead_returns_results(self):
        r = requests.get(f"{BASE_URL}/api/master-lookup/employees", params={"q": "jay"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body.get("items"), list)
        assert len(body["items"]) >= 1, f"Expected >=1 'jay' match, got count={len(body['items'])}"
        # Schema tolerance: each item must have id + at least one name field
        for it in body["items"]:
            assert "id" in it and it["id"]
            has_name = bool(
                it.get("name")
                or it.get("first_name")
                or it.get("last_name")
                or it.get("display_name")
            )
            assert has_name, f"Item missing any name field: {it}"

    def test_employee_empty_query_returns_empty(self):
        r = requests.get(f"{BASE_URL}/api/master-lookup/employees", params={"q": ""})
        assert r.status_code == 200
        assert r.json().get("items") == []


# ── Admin gating: /audit ──────────────────────────────────────────
class TestAuditGating:
    def test_audit_requires_admin_token(self):
        # No admin header — must 401
        s = requests.Session()
        r = s.get(
            f"{BASE_URL}/api/master-lookup/audit",
            headers={"X-Admin-Token": "invalid-token-xyz"},
        )
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}: {r.text}"

    def test_audit_with_admin_returns_shape(self):
        # conftest auto-attaches admin token; use requests.get directly
        r = requests.get(f"{BASE_URL}/api/master-lookup/audit")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "equipment_master_total" in body
        assert "employees_total" in body
        assert isinstance(body.get("equipment_coverage"), dict)
        assert isinstance(body.get("employee_coverage"), dict)
        # Per agent context: coverage exists for equipment_inspections + training records
        assert "equipment_inspections" in body["equipment_coverage"]
        assert "safety_training_records" in body["employee_coverage"]


# ── Backfill: equipment dry vs real, idempotent ───────────────────
class TestBackfillEquipment:
    def test_backfill_equipment_dry_run_no_mutation(self):
        # Snapshot pre-coverage
        pre = requests.get(f"{BASE_URL}/api/master-lookup/audit").json()
        pre_cov = pre["equipment_coverage"]
        # Dry run
        r = requests.post(
            f"{BASE_URL}/api/master-lookup/backfill/equipment",
            params={"dry_run": "true"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["dry_run"] is True
        assert "report" in body
        # Coverage should NOT have changed
        post = requests.get(f"{BASE_URL}/api/master-lookup/audit").json()
        assert post["equipment_coverage"] == pre_cov, (
            f"Dry run mutated DB! pre={pre_cov} post={post['equipment_coverage']}"
        )

    def test_backfill_equipment_real_run_idempotent(self):
        # Real run #1
        r1 = requests.post(
            f"{BASE_URL}/api/master-lookup/backfill/equipment",
            params={"dry_run": "false"},
        )
        assert r1.status_code == 200, r1.text
        body1 = r1.json()
        assert body1["dry_run"] is False
        # Real run #2 — should attach 0 NEW (idempotent)
        r2 = requests.post(
            f"{BASE_URL}/api/master-lookup/backfill/equipment",
            params={"dry_run": "false"},
        )
        assert r2.status_code == 200
        body2 = r2.json()
        # Sum attached across collections on 2nd run must be 0
        total_attached_run2 = sum(v.get("attached", 0) for v in body2["report"].values())
        assert total_attached_run2 == 0, (
            f"Backfill not idempotent: 2nd-run attached={total_attached_run2}, report={body2['report']}"
        )


# ── Backfill: employees ───────────────────────────────────────────
class TestBackfillEmployees:
    def test_backfill_employees_real_run(self):
        r = requests.post(
            f"{BASE_URL}/api/master-lookup/backfill/employees",
            params={"dry_run": "false"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["dry_run"] is False
        assert "report" in body
        # Targets per the route definition
        for coll in ("incidents", "corrective_actions", "safety_training_records"):
            assert coll in body["report"]
            assert "attached" in body["report"][coll]
            assert "unresolved" in body["report"][coll]


# ── Regression — training-center 18 guides + deploy-readiness ─────
class TestRegression:
    def test_training_center_portals_total_18(self):
        r = requests.get(f"{BASE_URL}/api/training-center/portals")
        assert r.status_code == 200, r.text
        body = r.json()
        # Per iteration_136: 18 guides total — endpoint returns portals[] with per-portal counts
        total = body.get("total") or sum(p.get("count", 0) for p in body.get("portals", []))
        assert total == 18, f"Expected total=18, got {total} from portals {body.get('portals')}"

    def test_deploy_readiness_overall_ready(self):
        r = requests.get(f"{BASE_URL}/api/admin/deploy-readiness")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("overall_status") == "ready", body

    def test_safety_corrective_actions_list_ok(self):
        # Listing endpoint (no /list path; the resource root list)
        r = requests.get(f"{BASE_URL}/api/safety/corrective-actions")
        # Safety endpoint may require safety token; accept either 200 (admin satisfies) or 401
        assert r.status_code in (200, 401), r.text

    def test_safety_fire_extinguishers_list_ok(self):
        r = requests.get(f"{BASE_URL}/api/safety/fire-extinguishers")
        assert r.status_code in (200, 401), r.text
