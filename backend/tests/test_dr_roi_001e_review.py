"""DR-ROI-001E review tests - independent verification of intelligence + attention endpoints."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback to frontend env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"

FORBIDDEN = ["claude", "anthropic", "openai", "gpt-", "gemini", "model:", "provider:"]
PRESETS = ["today", "yesterday", "this_week", "last_week", "month", "last_month", "quarter", "year"]


def _get(path, **params):
    r = requests.get(f"{API}{path}", params=params, timeout=30)
    return r


def _no_ai_branding(text):
    lower = text.lower()
    hits = [tok for tok in FORBIDDEN if tok in lower]
    return hits


# ---- Admin dashboard ----
def test_admin_dashboard_shape():
    r = _get("/ods/admin/dashboard", preset="this_week")
    assert r.status_code == 200, r.text
    b = r.json()
    for k in ["enabled", "role", "range", "company_kpis", "projects_health"]:
        assert k in b, f"missing {k}: {list(b.keys())}"
    assert b["role"] == "admin"
    kpi = b["company_kpis"]
    for k in ["labor_hours", "equipment_hours", "photo_count", "projects_included"]:
        assert k in kpi, f"missing KPI {k}"
    assert isinstance(b["projects_health"], list)


def test_admin_attention_shape():
    r = _get("/ods/admin/attention", preset="this_week", limit=25)
    assert r.status_code == 200, r.text
    b = r.json()
    assert b.get("role") == "admin"
    for k in ["enabled", "range", "totals", "total", "items"]:
        assert k in b, f"missing {k}: {list(b.keys())}"
    items = b["items"]
    for bucket in ["safety", "quality", "delay", "readiness"]:
        assert bucket in items, f"missing bucket {bucket}"
        assert isinstance(items[bucket], list)
        for item in items[bucket]:
            for f in ["fact_id", "project_id", "date", "source_type", "severity", "summary", "category"]:
                assert f in item, f"attention item missing {f}"


def test_pm_dashboard_shape():
    r = _get("/ods/pm/dashboard", preset="month")
    assert r.status_code == 200, r.text
    b = r.json()
    for k in ["enabled", "role", "range", "kpis", "projects"]:
        assert k in b, f"missing {k}"
    assert b["role"] == "pm"


def test_pm_attention_shape():
    r = _get("/ods/pm/attention", preset="this_week")
    assert r.status_code == 200, r.text
    b = r.json()
    assert "items" in b
    for bucket in ["safety", "quality", "delay", "readiness"]:
        assert bucket in b["items"]


def test_pm_project_attention():
    r = _get("/ods/pm/projects/24-115/attention", preset="this_week")
    assert r.status_code == 200, r.text
    b = r.json()
    assert "items" in b


def test_executive_health():
    r = _get("/ods/executive/health", preset="month")
    assert r.status_code == 200, r.text
    b = r.json()
    for k in ["range", "top_at_risk", "total_projects"]:
        assert k in b, f"missing {k}: {list(b.keys())}"


def test_admin_delays():
    r = _get("/ods/admin/delays", preset="month")
    assert r.status_code == 200, r.text
    b = r.json()
    for k in ["range", "by_category", "delays"]:
        assert k in b


def test_no_ai_branding_in_endpoints():
    endpoints = [
        ("/ods/admin/dashboard", {"preset": "this_week"}),
        ("/ods/admin/attention", {"preset": "this_week"}),
        ("/ods/pm/dashboard", {"preset": "month"}),
        ("/ods/pm/attention", {"preset": "this_week"}),
        ("/ods/pm/projects/24-115/attention", {"preset": "this_week"}),
        ("/ods/executive/health", {"preset": "month"}),
        ("/ods/admin/delays", {"preset": "month"}),
    ]
    for path, params in endpoints:
        r = _get(path, **params)
        assert r.status_code == 200, f"{path} => {r.status_code}"
        hits = _no_ai_branding(r.text)
        assert not hits, f"{path} leaked AI branding: {hits}"


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@pytest.mark.parametrize("preset", PRESETS)
def test_all_presets_resolve(preset):
    r = _get("/ods/admin/dashboard", preset=preset)
    assert r.status_code == 200, r.text
    b = r.json()
    rng = b.get("range", {})
    # range should be dict with iso dates - flexibility
    # look for start/end in keys
    keys = list(rng.keys())
    dates = [v for v in rng.values() if isinstance(v, str) and DATE_RE.match(v)]
    assert len(dates) >= 2, f"preset={preset} range={rng}"
