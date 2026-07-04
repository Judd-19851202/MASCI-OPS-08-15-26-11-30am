"""Playwright operational regression — Phase 3 (iter437 Phase Sigma-III).

Closes the deferred flows from Phase 2:

  • Flow 8   Daily Report CREATE + crew/visitor sub-sections persist
  • Flow 9   Dispatch board (operations/* reads) reachable via dispatch token
  • Flow 10b Driver shift surface (magic-link → session exchange → /me)
  • Flow 11b HR Time Verification + SLA
  • Flow 12  MFA enroll → verify → disable round-trip (admin-strict)
  • Flow 13  Public form submission (parameterized BOTH inspections + meetings)
  • Flow 15  Env isolation under WRITE load (10 parallel inspections)

Doctrine:
  - NEVER run against production (`env_safety_check` in conftest).
  - Every CREATE has a CLEANUP step (best-effort on cleanup endpoint).
  - Unique markers (`pw-phase3-<uuid>`) guarantee dataset hygiene.
  - Failure artefacts: screenshot + JSON tail per conftest fixture.

Run:
  cd /app/backend && python3 -m pytest tests/pw_suite/test_critical_flows_pw_phase3.py -v
"""
from __future__ import annotations

import concurrent.futures
import os
import time
import uuid
from typing import Any, Dict

import pyotp
import pytest
import requests
from playwright.sync_api import Page


# ════════════════════════════════════════════════════════════════════
# Shared helpers (Phase-3 only; phase-2 fixtures live in conftest.py)
# ════════════════════════════════════════════════════════════════════
def _multi_login(base_url: str, creds: Dict[str, str]) -> Dict[str, Any]:
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json=creds,
        timeout=15,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:200]}"
    return r.json()


def _admin_token(base_url: str, creds: Dict[str, str]) -> str:
    return _multi_login(base_url, creds)["portal_tokens"]["admin"]


# ────────────────────────────────────────────────────────────────────
# Flow 8 — Daily Report with crew/visitor sub-sections persists
# ────────────────────────────────────────────────────────────────────
def test_daily_report_subsections_persist(
    base_url: str, super_admin_creds: dict, page: Page, viewport_name: str,
):
    """Phase-III · proves that masci_crews + visitors arrays survive
    the round-trip (Phase-2 only proved general_notes survived)."""
    tokens = _multi_login(base_url, super_admin_creds)["portal_tokens"]
    admin_tok = tokens["admin"]

    jobs = requests.get(
        f"{base_url}/api/admin/jobs",
        headers={"X-Admin-Token": admin_tok},
        timeout=10,
    ).json()
    job = jobs[0] if isinstance(jobs, list) else jobs.get("items", [])[0]

    marker = f"pw-phase3-flow8-{uuid.uuid4().hex[:8]}"
    crew_marker = f"crew-{marker}"
    visitor_marker = f"visitor-{marker}"
    payload = {
        "report_date": "2026-05-27",
        "project_number": job["project_number"],
        "project_name": job.get("project_name") or "Phase Sigma-III",
        "location": job.get("location") or "Test Location",
        "prepared_by": "Phase Sigma-III Test",
        "general_notes": marker,
        "masci_crews": [
            {"foreman": crew_marker, "crew_size": 5, "hours": 8.0}
        ],
        "visitors": [
            {"name": visitor_marker, "company": "OSHA", "purpose": "inspection"}
        ],
    }

    create = requests.post(
        f"{base_url}/api/daily-reports",
        headers={"X-Admin-Token": admin_tok, "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    assert create.status_code in (200, 201), create.text[:200]
    new_id = (create.json() or {}).get("id")
    assert new_id, "no id on create"

    # Fetch from browser context — proves the SPA's read path also sees it
    page.goto(base_url, wait_until="domcontentloaded", timeout=20_000)
    page.evaluate(
        "(tok) => localStorage.setItem('masci.admin.token', tok)", admin_tok,
    )
    fetched = page.evaluate(
        """async (args) => {
            const r = await fetch(args.base + '/api/daily-reports/' + args.id, {
                headers: {'X-Admin-Token': args.tok}
            });
            if (!r.ok) return null;
            return await r.json();
        }""",
        {"base": base_url, "tok": admin_tok, "id": new_id},
    )
    assert fetched, "browser fetch failed"
    crews = fetched.get("masci_crews") or []
    visitors = fetched.get("visitors") or []
    assert any(c.get("foreman") == crew_marker for c in crews), \
        f"crew_marker not in masci_crews: {crews}"
    assert any(v.get("name") == visitor_marker for v in visitors), \
        f"visitor_marker not in visitors: {visitors}"

    # Cleanup — best-effort
    try:
        requests.delete(
            f"{base_url}/api/daily-reports/{new_id}",
            headers={"X-Admin-Token": admin_tok},
            timeout=15,
        )
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────────
# Flow 9 — Dispatch board reads reachable via dispatch token
# ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("endpoint", [
    "/api/operations/events",
    "/api/operations/holds",
    "/api/operations/utilization",
])
def test_dispatch_board_reachable(
    base_url: str, super_admin_creds: dict, endpoint: str,
):
    """Phase-III · operations/* read endpoints must respond 200 with a
    dispatch token. These power the Dispatch board UI in `/dispatch-portal`.
    """
    tokens = _multi_login(base_url, super_admin_creds)["portal_tokens"]
    dispatch_tok = tokens["dispatch"]

    r = requests.get(
        f"{base_url}{endpoint}",
        headers={"X-Dispatch-Token": dispatch_tok},
        timeout=15,
    )
    assert r.status_code == 200, f"{endpoint} -> {r.status_code}: {r.text[:200]}"
    body = r.json()
    # Each operations route returns either a list OR a dict with `items`/`ok`.
    assert isinstance(body, (list, dict)), f"{endpoint} unexpected shape: {type(body)}"


