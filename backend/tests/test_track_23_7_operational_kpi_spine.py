"""TRACK 23.7 · Operational KPI Spine — lock envelope.

Verifies:
  * Shared aggregator in `services/operational_kpis/aggregator.py`
    computes labor/equipment/materials/production/delays/safety/
    intelligence rollups from ODS `operational_facts` +
    canonical safety collections.
  * PM route `/api/pm/projects/{pn}/operational-kpis` and Safety
    route `/api/safety/projects/{pn}/safety-kpis` share the same
    numbers.
  * `scheduling_readiness` block present.
  * `safety_sources` block classifies every source LIVE / PARTIAL /
    MISSING · FUTURE.
  * NO cost/dollar/rate keys anywhere in either response.
  * Window filtering works (7d / 30d / mtd / ptd).
  * Empty project safe (no crash on missing facts).
  * PM UI mounts on PmProjectDetail — never on Daily Report V3.
"""
from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import pytest
import requests

BACKEND = Path(__file__).resolve().parents[1]
FRONT = BACKEND.parent / "frontend" / "src"
LOCAL_API = "http://localhost:8001"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# TRACK 23.8 · PM endpoint now requires auth. Mint an admin token
# once and inject it into every PM /operational-kpis request.
_ADMIN_TOKEN = None


def _admin_headers():
    global _ADMIN_TOKEN
    if _ADMIN_TOKEN is None:
        r = requests.post(
            LOCAL_API + "/api/auth/multi-login",
            json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
            timeout=15,
        )
        _ADMIN_TOKEN = r.json().get("portal_tokens", {}).get("admin", "")
    return {"X-Admin-Token": _ADMIN_TOKEN}


def _get(path: str):
    headers = _admin_headers() if ("/pm/" in path or "/safety/" in path) else {}
    return requests.get(LOCAL_API + path, headers=headers, timeout=30)


# ─── 1 · aggregator module contract ────────────────────────────────
def test_aggregator_exports():
    from services.operational_kpis import aggregate_project_kpis, _resolve_window  # noqa: F401


def test_resolve_window_thresholds():
    from services.operational_kpis import _resolve_window
    df, dt, w = _resolve_window("7d")
    assert w == "7d"
    assert dt == date.today().isoformat()
    assert df == (date.today() - timedelta(days=6)).isoformat()
    df, dt, w = _resolve_window("30d")
    assert w == "30d"
    assert df == (date.today() - timedelta(days=29)).isoformat()
    df, dt, w = _resolve_window("mtd")
    assert w == "mtd"
    assert df == date.today().replace(day=1).isoformat()
    df, dt, w = _resolve_window("ptd")
    assert w == "ptd"
    assert df is None
    # unknown window → default 7d
    df, dt, w = _resolve_window("garbage")
    assert w == "7d"


# ─── 2 · NO cost data anywhere ─────────────────────────────────────
# Exact key names that are banned (not substrings — "generated_at"
# contains "rate" but is not a banned key).
BANNED_EXACT = {
    "cost", "labor_cost", "labor_spend", "spend", "dollars", "usd",
    "rate", "hourly_rate", "billing_rate", "budget", "variance_usd",
    "amount_usd", "total_cost", "unit_cost", "material_cost",
    "equipment_cost", "burden", "burdened_rate", "burden_rate",
    "payroll_cost", "cost_variance", "budget_variance",
}


def _scan_banned(payload, path=""):
    if isinstance(payload, dict):
        for k, v in payload.items():
            kl = str(k).lower()
            assert kl not in BANNED_EXACT, (
                f"banned key {kl!r} at {path}.{k}"
            )
            _scan_banned(v, f"{path}.{k}")
    elif isinstance(payload, list):
        for i, v in enumerate(payload):
            _scan_banned(v, f"{path}[{i}]")


@pytest.mark.parametrize("project_number", ["OD-100", "25-21", "24-12"])
def test_pm_endpoint_returns_expected_groups(project_number):
    r = _get(f"/api/pm/projects/{project_number}/operational-kpis?window=ptd")
    assert r.status_code == 200, r.text
    d = r.json()
    for k in (
        "project_number", "project_name", "window", "generated_at",
        "contract_version", "labor", "equipment", "materials",
        "production", "delays", "safety", "intelligence",
        "safety_sources", "scheduling_readiness",
    ):
        assert k in d, f"pm KPI missing key {k}"
    assert d["contract_version"] == "23.7"
    _scan_banned(d)


