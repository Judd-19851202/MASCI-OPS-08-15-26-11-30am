"""P0-CAPACITY-2026-08-13 — real storage-capacity truth regressions.

Proves the canonical capacity owner uses REAL physical Atlas metrics, that the
legacy ATLAS_QUOTA_MB cannot masquerade as physical disk capacity, dynamic
capacity, UNKNOWN-not-fake fallback, operating-budget labeling, hysteresis
alert thresholds, and recovery semantics.
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from lib import storage_capacity_truth as sct


# ---- Pure severity truth ----
def test_physical_severity_thresholds():
    assert sct.canonical_physical_severity(10.0) == sct.SEV_HEALTHY
    assert sct.canonical_physical_severity(79.9) == sct.SEV_HEALTHY
    assert sct.canonical_physical_severity(80.0) == sct.SEV_WARNING
    assert sct.canonical_physical_severity(89.9) == sct.SEV_WARNING
    assert sct.canonical_physical_severity(90.0) == sct.SEV_HIGH
    assert sct.canonical_physical_severity(95.0) == sct.SEV_CRITICAL
    assert sct.canonical_physical_severity(98.0) == sct.SEV_EMERGENCY
    assert sct.canonical_physical_severity(99.9) == sct.SEV_EMERGENCY


def test_unknown_physical_is_not_faked():
    assert sct.canonical_physical_severity(None) == sct.SEV_UNKNOWN


def test_operating_budget_is_optional(monkeypatch):
    monkeypatch.delenv("ATLAS_OPERATING_BUDGET_MB", raising=False)
    monkeypatch.delenv("ATLAS_QUOTA_MB", raising=False)
    assert sct.operating_budget_mb() is None
    monkeypatch.setenv("ATLAS_QUOTA_MB", "0")
    assert sct.operating_budget_mb() is None  # 0 == unbounded
    monkeypatch.setenv("ATLAS_QUOTA_MB", "10240")
    assert sct.operating_budget_mb() == 10240
    monkeypatch.setenv("ATLAS_OPERATING_BUDGET_MB", "20480")
    assert sct.operating_budget_mb() == 20480  # new name wins


# ---- Fake async mongo client ----
class _FakeDB:
    def __init__(self, name, stats):
        self._name = name
        self._stats = stats

    async def command(self, *_a, **_k):
        if self._stats is None:
            raise RuntimeError("dbstats unavailable")
        return self._stats


class _FakeClient:
    def __init__(self, per_db):
        self._per_db = per_db

    def __getitem__(self, name):
        return _FakeDB(name, self._per_db.get(name))


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_build_truth_uses_real_physical_not_budget(monkeypatch):
    monkeypatch.setenv("ATLAS_QUOTA_MB", "10240")
    # Physical volume 100 GB, 50 GB used = 50% physical, but logical only 1 GB.
    stats = {
        "fsTotalSize": 100 * 1024 * 1024 * 1024,
        "fsUsedSize": 50 * 1024 * 1024 * 1024,
        "storageSize": 500 * 1024 * 1024,
        "indexSize": 500 * 1024 * 1024,
    }
    client = _FakeClient({"masci_safety": stats, "masci_safety_preview": stats})
    monkeypatch.setattr(sct, "managed_database_names", lambda _ri: ["masci_safety", "masci_safety_preview"])
    truth = _run(sct.build_capacity_truth(client, {"identity": {"db_name": "masci_safety"}}))
    assert truth["physical"]["status"] == "MEASURED"
    assert truth["physical"]["physical_utilization_percent"] == 50.0
    # Severity is driven by physical (50% = HEALTHY), NOT by logical-vs-budget.
    assert truth["severity"] == sct.SEV_HEALTHY
    assert truth["severity_basis"] == "physical_utilization"
    # Operating budget is present but clearly advisory/separate.
    assert truth["operating_budget"]["configured"] is True
    assert truth["operating_budget"]["operating_budget_mb"] == 10240


def test_dynamic_capacity_when_infra_expands(monkeypatch):
    monkeypatch.setattr(sct, "managed_database_names", lambda _ri: ["masci_safety"])
    small = {"fsTotalSize": 10 * 1024**3, "fsUsedSize": 9 * 1024**3, "storageSize": 0, "indexSize": 0}
    big = {"fsTotalSize": 100 * 1024**3, "fsUsedSize": 9 * 1024**3, "storageSize": 0, "indexSize": 0}
    t1 = _run(sct.build_capacity_truth(_FakeClient({"masci_safety": small}), {"identity": {"db_name": "masci_safety"}}))
    t2 = _run(sct.build_capacity_truth(_FakeClient({"masci_safety": big}), {"identity": {"db_name": "masci_safety"}}))
    assert t1["physical"]["physical_utilization_percent"] == 90.0  # HIGH
    assert t1["severity"] == sct.SEV_HIGH
    # No code/config change — just larger real infra → utilization drops automatically.
    assert t2["physical"]["physical_utilization_percent"] == 9.0
    assert t2["severity"] == sct.SEV_HEALTHY


def test_unknown_physical_when_fs_metrics_absent(monkeypatch):
    monkeypatch.setenv("ATLAS_QUOTA_MB", "10240")
    monkeypatch.setattr(sct, "managed_database_names", lambda _ri: ["masci_safety"])
    # dbStats returns logical sizes but NO fs metrics → physical UNKNOWN (not faked to budget).
    stats = {"storageSize": 9000 * 1024 * 1024, "indexSize": 0}
    truth = _run(sct.build_capacity_truth(_FakeClient({"masci_safety": stats}), {"identity": {"db_name": "masci_safety"}}))
    assert truth["physical"]["status"] == sct.SEV_UNKNOWN
    assert truth["severity"] == sct.SEV_UNKNOWN
    assert truth["severity_basis"] == "unknown_physical_telemetry"


# ---- Hysteresis / recovery ----
def test_should_alert_only_on_upward_cross():
    assert sct._should_alert(sct.SEV_HEALTHY, sct.SEV_WARNING, 82.0) is True
    assert sct._should_alert(sct.SEV_WARNING, sct.SEV_HIGH, 91.0) is True
    assert sct._should_alert(sct.SEV_HIGH, sct.SEV_WARNING, 85.0) is False  # downgrade → no new alert
    assert sct._should_alert(sct.SEV_WARNING, sct.SEV_WARNING, 83.0) is False  # same band


def test_recovery_uses_reset_thresholds():
    # Previously WARNING (reset 77). At 76% → recovered; at 78% → not yet.
    assert sct._has_recovered(sct.SEV_WARNING, 76.0) is True
    assert sct._has_recovered(sct.SEV_WARNING, 78.0) is False
    assert sct._has_recovered(sct.SEV_CRITICAL, 91.0) is True   # reset 92
    assert sct._has_recovered(sct.SEV_HEALTHY, 10.0) is False


def test_alert_recipients_never_empty_string(monkeypatch):
    for k in ("CAPACITY_ALERT_TO", "INFRA_ALERT_TO", "OPS_ALERT_TO", "ADMIN_DEAD_LETTER_EMAIL", "SUPER_ADMIN_EMAIL", "ADMIN_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    assert sct.resolve_capacity_alert_recipients() == []
    monkeypatch.setenv("CAPACITY_ALERT_TO", "ops@example.com, bad, owner@example.com")
    assert sct.resolve_capacity_alert_recipients() == ["ops@example.com", "owner@example.com"]


def test_no_employee_banner_mounted():
    """Phase 5 — the platform-wide capacity banner must NOT be mounted on the
    global App shell or the public routing tree."""
    app_js = open(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "App.js")).read()
    assert "<ClusterCapacityBanner" not in app_js
    routes = open(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "app", "routing", "AppRoutes.jsx")).read()
    assert "<ClusterCapacityBanner" not in routes