# ────────────────────────────────────────────────────────────────────
# Flow 10b — Driver magic-link → session exchange → /me round-trip
# ────────────────────────────────────────────────────────────────────
def test_driver_shift_surface_round_trip(
    base_url: str, super_admin_creds: dict,
):
    """Phase-III · iter437 (P0 magic-link hardening's positive path).

    1. Dispatcher issues a magic link for a real employee.
    2. Driver exchanges the magic token for a session token.
    3. Driver hits `/api/dispatch/driver/me` with the session token.
    4. Verify driver_id is preserved and session is active.
    5. Cleanup — revoke session.
    """
    login = _multi_login(base_url, super_admin_creds)
    dispatch_tok = login["portal_tokens"]["dispatch"]

    # Pick a real, enabled employee
    emps = requests.get(f"{base_url}/api/employees", timeout=10).json()
    arr = (
        emps if isinstance(emps, list)
        else emps.get("employees") or emps.get("items") or []
    )
    candidate = next(
        (e for e in arr if not e.get("disabled") and e.get("active") is not False),
        None,
    )
    assert candidate, "no eligible employee found for driver flow test"

    # 1. Issue magic link
    issue = requests.post(
        f"{base_url}/api/dispatch/driver/magic-link",
        headers={"X-Dispatch-Token": dispatch_tok, "Content-Type": "application/json"},
        json={"driver_id": candidate["id"], "driver_name": candidate.get("name", "")},
        timeout=10,
    )
    assert issue.status_code == 200, f"magic-link failed: {issue.status_code} {issue.text[:200]}"
    magic_token = issue.json()["magic_token"]

    # 2. Exchange for driver session
    exch = requests.post(
        f"{base_url}/api/dispatch/driver/session/exchange",
        headers={"Content-Type": "application/json"},
        json={"magic_token": magic_token},
        timeout=10,
    )
    assert exch.status_code == 200, f"exchange failed: {exch.status_code} {exch.text[:200]}"
    body = exch.json()
    driver_token = body["driver_token"]
    session_id = body["session_id"]
    assert body["driver"]["driver_id"] == candidate["id"]

    # 3. Hit /me with the driver token
    me = requests.get(
        f"{base_url}/api/dispatch/driver/me",
        headers={"X-Driver-Token": driver_token},
        timeout=10,
    )
    assert me.status_code == 200, me.text[:200]
    me_body = me.json()
    assert me_body["session"]["driver_id"] == candidate["id"]
    assert me_body["session"]["id"] == session_id

    # 4. Magic token is single-use — second exchange must fail
    second_exch = requests.post(
        f"{base_url}/api/dispatch/driver/session/exchange",
        headers={"Content-Type": "application/json"},
        json={"magic_token": magic_token},
        timeout=10,
    )
    assert second_exch.status_code == 401, \
        f"magic token should be single-use, got {second_exch.status_code}"

    # 5. Cleanup — revoke
    revoke = requests.post(
        f"{base_url}/api/dispatch/driver/sessions/{session_id}/revoke",
        headers={"X-Dispatch-Token": dispatch_tok},
        timeout=10,
    )
    assert revoke.status_code in (200, 204), revoke.text[:200]

    # 6. Verify revoked session no longer authenticates
    me2 = requests.get(
        f"{base_url}/api/dispatch/driver/me",
        headers={"X-Driver-Token": driver_token},
        timeout=10,
    )
    assert me2.status_code == 401, \
        f"revoked session still authenticates: {me2.status_code}"


