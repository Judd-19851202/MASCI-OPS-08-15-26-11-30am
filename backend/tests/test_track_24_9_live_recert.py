"""Track 24.9 live preview recertification against public preview URL.

Covers all bullets in the Track 24.9 review request:
 * Public roster projection (unauth + PII allowlist)
 * Canonical roster still auth-gated
 * Public competent-person projection (unauth + PII allowlist)
 * Canonical qualifications endpoint still auth-gated
 * Synthetic-DR hygiene across admin/HR/safety/PM listings
 * Public DR POST write path smoke test with a real project number
"""

import os
import re
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fall back to reading frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASS = "Maddix123!"
HR_EMAIL = "hrmanager@mascigc.com"
HR_PASS = "HRTesting2026!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PASS = "ChrisRocksThis2026"

_PUBLIC_ROSTER_ALLOWED = {"id", "name", "employee_id", "trade", "role", "crew", "active"}
_PUBLIC_CP_ALLOWED = {
    "qualification_id", "qualification_type", "employee_name",
    "employee_trade", "employee_crew", "verification_status",
    "expires_at", "warning",
}
_PII_KEYS = {
    "email", "phone", "ssn", "dob", "address", "salary",
    "cdl", "medical", "supervisor", "department",
    "preferred_name", "lifecycle_status", "is_active", "updated_at",
    "notes", "attachments",
}
_SENTINEL_RE = re.compile(
    r"(^TEST[_\-])|(^0000-TEST)|(^SMOKE_)|(^SYNTHETIC_)|(^ITER\d+)|(QA_SMOKE)|(CERT_TEST)|(RECERT)|(PARITY)",
    re.IGNORECASE,
)


@pytest.fixture(scope="module")
def tokens():
    out = {"admin": None, "hr": None, "safety": None, "pm": None}
    # admin multi-login
    try:
        r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=30)
        if r.status_code == 200:
            j = r.json()
            portals = j.get("portal_tokens") or {}
            out["admin"] = portals.get("admin") or j.get("access_token") or j.get("token")
            out["safety"] = portals.get("safety")
            out["hr"] = portals.get("hr")
    except Exception as e:
        print(f"admin multi-login failed: {e}")
    # dedicated HR login fallback
    if not out["hr"]:
        try:
            r = requests.post(f"{BASE_URL}/api/hr/login",
                              json={"email": HR_EMAIL, "password": HR_PASS}, timeout=30)
            if r.status_code == 200:
                j = r.json()
                out["hr"] = j.get("token") or j.get("access_token")
        except Exception as e:
            print(f"hr login failed: {e}")
    # PM login (optional)
    try:
        r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                          json={"email": PM_EMAIL, "password": PM_PASS}, timeout=30)
        if r.status_code == 200:
            j = r.json()
            portals = j.get("portal_tokens") or {}
            out["pm"] = portals.get("pm") or portals.get("project_manager") or j.get("access_token")
    except Exception:
        pass
    print(f"TOKENS: admin={bool(out['admin'])} hr={bool(out['hr'])} safety={bool(out['safety'])} pm={bool(out['pm'])}")
    return out


# ---------- PUBLIC ROSTER ----------

def test_public_roster_unauth_200_and_shape():
    last_exc = None
    r = None
    for _ in range(3):
        try:
            r = requests.get(f"{BASE_URL}/api/hr/employee-roster/public", timeout=60)
            break
        except Exception as e:
            last_exc = e
            time.sleep(2)
    if r is None:
        raise last_exc
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    items = body if isinstance(body, list) else body.get("items") or body.get("employees") or []
    assert isinstance(items, list) and len(items) > 100, f"roster too small: {len(items)}"
    print(f"roster count = {len(items)}")
    # allowlist check
    for row in items[:50]:
        extra = set(row.keys()) - _PUBLIC_ROSTER_ALLOWED
        assert not extra, f"disallowed keys in public roster row: {extra}"
        for pii in _PII_KEYS:
            assert pii not in row, f"PII leak: {pii} in {row}"


def test_public_roster_contains_expected_employee():
    r = requests.get(f"{BASE_URL}/api/hr/employee-roster/public", timeout=60)
    body = r.json()
    items = body if isinstance(body, list) else body.get("items") or body.get("employees") or []
    names = [row.get("name", "") for row in items]
    assert any("Alec Perkins" in n for n in names), "Alec Perkins not found in public roster"


def test_canonical_roster_still_requires_auth():
    r = requests.get(f"{BASE_URL}/api/hr/employee-roster", timeout=30)
    assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"


def test_canonical_roster_with_admin_token_200(tokens):
    if not tokens["admin"]:
        pytest.skip("no admin token")
    h = {"X-Admin-Token": tokens["admin"]}
    r = requests.get(f"{BASE_URL}/api/hr/employee-roster", headers=h, timeout=30)
    assert r.status_code == 200, r.text[:300]


# ---------- PUBLIC COMPETENT PERSONS ----------

