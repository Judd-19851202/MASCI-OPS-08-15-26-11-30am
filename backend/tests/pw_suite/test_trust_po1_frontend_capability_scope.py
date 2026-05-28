"""TRUST-PO-1 · Frontend Capability Scope · 2026-05-28.

Proves that the UI authority leak is fully closed: even when an admin
token coexists with a Field Leadership session in browser storage
(the Super Admin scenario), the PO Requests page rendered inside the
Field Leadership portal context MUST NOT show approval controls.

Three scenarios:
  A · Admin context  · admin token only · approval block visible
  B · Leadership context · leadership token only · approval block hidden
  C · Leadership context · BOTH tokens in storage · approval block hidden
       (this is the surgical fix — the capability gate honours portal
        context, not raw token-presence.)
"""
from __future__ import annotations

import os

import pytest
import requests
from dotenv import dotenv_values

pytestmark = [pytest.mark.parametrize("viewport_name", ["desktop"], indirect=True)]

BACKEND_ENV = dotenv_values("/app/backend/.env")


def _strip(v):
    return (v or "").strip().strip('"').strip("'")


def _admin_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("ADMIN_PASSWORD"))
    r = requests.post(
        f"{base_url}/api/admin/login",
        json={"password": pw},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["token"]


def _leadership_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("LEADERSHIP_PASSWORD")) or "MASCIGC"
    r = requests.post(
        f"{base_url}/api/field-leadership/login",
        json={"password": pw},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["token"]


def _seed_pending_po(base_url: str, admin_tok: str) -> str:
    """Create a PO request as admin so the list has at least one row
    in `Submitted` status — required for the approval block to be
    visible on the approver-context test."""
    body = {
        "project_number": "26-01",
        "vendor": "PW-TRUST-PO1-CapScope",
        "description": "Capability scope regression seed",
        "estimated_amount": 175.0,
        "category": "Materials",
        "urgency": "Normal",
    }
    r = requests.post(
        f"{base_url}/api/po-requests",
        headers={"X-Admin-Token": admin_tok, "Content-Type": "application/json"},
        json=body,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["id"]


def _open_drawer_for(page, po_id: str):
    """Open the PO drawer by clicking the row corresponding to po_id."""
    row = page.locator(f'[data-testid="po-row-{po_id}"]').first
    row.wait_for(state="visible", timeout=10_000)
    row.click()
    page.wait_for_selector('[data-testid="po-drawer"]', timeout=8_000)
    # The drawer's internal `getPo(id)` call is async — without this
    # wait, the body still reads "Loading…" and the approval-block
    # check would race against the data fetch.
    page.wait_for_timeout(1500)


def _navigate_with_storage(page, base_url: str, storage: dict, portal_ctx: str | None):
    """Land on the root, seed storage, optionally set portal context,
    then navigate to /po-requests."""
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(
        """(s) => {
          for (const [k, v] of Object.entries(s.local || {})) localStorage.setItem(k, v);
          for (const [k, v] of Object.entries(s.session || {})) sessionStorage.setItem(k, v);
        }""",
        storage,
    )
    if portal_ctx:
        page.evaluate(
            "(name) => sessionStorage.setItem('masci.portal-context', name)",
            portal_ctx,
        )
    page.goto(f"{base_url}/po-requests", wait_until="domcontentloaded")
    page.wait_for_selector('[data-testid="po-requests-page"]', timeout=15_000)
    page.wait_for_timeout(1500)


# ── Scenario A — Admin context shows approval block ─────────────────


def test_admin_context_renders_approval_block(page, base_url, viewport_name):
    admin_tok = _admin_token(base_url)
    po_id = _seed_pending_po(base_url, admin_tok)
    _navigate_with_storage(
        page,
        base_url,
        storage={"local": {"masci.admin.token": admin_tok}},
        portal_ctx="admin",
    )
    _open_drawer_for(page, po_id)
    block = page.locator('[data-testid="po-approval-block"]')
    assert block.count() == 1, "approval block MUST be visible in admin context"
    assert page.locator('[data-testid="po-approve-btn"]').count() == 1
    assert page.locator('[data-testid="po-reject-btn"]').count() == 1
    assert page.locator('[data-testid="po-clarify-btn"]').count() == 1


# ── Scenario B — Leadership-only context hides approval block ───────


def test_leadership_only_context_hides_approval_block(page, base_url, viewport_name):
    admin_tok = _admin_token(base_url)
    fl_tok = _leadership_token(base_url)
    po_id = _seed_pending_po(base_url, admin_tok)
    _navigate_with_storage(
        page,
        base_url,
        storage={"session": {
            "masci.leadership.token": fl_tok,
            "masci.leadership.issued": str(int(__import__("time").time() * 1000)),
        }},
        portal_ctx="field-leadership",
    )
    _open_drawer_for(page, po_id)
    # The approval block, the Manual PO #, the Approved amount, and ALL
    # three approver buttons MUST be absent.
    assert page.locator('[data-testid="po-approval-block"]').count() == 0, (
        "AUTHORITY LEAK · approval block surfaced in Field Leadership context"
    )
    for tid in (
        "po-approve-btn", "po-reject-btn", "po-clarify-btn",
        "po-approval-manual", "po-approval-amount", "po-approval-notes",
        "po-close-btn", "po-cancel-btn",
    ):
        assert page.locator(f'[data-testid="{tid}"]').count() == 0, (
            f"AUTHORITY LEAK · {tid!r} visible in Field Leadership context"
        )


# ── Scenario C — Super Admin in FL context (BOTH tokens) ────────────


def test_super_admin_in_fl_context_hides_approval_block(page, base_url, viewport_name):
    """The original field issue: an operator holds both admin and
    leadership tokens at once (e.g., a Super Admin who's also tested
    the FL portal). The PO Requests page must respect the portal
    CONTEXT, not the union of tokens."""
    admin_tok = _admin_token(base_url)
    fl_tok = _leadership_token(base_url)
    po_id = _seed_pending_po(base_url, admin_tok)
    _navigate_with_storage(
        page,
        base_url,
        storage={
            "local": {"masci.admin.token": admin_tok},
            "session": {
                "masci.leadership.token": fl_tok,
                "masci.leadership.issued": str(int(__import__("time").time() * 1000)),
            },
        },
        portal_ctx="field-leadership",
    )
    _open_drawer_for(page, po_id)
    # The approval block must NOT surface even with the admin token
    # present in storage. This is the surgical fix.
    assert page.locator('[data-testid="po-approval-block"]').count() == 0, (
        "AUTHORITY LEAK · approval block surfaced in FL context "
        "despite admin token co-existence (UI-layer leak unfixed)"
    )
    # The submitter affordances MUST still work — receipt upload is
    # the legitimate Field Leadership post-approval action.
    # (The seed PO is Submitted, so the receipt block won't render —
    # but the form-submit / page basic actions are still available.)


# ── Scenario D — Switching contexts updates capabilities ────────────


def test_context_switch_admin_to_leadership_recomputes_caps(page, base_url, viewport_name):
    """Defensive: simulate switching from Admin into FL (e.g., the
    operator clicks the FL portal tile mid-session). After the
    portal-context flip, the next mount of /po-requests must hide
    approver controls."""
    admin_tok = _admin_token(base_url)
    fl_tok = _leadership_token(base_url)
    po_id = _seed_pending_po(base_url, admin_tok)
    # Start in admin context — confirm visible.
    _navigate_with_storage(
        page,
        base_url,
        storage={"local": {"masci.admin.token": admin_tok}},
        portal_ctx="admin",
    )
    _open_drawer_for(page, po_id)
    assert page.locator('[data-testid="po-approval-block"]').count() == 1
    page.locator('[data-testid="po-drawer"]').first.press("Escape")
    # Switch context to FL (simulate hub re-mount).
    page.evaluate(
        """(t) => {
          sessionStorage.setItem('masci.leadership.token', t);
          sessionStorage.setItem('masci.leadership.issued', String(Date.now()));
          sessionStorage.setItem('masci.portal-context', 'field-leadership');
        }""",
        fl_tok,
    )
    page.goto(f"{base_url}/po-requests", wait_until="domcontentloaded")
    page.wait_for_selector('[data-testid="po-requests-page"]', timeout=15_000)
    page.wait_for_timeout(1500)
    _open_drawer_for(page, po_id)
    assert page.locator('[data-testid="po-approval-block"]').count() == 0, (
        "context switch did not recompute capabilities · approval block "
        "still visible after admin→FL portal flip"
    )
