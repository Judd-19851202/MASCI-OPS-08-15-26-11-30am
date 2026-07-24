from __future__ import annotations

import json
import re
from pathlib import Path

import requests


BASE_URL = next(
    line.split("=", 1)[1]
    for line in Path("/app/frontend/.env").read_text().splitlines()
    if line.startswith("REACT_APP_BACKEND_URL=")
)
CREDS_TEXT = Path("/app/memory/test_credentials.md").read_text()


def _extract_password(email: str) -> str:
    pattern = re.compile(rf"Email:\s*`{re.escape(email)}`.*?Password:\s*`([^`]+)`", re.S)
    match = pattern.search(CREDS_TEXT)
    if not match:
        raise AssertionError(f"Password for {email} not found in test_credentials.md")
    return match.group(1)


def _login(email: str, password: str) -> dict:
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": email, "password": password},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _headers(bundle: dict, portal: str) -> dict:
    headers = {"X-Directory-Token": bundle["session_token"]}
    if portal == "admin":
        headers["X-Admin-Token"] = bundle["portal_tokens"]["admin"]
    if portal == "pm":
        headers["X-PM-Token"] = bundle["portal_tokens"]["pm"]
    return headers


def test_preview_pm_scope_regression_matrix():
    admin_email = "jaymn.judd@mascigc.com"
    pm_email = "cert.pm@example.com"
    admin_bundle = _login(admin_email, _extract_password(admin_email))
    pm_bundle = _login(pm_email, _extract_password(pm_email))

    admin_admin_headers = _headers(admin_bundle, "admin")
    admin_pm_headers = _headers(admin_bundle, "pm")
    pm_headers = _headers(pm_bundle, "pm")

    admin_daily = requests.get(f"{BASE_URL}/api/daily-reports", headers=admin_admin_headers, timeout=60)
    admin_daily.raise_for_status()
    admin_daily_items = admin_daily.json()
    assert isinstance(admin_daily_items, list)
    assert admin_daily_items, "admin-token daily reports should be non-empty"

    admin_daily_pm_ctx = requests.get(f"{BASE_URL}/api/daily-reports", headers=admin_pm_headers, timeout=60)
    admin_daily_pm_ctx.raise_for_status()
    admin_daily_pm_ctx_items = admin_daily_pm_ctx.json()
    assert isinstance(admin_daily_pm_ctx_items, list)
    assert admin_daily_pm_ctx_items, "super admin PM-token daily reports should stay unrestricted"

    pm_daily = requests.get(f"{BASE_URL}/api/daily-reports", headers=pm_headers, timeout=60)
    pm_daily.raise_for_status()
    pm_daily_items = pm_daily.json()
    assert isinstance(pm_daily_items, list)
    assert pm_daily_items, "PM assigned daily reports should be visible"
    assert {item.get("project_number") for item in pm_daily_items if item.get("project_number")}, "PM daily reports should carry project numbers"

    assigned_daily = requests.get(
        f"{BASE_URL}/api/daily-reports/652b4e6f-bcb6-4065-8e89-4938c49d1f64",
        headers=pm_headers,
        timeout=60,
    )
    assert assigned_daily.status_code == 200
    assert assigned_daily.json().get("project_number") == "ZZ-RUNTIME-CERT-2026"

    unassigned_daily = requests.get(
        f"{BASE_URL}/api/daily-reports/forensic-dr-zz-for-unassign-01",
        headers=pm_headers,
        timeout=60,
    )
    assert unassigned_daily.status_code == 404

    admin_photos = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_admin_headers, timeout=60)
    admin_photos.raise_for_status()
    admin_photos_body = admin_photos.json()
    assert admin_photos_body.get("items"), "admin-token job photos should be non-empty"

    admin_photos_pm_ctx = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_pm_headers, timeout=60)
    admin_photos_pm_ctx.raise_for_status()
    admin_photos_pm_ctx_body = admin_photos_pm_ctx.json()
    assert admin_photos_pm_ctx_body.get("items"), "super admin PM-token job photos should stay unrestricted"

    pm_photos = requests.get(f"{BASE_URL}/api/job-photos", headers=pm_headers, timeout=60)
    pm_photos.raise_for_status()
    pm_photos_body = pm_photos.json()
    assert pm_photos_body.get("items"), "PM assigned job photos should be visible"
    assert any(item.get("project_number") == "ZZ-RUNTIME-CERT-2026" for item in pm_photos_body["items"])

    assigned_photo = requests.get(
        f"{BASE_URL}/api/job-photos/daily_report:652b4e6f-bcb6-4065-8e89-4938c49d1f64:1/raw",
        headers=pm_headers,
        timeout=60,
    )
    assert assigned_photo.status_code == 200

    unassigned_photo = requests.get(
        f"{BASE_URL}/api/job-photos/daily_report:85c5ed25-368e-46fe-8fa9-ae93993dd452:0/raw",
        headers=pm_headers,
        timeout=60,
    )
    assert unassigned_photo.status_code == 403

    no_token_daily = requests.get(f"{BASE_URL}/api/daily-reports", timeout=60)
    no_token_photos = requests.get(f"{BASE_URL}/api/job-photos", timeout=60)
    assert no_token_daily.status_code == 401
    assert no_token_photos.status_code == 401

    snapshot = {
        "admin_daily_count": len(admin_daily_items),
        "admin_daily_pm_context_count": len(admin_daily_pm_ctx_items),
        "pm_daily_count": len(pm_daily_items),
        "admin_photo_count": len(admin_photos_body.get("items") or []),
        "admin_photo_pm_context_count": len(admin_photos_pm_ctx_body.get("items") or []),
        "pm_photo_count": len(pm_photos_body.get("items") or []),
    }
    print(json.dumps(snapshot, indent=2))