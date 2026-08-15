"""Governed client/backend compatibility contract (Zero-Stale-Client).

Purpose
-------
After a deploy, an OLD browser (Release A) may keep talking to the NEW backend
(Release B). Normally that is fine and MUST remain fine — ordinary deploys do
NOT force clients to update. Only when a specific old release is declared
*incompatible* (breaking API contract, security-critical client bug, or a
data-integrity risk) does the backend answer that old client with an explicit,
governed CLIENT_UPDATE_REQUIRED response (HTTP 426 Upgrade Required) instead of
a misleading generic 400/401/403/500. The client then protects any unsaved work
and converges to the current release.

Design rules (owner-locked)
----------------------------
* This is COMPATIBILITY metadata, never authorization. The client-supplied
  ``X-MASCI-Client-Release`` header is untrusted and is used ONLY to decide
  whether the loaded release is on the incompatible list. It never grants or
  denies access to any resource.
* Default policy is EMPTY (no release is incompatible) so normal deploys never
  force an update.
* The incompatible set is governed via the ``CLIENT_COMPAT_BLOCKLIST`` env var
  (comma-separated release fingerprints / release ids). Absent ⇒ empty.
* The health/version endpoints and the compatibility probe itself are always
  exempt so a stale client can still discover the current release and update.
"""

from __future__ import annotations

import os
from typing import Dict, List, Set

CLIENT_RELEASE_HEADER = "x-masci-client-release"
UPDATE_REQUIRED_STATUS = 426  # Upgrade Required
UPDATE_REQUIRED_CODE = "CLIENT_UPDATE_REQUIRED"

# Paths a stale/incompatible client MUST still be able to reach so it can learn
# the current release and update itself. Never gate these.
_EXEMPT_PREFIXES = (
    "/api/health",
    "/api/version",
    "/api/deployment",
    "/api/auth",          # do not turn an incompatible client into a login failure
)


def _blocklist() -> Set[str]:
    raw = os.environ.get("CLIENT_COMPAT_BLOCKLIST", "") or ""
    return {tok.strip() for tok in raw.split(",") if tok.strip()}


def client_compat_policy() -> Dict[str, object]:
    """Non-secret compatibility policy for /api/version."""
    block = sorted(_blocklist())
    return {
        "header": "X-MASCI-Client-Release",
        "update_required_status": UPDATE_REQUIRED_STATUS,
        "update_required_code": UPDATE_REQUIRED_CODE,
        # Explicit, governed list of releases that are no longer supported.
        # Empty in normal operation — ordinary deploys never force updates.
        "incompatible_releases": block,
        "policy": "blocklist" if block else "accept-all",
    }


def is_incompatible_client(client_release: str | None) -> bool:
    if not client_release:
        return False
    return client_release.strip() in _blocklist()


def path_is_exempt(path: str) -> bool:
    p = (path or "").rstrip("/") or "/"
    return any(p == pre or p.startswith(pre + "/") or p.startswith(pre) for pre in _EXEMPT_PREFIXES)


def update_required_body(client_release: str | None) -> Dict[str, object]:
    return {
        "code": UPDATE_REQUIRED_CODE,
        "detail": "This version of MASCI OPS is no longer supported. The app will update to the current version automatically once your current work is saved.",
        "client_release": (client_release or None),
        "action": "reload_to_current_release",
    }


__all__ = [
    "CLIENT_RELEASE_HEADER",
    "UPDATE_REQUIRED_STATUS",
    "UPDATE_REQUIRED_CODE",
    "client_compat_policy",
    "is_incompatible_client",
    "path_is_exempt",
    "update_required_body",
]
