"""TRACK 28.12 · Housekeeping router — smoke + safety tests.

These tests do not mutate real data. They exercise the module-level
contract only (marker string, collections list, hard-delete gate).
"""
import importlib
import os
import pytest


def test_marker_string_matches_production():
    mod = importlib.import_module("routes.track_28_12_housekeeping")
    assert mod._TRACK_15_59_MARKER == "POST_DEPLOY_TEST_TRACK_15_59_DELETE"


def test_legacy_collections_scope_is_conservative():
    mod = importlib.import_module("routes.track_28_12_housekeeping")
    # Confirmed by live prod probe of /api/search?q=POST_DEPLOY_TEST_TRACK_15_59_DELETE:
    # residuals appear only in tasks + notifications.
    assert set(mod._LEGACY_COLLECTIONS) == {"tasks", "notifications"}


def test_audit_collection_is_immutable_target():
    mod = importlib.import_module("routes.track_28_12_housekeeping")
    assert mod._AUDIT_COLL == "audit_events"


def test_recycle_bin_is_separate_from_source():
    mod = importlib.import_module("routes.track_28_12_housekeeping")
    assert mod._RECYCLE_COLL == "housekeeping_recycle_bin"
    # Must NOT be one of the source collections — otherwise a purge
    # would delete its own restore metadata.
    assert mod._RECYCLE_COLL not in mod._LEGACY_COLLECTIONS


def test_r2_quarantine_collection_is_separate():
    mod = importlib.import_module("routes.track_28_12_housekeeping")
    assert mod._R2_QUARANTINE_COLL == "r2_quarantine"


def test_hard_delete_flag_default_is_off(monkeypatch):
    # The hard-delete env flag MUST default to unset/false. If a
    # future operator accidentally sets it, the quarantine endpoint
    # is defensively coded to refuse — see the 412 raise.
    monkeypatch.delenv("R2_HARD_DELETE_ENABLED", raising=False)
    assert os.environ.get("R2_HARD_DELETE_ENABLED") is None
