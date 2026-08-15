"""Zero-Stale-Client CLIENT_UPDATE_REQUIRED compatibility contract.

Proves an incompatible OLD client gets a specific 426 CLIENT_UPDATE_REQUIRED
(not a generic 400/401/403/500), that ordinary clients are untouched, that the
policy is off by default, and that health/version/auth remain reachable so a
stale client can always discover the current release and update.
"""

import importlib
import os

import client_compat as cc


def _reload_with_blocklist(value):
    if value is None:
        os.environ.pop("CLIENT_COMPAT_BLOCKLIST", None)
    else:
        os.environ["CLIENT_COMPAT_BLOCKLIST"] = value
    importlib.reload(cc)
    return cc


def test_default_policy_is_accept_all():
    mod = _reload_with_blocklist(None)
    policy = mod.client_compat_policy()
    assert policy["policy"] == "accept-all"
    assert policy["incompatible_releases"] == []
    assert mod.is_incompatible_client("dcf-anything") is False
    assert mod.is_incompatible_client(None) is False


def test_blocklisted_release_is_incompatible():
    mod = _reload_with_blocklist("dcf-OLD-1, dcf-OLD-2")
    policy = mod.client_compat_policy()
    assert policy["policy"] == "blocklist"
    assert "dcf-OLD-1" in policy["incompatible_releases"]
    assert mod.is_incompatible_client("dcf-OLD-1") is True
    assert mod.is_incompatible_client("dcf-OLD-2") is True
    # A current/unknown client is NOT forced to update.
    assert mod.is_incompatible_client("dcf-CURRENT") is False
    _reload_with_blocklist(None)


def test_update_required_body_is_specific_and_non_secret():
    mod = _reload_with_blocklist("dcf-OLD-1")
    body = mod.update_required_body("dcf-OLD-1")
    assert body["code"] == "CLIENT_UPDATE_REQUIRED"
    assert body["action"] == "reload_to_current_release"
    assert body["client_release"] == "dcf-OLD-1"
    # No secrets/tokens/URIs leaked.
    blob = str(body).lower()
    assert "token" not in blob and "mongodb" not in blob and "secret" not in blob
    _reload_with_blocklist(None)


def test_health_version_auth_paths_are_exempt():
    mod = _reload_with_blocklist("dcf-OLD-1")
    # Even an incompatible client must reach these to update.
    for p in ["/api/health", "/api/version", "/api/auth/multi-login", "/api/deployment/readiness"]:
        assert mod.path_is_exempt(p) is True
    # Ordinary business endpoints are gated.
    assert mod.path_is_exempt("/api/daily-reports") is False
    assert mod.path_is_exempt("/api/admin/jobs") is False
    _reload_with_blocklist(None)


def test_status_code_is_426_not_generic():
    mod = _reload_with_blocklist(None)
    assert mod.UPDATE_REQUIRED_STATUS == 426
    assert mod.UPDATE_REQUIRED_STATUS not in (400, 401, 403, 500)
