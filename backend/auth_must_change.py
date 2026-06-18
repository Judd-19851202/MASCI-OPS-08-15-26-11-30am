"""
auth_must_change.py — Layer 3 backstop for the Track 15.14A
"temporary password enforcement" recovery.

Every portal's `require_*` dependency calls
`enforce_password_change_required(request, actor)` immediately after
resolving the actor dict. If the actor's `must_change_password` flag is
True AND the current request path is not in the allow-list, we raise
HTTP 403 with a stable machine-readable code so the SPA axios layer can
bounce the user into the right `/change-password` flow.

This is intentionally enforced at the dependency layer (not inside the
token validators themselves) so that:

  - The change-password endpoints can still verify the token and rotate.
  - The /me + /logout + /forgot + /reset paths remain usable while the
    user is mid-rotation.
  - The backend is the source of truth: no client can deep-link, script,
    or bookmark its way around the rotation gate.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from fastapi import HTTPException, Request


# Path suffixes that REMAIN usable while must_change_password=True.
# Anything else is rejected. Keep this list short — every entry is a
# bypass we accept on purpose.
_ALLOWED_SUFFIXES: tuple[str, ...] = (
    "/change-password",
    "/change-master-password",
    "/logout",
    "/multi-logout",
    "/me",
    "/me-directory",
    "/forgot-password",
    "/reset-password",
    # FL portal uses /portal/change-password etc — caught by the
    # /change-password suffix above.
)

# Optional substrings for endpoints that don't end with the suffix
# (e.g. `/reset/{token}` is path-templated). Keep narrow.
_ALLOWED_SUBSTRINGS: tuple[str, ...] = (
    "/hr/reset/",
    "/pm/reset/",
    "/shop/reset/",
    "/safety/reset/",
    "/dispatch/reset/",
    "/field-leadership/portal/reset/",
)


def _path_allowed(path: str) -> bool:
    p = (path or "").lower().rstrip("/")
    for suf in _ALLOWED_SUFFIXES:
        if p.endswith(suf):
            return True
    for sub in _ALLOWED_SUBSTRINGS:
        if sub in p:
            return True
    return False


def actor_must_change(actor: Any) -> bool:
    """Return True iff the resolved actor explicitly carries
    must_change_password=True. Tolerant of legacy non-dict actors
    (`True`, `None`, env-token stubs) which we treat as not-required."""
    if isinstance(actor, dict):
        return bool(actor.get("must_change_password"))
    return False


def enforce_password_change_required(
    request: Optional[Request],
    actor: Any,
) -> None:
    """Raise HTTP 403 PASSWORD_CHANGE_REQUIRED when the actor must
    rotate before doing anything other than the allow-listed flows."""
    if not actor_must_change(actor):
        return
    path = ""
    if request is not None:
        try:
            path = request.scope.get("path") or request.url.path or ""
        except Exception:
            path = ""
    if _path_allowed(path):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "code": "PASSWORD_CHANGE_REQUIRED",
            "message": (
                "Your temporary password must be changed before you can "
                "use the platform. Please complete the password change."
            ),
        },
    )


__all__ = [
    "actor_must_change",
    "enforce_password_change_required",
]