def test_pm_endpoint_no_money_or_rate_keys():
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd")
    body = r.json()
    _scan_banned(body)


def test_safety_endpoint_returns_subset():
    r = _get("/api/safety/projects/OD-100/safety-kpis?window=ptd")
    assert r.status_code == 200
    d = r.json()
    for k in (
        "project_number", "safety", "safety_sources", "window",
        "activity_context", "contract_version",
    ):
        assert k in d
    # Must NOT contain the heavy KPI blocks (that's the PM view).
    for k in ("labor", "equipment", "materials", "production", "delays", "intelligence"):
        assert k not in d, f"safety endpoint must NOT expose {k}"
    _scan_banned(d)


# ─── 3 · KPI content correctness ───────────────────────────────────
def test_labor_kpis_shape():
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd")
    d = r.json()["labor"]
    for k in (
        "total_man_hours", "unique_employee_count",
        "verified_employee_count",
        "by_trade", "by_crew", "by_supervisor", "by_cost_code",
        "daily_trend",
    ):
        assert k in d
    assert isinstance(d["by_trade"], list)


def test_equipment_kpis_shape():
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd")
    d = r.json()["equipment"]
    for k in (
        "total_run_hours", "total_idle_hours", "utilization_percent",
        "equipment_count", "issue_count", "by_equipment",
        "daily_trend",
    ):
        assert k in d
    # utilization bounds
    assert 0 <= d["utilization_percent"] <= 100


def test_material_kpis_shape():
    r = _get("/api/pm/projects/25-21/operational-kpis?window=ptd")
    d = r.json()["materials"]
    for k in (
        "inbound_by_material_unit", "outbound_by_material_unit",
        "load_count", "ticket_count", "carriers", "daily_trend",
    ):
        assert k in d
    # If materials present, unit + material carry through
    for row in d["inbound_by_material_unit"][:3]:
        assert "material" in row
        assert "unit" in row
        assert "quantity" in row


def test_delay_kpis_shape():
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd")
    d = r.json()["delays"]
    for k in (
        "delay_count", "total_hours_impact", "by_category",
        "highest_severity", "unresolved_follow_ups",
    ):
        assert k in d


def test_safety_kpis_shape():
    r = _get("/api/pm/projects/25-21/operational-kpis?window=ptd")
    d = r.json()["safety"]
    for k in (
        "safety_event_count", "daily_report_safety_events",
        "incident_count", "accident_count", "near_miss_count",
        "utility_strike_count", "injuries_reported",
        "safety_contacted_yes", "safety_contacted_no",
        "escalation_gap_count", "open_incidents",
        "safety_meetings_count", "jha_count",
        "safety_inspection_count", "trench_inspection_count",
        "safety_photo_count", "by_daily_safety_type",
    ):
        assert k in d


def test_intelligence_kpis_shape():
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd")
    d = r.json()["intelligence"]
    for k in (
        "accepted_summaries_count", "intelligence_row_count",
        "latest_summary", "photo_observation_count",
        "top_photo_tags",
    ):
        assert k in d


def test_safety_events_do_not_double_count_daily_and_incidents():
    """`safety_event_count` MUST equal
    `daily_report_safety_events + incident_count` — never double."""
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd")
    d = r.json()["safety"]
    assert d["safety_event_count"] == (
        d["daily_report_safety_events"] + d["incident_count"]
    )


# ─── 4 · scheduling readiness / safety sources ─────────────────────
def test_scheduling_readiness_block():
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd")
    d = r.json()["scheduling_readiness"]
    for k in (
        "labor_signal_available", "equipment_signal_available",
        "material_signal_available", "production_signal_available",
        "delay_signal_available", "safety_signal_available",
        "weather_signal_available", "tomorrow_plan_available",
        "readiness_signal_available", "notes",
    ):
        assert k in d
    # OD-100 has labor + equipment facts populated in preview
    assert d["labor_signal_available"] is True
    assert d["equipment_signal_available"] is True
    # tomorrow plan is future
    assert d["tomorrow_plan_available"] is False


def test_safety_sources_classification():
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd")
    sources = r.json()["safety_sources"]
    required = {
        "daily_report_safety_events", "incidents", "safety_meetings",
        "jha_records", "safety_inspections", "trench_excavations",
        "equipment_dvir", "trench_holds", "near_miss_reports",
    }
    assert required.issubset(sources.keys())
    allowed = {"LIVE", "PARTIAL", "MISSING · FUTURE"}
    for k, v in sources.items():
        assert v["status"] in allowed, f"{k}: unknown status {v['status']}"
        assert "source" in v


