"""TRACK 15.88 · People & Access Credential Usability Clarity.

Single canonical helper that derives whether a directory user can
actually sign in *right now* — and if not, why not. Reads ONLY safe
metadata (`disabled`, `must_change_password`, `portals[]`, presence
of `password_hash`) and returns a normalized envelope. **Never returns
the password hash itself, the hash length, the salt, or any other
auth material.**

This is the source of truth for the Admin Console → People & Access
"usable now / blocked reason" badges introduced by Track 15.88. The
contract directly mirrors the per-portal login behaviour locked by
Track 15.87:

    Helper says ``usable_now=True``   ⇔   POST /api/{portal}/login
                                         would succeed for ANY of
                                         the user's granted portals
                                         (given the correct password).

    Helper says ``usable_now=False``  ⇔   every /login endpoint would
                                         deny this user regardless of
                                         their password, with the
                                         reason matching
                                         ``blocked_reason``.

Both backend (admin directory list / create / patch / reset endpoints)
and frontend (AdminAccessControlPanel) consume this contract.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


# ─── Canonical state enums ────────────────────────────────────────
#
# These strings are the contract — the frontend matches on them
# verbatim. Drift here would silently change the badge a row shows.

ACCESS_ACTIVE = "active"
ACCESS_INACTIVE = "inactive"  # disabled in the directory

CRED_ISSUED = "issued"                      # password_hash set, no rotation owed
CRED_NEVER_ISSUED = "never_issued"          # password_hash missing / empty
CRED_CHANGE_REQUIRED = "change_required"    # must_change_password = true
CRED_BLOCKED = "blocked"                    # disabled (subsumes credential)

# Blocked reasons — exhaustive list. Each maps to one operator-
# facing UI message:
BLOCKED_DISABLED = "disabled"
BLOCKED_NEVER_ISSUED = "never_issued"
BLOCKED_CHANGE_REQUIRED = "change_required"
BLOCKED_NO_PORTAL_ACCESS = "no_portal_access"


def _has_credentials(row: Dict[str, Any]) -> bool:
    """True iff a non-empty password_hash is present on the row.

    Reads the raw row (which DOES contain ``password_hash``) but
    returns only a boolean — the hash itself never escapes."""
    raw = row.get("password_hash")
    return isinstance(raw, str) and len(raw) > 0


def derive_directory_access_state(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the canonical access-state envelope for a directory
    row. Safe to merge into any admin-facing user view.

    Parameters
    ----------
    row : raw ``user_directory`` document. Must include at minimum
          ``disabled`` (bool), ``must_change_password`` (bool),
          ``portals`` (list[str]), ``password_hash`` (str). Missing
          fields are tolerated and treated as "not set".

    Returns
    -------
    dict with exactly these keys:

      * ``access_state``     : "active" | "inactive"
      * ``credential_state`` : "issued" | "never_issued" |
                               "change_required" | "blocked"
      * ``portal_count``     : int (size of ``portals`` array)
      * ``usable_now``       : bool — can this user sign in to AT
                               LEAST one of their granted portals
                               right now?
      * ``blocked_reason``   : str | None — one of the BLOCKED_*
                               constants, or None when usable_now.

    No password material is ever returned. No secrets. No hash.
    """
    if not row:
        return {
            "access_state": ACCESS_INACTIVE,
            "credential_state": CRED_BLOCKED,
            "portal_count": 0,
            "usable_now": False,
            "blocked_reason": BLOCKED_DISABLED,
        }

    disabled = bool(row.get("disabled"))
    must_change = bool(row.get("must_change_password"))
    portals = list(row.get("portals") or [])
    portal_count = len(portals)
    has_creds = _has_credentials(row)

    # Compute access state.
    access_state = ACCESS_INACTIVE if disabled else ACCESS_ACTIVE

    # Compute credential state.
    if disabled:
        credential_state = CRED_BLOCKED
    elif not has_creds:
        credential_state = CRED_NEVER_ISSUED
    elif must_change:
        credential_state = CRED_CHANGE_REQUIRED
    else:
        credential_state = CRED_ISSUED

    # Compute usable_now + blocked_reason.
    # Order matters: disabled > never_issued > change_required >
    # no_portal_access. This mirrors the login endpoint denial
    # order: every endpoint denies disabled first, then missing
    # credentials, then rotation owed, then portal grant.
    if disabled:
        usable_now = False
        blocked_reason = BLOCKED_DISABLED
    elif not has_creds:
        usable_now = False
        blocked_reason = BLOCKED_NEVER_ISSUED
    elif must_change:
        usable_now = False
        blocked_reason = BLOCKED_CHANGE_REQUIRED
    elif portal_count == 0:
        usable_now = False
        blocked_reason = BLOCKED_NO_PORTAL_ACCESS
    else:
        usable_now = True
        blocked_reason = None

    return {
        "access_state": access_state,
        "credential_state": credential_state,
        "portal_count": portal_count,
        "usable_now": usable_now,
        "blocked_reason": blocked_reason,
    }
