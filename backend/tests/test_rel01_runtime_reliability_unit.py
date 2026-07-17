from __future__ import annotations

from fastapi import FastAPI

from lib.runtime_reliability import RUNTIME_STATE, runtime_health_snapshot, set_readiness


def _app() -> FastAPI:
    app = FastAPI()
    app.state.ready = False
    RUNTIME_STATE["startup_complete"] = True
    RUNTIME_STATE["ready"] = False
    RUNTIME_STATE["readiness_reason"] = "startup_incomplete"
    RUNTIME_STATE["mongo"].update({"ok": True, "latency_ms": 10})
    RUNTIME_STATE["event_loop"].update({"lag_ms": 0.0, "max_lag_ms": 0.0, "last_checked_at": None})
    RUNTIME_STATE["resources"] = {"disk_percent": 10.0, "cpu_percent": 1.0, "rss_mb": 100.0}
    return app


def test_set_readiness_true_clears_shutdown_requested_and_restores_ready_snapshot():
    app = _app()
    RUNTIME_STATE["shutdown_requested"] = True

    set_readiness(app, ready=True, reason="startup_complete")
    snapshot = runtime_health_snapshot(app)

    assert RUNTIME_STATE["shutdown_requested"] is False
    assert snapshot["readiness"]["ok"] is True
    assert snapshot["readiness"]["state"] == "ready"