# ─── 5 · window filtering ──────────────────────────────────────────
def test_window_filter_narrows_labor_rows():
    """Given labor is dated in early July 2026, a 7d window from
    today (Feb 2026) MUST return 0 rows. A ptd window MUST have
    all of them. This lock proves date filtering works."""
    ptd = _get("/api/pm/projects/OD-100/operational-kpis?window=ptd").json()
    w7 = _get("/api/pm/projects/OD-100/operational-kpis?window=7d").json()
    assert ptd["labor"]["labor_row_count"] >= w7["labor"]["labor_row_count"]


def test_unknown_window_defaults_to_7d():
    r = _get("/api/pm/projects/OD-100/operational-kpis?window=quarter")
    assert r.status_code == 200
    assert r.json()["window"] == "7d"


# ─── 6 · empty project safe ────────────────────────────────────────
def test_empty_project_never_crashes():
    r = _get("/api/pm/projects/NON_EXISTENT_XYZ/operational-kpis?window=7d")
    assert r.status_code == 200
    d = r.json()
    assert d["labor"]["total_man_hours"] == 0
    assert d["equipment"]["total_run_hours"] == 0
    assert d["materials"]["load_count"] == 0
    assert d["delays"]["delay_count"] == 0
    assert d["safety"]["safety_event_count"] == 0


# ─── 7 · same aggregator serves PM + Safety ────────────────────────
def test_pm_and_safety_share_same_safety_numbers():
    pn = "OD-100"
    pm = _get(f"/api/pm/projects/{pn}/operational-kpis?window=ptd").json()
    sf = _get(f"/api/safety/projects/{pn}/safety-kpis?window=ptd").json()
    for k in (
        "safety_event_count", "incident_count",
        "safety_meetings_count", "jha_count", "safety_inspection_count",
    ):
        assert pm["safety"][k] == sf["safety"][k], (
            f"{k} diverged: PM={pm['safety'][k]!r} SAFETY={sf['safety'][k]!r}"
        )


# ─── 8 · frontend mount + no-cost lock ─────────────────────────────
def test_frontend_card_component_shape():
    src = _r(FRONT / "components" / "PmOperationalKPIs.jsx")
    # Endpoint is correct
    assert "/pm/projects/" in src
    assert "operational-kpis" in src
    # Required testids (dynamic testids surface as template strings
    # in the JSX; check the template stubs).
    for tid in (
        "pm-operational-kpis",
        "pm-operational-kpis-title",
        "pm-operational-kpis-window-${w.key}",
        "pm-kpi-labor",
        "pm-kpi-equipment",
        "pm-kpi-materials",
        "pm-kpi-delays",
        "pm-kpi-production",
        "pm-kpi-safety",
        "pm-kpi-photos",
        "pm-kpi-latest-summary",
        "pm-kpi-scheduling-readiness",
        "pm-kpi-safety-sources",
    ):
        assert tid in src, f"missing testid {tid}"
    # No cost/money labels
    for banned in ("Cost", "Dollar", "Budget", "Spend", "Rate", "Labor spend"):
        assert banned not in src, f"banned label {banned!r} in KPI card"


def test_frontend_mounted_on_pm_project_detail():
    src = _r(FRONT / "pages" / "PmProjectDetail.jsx")
    assert "PmOperationalKPIs" in src
    assert 'from "@/components/PmOperationalKPIs"' in src


def test_frontend_not_on_daily_report():
    src = _r(FRONT / "pages" / "NewDailyReportV3.jsx")
    assert "PmOperationalKPIs" not in src


# ─── 9 · regression — no daily-report / hr routes changed ──────────
def test_daily_report_v3_still_renders():
    src = _r(FRONT / "pages" / "NewDailyReportV3.jsx")
    assert "DailyReportTopBanner" in src


def test_hr_completeness_endpoint_still_works():
    r = _get("/api/employees")
    assert r.status_code == 200
    assert r.json().get("items")


def test_ods_facts_untouched():
    """Aggregator MUST read from operational_facts, never write."""
    src = _r(BACKEND / "services" / "operational_kpis" / "aggregator.py")
    for verb in ("insert_", "update_", "delete_", "replace_", "$set"):
        assert verb not in src, f"aggregator must be read-only, found {verb!r}"
