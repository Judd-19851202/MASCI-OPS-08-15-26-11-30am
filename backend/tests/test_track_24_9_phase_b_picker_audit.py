"""TRACK 24.9 Phase B · Platform-wide picker audit locks.

Certifies that every cmdk / Combobox / dropdown on the platform:
  * Uses the shared `useCmdkTouchGuard` hook (cmdk risk class).
  * Loads real data from its endpoint.
  * Returns truthful projections (no PII leak on public-facing endpoints).
  * Applies auth guards where PII fields are present.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT.parent / "frontend" / "src"


def _api_url() -> str:
    fe_env = ROOT.parent / "frontend" / ".env"
    for line in fe_env.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not found")


API = _api_url() + "/api"


# ── 1. Every cmdk picker uses the shared touch-guard hook ────────
#
# When cmdk's <CommandItem> receives raw `onSelect` on iOS Safari,
# a scroll gesture can commit the wrong row. Track 24.8 fixed this
# for JobPicker; Track 24.9 Phase B promoted the fix to a shared
# hook and applied it to every cmdk consumer. If a new picker is
# added later without the guard, this test fires.


CMDK_PICKER_FILES = [
    "components/JobPicker.jsx",
    "components/TopicPicker.jsx",
    "components/team/JobTeamRosterPanel.jsx",
    "components/trench/EmployeePicker.jsx",
]


@pytest.mark.parametrize("path", CMDK_PICKER_FILES)
def test_cmdk_picker_uses_shared_touch_guard(path: str):
    src = (FRONTEND / path).read_text()
    assert "useCmdkTouchGuard" in src, (
        f"{path} uses cmdk `<CommandItem>` but does not import "
        f"`useCmdkTouchGuard`. Every cmdk picker on the platform "
        f"MUST use the shared hook to prevent Track 24.8-class "
        f"wrong-row selection on mobile scroll."
    )
    assert "commitHandlersFor" in src, (
        f"{path} imports the hook but does not spread "
        f"`commitHandlersFor(...)` onto its `<CommandItem>` — the "
        f"guard is inert without it."
    )


def test_no_orphan_cmdk_picker_files():
    """Guard against a new cmdk picker being added without landing
    on the CMDK_PICKER_FILES allowlist."""
    import subprocess
    result = subprocess.run(
        ["grep", "-rln", "CommandItem", str(FRONTEND / "components"),
         str(FRONTEND / "pages"), "--include=*.jsx"],
        capture_output=True, text=True,
    )
    hits = set()
    for line in result.stdout.splitlines():
        # Exclude the shadcn wrapper itself.
        if line.endswith("components/ui/command.jsx"):
            continue
        hits.add(str(Path(line).relative_to(FRONTEND)))
    expected = set(CMDK_PICKER_FILES)
    orphans = hits - expected
    assert not orphans, (
        f"New cmdk consumer(s) detected without touch-guard "
        f"registration in tests/test_track_24_9_phase_b_picker_audit.py "
        f"CMDK_PICKER_FILES: {orphans}. Either add the file to the "
        f"allowlist (and apply useCmdkTouchGuard) or remove cmdk usage."
    )


# ── 2. Master-lookup PII leak fixed ──────────────────────────────


def test_master_lookup_employees_requires_auth():
    """Track 24.9 Phase B P0 · closing a Track 24.1-class PII leak.

    Before Phase B: /api/master-lookup/employees was open to the
    world and returned `email` — anyone could `q=@` and enumerate
    the roster + real emails. Now: 401 without a portal token.
    """
    r = requests.get(f"{API}/master-lookup/employees?q=%40&limit=5", timeout=15)
    assert r.status_code == 401, (
        f"master-lookup/employees auth gate regressed: got {r.status_code}"
    )


def test_master_lookup_employees_works_with_admin_token():
    tok_resp = requests.post(
        f"{API}/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=45,
    )
    tok = tok_resp.json().get("portal_tokens", {}).get("admin", "")
    assert tok
    r = requests.get(
        f"{API}/master-lookup/employees?q=@&limit=5",
        headers={"X-Admin-Token": tok},
        timeout=30,
    )
    assert r.status_code == 200


def test_master_lookup_employee_by_id_requires_auth():
    r = requests.get(f"{API}/master-lookup/employees/by-id/xxx", timeout=15)
    assert r.status_code == 401


# ── 3. Every public picker endpoint used by DR V3 works ──────────


@pytest.mark.parametrize("endpoint,keys_present,pii_forbidden", [
    ("/jobs", {"project_number", "project_name"}, set()),
    ("/equipment-master", {"unit_number", "make_model"}, {"email", "phone", "ssn", "dob", "address", "salary"}),
    ("/suppliers", {"id", "name"}, {"email", "phone", "ssn", "dob"}),
    ("/hr/employee-roster/public", {"id", "name"}, {"email", "phone", "ssn", "dob", "address", "salary", "supervisor"}),
    ("/employees/competent-persons/public", {"employee_name"}, {"email", "phone", "ssn", "dob", "address"}),
    ("/trench-safety/excavations/public/asset-roster", {"asset_id"}, {"email", "phone"}),
    ("/field-leadership-roster", {"name"}, {"email", "phone", "ssn"}),
])
def test_public_picker_endpoint_no_pii(endpoint, keys_present, pii_forbidden):
    r = requests.get(f"{API}{endpoint}", timeout=15)
    assert r.status_code == 200, f"{endpoint} unexpectedly returned {r.status_code}"
    body = r.json()
    if isinstance(body, dict):
        items = body.get("items") or body.get("rows") or body.get("categories") or []
    else:
        items = body
    if not items or not isinstance(items, list) or not isinstance(items[0], dict):
        return  # nothing to audit
    row_keys = set(items[0].keys())
    # Sanity: the picker gets what it needs.
    assert row_keys & keys_present, (
        f"{endpoint} projection missing expected picker fields "
        f"{keys_present}. Got: {row_keys}"
    )
    # No PII slipped into a public projection.
    leaked = row_keys & pii_forbidden
    assert not leaked, (
        f"{endpoint} public projection leaks PII keys: {leaked}"
    )


# ── 4. Shared hook file exists + exports expected shape ──────────


def test_touch_guard_hook_present_and_exports():
    p = FRONTEND / "lib" / "useCmdkTouchGuard.js"
    assert p.exists(), "shared touch-guard hook missing"
    src = p.read_text()
    assert "export function useCmdkTouchGuard" in src
    assert "commitHandlersFor" in src
    assert "scrolledRef" in src
    assert "onPointerDown" in src
    assert "onPointerUp" in src
