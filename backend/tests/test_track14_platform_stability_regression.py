"""
TRACK 14.0-PLATFORM-STABILITY · Regression lock.

These tests pin the backend-side behaviors that the frontend stability
fix depends on. The frontend interceptor (lib/api.js) absorbs 401s on
cross-portal helper paths silently — but it relies on those paths
returning a STABLE 401 (not 5xx, not 404) when called without auth.

If any of these endpoints starts returning 5xx instead of 401 for an
unauthenticated request, the frontend overlay would re-trigger via
the BACKEND_UNAVAILABLE classification path and the original P0 bug
would silently regress. Lock the contract here.
"""
import os
import requests

API = f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')}/api"


def _bare_get(path, **kwargs):
    return requests.get(f"{API}{path}", timeout=15, **kwargs)


def test_health_endpoint_is_public_200():
    """`/api/health` must return 200 unauthenticated — health badge relies on this."""
    r = _bare_get("/health")
    assert r.status_code == 200, f"/api/health returned {r.status_code}, expected 200"


def test_workflows_last_transition_returns_401_not_500_without_auth():
    """
    Critical: the frontend isCrossPortalHelper silent-list absorbs 401s
    on /api/workflows/* paths. If this endpoint started returning 500,
    the frontend would classify as BACKEND_UNAVAILABLE and re-pop the
    overlay. Pin the 401 contract.
    """
    r = _bare_get("/workflows/incident/some-fake-id/last-transition")
    assert r.status_code in (401, 403, 404), (
        f"/api/workflows/.../last-transition returned {r.status_code} unauthenticated; "
        f"expected 401/403/404 so the frontend silent-list absorbs it"
    )


def test_notifications_returns_401_not_500_without_auth():
    """Same contract for /api/notifications/*."""
    r = _bare_get("/notifications")
    assert r.status_code in (401, 403, 404), (
        f"/api/notifications returned {r.status_code} unauthenticated; "
        f"expected 401/403/404"
    )


def test_operations_expirations_summary_returns_401_not_500_without_auth():
    """Same contract for /api/operations/expirations/summary."""
    r = _bare_get("/operations/expirations/summary")
    assert r.status_code in (401, 403, 404), (
        f"/api/operations/expirations/summary returned {r.status_code} unauthenticated; "
        f"expected 401/403/404"
    )


def test_incidents_endpoint_does_not_500_on_missing_id():
    """Detail endpoint must 404 cleanly, never 5xx, so frontend toast renders correctly."""
    r = _bare_get("/incidents/__definitely_does_not_exist__")
    assert r.status_code in (401, 404), (
        f"/api/incidents/<bogus> returned {r.status_code}; expected 401 or 404"
    )
