"""TRACK 15.83B · Production Excellence Completion Sweep regression.

Locks the Track 15.83B deliverables so they cannot silently regress:

1. Backend canonical operator transfer visibility
   * `lib/transfer_visibility.py` — pure helpers used by both
     `/api/asset-transfers?audience=operator` and
     `/api/operations/transfers?audience=operator`.
   * `is_operator_visible_transfer(record)` and
     `filter_operator_visible_transfers(records)`.
2. Live wiring on `/api/operations/transfers?audience=operator`
   returns `{items, total, audience, suppressed_count}` and suppresses
   AUDIT-2 / AUDIT residue.
3. Default (no audience) calls still return the legacy flat-list
   contract — admin/audit history is NEVER silently filtered.
4. Stale production-facing copy is removed (`Admin-gated for now`,
   `iter124` Dispatch header noise).
5. Frontend Dispatch landing requests the canonical audience.
6. Preview/demo routes (DesignSystemDemo, V2*, *V2Preview) stay
   mounted under `/_internal/...` only — never on operator nav.
7. Earlier Track parity tests (15.81 Admin RBAC + 15.82B Roll-Off +
   15.83 map CSS + transfer filter) still pass.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values


FRONTEND_SRC = Path("/app/frontend/src")
APP_JS = FRONTEND_SRC / "App.js"
# TRACK 22.5A · re-anchor to current routing shell.
APP_ROUTES = FRONTEND_SRC / "app" / "routing" / "AppRoutes.jsx"
ADMIN_DISPATCH = FRONTEND_SRC / "pages/admin/AdminDispatch.jsx"
DISPATCH_HUB = FRONTEND_SRC / "pages/DispatchHub.jsx"
BACKEND_LIB = Path("/app/backend/lib/transfer_visibility.py")
OPERATIONS_PY = Path("/app/backend/routes/operations.py")
ASSET_TRANSFERS_PY = Path("/app/backend/routes/asset_transfers.py")

FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BASE = (os.environ.get("REACT_APP_BACKEND_URL") or FRONTEND_ENV.get("REACT_APP_BACKEND_URL") or "").rstrip("/")

SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── Backend canonical helper (unit) ───────────────────────────────


def test_transfer_visibility_module_exists():
    assert BACKEND_LIB.exists(), (
        "Track 15.83B regression: backend/lib/transfer_visibility.py "
        "must exist (canonical operator filter)."
    )


def test_is_operator_visible_transfer_filters_audit_2_pattern():
    from lib.transfer_visibility import is_operator_visible_transfer
    # Exact production-reported pattern.
    assert is_operator_visible_transfer(
        {"to_project_number": "AUDIT-2", "status": "Cancelled"}
    ) is False
    assert is_operator_visible_transfer(
        {"from_project_number": "AUDIT-2"}
    ) is False
    # All documented project markers.
    for marker in [
        "AUDIT", "AUDIT-1", "AUDIT_3", "TEST", "TEST-1",
        "DEMO", "DEMO-7", "VALIDATION", "VAL-9",
        "SMOKE", "SMOKE-2", "SAMPLE", "SAMPLE-1",
    ]:
        assert is_operator_visible_transfer(
            {"to_project_number": marker}
        ) is False, marker
        assert is_operator_visible_transfer(
            {"from_project_number": marker}
        ) is False, marker


def test_is_operator_visible_transfer_filters_reason_signals():
    from lib.transfer_visibility import is_operator_visible_transfer
    cases = [
        {"reason": "deployment validation cancel"},
        {"reason": "Smoke test cleanup"},
        {"reason": "AUDIT pass — self-test residue"},
        {"decision_reason": "validation run"},
        {"reason": "test fixture"},
        {"reason": "seed validation re-run"},
    ]
    for c in cases:
        assert is_operator_visible_transfer(c) is False, c


def test_is_operator_visible_transfer_filters_source_signals():
    from lib.transfer_visibility import is_operator_visible_transfer
    cases = [
        {"created_by": "audit-bot"},
        {"requested_by": "smoke-runner"},
        {"source_system": "validator"},
        {"audit_marker": "AUDIT"},
        {"record_type": "audit"},
        {"transfer_type": "fixture"},
    ]
    for c in cases:
        assert is_operator_visible_transfer(c) is False, c


def test_is_operator_visible_transfer_filters_explicit_flags():
    from lib.transfer_visibility import is_operator_visible_transfer
    for flag in ("is_audit", "is_validation", "is_test"):
        assert is_operator_visible_transfer({flag: True}) is False, flag


def test_is_operator_visible_transfer_preserves_real_records():
    from lib.transfer_visibility import is_operator_visible_transfer
    real = [
        {"to_project_number": "12345", "status": "Submitted"},
        {"from_project_number": "EDGE-001", "status": "Approved"},
        {"to_project_number": "PORT-3142", "reason": "weekly redeploy"},
        {"status": "Cancelled", "reason": "Customer rescheduled"},
        {"to_project_number": "", "status": "Submitted"},
    ]
    for r in real:
        assert is_operator_visible_transfer(r) is True, r


def test_filter_helper_returns_suppressed_count():
    from lib.transfer_visibility import filter_operator_visible_transfers
    records = [
        {"to_project_number": "AUDIT-2", "status": "Cancelled"},
        {"to_project_number": "12345", "status": "Submitted"},
        {"to_project_number": "TEST-9"},
        {"to_project_number": "EDGE-001", "status": "Approved"},
    ]
    visible, suppressed = filter_operator_visible_transfers(records)
    assert suppressed == 2
    assert len(visible) == 2
    # Real records survived in original order.
    assert visible[0]["to_project_number"] == "12345"
    assert visible[1]["to_project_number"] == "EDGE-001"


# ─── Backend endpoint contracts (static · file-content) ───────────


def test_operations_transfers_supports_audience_query():
    src = _read(OPERATIONS_PY)
    # Audience query parameter is wired into the signature.
    assert "audience: Optional[str] = Query" in src, (
        "Track 15.83B regression: /api/operations/transfers must accept "
        "an `audience` query parameter."
    )
    # Backend imports the canonical helper (not duplicating regex).
    assert "from lib.transfer_visibility import" in src, (
        "Track 15.83B regression: operations.py must import the "
        "canonical transfer_visibility helper."
    )
    # Operator audience returns the metadata envelope.
    assert '"audience": "operator"' in src
    assert '"suppressed_count"' in src


def test_asset_transfers_supports_audience_query():
    src = _read(ASSET_TRANSFERS_PY)
    assert "audience: Optional[str] = Query" in src, (
        "Track 15.83B regression: /api/asset-transfers must accept "
        "the `audience` query parameter so any client (dispatch, "
        "native, future mobile) can opt into operator filtering."
    )
    assert "from lib.transfer_visibility import" in src
    assert '"audience": "operator"' in src
    assert '"suppressed_count"' in src


# ─── Stale copy cleanup (Defect: production-facing scaffolding) ────


def test_dispatch_landing_does_not_show_admin_gated_copy():
    src = _read(ADMIN_DISPATCH)
    forbidden = [
        "Admin-gated for now",
        "admin-gated for now",
        "dedicated dispatch users",
        "ship in the next pass",
    ]
    for needle in forbidden:
        assert needle not in src, (
            f"Track 15.83B regression: AdminDispatch.jsx still contains "
            f"the stale production-facing string {needle!r}."
        )


def test_dispatch_landing_does_not_show_iter_label():
    src = _read(ADMIN_DISPATCH)
    # The DispatchPortal banner block must not surface internal
    # iteration labels (iter124, iter###) to the operator.
    banner_section = src.split("Dispatch Portal")[1][:600] if "Dispatch Portal" in src else ""
    assert not re.search(r"iter\d{2,3}\b", banner_section), (
        "Track 15.83B regression: Dispatch banner header must not show "
        "internal iteration labels (e.g. `iter124`) to operators."
    )


# ─── Frontend uses canonical backend audience ──────────────────────


def test_dispatch_transfers_tab_uses_operator_audience():
    src = _read(ADMIN_DISPATCH)
    assert "audience=operator" in src, (
        "Track 15.83B regression: DispatchTransfersTab must request the "
        "canonical `?audience=operator` endpoint contract so the backend "
        "filter applies."
    )


# ─── Preview / demo route hardening ────────────────────────────────


def test_preview_routes_mounted_only_under_internal_namespace():
    src = (_read(APP_JS) + "\n" + _read(APP_ROUTES))
    for needle in [
        "DesignSystemDemo", "PmV2Preview", "HrV2Preview",
        "V2Index", "V2Compare",
    ]:
        assert needle in src, f"{needle} expected in App.js"
    # All `_internal/...` routes must be wrapped in the `D(...)` dev guard.
    internal_lines = [
        ln for ln in src.splitlines()
        if "/_internal/" in ln and "<Route" in ln
    ]
    assert internal_lines, "No /_internal routes found — check Track 15.83B route hardening"
    for ln in internal_lines:
        assert "D(" in ln or "RequireDev" in ln, (
            f"Track 15.83B regression: dev-only route must be wrapped "
            f"in `D(...)` / RequireDev — offending line: {ln.strip()}"
        )
    # No demo / v2-preview / design-system route may be reachable from a
    # non `_internal` path.
    bad = re.findall(
        r'<Route\s+path="(/(?:design-system|v2-(?:compare|index)|pm-v2-preview|hr-v2-preview)[^"]*)"',
        src,
    )
    assert not bad, (
        f"Track 15.83B regression: preview/demo routes leaked into "
        f"production navigation: {bad}"
    )


# ─── Parity preservation (15.81 / 15.82B / 15.83) ──────────────────


def test_admin_operations_map_route_still_admin_only():
    src = (_read(APP_JS) + "\n" + _read(APP_ROUTES))
    assert re.search(
        r'<Route\s+path="/operations-map"\s+element=\{A\(<OperationsMapPage\s*/>\)\}',
        src,
    ), "Track 15.81 parity broken by 15.83B"


def test_roll_off_tile_still_on_dispatch_hub():
    src = _read(DISPATCH_HUB)
    assert 'testId="ds-issue-roll-off"' in src, "Track 15.82B parity broken"
    assert 'issueWork("Roll-Off")' in src


# ─── Live endpoint smoke (uses preview backend) ────────────────────


@pytest.fixture(scope="module")
def super_admin_tokens() -> dict:
    if not BASE:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    tokens = data.get("portal_tokens") or {}
    tokens["session_token"] = data.get("session_token")
    return tokens


def test_operations_transfers_default_returns_legacy_shape(super_admin_tokens):
    admin = super_admin_tokens.get("admin")
    assert admin
    r = requests.get(
        f"{BASE}/api/operations/transfers?limit=5",
        headers={"X-Admin-Token": admin, "X-Directory-Token": super_admin_tokens.get("session_token", "")},
        timeout=45,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, list), (
        "Track 15.83B contract: default (no audience) MUST still return "
        "the legacy flat list. Got: {0!r}".format(type(body))
    )


def test_operations_transfers_operator_audience_returns_envelope(super_admin_tokens):
    admin = super_admin_tokens.get("admin")
    assert admin
    r = requests.get(
        f"{BASE}/api/operations/transfers?audience=operator&limit=200",
        headers={"X-Admin-Token": admin, "X-Directory-Token": super_admin_tokens.get("session_token", "")},
        timeout=45,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, dict)
    assert "items" in body
    assert "audience" in body and body["audience"] == "operator"
    assert "suppressed_count" in body
    assert isinstance(body["suppressed_count"], int)
    assert body["suppressed_count"] >= 0
    # No item in the operator-visible list may have an AUDIT-style
    # project marker (defense in depth — proves the filter ran).
    audit_rx = re.compile(
        r"^(AUDIT|TEST|DEMO|VALIDATION|VAL|SMOKE|SAMPLE)[-_]?\d*$",
        re.IGNORECASE,
    )
    leaks = []
    for it in body["items"]:
        for k in ("to_project_number", "from_project_number"):
            v = it.get(k)
            if v and audit_rx.match(str(v).strip()):
                leaks.append({"id": it.get("id"), k: v})
    assert not leaks, (
        f"Track 15.83B regression: operator audience leaked AUDIT-style "
        f"records: {leaks[:5]}"
    )


def test_asset_transfers_operator_audience_smoke(super_admin_tokens):
    admin = super_admin_tokens.get("admin")
    assert admin
    r = requests.get(
        f"{BASE}/api/asset-transfers?audience=operator&limit=200",
        headers={"X-Admin-Token": admin, "X-Directory-Token": super_admin_tokens.get("session_token", "")},
        timeout=45,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, dict)
    assert body.get("audience") == "operator"
    assert "items" in body
    assert "suppressed_count" in body