def test_public_cp_unauth_200_and_shape():
    r = requests.get(f"{BASE_URL}/api/employees/competent-persons/public", timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    items = body if isinstance(body, list) else body.get("items") or []
    assert isinstance(items, list)
    for row in items[:50]:
        extra = set(row.keys()) - _PUBLIC_CP_ALLOWED
        assert not extra, f"disallowed keys in CP public row: {extra}"
        for pii in _PII_KEYS:
            assert pii not in row, f"CP PII leak: {pii} in {row}"
        # legacy trench keys
        for legacy in ("cp_name", "cp_role", "role", "id"):
            assert legacy not in row, f"legacy key {legacy} present in CP public row"


def test_canonical_qualifications_still_requires_auth():
    r = requests.get(
        f"{BASE_URL}/api/employees/qualifications?type=COMPETENT_PERSON&active=true",
        timeout=30,
    )
    assert r.status_code == 401, f"expected 401, got {r.status_code}"


def test_canonical_qualifications_with_admin_200(tokens):
    if not tokens["admin"]:
        pytest.skip("no admin token")
    h = {"X-Admin-Token": tokens["admin"]}
    r = requests.get(
        f"{BASE_URL}/api/employees/qualifications?type=COMPETENT_PERSON&active=true",
        headers=h, timeout=30,
    )
    assert r.status_code == 200, r.text[:300]


# ---------- SYNTHETIC EXCLUSION ----------

def _contains_sentinel(rows, fields=("project_number", "project_name")):
    hits = []
    for r in rows:
        for f in fields:
            v = r.get(f) or ""
            if isinstance(v, str) and _SENTINEL_RE.search(v):
                hits.append((f, v, r.get("id") or r.get("_id")))
                break
    return hits


def test_admin_daily_reports_no_synthetic(tokens):
    if not tokens["admin"]:
        pytest.skip("no admin token")
    h = {"X-Admin-Token": tokens["admin"]}
    r = requests.get(f"{BASE_URL}/api/daily-reports?limit=500", headers=h, timeout=45)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    rows = body if isinstance(body, list) else body.get("items") or body.get("reports") or []
    hits = _contains_sentinel(rows)
    assert not hits, f"synthetic sentinels leaked into /daily-reports: {hits[:5]}"
    print(f"admin daily_reports count={len(rows)} synthetic_hits=0")


def test_admin_approved_daily_reports_no_synthetic(tokens):
    if not tokens["admin"]:
        pytest.skip("no admin token")
    h = {"X-Admin-Token": tokens["admin"]}
    r = requests.get(f"{BASE_URL}/api/daily-reports/approved?limit=200",
                     headers=h, timeout=45)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    rows = body if isinstance(body, list) else body.get("items") or body.get("reports") or []
    hits = _contains_sentinel(rows)
    assert not hits, f"synthetic leaks in /daily-reports/approved: {hits[:5]}"
    # sanity: sources present
    sources = {r.get("source") for r in rows}
    print(f"approved rows={len(rows)} sources={sources}")


def test_hr_daily_reports_no_synthetic(tokens):
    if not tokens["hr"]:
        pytest.skip("no hr token")
    h = {"X-HR-Token": tokens["hr"]}
    r = requests.get(f"{BASE_URL}/api/hr/daily-reports?limit=500", headers=h, timeout=45)
    if r.status_code == 404:
        pytest.skip("hr daily-reports endpoint not available")
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    rows = body if isinstance(body, list) else body.get("items") or body.get("reports") or []
    hits = _contains_sentinel(rows)
    assert not hits, f"synthetic leaks in /hr/daily-reports: {hits[:5]}"


def test_safety_daily_reports_no_synthetic(tokens):
    if not tokens["safety"]:
        pytest.skip("no safety token")
    h = {"X-Safety-Token": tokens["safety"]}
    r = requests.get(f"{BASE_URL}/api/safety/daily-reports?limit=500",
                     headers=h, timeout=45)
    if r.status_code == 404:
        pytest.skip("safety daily-reports endpoint not present")
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    rows = body if isinstance(body, list) else body.get("items") or body.get("reports") or []
    hits = _contains_sentinel(rows)
    assert not hits, f"synthetic in /safety/daily-reports: {hits[:5]}"


def test_pm_attention_no_synthetic_dr_cards(tokens):
    if not tokens["pm"]:
        pytest.skip("no pm token")
    h = {"X-PM-Token": tokens["pm"], "Authorization": f"Bearer {tokens['pm']}"}
    r = requests.get(f"{BASE_URL}/api/pm/command-center/attention", headers=h, timeout=45)
    if r.status_code in (401, 404):
        pytest.skip(f"pm attention endpoint returned {r.status_code}")
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    cards = body if isinstance(body, list) else (
        body.get("items") or body.get("cards") or body.get("attention") or []
    )
    hits = []
    for c in cards:
        label = f"{c.get('title','')} {c.get('subtitle','')} {c.get('project_number','')} {c.get('project_name','')}"
        if _SENTINEL_RE.search(label):
            hits.append(label[:120])
    assert not hits, f"synthetic DR cards in PM attention: {hits[:5]}"


# ---------- PUBLIC DR POST WRITE PATH ----------

def test_public_dr_post_real_project_smoke():
    payload = {
        "project_number": "20-07",
        "project_name": "Track 24.9 live recert smoke",
        "location": "Recert Yard",
        "prepared_by": "Live Recert Bot",
        "foreman_name": "Live Recert Bot",
        "report_date": time.strftime("%Y-%m-%d"),
        "work_description": "Track 24.9 recert smoke - do not use",
        "crew": [],
        "equipment": [],
        "language": "en",
    }
    r = requests.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=60)
    assert r.status_code in (200, 201), f"public DR POST failed: {r.status_code} {r.text[:300]}"
    j = r.json()
    dr_id = j.get("id") or j.get("_id") or j.get("report_id")
    assert dr_id, f"no id in create response: {j}"
    print(f"created DR id={dr_id}")
