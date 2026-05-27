"""iter440 · P0 field-incident · Daily Report draft loss · backend telemetry.

Locks the behavioural contract for the new /api/draft-telemetry route:
  * 401 without portal token
  * Accepts batches with any portal token
  * Idempotent on eventId (duplicate insert → deduplicated++)
  * Rejects oversized batches (>50 events) and meta payloads
  * Admin-only /recent debug feed
  * Health endpoint returns ok + recent_events_60s

Reference: routes/draft_telemetry.py + P0_REMEDIATION_PLAN.md §2.11.
"""
from __future__ import annotations

import os
import time
import uuid

import requests
from dotenv import dotenv_values

BACKEND_ENV = dotenv_values("/app/backend/.env")


def _strip(v):
    return (v or "").strip().strip('"').strip("'")


def _admin_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("ADMIN_PASSWORD"))
    assert pw, "ADMIN_PASSWORD missing from backend/.env"
    r = requests.post(
        f"{base_url}/api/admin/login",
        json={"password": pw},
        timeout=10,
    )
    r.raise_for_status()
    tok = r.json().get("token")
    assert tok, f"login response missing token: {r.text}"
    return tok


def _ev(event_id: str, event: str = "draft.write.ok", form_key: str = "daily-report-new", meta=None):
    return {
        "eventId": event_id,
        "event": event,
        "actorId": "d.test-actor",
        "deviceId": "d.test-device-001",
        "formKey": form_key,
        "ts": int(time.time() * 1000),
        "meta": meta or {"trigger": "debounce", "payloadBytes": 1024},
    }


def test_draft_telemetry_health_unauth_401(base_url: str):
    # Pass an explicit empty X-Admin-Token to bypass the conftest
    # auto-auth monkey-patch (which uses headers.setdefault). The
    # backend sees an empty token → 401.
    r = requests.get(
        f"{base_url}/api/draft-telemetry/health",
        headers={"X-Admin-Token": ""},
        timeout=10,
    )
    assert r.status_code == 401, r.text


def test_draft_telemetry_health_with_token(base_url: str):
    tok = _admin_token(base_url)
    r = requests.get(
        f"{base_url}/api/draft-telemetry/health",
        headers={"X-Admin-Token": tok},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    assert isinstance(body.get("recent_events_60s"), int)


def test_draft_telemetry_post_accepts_batch(base_url: str):
    tok = _admin_token(base_url)
    batch = [_ev(f"pw-{uuid.uuid4().hex[:16]}") for _ in range(3)]
    r = requests.post(
        f"{base_url}/api/draft-telemetry",
        headers={"X-Admin-Token": tok, "Content-Type": "application/json"},
        json={"batch": batch},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("received") == 3
    assert body.get("deduplicated") == 0


def test_draft_telemetry_dedupes_same_event_id(base_url: str):
    tok = _admin_token(base_url)
    eid = f"pw-dedupe-{uuid.uuid4().hex[:16]}"
    headers = {"X-Admin-Token": tok, "Content-Type": "application/json"}
    r1 = requests.post(
        f"{base_url}/api/draft-telemetry",
        headers=headers, json={"batch": [_ev(eid)]}, timeout=10,
    )
    assert r1.status_code == 200
    assert r1.json()["received"] == 1
    r2 = requests.post(
        f"{base_url}/api/draft-telemetry",
        headers=headers, json={"batch": [_ev(eid)]}, timeout=10,
    )
    assert r2.status_code == 200
    assert r2.json()["received"] == 0
    assert r2.json()["deduplicated"] == 1


def test_draft_telemetry_unknown_event_rejected(base_url: str):
    tok = _admin_token(base_url)
    bad = _ev(f"pw-bad-{uuid.uuid4().hex[:8]}", event="draft.NOT_ALLOWED")
    r = requests.post(
        f"{base_url}/api/draft-telemetry",
        headers={"X-Admin-Token": tok, "Content-Type": "application/json"},
        json={"batch": [bad]},
        timeout=10,
    )
    assert r.status_code in (400, 422), r.text


def test_draft_telemetry_oversized_batch_rejected(base_url: str):
    tok = _admin_token(base_url)
    huge = [_ev(f"pw-huge-{i}-{uuid.uuid4().hex[:8]}") for i in range(60)]
    r = requests.post(
        f"{base_url}/api/draft-telemetry",
        headers={"X-Admin-Token": tok, "Content-Type": "application/json"},
        json={"batch": huge},
        timeout=10,
    )
    assert r.status_code in (400, 422), r.text


def test_draft_telemetry_unauth_post_401(base_url: str):
    # Empty X-Admin-Token bypasses the conftest auto-auth monkey-patch.
    r = requests.post(
        f"{base_url}/api/draft-telemetry",
        headers={"X-Admin-Token": "", "Content-Type": "application/json"},
        json={"batch": [_ev(f"pw-{uuid.uuid4().hex[:8]}")]},
        timeout=10,
    )
    assert r.status_code == 401


def test_draft_telemetry_recent_admin_only(base_url: str):
    tok = _admin_token(base_url)
    r = requests.get(
        f"{base_url}/api/draft-telemetry/recent",
        headers={"X-Admin-Token": tok},
        params={"formKey": "daily-report-new", "limit": 5},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    for item in body["items"]:
        assert "_id" not in item, "MongoDB _id must NEVER be returned"
        assert "eventId" in item


def test_draft_telemetry_recent_unauth_rejected(base_url: str):
    # Empty X-Admin-Token bypasses the conftest auto-auth monkey-patch.
    r = requests.get(
        f"{base_url}/api/draft-telemetry/recent",
        headers={"X-Admin-Token": ""},
        timeout=10,
    )
    # No admin token → either 401 (no token) or 403 (wrong scope).
    assert r.status_code in (401, 403), r.text
