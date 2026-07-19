from __future__ import annotations

from pathlib import Path

from lib import canonical_status
from routes import admin_ops, integration_truth, occ_health_aggregator, platform_data_truth


def test_canonical_status_uses_only_d2_vocabulary() -> None:
    assert canonical_status.CANONICAL_STATES == {
        "VERIFIED",
        "MISMATCH",
        "UNVERIFIABLE",
        "DEGRADED",
        "NOT_APPLICABLE",
    }


def test_legacy_statuses_map_into_d2_vocabulary() -> None:
    assert canonical_status.to_canonical("green") == "VERIFIED"
    assert canonical_status.to_canonical("yellow") == "DEGRADED"
    assert canonical_status.to_canonical("red") == "MISMATCH"
    assert canonical_status.to_canonical("unknown") == "UNVERIFIABLE"
    assert canonical_status.to_canonical("disabled", mocked=True) == "NOT_APPLICABLE"


def test_summarize_returns_d2_count_shape() -> None:
    summary = canonical_status.summarize([
        {"canonical_status": "VERIFIED"},
        {"canonical_status": "DEGRADED"},
        {"canonical_status": "MISMATCH"},
        {"canonical_status": "UNVERIFIABLE"},
        {"canonical_status": "NOT_APPLICABLE"},
    ])
    assert summary["verified"] == 1
    assert summary["degraded"] == 1
    assert summary["mismatch"] == 1
    assert summary["unverifiable"] == 1
    assert summary["not_applicable"] == 1
    assert summary["highest"] == "MISMATCH"


def test_occ_worst_status_uses_d2_ordering() -> None:
    assert occ_health_aggregator._worst_status([
        {"status": "VERIFIED"},
        {"status": "DEGRADED"},
        {"status": "MISMATCH"},
    ]) == "MISMATCH"
    assert occ_health_aggregator._worst_status([
        {"status": "VERIFIED"},
        {"status": "UNVERIFIABLE"},
    ]) == "UNVERIFIABLE"


def test_d2_surfaces_no_longer_depend_on_local_env_parsing() -> None:
    admin_source = Path(admin_ops.__file__).read_text(encoding="utf-8")
    integration_source = Path(integration_truth.__file__).read_text(encoding="utf-8")
    occ_source = Path(occ_health_aggregator.__file__).read_text(encoding="utf-8")
    platform_source = Path(platform_data_truth.__file__).read_text(encoding="utf-8")
    assert "APP_ENV" not in admin_source
    assert "DB_NAME" not in admin_source
    assert "APP_ENV" not in occ_source
    assert "DB_NAME" not in occ_source
    assert "APP_ENV" not in platform_source
    assert "DB_NAME" not in platform_source
    assert "get_runtime_identity" in integration_source
