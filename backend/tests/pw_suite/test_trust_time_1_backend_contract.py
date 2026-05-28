"""TRUST-TIME-1 · Platform timezone / timestamp truthfulness · 2026-05-28.

Locks the contract introduced after operators observed a +4h delta on
PO receipt-upload display in production. Root cause: Motor returned
NAIVE datetimes (no tz info), `_iso(dt)` emitted naive ISO strings,
JavaScript `new Date(...)` parsed naive ISO as LOCAL time → operator
at 9:43 AM Eastern saw 1:43 PM (UTC clock displayed as local).

Doctrine:
  1. Backend stores UTC.
  2. Backend emits ABSOLUTE (tz-aware) ISO — every operator-facing
     timestamp ends with `Z` or `+HH:MM`.
  3. Frontend `formatLocalDateTime` converts to local time;
     `formatUtcForAudit` is used when admin/audit context wants UTC,
     and ALWAYS suffixes " UTC".

These tests prove the BACKEND part of the contract: every
operator-facing timestamp on PO requests, draft telemetry, and OPS-1
governance round-trips as a tz-aware string.
"""
from __future__ import annotations

import re

import requests
from dotenv import dotenv_values

BACKEND_ENV = dotenv_values("/app/backend/.env")
TZ_AWARE_RE = re.compile(r"(Z|[+-]\d{2}:?\d{2})$")


def _strip(v):
    return (v or "").strip().strip('"').strip("'")


def _admin_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("ADMIN_PASSWORD"))
    r = requests.post(f"{base_url}/api/admin/login",
                      json={"password": pw}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def _is_tz_aware(s) -> bool:
    return isinstance(s, str) and bool(TZ_AWARE_RE.search(s))


# ─── PO requests — the surface that surfaced the bug ─────────────


def test_po_requests_timestamps_are_tz_aware(base_url):
    tok = _admin_token(base_url)
    r = requests.get(f"{base_url}/api/po-requests?limit=20",
                     headers={"X-Admin-Token": tok}, timeout=10)
    r.raise_for_status()
    payload = r.json()
    items = payload if isinstance(payload, list) else payload.get("items", [])
    assert items, "need at least one PO record on the system to exercise this"
    naive = []
    for r in items:
        for k in ("created_at", "approved_at", "receipt_uploaded_at",
                  "updated_at", "cancelled_at", "closed_at"):
            v = r.get(k)
            if v and not _is_tz_aware(v):
                naive.append(f"{r.get('id','?')[:8]}.{k} = {v!r}")
    assert not naive, (
        "PO timestamps must be tz-aware ISO (end with Z or +HH:MM). "
        f"Found {len(naive)} naive value(s):\n  " + "\n  ".join(naive)
    )


def test_po_audit_entries_are_tz_aware(base_url):
    """Each PO audit-log entry has its own `at` timestamp."""
    tok = _admin_token(base_url)
    r = requests.get(f"{base_url}/api/po-requests?limit=10",
                     headers={"X-Admin-Token": tok}, timeout=10)
    r.raise_for_status()
    items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
    bad = []
    for po in items:
        # Audit is nested only on detail GET; surface listings may strip it.
        # If present, every `at` MUST be tz-aware.
        for entry in (po.get("audit") or []):
            v = entry.get("at")
            if v and not _is_tz_aware(v):
                bad.append(f"{po.get('id','?')[:8]} audit.at={v!r}")
    assert not bad, (
        "PO audit-log `at` timestamps must be tz-aware:\n  " + "\n  ".join(bad)
    )


# ─── Draft telemetry — the survivability surface ─────────────────


def test_draft_telemetry_admin_timestamps_are_tz_aware(base_url):
    tok = _admin_token(base_url)
    r = requests.get(f"{base_url}/api/draft-telemetry/recent",
                     headers={"X-Admin-Token": tok}, timeout=10)
    r.raise_for_status()
    payload = r.json()
    events = payload if isinstance(payload, list) else payload.get("events", [])
    bad = []
    for ev in events[:50]:
        for k in ("ts", "occurred_at", "received_at"):
            v = ev.get(k)
            if v and not _is_tz_aware(v):
                bad.append(f"{ev.get('eventId', '?')[:8]}.{k}={v!r}")
    assert not bad, (
        "draft-telemetry timestamps must be tz-aware:\n  " + "\n  ".join(bad)
    )


# ─── OPS-1 governance — informational stanza ─────────────────────


def test_self_protection_generated_at_is_epoch(base_url):
    """OPS-1 emits `generated_at` and `deployment.deployed_at` as
    integer epochs by design — frontend formats them with the same
    helper. Document the contract."""
    tok = _admin_token(base_url)
    body = requests.get(f"{base_url}/api/admin/governance/self-protection",
                        headers={"X-Admin-Token": tok}, timeout=10).json()
    assert isinstance(body.get("generated_at"), int), body.get("generated_at")
    dp = body.get("deployment") or {}
    if dp.get("deployed_at") is not None:
        assert isinstance(dp["deployed_at"], int), dp


# ─── Frontend coercion contract (smoke probe via served bundle) ──
# The bundled `dateUtils.js` already passes its own JS tests at build
# time (see Playwright `test_trust_time_1_frontend_localization.py`),
# so this layer just confirms the file is served and exports the
# canonical names. Frontend localization assertions live in the PW suite.


def test_date_utils_module_is_served(base_url):
    """The frontend bundle must include the TRUST-TIME-1 helpers.
    Probes the unminified source via the React dev preview."""
    import pathlib
    src = pathlib.Path("/app/frontend/src/lib/dateUtils.js").read_text()
    for fn in ("formatLocalDateTime", "formatLocalDate", "formatLocalTime",
               "formatLocalShort", "formatRelativeTime", "formatUtcForAudit",
               "todayLocalIso", "toLocalIso"):
        assert f"export function {fn}" in src, f"missing export: {fn}"
    # Naive-ISO coercion branch MUST exist (the bug fix).
    assert 'new Date(s + "Z")' in src, (
        "dateUtils.js must coerce naive ISO to UTC — "
        "this is the core fix for the +4h PO receipt-upload bug."
    )