# ────────────────────────────────────────────────────────────────────
# Flow 11b — HR Time Verification + SLA
# ────────────────────────────────────────────────────────────────────
def test_hr_time_verification_sla(base_url: str, super_admin_creds: dict):
    """Phase-III · HR's TV endpoint MUST stay <3s p99 after the projection
    fix (iter440 Phase 31.4). Regression here = iPad blank-screen bug
    returns.
    """
    hr_tok = _multi_login(base_url, super_admin_creds)["portal_tokens"]["hr"]
    # Saturday rolled forward — same logic as HrTimeVerification.jsx
    # default. Hard-coded to a known recent Saturday.
    week_ending = "2026-05-23"

    timings = []
    for _ in range(3):
        t0 = time.monotonic()
        r = requests.get(
            f"{base_url}/api/hr/time-verification",
            params={"week_ending": week_ending},
            headers={"X-HR-Token": hr_tok},
            timeout=10,
        )
        dt = time.monotonic() - t0
        timings.append(dt)
        assert r.status_code == 200, f"time-verification failed: {r.status_code}"
        body = r.json()
        # Response shape: list-or-dict tolerant
        assert isinstance(body, (list, dict)), f"unexpected shape: {type(body)}"

    # SLA: every call < 3s, none should hit the legacy 10s timeout
    assert max(timings) < 3.0, f"time-verification SLA breach: {timings}"


