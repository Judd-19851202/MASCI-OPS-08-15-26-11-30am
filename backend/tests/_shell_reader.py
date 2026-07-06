"""TRACK 22.5A · shared shell-reader for legacy governance linters.

Post-Track-22.2, `frontend/src/App.js` no longer contains inline
route/auth registrations — they were extracted into
`frontend/src/app/routing/AppRoutes.jsx`. Legacy linters that
literal-substring-match on the app's routing shell must now read
BOTH files concatenated so their safety intent ("these routes /
auth guards are still mounted in the shipped app") continues to
hold without weakening.

This helper exists so every legacy linter uses the SAME anchor —
one place to update if the routing shell ever moves again.
"""
from __future__ import annotations

import pathlib


_APP_JS = pathlib.Path("/app/frontend/src/App.js")
_APP_ROUTES = pathlib.Path("/app/frontend/src/app/routing/AppRoutes.jsx")


def read_app_shell() -> str:
    """Return App.js + AppRoutes.jsx concatenated (canonical routing shell)."""
    parts = []
    if _APP_JS.exists():
        parts.append(_APP_JS.read_text())
    if _APP_ROUTES.exists():
        parts.append(_APP_ROUTES.read_text())
    return "\n".join(parts)
