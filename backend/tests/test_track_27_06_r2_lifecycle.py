"""
TRACK 27.06 · R2 lifecycle governance — regression tests.

Pure-function coverage for the classification engine, the reference
extractor, the cost estimator, and the storage-health sub-scores.

The R2 walker + Mongo cross-reference walker are I/O bound; they get a
smaller happy-path test using a fake `AsyncIOMotorCollection`-shaped
stub and a fake boto3 client.  End-to-end coverage lives with the
frontend testing agent + the live post-deploy checks — this suite is
strictly the pure-logic guard.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

import pytest

from services.r2_lifecycle.classification import (
    ALLOWED_FOR_DELETION,
    CLASSIFICATIONS,
    DRY_RUN_REFUSAL_STATES,
    classify_object,
)
from services.r2_lifecycle.intelligence import estimate_cost
from services.r2_lifecycle.health import (
    _band,
    _clamp,
)
from services.r2_lifecycle.references import (
    REFERENCE_SOURCES,
    _extract_key,
    _walk_path,
)


NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)


def _iso(delta_hours: float = 0) -> str:
    return (NOW - timedelta(hours=delta_hours)).isoformat()


# ── Classification engine ──────────────────────────────────────────────
def test_classifications_are_a_closed_set():
    assert set(CLASSIFICATIONS) == {
        "VERIFIED_OWNER", "VERIFIED_ORPHAN", "AMBIGUOUS", "SYSTEM_RESERVED",
        "RETENTION_PROTECTED", "BACKUP_PROTECTED", "LEGAL_HOLD",
        "HISTORICAL", "PENDING", "UNKNOWN",
    }


def test_only_orphans_are_deletable():
    assert ALLOWED_FOR_DELETION == {"VERIFIED_ORPHAN"}
    # Every non-orphan class refuses a batch.
    assert "AMBIGUOUS" in DRY_RUN_REFUSAL_STATES
    assert "SYSTEM_RESERVED" in DRY_RUN_REFUSAL_STATES
    assert "PENDING" in DRY_RUN_REFUSAL_STATES
    assert "VERIFIED_ORPHAN" not in DRY_RUN_REFUSAL_STATES


def test_system_reserved_prefix_wins_even_with_references():
    inv = {"key": "system/protected.zip", "last_modified": _iso(24 * 365), "size": 1}
    refs = [{"collection": "photos"}]
    r = classify_object(inv, refs, now=NOW)
    assert r.classification == "SYSTEM_RESERVED"
    assert "system_reserved" in r.protective_flags


def test_backup_prefix_is_protected():
    inv = {"key": "MASCI_complete_backup_2026-07-10.zip",
           "last_modified": _iso(24 * 90), "size": 100}
    r = classify_object(inv, refs=[], now=NOW)
    assert r.classification == "BACKUP_PROTECTED"


def test_historical_prefix_is_protected():
    inv = {"key": "legacy-imports/scan-2019.pdf",
           "last_modified": _iso(24 * 365), "size": 100}
    r = classify_object(inv, refs=[], now=NOW)
    assert r.classification == "HISTORICAL"


def test_pending_window_blocks_fresh_uploads():
    inv = {"key": "photos/2026/xyz.jpg", "last_modified": _iso(0.5), "size": 100}
    r = classify_object(inv, refs=[], now=NOW)
    assert r.classification == "PENDING"


def test_verified_owner_when_mongo_reference_exists():
    inv = {"key": "photos/2026/known.jpg", "last_modified": _iso(48), "size": 100}
    refs = [{"collection": "daily_reports", "owner": "Daily Report",
             "feature": "daily_reports", "doc_id": "dr-1",
             "field_path": "photos.*.storage_ref"}]
    r = classify_object(inv, refs, now=NOW)
    assert r.classification == "VERIFIED_OWNER"
    assert r.evidence[0]["collection"] == "daily_reports"


def test_verified_orphan_when_no_reference_and_older_than_window():
    inv = {"key": "photos/2024/lost.jpg", "last_modified": _iso(24 * 200), "size": 100}
    r = classify_object(inv, refs=[], now=NOW)
    assert r.classification == "VERIFIED_ORPHAN"
    assert not r.protective_flags


def test_classifier_never_returns_unknown_for_well_formed_input():
    inv = {"key": "photos/2024/x.jpg", "last_modified": _iso(48), "size": 1}
    r = classify_object(inv, refs=[], now=NOW)
    assert r.classification in CLASSIFICATIONS
    assert r.classification != "UNKNOWN"


# ── Reference extractor ────────────────────────────────────────────────
def test_extract_key_photo_scheme():
    assert _extract_key("photo://bucket/photos/x.jpg", "photo://") == "photos/x.jpg"
    assert _extract_key("photo://bucket/", "photo://") is None
    assert _extract_key("not-a-ref", "photo://") is None
    assert _extract_key("", "photo://") is None
    assert _extract_key(None, "photo://") is None
    assert _extract_key(123, "photo://") is None


def test_extract_key_r2_scheme():
    assert _extract_key("r2://bucket/complete-backups/x.zip", "r2://") == "complete-backups/x.zip"


def test_extract_key_raw_scheme():
    assert _extract_key("complete-backups/x.zip", "raw_key") == "complete-backups/x.zip"
    assert _extract_key("/complete-backups/x.zip", "raw_key") == "complete-backups/x.zip"
    assert _extract_key("photo://bucket/x.jpg", "raw_key") is None  # has scheme prefix


def test_walk_path_dot_and_wildcard():
    doc = {
        "attachments": [
            {"storage_ref": "photo://b/a.jpg"},
            {"storage_ref": "photo://b/c.jpg"},
        ],
        "cover": {"storage_ref": "photo://b/cover.jpg"},
    }
    assert list(_walk_path(doc, "cover.storage_ref")) == ["photo://b/cover.jpg"]
    values = sorted(list(_walk_path(doc, "attachments.*.storage_ref")))
    assert values == ["photo://b/a.jpg", "photo://b/c.jpg"]
    assert list(_walk_path(doc, "missing.path")) == []


def test_reference_sources_registry_shape():
    seen: List[str] = []
    for src in REFERENCE_SOURCES:
        assert src.collection and src.owner and src.feature
        assert src.ref_scheme in {"photo://", "r2://", "raw_key", "doc://"}
        assert isinstance(src.paths, list) and src.paths
        seen.append(src.collection)
    # A minimum floor — the classifier depends on these being registered.
    for required in ("photos", "daily_reports", "backup_health"):
        assert required in seen


# ── Cost + health scoring ──────────────────────────────────────────────
def test_estimate_cost_scales_with_bytes():
    gb = 1024 ** 3  # 1 GiB
    result = estimate_cost(total_bytes=100 * gb, orphan_bytes=10 * gb)
    assert result["unit_price_usd_per_gb_month"] == pytest.approx(0.015)
    assert result["current_monthly_usd"] == pytest.approx(1.5, rel=1e-3)
    assert result["orphan_reclaim_monthly_usd"] == pytest.approx(0.15, rel=1e-3)
    assert result["projected_savings_pct"] == pytest.approx(10.0, rel=1e-2)


def test_estimate_cost_handles_zero_total():
    assert estimate_cost(0, 0)["projected_savings_pct"] == 0.0


# TRACK 27.07A · PHASE 1 · The `_capacity_score` helper was retired
# because it hardcoded the obsolete 45/50 GB heuristic. Capacity
# signalling is now sourced from the composite policy (technical_capacity
# dimension) against the *provider ceiling* only, and cost pressure is
# a separate dimension. See test_track_27_07a_composite_policy.py.


def test_band_thresholds():
    assert _band(90) == "GREEN"
    assert _band(70) == "AMBER"
    assert _band(50) == "RED"


def test_clamp_bounds():
    assert _clamp(-5) == 0
    assert _clamp(50) == 50
    assert _clamp(150) == 100
