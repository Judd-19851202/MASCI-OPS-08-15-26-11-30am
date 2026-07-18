from __future__ import annotations

import importlib
import os
import sys


sys.path.insert(0, "/app/backend")


def _fresh_server_module():
    sys.modules.pop("server", None)
    return importlib.import_module("server")


def test_mongo_client_kwargs_have_fail_fast_timeouts(monkeypatch):
    monkeypatch.setenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "4321")
    monkeypatch.setenv("MONGO_CONNECT_TIMEOUT_MS", "5432")
    monkeypatch.setenv("MONGO_SOCKET_TIMEOUT_MS", "6543")
    srv = _fresh_server_module()
    kwargs = srv._mongo_client_kwargs()
    assert kwargs["tz_aware"] is True
    assert kwargs["maxPoolSize"] == 50
    assert kwargs["serverSelectionTimeoutMS"] == 4321
    assert kwargs["connectTimeoutMS"] == 5432
    assert kwargs["socketTimeoutMS"] == 6543


def test_mongo_client_kwargs_default_to_safe_production_values(monkeypatch):
    monkeypatch.delenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", raising=False)
    monkeypatch.delenv("MONGO_CONNECT_TIMEOUT_MS", raising=False)
    monkeypatch.delenv("MONGO_SOCKET_TIMEOUT_MS", raising=False)
    srv = _fresh_server_module()
    kwargs = srv._mongo_client_kwargs()
    assert kwargs["serverSelectionTimeoutMS"] == 8000
    assert kwargs["connectTimeoutMS"] == 8000
    assert kwargs["socketTimeoutMS"] == 15000