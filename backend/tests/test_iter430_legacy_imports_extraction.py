"""
test_iter430_legacy_imports_extraction.py · Phase 28.2 · iter430
─────────────────────────────────────────────────────────────────────
Parity-lock guard for the legacy-imports extraction.

The 11 routes that used to be inline `@app.{verb}(...)` decorators in
server.py are now declared inside the `routes.legacy_imports.build_
legacy_imports_router(...)` factory and mounted via include_router.

The contract this test pins down:
  - Every documented path/method pair is registered on the FastAPI app.
  - The legacy uploader auth dep (HR / Safety / Admin) is enforced
    on every uploader-scoped route → 401 without a token.
  - Admin-strict routes still 401 without a strict admin token.

If any route falls off (typo in path, missing decorator, double mount,
etc.) this test fails immediately — so the extraction can never
silently drift from server.py's prior behavior.
"""
from __future__ import annotations

from typing import List, Tuple

import pytest


EXPECTED_ROUTES: List[Tuple[str, str]] = [
    ("POST",  "/api/legacy-imports/upload"),
    ("GET",   "/api/legacy-imports/_meta"),
    ("GET",   "/api/legacy-imports"),
    ("GET",   "/api/legacy-imports/{import_id}"),
    ("GET",   "/api/legacy-imports/{import_id}/file"),
    ("PATCH", "/api/legacy-imports/{import_id}"),
    ("POST",  "/api/legacy-imports/{import_id}/approve"),
    ("POST",  "/api/legacy-imports/{import_id}/reject"),
    ("POST",  "/api/legacy-imports/{import_id}/retry-ocr"),
    ("GET",   "/api/admin/legacy-imports/audit"),
    ("GET",   "/api/admin/legacy-imports/pilot-debrief"),
]


@pytest.fixture(scope="module")
def app_routes():
    """Boot the real FastAPI app and return the (method, path) set."""
    import server  # noqa: PLC0415
    pairs = set()
    for r in server.app.routes:
        for m in getattr(r, "methods", []) or []:
            pairs.add((m, r.path))
    return pairs


def test_iter430_all_eleven_routes_mounted(app_routes):
    """Every previously inline route must remain reachable on the app."""
    missing = [(m, p) for (m, p) in EXPECTED_ROUTES if (m, p) not in app_routes]
    assert not missing, (
        "Legacy-imports routes missing from app after extraction:\n  "
        + "\n  ".join(f"{m} {p}" for m, p in missing)
    )


def test_iter430_no_duplicate_legacy_imports_mounts(app_routes):
    """Guard against the extraction accidentally double-registering the
    routes (which would happen if the inline decorators were left in
    place AND the new factory was included). Each (method, path) must
    appear exactly once."""
    import server  # noqa: PLC0415
    counts = {}
    for r in server.app.routes:
        path = r.path
        if "/legacy-imports" not in path:
            continue
        for m in getattr(r, "methods", []) or []:
            key = (m, path)
            counts[key] = counts.get(key, 0) + 1
    dupes = {k: v for k, v in counts.items() if v > 1}
    assert not dupes, f"Duplicate legacy-imports route registrations: {dupes}"


def test_iter430_unauth_returns_401_not_404(app_routes):
    """Belt-and-braces: 404 would mean the route is gone; 401 means it
    is mounted but auth correctly rejects an empty caller. We only
    test the GET-shaped routes here to keep this fast and dependency-
    free (no need for multipart upload payloads)."""
    from fastapi.testclient import TestClient
    import server  # noqa: PLC0415
    client = TestClient(server.app)
    for method, path in EXPECTED_ROUTES:
        if method != "GET":
            continue
        # Substitute path params with a harmless placeholder so FastAPI
        # actually routes to the handler (and then the auth dep rejects).
        live_path = path.replace("{import_id}", "nope")
        r = client.get(live_path)
        assert r.status_code in (401, 403), (
            f"{method} {live_path} returned {r.status_code} — "
            f"expected 401/403 from auth dep. Body: {r.text[:200]}"
        )
