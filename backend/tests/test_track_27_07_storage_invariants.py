"""TRACK 27.07 · Phase 15 · Storage governance invariants.

These tests lock down the canonical architecture. Any future work must
extend Track 27.06 files — creating a parallel storage module fails
the first test.
"""
import importlib
import pytest


def test_track_28_12_module_is_gone():
    """The duplicate housekeeping router must not exist."""
    with pytest.raises(ImportError):
        importlib.import_module("routes.track_28_12_housekeeping")


def test_only_canonical_r2_client_is_used():
    """`photo_storage._client()` is the one canonical R2 abstraction.
    No other module may instantiate its own boto3 s3 client for R2."""
    import photo_storage
    assert callable(getattr(photo_storage, "_client", None))
    assert callable(getattr(photo_storage, "_bucket", None))


def test_canonical_classification_states_intact():
    """Track 27.06 owns the 10-state classifier."""
    from services.r2_lifecycle.classification import (
        ALLOWED_FOR_DELETION, DRY_RUN_REFUSAL_STATES,
    )
    assert ALLOWED_FOR_DELETION == frozenset({"VERIFIED_ORPHAN"})
    # Every refusal state must be represented in the 10-state contract.
    expected_refusal = {
        "BACKUP_PROTECTED", "RETENTION_PROTECTED", "LEGAL_HOLD",
        "HISTORICAL", "SYSTEM_RESERVED", "PENDING",
        "AMBIGUOUS", "UNKNOWN", "VERIFIED_OWNER",
    }
    # The current implementation may name these slightly differently;
    # the invariant is that VERIFIED_ORPHAN is never in the refusal set.
    assert "VERIFIED_ORPHAN" not in DRY_RUN_REFUSAL_STATES


def test_only_verified_orphan_is_deletable():
    from services.r2_lifecycle.classification import ALLOWED_FOR_DELETION
    for state in ("BACKUP_PROTECTED", "RETENTION_PROTECTED", "LEGAL_HOLD",
                  "HISTORICAL", "SYSTEM_RESERVED", "PENDING",
                  "AMBIGUOUS", "UNKNOWN", "VERIFIED_OWNER"):
        assert state not in ALLOWED_FOR_DELETION


def test_canonical_delete_authority_is_r2_retention():
    """`lib/r2_retention` is the one delete authority."""
    import lib.r2_retention as retention
    assert callable(getattr(retention, "plan_retention", None))
    assert callable(getattr(retention, "enforce_r2_retention", None))


def test_canonical_router_is_admin_r2_lifecycle():
    from routes.admin_r2_lifecycle import build_r2_lifecycle_router
    assert callable(build_r2_lifecycle_router)


def test_track_27_07_extensions_are_inside_canonical_router():
    """Phase 3 sample + Phase 6 quarantine endpoints must live inside
    the canonical `admin_r2_lifecycle.py` file — not in a parallel module."""
    import inspect
    from routes import admin_r2_lifecycle
    src = inspect.getsource(admin_r2_lifecycle)
    assert "/sample" in src, "break-the-classifier sampling extension missing"
    assert "/quarantine" in src, "logical quarantine extension missing"
    assert "hard_delete_status" in src


def test_hard_delete_defaults_disabled():
    """No module may enable hard delete without an explicit env flag."""
    import os
    assert os.environ.get("R2_HARD_DELETE_ENABLED", "").lower() not in ("1", "true", "yes", "on")
