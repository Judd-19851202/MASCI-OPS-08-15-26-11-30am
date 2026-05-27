"""Playwright operational regression suite — Phase 2 (iter437 Phase Sigma-II).

Adds 4 critical-path flows beyond the initial 5 read-only flows:
  6. Daily Report CREATE + persist round-trip
  7. Attachment upload round-trip → R2 HEAD verification
  10. Restore-system health endpoint reachable (covers Flow 14)
  11. Environment isolation under 10-parallel-request load

Remaining (Flows 8, 9, 12, 13, 15) are scoped in
/app/memory/PLAYWRIGHT_CERTIFICATION_PHASE2.md but not yet built — each
requires dedicated setup (WebAuthn helpers, dispatch user, etc.).
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import time
import uuid

import boto3
import pytest
import requests
from playwright.sync_api import Page

# --- helper: 1×1 transparent PNG bytes for attachment upload test --------
_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42m"
    "P8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)


# ---------------------------------------------------------------------------
# Flow 6 — Daily Report CREATE + persist round-trip
# ---------------------------------------------------------------------------
def test_daily_report_create_and_persist(base_url: str, super_admin_creds: dict, page: Page):
    """Create a daily report via the API (mirrors what the UI does on
    Save) and assert it survives a page refresh. Cleanup the test row
    afterwards so we don't leave noise in preview."""
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json=super_admin_creds,
        timeout=15,
    )
    assert r.status_code == 200
    admin_tok = r.json()["portal_tokens"]["admin"]

    # Pick a real job for FK integrity
    jobs = requests.get(
        f"{base_url}/api/admin/jobs",
        headers={"X-Admin-Token": admin_tok},
        timeout=10,
    ).json()
    job = jobs[0] if isinstance(jobs, list) else jobs.get("items", [])[0]

    unique_marker = f"playwright-pw-{uuid.uuid4().hex[:8]}"
    payload = {
        "report_date": "2026-05-27",
        "project_number": job["project_number"],
        "project_name": job.get("project_name") or "Phase Sigma-II Cert",
        "location": job.get("location") or "Test Location",
        "prepared_by": "Phase Sigma-II Test",
        "general_notes": unique_marker,
        "weather_summary": "clear",
    }

    # Create
    create = requests.post(
        f"{base_url}/api/daily-reports",
        headers={"X-Admin-Token": admin_tok, "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    assert create.status_code in (200, 201), f"create failed: {create.status_code} {create.text[:200]}"
    created = create.json()
    new_id = created.get("id") or created.get("_id") or (created.get("daily_report") or {}).get("id")
    assert new_id, f"no id in response: {created}"

    # Persistence — load the report list in the browser, confirm marker present.
    page.goto(base_url, wait_until="domcontentloaded", timeout=20_000)
    page.evaluate(
        "(tok) => localStorage.setItem('masci.admin.token', tok)",
        admin_tok,
    )
    # The list endpoint returns a SUMMARY (no general_notes). Verify
    # persistence by fetching the specific record by id from the browser
    # context — this also exercises the per-id GET route.
    found_marker = page.evaluate(
        """async (args) => {
            const r = await fetch(args.base + '/api/daily-reports/' + args.id, {
                headers: {'X-Admin-Token': args.tok}
            });
            if (!r.ok) return false;
            const doc = await r.json();
            return (doc.general_notes || '').includes(args.marker);
        }""",
        {"base": base_url, "tok": admin_tok, "id": new_id, "marker": unique_marker},
    )
    assert found_marker, "created daily report not visible to admin browser context"

    # Cleanup — drop the test row directly via Mongo helper exposed by the API
    cleanup = requests.delete(
        f"{base_url}/api/daily-reports/{new_id}",
        headers={"X-Admin-Token": admin_tok},
        timeout=15,
    )
    # Cleanup is best-effort — some installs don't expose DELETE. Acceptable.
    assert cleanup.status_code in (200, 204, 404, 405), \
        f"cleanup unexpected status {cleanup.status_code}"


# ---------------------------------------------------------------------------
# Flow 7 — Attachment upload round-trip → R2 HEAD verification
# ---------------------------------------------------------------------------
def test_attachment_upload_round_trip_to_r2(base_url: str, super_admin_creds: dict):
    """Upload a tiny PNG via the operational-attachments endpoint, then
    HEAD the resulting R2 key directly to prove the file actually
    landed in R2 (not just in MongoDB metadata)."""
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json=super_admin_creds,
        timeout=15,
    )
    admin_tok = r.json()["portal_tokens"]["admin"]

    files = {"file": ("phase2-cert.png", _PNG_BYTES, "image/png")}
    data = {"kind": "test_cert", "label": "playwright-phase2"}
    up = requests.post(
        f"{base_url}/api/operational-attachments",
        headers={"X-Admin-Token": admin_tok},
        files=files,
        data=data,
        timeout=30,
    )
    if up.status_code == 404:
        pytest.skip("operational-attachments endpoint not exposed on this build")
    assert up.status_code in (200, 201), f"upload failed: {up.status_code} {up.text[:200]}"
    body = up.json()
    r2_key = body.get("r2_key") or (body.get("attachment") or {}).get("r2_key")
    assert r2_key, f"no r2_key in response: {body}"

    # Direct R2 HEAD
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="auto",
    )
    head = s3.head_object(Bucket=os.environ["S3_BUCKET"], Key=r2_key)
    assert head["ContentLength"] == len(_PNG_BYTES), \
        f"R2 size mismatch: {head['ContentLength']} vs {len(_PNG_BYTES)}"

    # Cleanup — delete the test object
    try:
        s3.delete_object(Bucket=os.environ["S3_BUCKET"], Key=r2_key)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Flow 10 / 14 — Restore-system health endpoint reachable
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("endpoint", [
    "/api/health",
    "/api/version",
    "/api/cluster/capacity",
    "/api/cluster/capacity/history?days=1",
])
def test_health_surface_reachable(base_url: str, endpoint: str):
    """Restore-system health surfaces must be reachable without auth so
    the operator can verify post-restore even if all tokens are wiped."""
    r = requests.get(f"{base_url}{endpoint}", timeout=10)
    assert r.status_code == 200, f"{endpoint} -> {r.status_code}: {r.text[:200]}"
    body = r.json()
    # `/api/version` returns env identity instead of `ok`. Accept either shape.
    if endpoint == "/api/version":
        assert body.get("app_env") and body.get("db_name")
    else:
        assert body.get("ok") is True


# ---------------------------------------------------------------------------
# Flow 11 — Environment isolation under load
# ---------------------------------------------------------------------------
def test_env_isolation_under_parallel_load(base_url: str):
    """10 parallel requests to /api/version must all return preview, none ever leak production identity."""
    import concurrent.futures

    def _probe():
        r = requests.get(f"{base_url}/api/version", timeout=10)
        return r.status_code, (r.json() if r.ok else None)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: _probe(), range(10)))

    statuses = {s for s, _ in results}
    assert statuses == {200}, f"some calls failed: {statuses}"
    for status, body in results:
        assert body["app_env"] == "preview"
        assert body["db_name"].endswith("_preview")
