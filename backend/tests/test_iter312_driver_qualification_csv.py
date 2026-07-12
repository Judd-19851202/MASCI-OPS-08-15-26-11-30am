"""
iter312 · Driver Qualification CSV export invariant.

Bounded operational-visibility export sibling of the existing
`/api/hr/driver-qualification/dashboard` endpoint. NOT a reporting
framework. NOT analytics. NOT a BI tool. Just: HR/Dispatch can ship
the current driver-qualification slice to FDOT / insurance carriers /
attorneys / auditors without screen-scraping.

Scope discipline (operator-bounded):
  - Same filters as the existing dashboard endpoint (zero query drift).
  - Same auth gate (HR or Admin).
  - Same projection — what HR sees on screen is what the CSV ships.
  - HR-friendly format: Yes/No flags, joined endorsement/restriction
    lists, summary rollup tail for archival/audit purposes.
  - `Cache-Control: no-store` — personnel data, never cached.
  - `Content-Disposition: attachment; filename="MASCI_..._YYYY-MM-DD.csv"`.
  - Operator-attributed audit trail (`GENERATED FOR <email>` line in CSV).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_PY = REPO_ROOT / "backend/routes/employee_lifecycle.py"

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://backup-forensics.preview.emergentagent.com",
).rstrip("/")
HR_EMAIL = "hrmanager@mascigc.com"
HR_PASSWORD = "HRTesting2026!"


@pytest.fixture(scope="module")
def hr_token():
    try:
        r = requests.post(
            f"{BASE_URL}/api/hr/login",
            json={"email": HR_EMAIL, "password": HR_PASSWORD},
            timeout=15,
        )
    except Exception as e:
        pytest.skip(f"preview HR login unreachable: {e}")
    if r.status_code != 200:
        pytest.skip(f"HR login non-200: {r.status_code} {r.text[:200]}")
    token = (r.json() or {}).get("token")
    if not token:
        pytest.skip("HR login response missing token")
    return token


@pytest.fixture(scope="module")
def hr_headers(hr_token):
    return {"X-HR-Token": hr_token}


# ── Static-code invariants ──────────────────────────────────────────


def test_iter312_csv_endpoint_registered():
    """The CSV sibling route must be registered on the employee
    lifecycle router."""
    text = LIFECYCLE_PY.read_text()
    assert '"/api/hr/driver-qualification/dashboard.csv"' in text, (
        "iter312 endpoint /api/hr/driver-qualification/dashboard.csv not registered"
    )


def test_iter312_csv_reuses_dashboard_handler():
    """The CSV endpoint must reuse the dashboard handler so the slice
    represents EXACTLY what the user just saw — no second query path."""
    text = LIFECYCLE_PY.read_text()
    # Find the csv handler block.
    idx = text.find("driver_qualification_dashboard_csv")
    assert idx > 0, "csv handler not found"
    end = text.find("return Response(", idx)
    block = text[idx:end + 200]
    assert "driver_qualification_dashboard(" in block, (
        "iter312 CSV handler must call driver_qualification_dashboard() to "
        "reuse the dashboard's filter/projection logic — no query drift allowed."
    )


def test_iter312_csv_same_auth_gate():
    """The CSV endpoint must use the same require_hr_or_admin gate as
    the dashboard endpoint. No weaker auth, no anon access."""
    text = LIFECYCLE_PY.read_text()
    idx = text.find("driver_qualification_dashboard_csv")
    block = text[idx:idx + 600]
    assert "require_hr_or_admin" in block, (
        "iter312 CSV endpoint missing require_hr_or_admin dependency — "
        "personnel data must not be accessible anonymously."
    )


def test_iter312_cache_control_no_store():
    """Personnel data — CSV response must carry Cache-Control: no-store
    so browsers/proxies never persist a qualification snapshot."""
    text = LIFECYCLE_PY.read_text()
    idx = text.find("driver_qualification_dashboard_csv")
    # Find the end of this handler by looking for the next `@router.`
    # decorator OR end of file.
    end_decorator = text.find("@router.", idx + 50)
    if end_decorator == -1:
        end_decorator = len(text)
    block = text[idx:end_decorator]
    assert "no-store" in block, (
        "iter312 CSV response missing Cache-Control: no-store header"
    )


# ── Runtime invariants ──────────────────────────────────────────────


def test_iter312_runtime_anonymous_blocked():
    """Anonymous access to the CSV must return 401.

    Uses raw urllib to BYPASS the conftest.py auto-token injection
    (which patches requests.* but not urllib.request) — verifies the
    real auth gate, not the test framework's fixture behavior.
    """
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/hr/driver-qualification/dashboard.csv",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        pytest.skip(f"preview backend unreachable: {e}")
    assert status in (401, 403), (
        f"CSV endpoint accessible anonymously: HTTP {status}. "
        f"Personnel data must be auth-gated."
    )


def test_iter312_runtime_full_export_returns_csv(hr_headers):
    """Authenticated GET returns text/csv with attachment disposition."""
    r = requests.get(
        f"{BASE_URL}/api/hr/driver-qualification/dashboard.csv",
        headers=hr_headers,
        timeout=15,
    )
    assert r.status_code == 200, f"unexpected {r.status_code}: {r.text[:200]}"
    assert "text/csv" in r.headers.get("content-type", "").lower(), (
        f"wrong content-type: {r.headers.get('content-type')}"
    )
    disp = r.headers.get("content-disposition", "")
    assert "attachment" in disp.lower(), (
        f"missing attachment disposition: {disp}"
    )
    assert "MASCI_driver_qualification_" in disp, (
        f"filename pattern drift: {disp}"
    )


def test_iter312_runtime_csv_headers_and_summary(hr_headers):
    """CSV body must have the canonical header row AND a summary tail
    with the operational rollup numbers."""
    r = requests.get(
        f"{BASE_URL}/api/hr/driver-qualification/dashboard.csv",
        headers=hr_headers,
        timeout=15,
    )
    assert r.status_code == 200
    body = r.text
    # Header row
    assert "Name,Employee ID,Trade,Supervisor" in body, (
        "iter312 CSV header row drift"
    )
    assert "Approved Company Driver,CDL Holder,Driver Status" in body
    # Summary tail
    assert "SUMMARY (operational rollup)" in body
    assert "Total drivers in scope" in body
    assert "CDL expiring within 30 days" in body
    assert "Medical card expiring within 30 days" in body
    assert "Tanker-capable (N or X endorsement)" in body
    # Audit attribution
    assert "GENERATED FOR" in body, (
        "iter312 CSV missing 'GENERATED FOR' audit attribution line"
    )
    assert "AS OF" in body


def test_iter312_runtime_filter_cdl_holder_matches_dashboard(hr_headers):
    """Same filter passed to the CSV must return the same slice as
    the dashboard JSON — zero query drift."""
    json_r = requests.get(
        f"{BASE_URL}/api/hr/driver-qualification/dashboard?cdl_holder=true",
        headers=hr_headers,
        timeout=15,
    )
    csv_r = requests.get(
        f"{BASE_URL}/api/hr/driver-qualification/dashboard.csv?cdl_holder=true",
        headers=hr_headers,
        timeout=15,
    )
    assert json_r.status_code == 200 and csv_r.status_code == 200
    json_count = (json_r.json() or {}).get("count", -1)
    # Count CSV data rows: total lines − header − blank lines − summary tail
    lines = csv_r.text.splitlines()
    summary_idx = next((i for i, ln in enumerate(lines) if ln.startswith("SUMMARY")), len(lines))
    # Data rows are lines after the header (idx 0) and before the
    # blank-line separator that precedes "SUMMARY".
    data_lines = [
        ln for ln in lines[1:summary_idx]
        if ln.strip()
    ]
    assert len(data_lines) == json_count, (
        f"iter312 query drift: JSON returned {json_count} drivers, "
        f"CSV returned {len(data_lines)} for the same cdl_holder=true filter"
    )
