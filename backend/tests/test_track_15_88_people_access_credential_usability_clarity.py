"""TRACK 15.88 · People & Access Credential Usability Clarity · tests.

26 tests covering:
  * The canonical access-state helper is correct for every state.
  * The helper never returns the password hash.
  * The admin /directory list+create+update+reset endpoints return
    the derived envelope.
  * The frontend AdminAccessControlPanel consumes the helper's
    canonical strings without drift.
  * Track 15.87 behaviour is preserved.
  * The deployment gate is wired.

Pure static + unit tests — no live DB, no HTTP. Runs <100 ms.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

BACKEND = Path("/app/backend")
HELPER = BACKEND / "lib" / "directory_access_state.py"
ROUTES = BACKEND / "routes" / "auth_directory_routes.py"
PANEL = BACKEND.parent / "frontend" / "src" / "components" / "AdminAccessControlPanel.jsx"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_helper():
    spec = importlib.util.spec_from_file_location(
        "track_15_88_helper", str(HELPER))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["track_15_88_helper"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── 1. Helper exists + correct surface ──────────────────────────


def test_helper_module_exists():
    assert HELPER.exists(), (
        "Track 15.88: lib/directory_access_state.py must exist."
    )


def test_helper_exports_derive_function():
    h = _load_helper()
    assert hasattr(h, "derive_directory_access_state"), (
        "Track 15.88: helper must export "
        "`derive_directory_access_state(row)`."
    )


def test_helper_canonical_state_constants_exist():
    h = _load_helper()
    for name in (
        "ACCESS_ACTIVE", "ACCESS_INACTIVE",
        "CRED_ISSUED", "CRED_NEVER_ISSUED",
        "CRED_CHANGE_REQUIRED", "CRED_BLOCKED",
        "BLOCKED_DISABLED", "BLOCKED_NEVER_ISSUED",
        "BLOCKED_CHANGE_REQUIRED", "BLOCKED_NO_PORTAL_ACCESS",
    ):
        assert hasattr(h, name), f"Track 15.88: helper must export `{name}`."


# ─── 2. State derivation matrix · every input → expected output ──


def _state(row):
    return _load_helper().derive_directory_access_state(row)


def test_usable_active_issued_with_grants():
    s = _state({
        "disabled": False, "must_change_password": False,
        "portals": ["pm", "shop"],
        "password_hash": "$2b$12$xyz",
    })
    assert s == {
        "access_state": "active",
        "credential_state": "issued",
        "portal_count": 2,
        "usable_now": True,
        "blocked_reason": None,
    }


def test_blocked_disabled_takes_precedence_over_everything():
    s = _state({
        "disabled": True, "must_change_password": True,
        "portals": ["pm"],
        "password_hash": "",
    })
    assert s["access_state"] == "inactive"
    assert s["credential_state"] == "blocked"
    assert s["usable_now"] is False
    assert s["blocked_reason"] == "disabled"


def test_blocked_never_issued_for_missing_hash():
    s = _state({
        "disabled": False, "must_change_password": False,
        "portals": ["pm"], "password_hash": "",
    })
    assert s["credential_state"] == "never_issued"
    assert s["usable_now"] is False
    assert s["blocked_reason"] == "never_issued"


def test_blocked_change_required():
    s = _state({
        "disabled": False, "must_change_password": True,
        "portals": ["pm"], "password_hash": "$2b$12$xyz",
    })
    assert s["credential_state"] == "change_required"
    assert s["usable_now"] is False
    assert s["blocked_reason"] == "change_required"


def test_blocked_no_portal_access():
    s = _state({
        "disabled": False, "must_change_password": False,
        "portals": [], "password_hash": "$2b$12$xyz",
    })
    assert s["credential_state"] == "issued"
    assert s["usable_now"] is False
    assert s["blocked_reason"] == "no_portal_access"


def test_empty_row_treated_as_inactive_disabled():
    s = _state(None)
    assert s["usable_now"] is False
    assert s["blocked_reason"] == "disabled"


def test_portal_count_matches_input_array():
    s = _state({
        "disabled": False, "must_change_password": False,
        "portals": ["pm", "shop", "hr", "safety", "dispatch"],
        "password_hash": "$2b$12$xyz",
    })
    assert s["portal_count"] == 5
    assert s["usable_now"] is True


# ─── 3. Helper NEVER returns the password hash ──────────────────


def test_helper_never_leaks_password_hash():
    h = _load_helper()
    secret_hash = "$2b$12$THIS_IS_SECRET_DO_NOT_LEAK"
    s = h.derive_directory_access_state({
        "disabled": False, "must_change_password": False,
        "portals": ["pm"], "password_hash": secret_hash,
    })
    for k, v in s.items():
        assert "$2b" not in str(v), (
            f"Track 15.88 SECURITY: helper leaked bcrypt hash in field `{k}`."
        )
        assert "SECRET" not in str(v), (
            f"Track 15.88 SECURITY: helper leaked password material in field `{k}`."
        )
    # The returned dict's keys are exactly the published contract.
    assert set(s.keys()) == {
        "access_state", "credential_state", "portal_count",
        "usable_now", "blocked_reason",
    }


def test_helper_only_reads_safe_fields():
    """The helper code must read only documented fields. No call into
    user_directory, no DB hit, no email send."""
    src = _read(HELPER)
    for forbidden in [
        "import requests", "httpx", "motor", "find_one(", "delete_one(",
        "send_email", "smtplib", "open(",
    ]:
        assert forbidden not in src, (
            f"Track 15.88: helper must NOT use `{forbidden}` — it must "
            "be a pure-function derivation."
        )


# ─── 4. Routes wire the helper in ────────────────────────────────


def test_directory_routes_import_helper():
    src = _read(ROUTES)
    assert "from lib.directory_access_state import derive_directory_access_state" in src, (
        "Track 15.88: auth_directory_routes.py must import the helper."
    )


def test_list_endpoint_enriches_views():
    src = _read(ROUTES)
    # Must call _enrich_with_access_state inside list_users.
    m = re.search(r"async def list_users\(.*?return \{.*?\}", src, re.S)
    assert m
    body = m.group(0)
    assert "_enrich_with_access_state" in body, (
        "Track 15.88: GET /admin/directory must enrich each user "
        "view with the access-state envelope so the UI can render "
        "the usability badges."
    )


def test_create_update_reset_endpoints_enrich_views():
    src = _read(ROUTES)
    for fname in ("create_user", "update_user", "reset_password"):
        m = re.search(rf"async def {fname}\(.*?\n    @router", src, re.S)
        # last endpoint won't have a trailing decorator; use to-end-of-file.
        if not m:
            m = re.search(rf"async def {fname}\(.*?\Z", src, re.S)
        assert m
        body = m.group(0)
        assert "_enrich_with_access_state" in body, (
            f"Track 15.88: {fname} response must include the "
            "access-state envelope."
        )


def test_enrich_helper_strips_no_hash_from_view():
    """The route-level enricher reads `password_hash` from the raw
    row via the canonical helper but must NEVER read or write it
    directly in route code. We tolerate the substring in the
    docstring (which documents the contract) but disallow any
    actual statement that touches the hash."""
    src = _read(ROUTES)
    m = re.search(
        r"def _enrich_with_access_state\(.*?\n(?:\s{4}.*?\n)*?(?=\ndef|\nclass|\nasync def|\n@)",
        src, re.S)
    assert m, "Track 15.88: _enrich_with_access_state must exist in routes."
    body = m.group(0)
    # Strip triple-quoted docstrings before scanning for hash access.
    body_no_doc = re.sub(r'"""[\s\S]*?"""', "", body)
    for needle in (
        'row.get("password_hash")',
        "row.get('password_hash')",
        '["password_hash"]',
        "['password_hash']",
    ):
        assert needle not in body_no_doc, (
            f"Track 15.88 SECURITY: enricher must not read `{needle}` "
            "directly — it must rely on the helper, which is the "
            "single canonical reader."
        )


# ─── 5. Frontend UsabilityBadges consumes canonical strings ─────


def test_panel_imports_and_renders_usability_badges():
    src = _read(PANEL)
    assert "function UsabilityBadges" in src, (
        "Track 15.88: AdminAccessControlPanel must define the "
        "`UsabilityBadges` row helper."
    )
    assert "<UsabilityBadges user={u} />" in src, (
        "Track 15.88: AdminAccessControlPanel must render "
        "<UsabilityBadges> inside each row."
    )


def test_panel_credential_badge_map_keys_match_backend_contract():
    src = _read(PANEL)
    # All 4 canonical credential_state values must be branched on.
    for key in ("issued", "never_issued", "change_required", "blocked"):
        assert f'  {key}:' in src or f'"{key}"' in src or f"'{key}'" in src, (
            f"Track 15.88: AdminAccessControlPanel CREDENTIAL_BADGE "
            f"map must include `{key}`."
        )


def test_panel_blocked_reason_map_keys_match_backend_contract():
    src = _read(PANEL)
    for key in ("disabled", "never_issued", "change_required",
                "no_portal_access"):
        assert f'  {key}:' in src or f'"{key}"' in src or f"'{key}'" in src, (
            f"Track 15.88: AdminAccessControlPanel "
            f"BLOCKED_REASON_COPY must include `{key}`."
        )


def test_panel_renders_data_testids_for_state():
    """data-testids are required for the Track 15.86 smoke gate +
    the Track 15.88 ledger's smoke checklist."""
    src = _read(PANEL)
    for needle in (
        "acc-row-state-",
        "acc-row-credstate-",
        "acc-row-usable-",
        "acc-row-blocked-",
    ):
        assert needle in src, (
            f"Track 15.88: AdminAccessControlPanel must render the "
            f"`{needle}*` data-testid for the usability row state."
        )


