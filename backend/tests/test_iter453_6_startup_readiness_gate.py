"""iter453.6 · Startup-readiness gate test (HOTFIX BUNDLE A · Part C).

Verifies that the readiness gate added to backend/server.py:
  1. Returns 503 {"detail":"service_starting"} for public WRITE requests
     while `app.state.ready` is False.
  2. Allows /api/health and /api/version through regardless of ready state.
  3. Allows GETs through regardless of ready state.
  4. Allows non-/api paths through regardless of ready state.
  5. Allows requests through once `app.state.ready` is True.
"""
import importlib
import os

os.environ.setdefault("REACT_APP_BACKEND_URL", "http://localhost:8001")

# Lazy import to avoid heavy module load if pytest collection-only is used.
def _get_app_and_client():
    # Reuse the running server's app instance — server.py module-level
    # state already has @app.middleware('http') registered.
    import sys
    sys.path.insert(0, "/app/backend")
    if "server" in sys.modules:
        srv = sys.modules["server"]
    else:
        srv = importlib.import_module("server")
    from fastapi.testclient import TestClient
    return srv.app, TestClient(srv.app)


def test_health_passes_when_not_ready():
    app, client = _get_app_and_client()
    app.state.ready = False
    try:
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json().get("ok") is True
    finally:
        app.state.ready = True


def test_version_passes_when_not_ready():
    app, client = _get_app_and_client()
    app.state.ready = False
    try:
        r = client.get("/api/version")
        assert r.status_code == 200
        assert "source_hash" in r.json()
    finally:
        app.state.ready = True


def test_get_passes_when_not_ready():
    """GETs are never gated — only writes are."""
    app, client = _get_app_and_client()
    app.state.ready = False
    try:
        # /api/hr/employee-requests would 403 (HR-or-Admin gate) but the
        # readiness gate must NOT pre-empt with 503 on a GET.
        r = client.get("/api/hr/employee-requests")
        assert r.status_code != 503
    finally:
        app.state.ready = True


def test_post_employees_add_returns_503_when_not_ready():
    app, client = _get_app_and_client()
    app.state.ready = False
    try:
        r = client.post(
            "/api/employees/add",
            json={"name": "iter453.6 GATE TEST"},
        )
        assert r.status_code == 503
        assert r.json() == {"detail": "service_starting"}
    finally:
        app.state.ready = True


def test_post_employee_requests_returns_503_when_not_ready():
    app, client = _get_app_and_client()
    app.state.ready = False
    try:
        r = client.post(
            "/api/employee-requests",
            json={"kind": "new_hire"},
        )
        assert r.status_code == 503
        assert r.json() == {"detail": "service_starting"}
    finally:
        app.state.ready = True


def test_post_webhook_returns_503_when_not_ready():
    app, client = _get_app_and_client()
    app.state.ready = False
    try:
        r = client.post("/api/webhooks/resend", json={})
        assert r.status_code == 503
        assert r.json() == {"detail": "service_starting"}
    finally:
        app.state.ready = True


def test_put_admin_employees_returns_503_when_not_ready():
    app, client = _get_app_and_client()
    app.state.ready = False
    try:
        r = client.put(
            "/api/admin/employees/whatever",
            json={"is_active": False},
        )
        assert r.status_code == 503
    finally:
        app.state.ready = True


def test_delete_returns_503_when_not_ready():
    app, client = _get_app_and_client()
    app.state.ready = False
    try:
        r = client.delete("/api/admin/employees/whatever")
        assert r.status_code == 503
    finally:
        app.state.ready = True


def test_post_employees_add_returns_410_when_ready():
    """Once ready=True, the canonical Phase Alpha G-1 410 response is reached."""
    app, client = _get_app_and_client()
    app.state.ready = True
    r = client.post(
        "/api/employees/add",
        json={"name": "iter453.6 READY TEST"},
    )
    assert r.status_code == 410
    body = r.json()
    assert body.get("detail", {}).get("code") == "endpoint_deprecated"


def test_health_passes_when_ready():
    app, client = _get_app_and_client()
    app.state.ready = True
    r = client.get("/api/health")
    assert r.status_code == 200