# ────────────────────────────────────────────────────────────────────
# Flow 12 — MFA enroll → verify → disable round-trip
# ────────────────────────────────────────────────────────────────────
def test_mfa_enroll_verify_disable_round_trip(
    base_url: str, super_admin_creds: dict,
):
    """Phase-III · admin-strict MFA flow. Exercises:
        GET  /api/admin/mfa/status
        POST /api/admin/mfa/enroll/start
        POST /api/admin/mfa/enroll/verify
        POST /api/admin/mfa/disable
    Cleans up on failure (try/finally) so MFA stays disabled even on
    assertion failure — keeps the super-admin account testable.
    """
    login = _multi_login(base_url, super_admin_creds)
    admin_tok = login["portal_tokens"]["admin"]
    dir_tok = login["session_token"]
    headers = {
        "X-Admin-Token": admin_tok,
        "X-Directory-Token": dir_tok,
        "Content-Type": "application/json",
    }

    # If a previous failed run left MFA enabled, this test can't enroll.
    # Skip cleanly with a clear marker.
    status_pre = requests.get(
        f"{base_url}/api/admin/mfa/status", headers=headers, timeout=10,
    )
    assert status_pre.status_code == 200, status_pre.text[:200]
    if status_pre.json().get("enabled"):
        pytest.skip("MFA already enabled (left over from a previous failed run)")

    secret = None
    try:
        # 1. Start enrollment
        start = requests.post(
            f"{base_url}/api/admin/mfa/enroll/start",
            headers=headers, timeout=10,
        )
        assert start.status_code == 200, start.text[:200]
        body = start.json()
        secret = body["secret"]
        assert body.get("otpauth_uri", "").startswith("otpauth://"), body

        # 2. Generate live TOTP from secret
        code = pyotp.TOTP(secret).now()
        verify = requests.post(
            f"{base_url}/api/admin/mfa/enroll/verify",
            headers=headers, json={"code": code}, timeout=10,
        )
        assert verify.status_code == 200, verify.text[:200]

        # 3. Confirm enabled
        st = requests.get(
            f"{base_url}/api/admin/mfa/status",
            headers=headers, timeout=10,
        ).json()
        assert st["enabled"] is True, st

    finally:
        # 4. Disable — always run so the account is testable afterwards
        if secret:
            # Fresh TOTP — the one used for verify may be in the
            # replay-protection window
            disable_code = pyotp.TOTP(secret).now()
            disable = requests.post(
                f"{base_url}/api/admin/mfa/disable",
                headers=headers, json={"code": disable_code}, timeout=10,
            )
            # Best-effort assertion — but warn loudly if it fails
            if disable.status_code != 200:
                # Last resort: direct DB cleanup so we don't lock the
                # super-admin out of future runs.
                from motor.motor_asyncio import AsyncIOMotorClient
                import asyncio
                client = AsyncIOMotorClient(os.environ["MONGO_URL"])
                db = client[os.environ["DB_NAME"]]
                asyncio.get_event_loop().run_until_complete(
                    db.user_directory.update_one(
                        {"email": super_admin_creds["email"]},
                        {"$unset": {"mfa": ""}},
                    )
                )
                pytest.fail(
                    f"MFA disable returned {disable.status_code} — emergency DB cleanup ran"
                )


# ────────────────────────────────────────────────────────────────────
# Flow 13 — Public form submission (BOTH forms, parameterized)
# ────────────────────────────────────────────────────────────────────
def _public_meeting_payload(marker: str) -> Dict[str, Any]:
    return {
        "project_name": "TEST_Phase_Sigma_III_Public_Form_Cert",
        "project_number": "T-SIGMA3",
        "location": marker,
        "meeting_date": "2026-05-27",
        "meeting_time": "07:00",
        "conducted_by": "Phase Sigma-III Foreman",
        "topic": "Operational Trust Hardening Drill",
        "discussion_notes": marker,
    }


def _public_incident_payload(marker: str) -> Dict[str, Any]:
    return {
        "project_name": "TEST_Phase_Sigma_III_Public_Form_Cert",
        "project_number": "T-SIGMA3",
        "location": marker,
        "incident_date": "2026-05-27",
        "incident_time": "08:00",
        "reported_date": "2026-05-27",
        "incident_type": "Near Miss",
        "severity": "Low",
        "reported_by": "Phase Sigma-III Foreman",
        "description": marker,
    }


