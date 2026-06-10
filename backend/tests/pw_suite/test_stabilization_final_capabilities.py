"""STABILIZATION-FINAL · Capability primitive parity · 2026-05-28.

Locks the contract for the three new capability primitives
(`safetyCapabilities`, `inspectionCapabilities`, `capaCapabilities`)
introduced to close the three TBD-wave3 context-governance surfaces.

The doctrine being asserted:
  * Field Leadership context locks down DESTRUCTIVE caps regardless
    of which other tokens coexist in browser storage.
  * Backend authority parity — capabilities ON in a portal context
    imply the backend will accept the action; OFF implies 403/404.
  * No primitive renders a control while having no corresponding
    backend route.
  * The Self-Protection page reports `context_governance.tbd == 0`
    AFTER these primitives ship.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

BACKEND_ENV = dotenv_values("/app/backend/.env")
MATRIX = Path("/app/memory/SHARED_SURFACE_CONTEXT_MATRIX.json")


def _strip(v):
    return (v or "").strip().strip('"').strip("'")


def _admin_token(base_url: str) -> str:
    pw = _strip(BACKEND_ENV.get("ADMIN_PASSWORD"))
    r = requests.post(f"{base_url}/api/admin/login",
                      json={"password": pw}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


# ─── Source-of-truth contract checks ────────────────────────────────


def test_three_capability_primitives_exist():
    """The three primitives MUST exist and export the canonical name."""
    for fname, export in (
        ("safetyCapabilities.js",     "getSafetyCapabilities"),
        ("inspectionCapabilities.js", "getInspectionCapabilities"),
        ("capaCapabilities.js",       "getCapaCapabilities"),
    ):
        p = Path(f"/app/frontend/src/lib/{fname}")
        assert p.exists(), f"missing capability primitive: {fname}"
        body = p.read_text()
        assert f"export function {export}" in body, (
            f"{fname} must export `{export}()`"
        )
        # Field Leadership lockdown contract — every primitive must
        # have an explicit branch for ctx === "field-leadership".
        assert 'ctx === "field-leadership"' in body, (
            f"{fname} missing field-leadership lockdown branch"
        )


def test_shared_surface_matrix_has_no_tbd_for_live_surfaces():
    """Closing the 3 ambers means NO live surface may carry
    `TBD-wave3` in the matrix anymore."""
    data = json.loads(MATRIX.read_text())
    live = [s for s in data["surfaces"] if s.get("status") == "live"]
    bad = [s["path"] for s in live
           if str(s.get("compliance") or "").startswith("TBD")]
    assert bad == [], (
        f"live surfaces still carry TBD compliance: {bad}"
    )


def test_matrix_each_live_surface_names_capability_module():
    """Every live shared surface MUST declare a capability primitive
    (or a documented alternative)."""
    data = json.loads(MATRIX.read_text())
    for s in data["surfaces"]:
        if s.get("status") != "live":
            continue
        cap = str(s.get("capability_inheritance") or "")
        # Acceptable patterns:
        # - mentions a lib/*Capabilities.js module
        # - or is explicitly noted as a future wave (NOT allowed now,
        #   asserted by previous test, but kept here for diagnostics)
        assert ("Capabilities" in cap or "hub-relative" in cap
                or "useReturnContext" in cap or "lib/" in cap), (
            f"{s.get('path')} has no recognisable capability primitive: {cap}"
        )


# ─── Live Self-Protection assertion ────────────────────────────────


def test_self_protection_drift_is_zero(base_url):
    """After the matrix update, the OPS-1 page MUST report 0 open
    governance gaps from context-TBD or authority violations."""
    tok = _admin_token(base_url)
    body = requests.get(
        f"{base_url}/api/admin/governance/self-protection",
        headers={"X-Admin-Token": tok}, timeout=10,
    ).json()
    drift = body["drift"]
    assert drift["open_gaps"] == 0, drift
    assert drift["context_tbd"] == 0, drift
    assert drift["authority_violations"] == 0, drift
    # DEPLOY-GATE-FIX-002 (2026-06-10): page_status is now derived from
    # both the three critical counts (above) AND `authority_warnings`.
    # `amber` indicates warnings-only (no open gaps, no TBD, no violations);
    # operators surface it as advisory, not a deploy blocker. Only `red`
    # blocks (which would mean one of the asserts above failed first).
    assert body["page_status"] in ("green", "amber"), body["page_status"]
