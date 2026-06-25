"""
test_iter430_persistence_health_and_sentry_tags.py · Phase 28.2 · iter430
─────────────────────────────────────────────────────────────────────
Parity-lock for two Phase 28.2 invisible-infrastructure additions:

1. `/api/admin-strict/diag/persistence-health` — admin-strict, JSON
   only. Verifies the route is reachable with a valid admin token,
   returns 401 without one, and carries the documented field set.

2. Sentry tag enrichment middleware — coarse UA/portal/language/
   tenant classification. Tested in isolation against the helper
   functions (no live Sentry hub needed).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.admin_persistence_health import (
    _is_atlas_url,
    build_admin_persistence_health_router,
)
from sentry_tags import (
    _coarse_device,
    _coarse_browser,
    _classify_portal,
)


# ─────────────────────────────────────────────────────────────────────
# Fake Mongo: just enough surface for the persistence-health route.
# ─────────────────────────────────────────────────────────────────────
class _FakeColl:
    def __init__(self, docs=None):
        self._docs = docs or []

    async def find_one(self, q=None, projection=None, sort=None):
        return self._docs[0] if self._docs else None


class _FakeDB:
    def __init__(self):
        self.backup_runs = _FakeColl([{"ok": True, "ts": "2026-05-25T00:00:00+00:00",
                                       "kind": "complete", "size_bytes": 12345,
                                       "destinations": ["r2"], "filename": "x.zip",
                                       "error": None}])
        self.backup_drift_watch = _FakeColl([])
        self.continuity_events = _FakeColl([])

    def __getitem__(self, name):
        # for db[name] dynamic access in the persistence probe
        return getattr(self, name, _FakeColl([]))

    async def list_collection_names(self):
        return ["backup_runs", "continuity_events", "operational_attachments"]

    async def command(self, cmd):
        if cmd == "buildInfo":
            return {"version": "7.0.99"}
        return {}


async def _admin_strict_ok():
    return True


async def _admin_strict_fail():
    from fastapi import HTTPException
    raise HTTPException(401, "admin-strict required")


# ─────────────────────────────────────────────────────────────────────
# 1 · Atlas URL classifier
# ─────────────────────────────────────────────────────────────────────
def test_iter430_is_atlas_url():
    assert _is_atlas_url("mongodb+srv://u:p@cluster.mongodb.net/?x=1") is True  # secret-scan: allow-line
    assert _is_atlas_url("mongodb://localhost:27017") is False
    assert _is_atlas_url("mongodb+srv://u:p@self-hosted.example.com/?x=1") is False  # secret-scan: allow-line
    assert _is_atlas_url("") is False


# ─────────────────────────────────────────────────────────────────────
# 2 · Persistence-health returns documented field set when authorised
# ─────────────────────────────────────────────────────────────────────
def test_iter430_persistence_health_authorised(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb+srv://u:p@masci-prod.mongodb.net/?x=1")  # secret-scan: allow-line
    monkeypatch.setenv("DB_NAME", "masci_safety")

    app = FastAPI()
    app.include_router(build_admin_persistence_health_router(
        db=_FakeDB(),
        require_admin_strict_dep=_admin_strict_ok,
    ))
    client = TestClient(app)
    r = client.get("/api/admin-strict/diag/persistence-health")
    assert r.status_code == 200, r.text
    body = r.json()
    required = {
        "captured_at", "atlas_connected", "atlas_host", "db_name",
        "mongo_version", "collections_detected", "last_backup_time",
        "r2_backup_success", "persistent_storage_confirmed",
        "drift_watch_active", "drift_watch_reason",
    }
    assert required.issubset(body.keys()), f"missing: {required - body.keys()}"
    assert body["atlas_connected"] is True
    assert body["mongo_version"] == "7.0.99"
    assert body["collections_detected"] == 3
    # password masked in atlas_host
    assert "***" in body["atlas_host"]
    assert "p@" not in body["atlas_host"]


# ─────────────────────────────────────────────────────────────────────
# 3 · Persistence-health enforces admin-strict
# ─────────────────────────────────────────────────────────────────────
def test_iter430_persistence_health_unauth():
    app = FastAPI()
    app.include_router(build_admin_persistence_health_router(
        db=_FakeDB(),
        require_admin_strict_dep=_admin_strict_fail,
    ))
    client = TestClient(app)
    r = client.get("/api/admin-strict/diag/persistence-health")
    assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────
# 4 · Sentry coarse UA classifier — no PII, just buckets
# ─────────────────────────────────────────────────────────────────────
def test_iter430_sentry_coarse_ua():
    # iPhone Safari
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1"
    assert _coarse_device(ua) == "ios"
    assert _coarse_browser(ua) == "safari"
    # Android Chrome
    ua = "Mozilla/5.0 (Linux; Android 14; SM-S918U) Chrome/118.0.0.0 Mobile Safari/537.36"
    assert _coarse_device(ua) == "android"
    assert _coarse_browser(ua) == "chrome"
    # Windows Edge
    ua = "Mozilla/5.0 (Windows NT 10.0) Chrome/118 Edg/118"
    assert _coarse_device(ua) == "windows"
    assert _coarse_browser(ua) == "edge"
    # Mac Safari
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605"
    assert _coarse_device(ua) == "mac"
    assert _coarse_browser(ua) == "safari"
    # Unknown
    assert _coarse_device("totally-random-thing") == "unknown"
    assert _coarse_browser("totally-random-thing") == "unknown"


# ─────────────────────────────────────────────────────────────────────
# 5 · Sentry portal classifier
# ─────────────────────────────────────────────────────────────────────
def test_iter430_sentry_portal_classifier():
    class _R:  # tiny mock for request
        def __init__(self, headers=None, path="/api/health"):
            from starlette.datastructures import Headers, URL
            self.headers = Headers(headers or {})
            self.url = URL(f"http://x{path}")
    # By header
    assert _classify_portal(_R(headers={"X-Admin-Token": "x"})) == "admin"
    assert _classify_portal(_R(headers={"X-Dispatch-Token": "x"})) == "dispatch"
    assert _classify_portal(_R(headers={"X-HR-Token": "x"})) == "hr"
    assert _classify_portal(_R(headers={"X-Shop-Token": "x"})) == "shop"
    assert _classify_portal(_R(headers={"X-Safety-Token": "x"})) == "safety"
    assert _classify_portal(_R(headers={"X-Field-Leadership-Token": "x"})) == "field"
    assert _classify_portal(_R(headers={"X-PM-Token": "x"})) == "pm"
    # By path fallback
    assert _classify_portal(_R(path="/api/driver/start")) == "driver"
    assert _classify_portal(_R(path="/api/admin/something")) == "admin"
    assert _classify_portal(_R(path="/api/health")) == "public"
