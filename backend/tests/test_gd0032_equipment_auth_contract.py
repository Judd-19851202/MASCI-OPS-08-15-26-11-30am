"""GD-0032 — TD-0015(A) governed AUTH CONTRACT for /api/equipment-master (Wave 9).

CLASSIFICATION: INTENTIONAL_AUTH_CONTRACT (session binding), NOT a false-deny.
Runtime evidence (against the running preview backend, Super Admin via multi-login):
    X-Admin-Token + X-Directory-Token -> 200 (766 units)
    X-Admin-Token alone                -> 401 (Authenticated portal session required)
    no auth                            -> 401
The SPA sends BOTH headers because the admin portal is directory-compatible
(authHeaders.js), so the legitimate application path succeeds; the earlier raw/agent
401 lacked X-Directory-Token. No auth source change is required. This test locks the
governed contract in source so it cannot silently regress.
"""
import os

FE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "src")


def test_admin_portal_is_directory_compatible_sends_directory_token():
    src = open(os.path.join(FE, "lib", "authHeaders.js")).read()
    assert "DIRECTORY_COMPATIBLE_PORTALS" in src
    assert 'headers["X-Directory-Token"] = directory' in src
    # admin must be a directory-compatible portal so the SPA sends X-Directory-Token with X-Admin-Token
    block = src[src.index("DIRECTORY_COMPATIBLE_PORTALS"): src.index("DIRECTORY_COMPATIBLE_PORTALS") + 200]
    assert "admin" in block


def test_equipment_panel_shows_unavailable_not_zero_on_auth_denial():
    # TD-0015(B): a 401 (or any load failure) renders UNAVAILABLE, never a false 0 / empty fleet.
    src = open(os.path.join(FE, "components", "EquipmentMasterPanel.jsx")).read()
    assert "setLoadError(operationalError(e" in src
    assert "UNAVAILABLE" in src
    assert 'data-testid="equipment-master-load-error"' in src