def test_panel_does_not_render_password_hash():
    """Hard belt-and-suspenders: the UI source must not reference
    `password_hash` anywhere. The backend already strips it but the
    UI must not even attempt to read it."""
    src = _read(PANEL)
    assert "password_hash" not in src, (
        "Track 15.88 SECURITY: AdminAccessControlPanel must not "
        "reference `password_hash` — the backend never exposes it "
        "and the UI must not even attempt to read it."
    )


# ─── 6. Backend contract strings — drift guard ──────────────────


def test_backend_state_strings_match_frontend_keys():
    """If the backend renames a canonical string (e.g.
    'change_required' → 'rotate_required'), the frontend would
    silently fall through to a generic 'Blocked' badge. Lock both
    sides to the same set."""
    h = _load_helper()
    for cred_key in (h.CRED_ISSUED, h.CRED_NEVER_ISSUED,
                     h.CRED_CHANGE_REQUIRED, h.CRED_BLOCKED):
        # cred_key is a python string. We just check it appears in
        # the frontend file as one of the CREDENTIAL_BADGE map keys.
        src = _read(PANEL)
        assert cred_key in src, (
            f"Track 15.88 contract drift: backend ships "
            f"credential_state=`{cred_key}` but the frontend "
            "AdminAccessControlPanel does not branch on it."
        )
    for br_key in (h.BLOCKED_DISABLED, h.BLOCKED_NEVER_ISSUED,
                   h.BLOCKED_CHANGE_REQUIRED, h.BLOCKED_NO_PORTAL_ACCESS):
        src = _read(PANEL)
        assert br_key in src, (
            f"Track 15.88 contract drift: backend ships "
            f"blocked_reason=`{br_key}` but the frontend "
            "AdminAccessControlPanel does not branch on it."
        )


