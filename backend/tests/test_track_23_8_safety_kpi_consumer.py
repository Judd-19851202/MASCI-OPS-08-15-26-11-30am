"""TRACK 23.8 · Safety Portal KPI Consumer — lock envelope.

Verifies:
  * PM KPI endpoint requires auth AND enforces PmScope
    (per-PM tokens see only assigned projects; admin bypasses).
  * Safety per-project endpoint requires safety-or-admin auth
    (never PM-assignment blocked).
  * NEW Safety company-wide endpoint
    `GET /api/safety/company/safety-kpis` aggregates every active
    project + returns totals + top_projects + source_status_summary.
  * NO cost/dollar/rate keys anywhere.
  * Same aggregator serves PM and Safety (identical safety numbers).
  * No double-counting between DR safety events + linked incidents.
  * Safety UI card mounted on SafetyHubV2, not on Daily Report.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests

BACKEND = Path(__file__).resolve().parents[1]
FRONT = BACKEND.parent / "frontend" / "src"
LOCAL_API = "http://localhost:8001"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{LOCAL_API}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    tok = r.json().get("portal_tokens", {}).get("admin", "")
    assert tok, "no admin token minted"
    return tok


# ─── 1 · PM endpoint requires auth + enforces scope ────────────────
def test_pm_kpi_endpoint_requires_auth():
    r = requests.get(f"{LOCAL_API}/api/pm/projects/OD-100/operational-kpis", timeout=30)
    assert r.status_code in (401, 403), r.text


def test_pm_kpi_endpoint_admin_bypass(admin_token):
    r = requests.get(
        f"{LOCAL_API}/api/pm/projects/OD-100/operational-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=20,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["contract_version"] == "23.7"


# ─── 2 · Safety per-project endpoint (safety-or-admin) ─────────────
def test_safety_project_kpi_requires_auth():
    r = requests.get(
        f"{LOCAL_API}/api/safety/projects/OD-100/safety-kpis",
        timeout=15,
    )
    assert r.status_code == 401, r.text


def test_safety_project_kpi_admin_ok(admin_token):
    r = requests.get(
        f"{LOCAL_API}/api/safety/projects/OD-100/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=20,
    )
    assert r.status_code == 200
    d = r.json()
    for k in ("safety", "safety_sources", "activity_context",
              "contract_version"):
        assert k in d


# ─── 3 · NEW Safety company-wide endpoint ──────────────────────────
def test_safety_company_endpoint_requires_auth():
    r = requests.get(
        f"{LOCAL_API}/api/safety/company/safety-kpis",
        timeout=15,
    )
    assert r.status_code == 401


def test_safety_company_endpoint_shape(admin_token):
    r = requests.get(
        f"{LOCAL_API}/api/safety/company/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    for k in (
        "window", "date_from", "date_to", "generated_at",
        "contract_version",
        "active_project_count", "projects_with_safety_signal",
        "totals", "status_band", "top_projects", "projects",
        "source_status_summary",
    ):
        assert k in d, f"missing key {k}"
    assert d["contract_version"] == "23.8"
    assert d["status_band"] in ("green", "amber", "red")
    # totals must contain every safety KPI counter (no drift from
    # the shared aggregator).
    for kt in (
        "safety_event_count", "daily_report_safety_events",
        "incident_count", "accident_count", "near_miss_count",
        "utility_strike_count", "injuries_reported",
        "safety_contacted_yes", "safety_contacted_no",
        "escalation_gap_count", "open_incidents",
        "safety_meetings_count", "jha_count",
        "safety_inspection_count", "trench_inspection_count",
        "safety_photo_count",
    ):
        assert kt in d["totals"], f"totals missing {kt!r}"


def test_safety_company_top_projects_sorted_by_attention(admin_token):
    r = requests.get(
        f"{LOCAL_API}/api/safety/company/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    scores = [p["attention_score"] for p in r["top_projects"]]
    assert scores == sorted(scores, reverse=True), (
        "top_projects must be descending by attention_score"
    )


def test_safety_company_source_status_summary_contract(admin_token):
    r = requests.get(
        f"{LOCAL_API}/api/safety/company/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    ss = r["source_status_summary"]
    required = {
        "daily_report_safety_events", "incidents", "safety_meetings",
        "jha_records", "safety_inspections", "trench_excavations",
        "equipment_dvir", "trench_holds", "near_miss_reports",
    }
    assert required.issubset(ss.keys())
    for k, buckets in ss.items():
        assert set(buckets.keys()) <= {"LIVE", "PARTIAL", "MISSING · FUTURE"}
        # counts sum to active_project_count
        assert sum(buckets.values()) == r["active_project_count"], (
            f"{k}: source counts must partition active_project_count"
        )


# ─── 4 · No cost / dollar / rate anywhere ──────────────────────────
BANNED_EXACT = {
    "cost", "labor_cost", "labor_spend", "spend", "dollars", "usd",
    "rate", "hourly_rate", "billing_rate", "budget", "variance_usd",
    "amount_usd", "total_cost", "unit_cost", "material_cost",
    "equipment_cost", "burden", "burdened_rate", "burden_rate",
    "payroll_cost", "cost_variance", "budget_variance",
}


def _scan_no_cost(payload, path=""):
    if isinstance(payload, dict):
        for k, v in payload.items():
            assert str(k).lower() not in BANNED_EXACT, (
                f"banned key {k!r} at {path}.{k}"
            )
            _scan_no_cost(v, f"{path}.{k}")
    elif isinstance(payload, list):
        for i, v in enumerate(payload):
            _scan_no_cost(v, f"{path}[{i}]")


def test_safety_company_no_cost_fields(admin_token):
    r = requests.get(
        f"{LOCAL_API}/api/safety/company/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    _scan_no_cost(r)


def test_safety_project_no_cost_fields(admin_token):
    r = requests.get(
        f"{LOCAL_API}/api/safety/projects/OD-100/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=20,
    ).json()
    _scan_no_cost(r)


# ─── 5 · Same aggregator · PM and Safety see identical numbers ─────
def test_pm_and_safety_share_safety_numbers(admin_token):
    pn = "25-21"
    pm = requests.get(
        f"{LOCAL_API}/api/pm/projects/{pn}/operational-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    sf = requests.get(
        f"{LOCAL_API}/api/safety/projects/{pn}/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    for k in (
        "safety_event_count", "incident_count",
        "safety_meetings_count", "jha_count", "safety_inspection_count",
        "escalation_gap_count",
    ):
        assert pm["safety"][k] == sf["safety"][k], (
            f"{k}: PM={pm['safety'][k]!r} SAFETY={sf['safety'][k]!r}"
        )


def test_safety_events_never_double_counted(admin_token):
    """Contract lock — `safety_event_count == DR_events + incidents`
    forever. Never larger. Company + per-project."""
    company = requests.get(
        f"{LOCAL_API}/api/safety/company/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    assert company["totals"]["safety_event_count"] == (
        company["totals"]["daily_report_safety_events"]
        + company["totals"]["incident_count"]
    )
    for p in company["projects"]:
        # Only enforceable on rows carrying both fields (`projects`
        # only has aggregate counts; assert via a per-project call).
        r = requests.get(
            f"{LOCAL_API}/api/safety/projects/{p['project_number']}/safety-kpis?window=ptd",
            headers={"X-Admin-Token": admin_token}, timeout=20,
        ).json()
        assert r["safety"]["safety_event_count"] == (
            r["safety"]["daily_report_safety_events"]
            + r["safety"]["incident_count"]
        )


# ─── 6 · Window filter ─────────────────────────────────────────────
def test_company_window_filter(admin_token):
    ptd = requests.get(
        f"{LOCAL_API}/api/safety/company/safety-kpis?window=ptd",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    w7 = requests.get(
        f"{LOCAL_API}/api/safety/company/safety-kpis?window=7d",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    assert ptd["totals"]["safety_event_count"] >= w7["totals"]["safety_event_count"]


# ─── 7 · Frontend · Safety Portal card ─────────────────────────────
def test_safety_card_component_shape():
    src = _r(FRONT / "components" / "SafetyOperationalKpisCard.jsx")
    for token in (
        "/safety/company/safety-kpis",
        "/safety/projects/",
        "safety-operational-kpis",
        "safety-kpis-title",
        "safety-kpis-window-${w.key}",
        "safety-kpis-band",
        "safety-kpi-total-events",
        "safety-kpi-total-injuries",
        "safety-kpi-total-nearmiss",
        "safety-kpi-total-inspections",
        "safety-kpis-project-ranking",
        "safety-kpis-source-status",
        "safety-kpis-drilldown",
        "safety-kpis-drilldown-close",
        "safety-source-",
        "safety-drilldown-events",
    ):
        assert token in src, f"missing token {token!r}"
    # No money labels
    for banned in ("Cost", "Dollars", "Budget", "Spend", "Rate", "Labor spend"):
        assert banned not in src, f"banned label {banned!r}"


def test_safety_card_mounted_on_safety_hub_v2():
    src = _r(FRONT / "pages" / "SafetyHubV2.jsx")
    assert "SafetyOperationalKpisCard" in src


def test_safety_card_not_mounted_on_daily_report():
    src = _r(FRONT / "pages" / "NewDailyReportV3.jsx")
    assert "SafetyOperationalKpisCard" not in src


# ─── 8 · PmScope P0 fix lock ───────────────────────────────────────
def test_pm_kpi_route_enforces_pm_scope():
    src = _r(BACKEND / "routes" / "operational_kpis.py")
    idx = src.find("pm_project_operational_kpis")
    assert idx > 0
    window = src[idx:idx + 3000]
    assert "compute_pm_scope" in window, (
        "PM KPI route must call compute_pm_scope for per-PM scoping"
    )
    assert "scope.allows(project_number)" in window
    assert "status_code=403" in window


# ─── 9 · Regression — Daily Report V3 untouched ────────────────────
def test_daily_report_v3_untouched():
    src = _r(FRONT / "pages" / "NewDailyReportV3.jsx")
    assert "DailyReportTopBanner" in src
