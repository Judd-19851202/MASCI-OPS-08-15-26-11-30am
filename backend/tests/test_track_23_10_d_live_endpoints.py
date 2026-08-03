"""Live endpoint tests for Track 23.10-D Safety Portal Trench KPI Lift.
Runs against REACT_APP_BACKEND_URL public URL and validates real auth/data.
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASS = "Maddix123!"

PM_EMAIL = "track15.11b.cert.pm@mascicert.local"
PM_PASS = "Track15Cert!2026"

FORBIDDEN_MONEY_KEYS = {"cost", "rate", "budget", "payroll", "wage", "dollars", "amount", "price", "spend"}


@pytest.fixture(scope="module")
def admin_tokens():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=90)
    assert r.status_code == 200, f"admin multi-login failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    return data.get("portal_tokens") or data.get("tokens") or data


@pytest.fixture(scope="module")
def admin_headers(admin_tokens):
    admin_tok = admin_tokens.get("admin")
    safety_tok = admin_tokens.get("safety")
    assert admin_tok or safety_tok, f"no admin/safety token found in {list(admin_tokens.keys())}"
    h = {}
    if admin_tok:
        h["X-Admin-Token"] = admin_tok
    if safety_tok:
        h["X-Safety-Token"] = safety_tok
    return h


@pytest.fixture(scope="module")
def pm_tokens():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": PM_EMAIL, "password": PM_PASS}, timeout=90)
    if r.status_code != 200:
        pytest.skip(f"PM login unavailable: {r.status_code}")
    data = r.json()
    tokens = data.get("portal_tokens") or data.get("tokens") or data
    return tokens


def _deep_scan_forbidden(obj, path="root"):
    """Recursively scan dict/list for forbidden money-related keys.
    We only flag as actual violation if a key equals a forbidden term OR clearly relates.
    """
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            klc = str(k).lower()
            for term in FORBIDDEN_MONEY_KEYS:
                # exact key or key contains the term
                if klc == term or term in klc.split("_"):
                    hits.append(f"{path}.{k}")
            hits.extend(_deep_scan_forbidden(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            hits.extend(_deep_scan_forbidden(item, f"{path}[{i}]"))
    return hits


# ---------- Company Trench Safety KPIs ----------

def test_company_trench_kpis_admin_ok(admin_headers):
    r = requests.get(f"{BASE_URL}/api/safety/company/trench-safety-kpis?window=30d",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:400]}"
    j = r.json()
    # Top level structure
    for key in ("window", "trench", "certifications", "top_projects", "source_classification"):
        assert key in j, f"missing top-level key: {key}"
    # Trench block
    t = j["trench"]
    for key in ("excavation_days", "trench_inspections", "open_holds", "closed_holds",
                "safe_to_use_verified", "repairs_total", "competent_person_assignments",
                "max_depth_observed_ft", "linkage_breakdown",
                "historical_missing_link_count", "historical_missing_by_type"):
        assert key in t, f"missing trench key: {key}"
    lb = t["linkage_breakdown"]
    for key in ("live", "partial", "missing", "ambiguous"):
        assert key in lb
    # Certifications block
    c = j["certifications"]
    for key in ("active_competent_persons", "expiring_soon", "expired",
                "suspended", "revoked", "pending", "cp_registry_sample"):
        assert key in c, f"missing certifications key: {key}"
    # Source classification
    sc = j["source_classification"]
    assert "trench" in sc and "certifications" in sc
    assert sc["trench"] in ("LIVE", "PARTIAL", "MISSING")
    assert sc["certifications"] in ("LIVE", "PARTIAL", "MISSING")


def test_company_trench_kpis_nonzero_live(admin_headers):
    r = requests.get(f"{BASE_URL}/api/safety/company/trench-safety-kpis?window=30d",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200
    j = r.json()
    t = j["trench"]
    # Live preview per problem statement expects ~260 excavations, 82 open holds
    assert t["excavation_days"] > 0, f"excavation_days should be >0, got {t['excavation_days']}"
    # We don't strictly require 260/82 but should be substantial (>10)
    assert t["excavation_days"] >= 10, f"excavation_days too low: {t['excavation_days']}"


def test_company_trench_kpis_no_money_keys(admin_headers):
    r = requests.get(f"{BASE_URL}/api/safety/company/trench-safety-kpis?window=30d",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200
    hits = _deep_scan_forbidden(r.json())
    assert not hits, f"forbidden money keys in response: {hits}"


def test_company_trench_kpis_unauth_401():
    r = requests.get(f"{BASE_URL}/api/safety/company/trench-safety-kpis?window=30d", timeout=20)
    assert r.status_code in (401, 403), f"expected 401/403 unauth, got {r.status_code}"


def test_company_trench_kpis_invalid_window(admin_headers):
    r = requests.get(f"{BASE_URL}/api/safety/company/trench-safety-kpis?window=INVALID",
                     headers=admin_headers, timeout=20)
    assert r.status_code in (400, 422), f"expected 400/422 for bad window, got {r.status_code}: {r.text[:200]}"


def test_company_trench_kpis_pm_403(pm_tokens):
    pm_tok = pm_tokens.get("pm")
    if not pm_tok:
        pytest.skip("no pm token")
    r = requests.get(f"{BASE_URL}/api/safety/company/trench-safety-kpis?window=30d",
                     headers={"X-PM-Token": pm_tok}, timeout=20)
    assert r.status_code == 403, f"PM should be denied company-wide safety data, got {r.status_code}: {r.text[:300]}"


# ---------- Cleanup ----------

def test_cleanup_admin_ok(admin_headers):
    r = requests.get(f"{BASE_URL}/api/safety/company/trench-safety-cleanup?limit=100",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:400]}"
    j = r.json()
    for key in ("totals", "items", "read_only", "note"):
        assert key in j, f"missing cleanup key: {key}"
    for key in ("missing", "ambiguous", "asset_only"):
        assert key in j["totals"]
    assert j["read_only"] is True
    # The note SHOULD say "No auto-fix" (i.e., the API explicitly does not offer auto-fix).
    # Verify that if "auto-fix" appears at all, it is only in a negating context (No/no).
    blob = str(j).lower()
    if "auto-fix" in blob or "auto fix" in blob or "auto-repair" in blob:
        # Only allowed in negation context
        assert re.search(r"no\s+auto[- ]?fix", blob) or re.search(r"no\s+auto[- ]?repair", blob), \
            "auto-fix mentioned outside of 'No auto-fix' disclaimer"
    # If items include possible_project, note must clarify candidate only
    for it in j.get("items", [])[:10]:
        pp = it.get("possible_project")
        if pp:  # only assert note when a real candidate exists
            note = str(it.get("possible_project_note", "")).lower()
            assert "candidate" in note or "not applied" in note, f"possible_project_note weak: {note}"


def test_cleanup_unauth():
    r = requests.get(f"{BASE_URL}/api/safety/company/trench-safety-cleanup?limit=10", timeout=20)
    assert r.status_code in (401, 403)


# ---------- Project-scoped ----------

def test_project_trench_kpis_admin(admin_headers):
    r = requests.get(f"{BASE_URL}/api/safety/projects/FT-JOB-1001/trench-safety-kpis",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:400]}"
    j = r.json()
    for key in ("project_number", "excavation_days", "safe_to_use_verified",
                "latest_excavation_day", "source_classification", "linkage_breakdown"):
        assert key in j, f"missing project key: {key}"
    assert j["project_number"] == "FT-JOB-1001"


# ---------- Regressions ----------

def test_reg_qualification_types_still_16(admin_headers):
    r = requests.get(f"{BASE_URL}/api/employees/qualifications/types",
                     headers=admin_headers, timeout=20)
    assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
    data = r.json()
    types = data if isinstance(data, list) else data.get("types") or data.get("items") or []
    assert len(types) == 16, f"expected 16 qualification types, got {len(types)}"


def test_reg_trench_intelligence_company_summary(admin_headers):
    r = requests.get(f"{BASE_URL}/api/trench-intelligence/company/summary",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"


def test_reg_safety_company_safety_kpis(admin_headers):
    r = requests.get(f"{BASE_URL}/api/safety/company/safety-kpis",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