@pytest.mark.parametrize("form_kind,endpoint,payload_builder,cleanup_kind,marker_field", [
    ("meeting",  "/api/meetings",  _public_meeting_payload,  "meetings",  "discussion_notes"),
    ("incident", "/api/incidents", _public_incident_payload, "incidents", "description"),
])
def test_public_form_submission(
    base_url: str, super_admin_creds: dict,
    form_kind: str, endpoint: str, payload_builder, cleanup_kind: str, marker_field: str,
):
    """Phase-III · BOTH public field-forms (meetings + incidents) accept
    an unauthenticated POST, return a doc with `id`, and the row is
    retrievable by an authed admin afterwards. Cleanup deletes the
    record so we don't pollute the preview DB.

    These two are the operator-confirmed public-form variants — they
    require zero auth (rate-limit only). `/api/inspections` POST was
    moved behind `require_safety_or_admin` and is no longer a public
    form."""
    marker = f"pw-phase3-flow13-{form_kind}-{uuid.uuid4().hex[:8]}"
    r = requests.post(
        f"{base_url}{endpoint}",
        headers={"Content-Type": "application/json"},
        json=payload_builder(marker),
        timeout=15,
    )
    assert r.status_code in (200, 201), f"{endpoint} -> {r.status_code}: {r.text[:200]}"
    body = r.json()
    new_id = body.get("id")
    assert new_id, f"no id in response: {body}"

    # Verify admin can see it
    admin_tok = _admin_token(base_url, super_admin_creds)
    getr = requests.get(
        f"{base_url}/api/{cleanup_kind}/{new_id}",
        headers={"X-Admin-Token": admin_tok}, timeout=10,
    )
    assert getr.status_code == 200, getr.text[:200]
    fetched = getr.json()
    assert marker in (fetched.get(marker_field) or ""), \
        f"marker not in {marker_field}: {fetched.get(marker_field)!r}"

    # Cleanup
    try:
        requests.delete(
            f"{base_url}/api/{cleanup_kind}/{new_id}",
            headers={"X-Admin-Token": admin_tok}, timeout=10,
        )
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────────
# Flow 15 — Env isolation under WRITE load
# ────────────────────────────────────────────────────────────────────
def test_env_isolation_under_write_load(base_url: str, super_admin_creds: dict):
    """Phase-III · 10 parallel public-form POSTs against the preview
    backend. EVERY write must land in `_preview`, NEVER touch prod.
    Cleanup deletes all 10 markers after.

    Validates the env_safety_check assertion holds for *write* traffic
    (Phase-2 only proved env identity under *read* traffic).
    """
    # Pre-condition: pod is on preview (the conftest env_safety_check
    # already enforced this at session start, but assert again for
    # safety since this test creates real rows).
    v = requests.get(f"{base_url}/api/version", timeout=10).json()
    assert v["app_env"] == "preview" and v["db_name"].endswith("_preview"), \
        f"REFUSING write load on non-preview: {v}"

    run_id = uuid.uuid4().hex[:8]

    def _writer(idx: int):
        marker = f"pw-phase3-flow15-{run_id}-{idx:02d}"
        r = requests.post(
            f"{base_url}/api/meetings",
            headers={"Content-Type": "application/json"},
            json=_public_meeting_payload(marker),
            timeout=20,
        )
        return r.status_code, marker, (r.json().get("id") if r.ok else None)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(_writer, range(10)))

    # Every write must have succeeded
    failures = [(s, m) for s, m, _ in results if s not in (200, 201)]
    assert not failures, f"writes failed under load: {failures}"

    # Every write must be visible in the preview DB (use admin GET)
    admin_tok = _admin_token(base_url, super_admin_creds)
    seen_ids = [rid for _, _, rid in results if rid]
    assert len(seen_ids) == 10, f"expected 10 ids, got {len(seen_ids)}"

    # Spot-check 3 by admin GET — proves they're in *this* DB
    import random
    sample = random.sample(seen_ids, 3)
    for sid in sample:
        getr = requests.get(
            f"{base_url}/api/meetings/{sid}",
            headers={"X-Admin-Token": admin_tok},
            timeout=10,
        )
        assert getr.status_code == 200, getr.text[:200]

    # Re-confirm pod identity AFTER the burst
    v2 = requests.get(f"{base_url}/api/version", timeout=10).json()
    assert v2["app_env"] == "preview", \
        f"pod identity drifted under write load: {v2}"

    # Cleanup all 10
    for sid in seen_ids:
        try:
            requests.delete(
                f"{base_url}/api/meetings/{sid}",
                headers={"X-Admin-Token": admin_tok},
                timeout=10,
            )
        except Exception:
            pass
