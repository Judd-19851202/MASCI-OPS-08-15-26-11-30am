"""ODS-001 + AI Gateway independent e2e verification.

Runs against REACT_APP_BACKEND_URL (preview URL). No auth in preview.
Covers the 12 review items from the ODS-001 review request.
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
PROJECT_NUMBER = "OD-100"
REPORT_DATE = "2026-07-05"


@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Meta ------------------------------------------------------
class TestOdsMeta:
    def test_meta_shape(self, api):
        r = api.get(f"{BASE_URL}/api/ods/meta", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["enabled"] is True
        assert d["dr_v2_emission"] is True
        assert len(d["fact_types"]) == 11
        assert len(d["source_types"]) == 10
        g = d["ai_gateway"]
        assert set(g["registered_providers"]) == {"anthropic", "openai", "google"}
        assert len(g["task_routes"]) == 11
        # Env snapshot must never leak actual keys — only booleans
        pwk = g["env"]["providers_with_keys"]
        assert isinstance(pwk, dict)
        for k, v in pwk.items():
            assert isinstance(v, bool), f"providers_with_keys[{k}] is not bool: {v!r}"
        # Default routes match spec
        assert g["task_routes"]["operational_narrative"]["provider"] == "anthropic"
        assert g["task_routes"]["operational_narrative"]["model"] == "claude-sonnet-4-5-20250929"
        assert g["task_routes"]["photo_vision"]["provider"] == "openai"
        assert g["task_routes"]["photo_vision"]["model"] == "gpt-5.2-vision"


# ---------- DR-V2 draft → spine emission -----------------------------
DRAFT_TEMPLATE: Dict[str, Any] = {
    "day_setup": {
        "project_number": PROJECT_NUMBER,
        "report_date": REPORT_DATE,
        "supervisor_name": "TEST_Supervisor",
        "supervisor_email": "test_supervisor@example.com",
    },
    "masci_crews": [
        {
            "crew_id": "TEST_C1",
            "crew_name": "Test Crew A",
            "foreman": "F1",
            "members": [{"name": "W1"}, {"name": "W2"}, {"name": "W3"}],
            "hours": 8.0,
            "cost_code": "Trench",
        },
    ],
    "equipment_used": [
        {"equipment_id": "TEST_EQ1", "description": "Excavator", "hours": 6.5, "cost_code": "Trench"},
    ],
    "activity_cards": [
        {"cost_code": "Trench", "description": "trenching", "quantity": 120.0, "unit": "LF"},
    ],
    "constraint_cards": [
        {"category": "missing_material", "description": "waiting on pipe", "duration_hours": 2.0},
    ],
    "weather": {"conditions": "clear", "temp_high": 82, "temp_low": 60},
}


class TestSpineEmission:
    def test_draft_triggers_emission_within_5s(self, api):
        # Capture baseline
        r0 = api.get(f"{BASE_URL}/api/ods/facts?project_id={PROJECT_NUMBER}", timeout=30)
        assert r0.status_code == 200
        baseline_count = r0.json().get("count", 0)

        payload = {
            "report_id": f"drv2-test-{uuid.uuid4().hex[:12]}",
            **DRAFT_TEMPLATE,
        }
        r = api.post(f"{BASE_URL}/api/dr-v2/drafts", json=payload, timeout=30)
        assert r.status_code in (200, 201), f"draft save failed: {r.status_code} {r.text[:400]}"

        # Poll ODS facts for up to 6s
        deadline = time.time() + 6.0
        current = 0
        while time.time() < deadline:
            rr = api.get(f"{BASE_URL}/api/ods/facts?project_id={PROJECT_NUMBER}", timeout=30)
            current = rr.json().get("count", 0)
            if current >= max(baseline_count, 6):
                break
            time.sleep(0.5)
        assert current >= 6, f"expected >=6 facts, got {current}"

        # Verify fact_type coverage
        rr = api.get(f"{BASE_URL}/api/ods/facts?project_id={PROJECT_NUMBER}", timeout=30)
        facts = rr.json().get("facts", [])
        types = {f.get("fact_type") for f in facts}
        for t in ("labor_fact", "equipment_fact", "production_fact", "delay_fact", "weather_fact"):
            assert t in types, f"missing fact_type: {t}. saw={types}"


# ---------- Idempotency ----------------------------------------------
class TestIdempotency:
    def test_manual_reingest_idempotent(self, api):
        # find an existing report_id via facts (source_run_id often == report_id)
        rr = api.get(f"{BASE_URL}/api/ods/facts?project_id={PROJECT_NUMBER}&limit=200", timeout=30)
        facts = rr.json().get("facts", [])
        assert facts, "no facts present to reingest"
        report_id = None
        for f in facts:
            rid = f.get("source_run_id") or f.get("report_id") or f.get("source_ref")
            if isinstance(rid, str) and rid.startswith("drv2"):
                report_id = rid
                break
        if not report_id:
            # fallback known-good report from task context
            report_id = "drv2-b9f643a26802"

        # First reingest — establishes a supersedes baseline for the draft's project
        r1 = api.post(f"{BASE_URL}/api/ods/ingest/dr-v2/{report_id}", timeout=45)
        assert r1.status_code == 200, f"ingest#1 failed: {r1.status_code} {r1.text[:400]}"
        d1 = r1.json()
        pid_of_report = d1.get("project_id") or PROJECT_NUMBER

        r_pre = api.get(f"{BASE_URL}/api/ods/facts?project_id={pid_of_report}&limit=500", timeout=30)
        pre_count = r_pre.json().get("count", 0)

        # Second reingest — should be idempotent (inserted == superseded == same count)
        r2 = api.post(f"{BASE_URL}/api/ods/ingest/dr-v2/{report_id}", timeout=45)
        assert r2.status_code == 200, f"ingest#2 failed: {r2.status_code} {r2.text[:400]}"
        d2 = r2.json()
        inserted = d2.get("facts_inserted") or d2.get("inserted") or 0
        superseded = d2.get("facts_superseded") or d2.get("superseded") or 0
        assert inserted == superseded, f"non-idempotent: inserted={inserted} superseded={superseded} resp={d2}"
        assert inserted > 0

        r_post = api.get(f"{BASE_URL}/api/ods/facts?project_id={pid_of_report}&limit=500", timeout=30)
        post_count = r_post.json().get("count", 0)
        assert post_count == pre_count, f"current fact count changed pre={pre_count} post={post_count}"


# ---------- Project summary aggregates -------------------------------
class TestProjectSummary:
    def test_summary_aggregates(self, api):
        r = api.get(f"{BASE_URL}/api/ods/projects/{PROJECT_NUMBER}/summary", timeout=30)
        assert r.status_code == 200
        s = r.json()["summary"]
        # Fact counts by type
        assert "fact_counts" in s and isinstance(s["fact_counts"], dict)
        assert s["fact_counts"].get("labor_fact", 0) >= 1
        # Aggregates present and > 0
        assert s["labor_hours"] > 0
        assert s["equipment_hours"] > 0
        assert s["production_total"] > 0
        assert s["delay_hours"] > 0


# ---------- Snapshot -------------------------------------------------
class TestSnapshot:
    def test_snapshot_has_aggregates_and_dicts(self, api):
        r = api.get(f"{BASE_URL}/api/ods/snapshots?project_id={PROJECT_NUMBER}&date={REPORT_DATE}", timeout=30)
        assert r.status_code == 200
        snap = r.json()["snapshot"]
        assert snap is not None
        assert snap["labor_hours"] > 0
        assert snap["equipment_hours"] > 0
        assert isinstance(snap["production_by_cost_code"], dict)
        assert isinstance(snap["delay_hours_by_category"], dict)
        assert snap["production_by_cost_code"], "empty production_by_cost_code"
        assert snap["delay_hours_by_category"], "empty delay_hours_by_category"


# ---------- Project config PUT versioning ---------------------------
class TestProjectConfig:
    def test_put_creates_and_increments_version(self, api):
        # Use isolated project id to avoid clobbering
        pid = f"TEST_CFG_{uuid.uuid4().hex[:8]}"
        body1 = {"project_id": pid, "tenant_id": "masci", "cost_codes": [
            {"code": "Trench", "description": "trenching"},
            {"code": "Backfill", "description": "backfill"},
        ]}
        r1 = api.put(f"{BASE_URL}/api/ods/projects/{pid}/config", json=body1, timeout=30)
        assert r1.status_code == 200, r1.text[:400]
        assert r1.json()["version"] == 1

        g1 = api.get(f"{BASE_URL}/api/ods/projects/{pid}/config", timeout=30).json()
        assert g1["config"]["version"] == 1
        assert len(g1["config"]["cost_codes"]) == 2

        body2 = {"project_id": pid, "tenant_id": "masci", "cost_codes": [{"code": "Trench"}]}
        r2 = api.put(f"{BASE_URL}/api/ods/projects/{pid}/config", json=body2, timeout=30)
        assert r2.status_code == 200
        assert r2.json()["version"] == 2

        g2 = api.get(f"{BASE_URL}/api/ods/projects/{pid}/config", timeout=30).json()
        assert g2["config"]["version"] == 2


# ---------- V1 zero drift -------------------------------------------
class TestV1ZeroDrift:
    def test_v1_daily_reports_get(self, api):
        r = api.get(f"{BASE_URL}/api/daily-reports", timeout=30)
        # Endpoint still exists (200 or 401 auth-gated). Any 5xx or 404 would be drift.
        assert r.status_code in (200, 401, 403), f"V1 daily-reports drift: {r.status_code}"

    def test_route_count_1455(self, api):
        # Preview route hides /openapi.json externally — fetch via localhost:8001
        try:
            r = requests.get("http://localhost:8001/openapi.json", timeout=15)
        except Exception as e:
            pytest.skip(f"internal openapi unreachable: {e}")
        assert r.status_code == 200
        spec = r.json()
        route_count = sum(
            1 for _, methods in spec.get("paths", {}).items()
            for m in methods if m.lower() in ("get", "post", "put", "delete", "patch")
        )
        # Report actual count. Review spec claims 1455 — flag any drift.
        assert route_count == 1455, f"route_count={route_count} (expected 1455 per review spec)"


# ---------- DR-V2 AI synthesis (Invisible Intelligence) --------------
class TestDrV2AISynthesis:
    def test_synthesis_returns_three_outputs(self, api):
        rid = "drv2-b9f643a26802"
        r = api.post(f"{BASE_URL}/api/dr-v2/ai/synthesize", json={"report_id": rid}, timeout=90)
        assert r.status_code == 200, f"synthesize failed: {r.status_code} {r.text[:400]}"
        d = r.json()
        outputs = d.get("outputs") or {}
        keys_expected = {"day_narrative", "risk_and_constraints", "tomorrow_readiness"}
        found_keys = set(outputs.keys())
        missing = keys_expected - found_keys
        assert not missing, f"missing outputs {missing}; got {found_keys}"
        for k in keys_expected:
            o = outputs[k]
            conf = o.get("confidence")
            assert isinstance(conf, (int, float)) and 0.0 <= float(conf) <= 1.0
            provider = o.get("provider", "")
            model = o.get("model", "")
            assert provider in ("emergent", "anthropic"), f"{k} provider={provider}"
            assert "claude-sonnet-4-5" in str(model), f"{k} model={model}"