# ─── 7. Track 15.87 RBAC preservation ─────────────────────────


def test_track_15_87_test_file_still_present():
    p = BACKEND / "tests" / "test_track_15_87_multi_portal_access_authority.py"
    assert p.exists(), (
        "Track 15.88: Track 15.87 multi-portal access regression file "
        "must remain in place — Track 15.88 extends 15.87, not "
        "replaces it."
    )


def test_track_15_87_helper_still_present():
    p = BACKEND / "lib" / "directory_portal_login.py"
    assert p.exists(), (
        "Track 15.88: Track 15.87 canonical portal-login helper must "
        "remain in place."
    )


def test_track_15_86_and_15_85_files_preserved():
    for name in (
        "test_track_15_85_mandatory_full_platform_certification.py",
        "test_track_15_86_browser_smoke_gate.py",
    ):
        assert (BACKEND / "tests" / name).exists(), (
            f"Track 15.88: {name} must remain present."
        )


# ─── 8. Deployment gate wiring ─────────────────────────────────


def test_deployment_gate_wires_track_15_88():
    gate = _read(BACKEND.parent / "scripts" / "deployment_gate.py")
    assert "test_track_15_88" in gate, (
        "Track 15.88: scripts/deployment_gate.py must list this file "
        "in REGRESSION_FILES."
    )
