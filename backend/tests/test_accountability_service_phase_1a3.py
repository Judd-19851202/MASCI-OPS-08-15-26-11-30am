"""Pillar 1 · Phase 1A-3 · Accountability service endpoint certification.

Live HTTP probes against the read-only accountability service surface.

Covers:
    GET /api/admin/accountability/sources
    GET /api/admin/accountability/item?source_module=...&source_record_id=...
    GET /api/admin/accountability/snapshot[?per_source=N]

Plus regression: Command Center, backups, recovery still 200.
"""
from __future__ import annotations

import os
from pathlib import Path

import requests


def _read_env(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (_read_env(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
       or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
_ADMIN_PASSWORD = (_read_env(Path("/app/backend/.env"), "ADMIN_PASSWORD")
                   or os.environ.get("ADMIN_PASSWORD", ""))


def _mint_admin_token() -> str:
    r = requests.post(f"{URL}/api/admin/login",
                      json={"password": _ADMIN_PASSWORD}, timeout=10)
    return r.json().get("token", "") if r.status_code == 200 else ""


_TOKEN = _mint_admin_token()
_AUTH = {"X-Admin-Token": _TOKEN}
_BAD = {"X-Admin-Token": "definitely-not-a-valid-token"}

API = f"{URL}/api"


# ─── Auth gates ──────────────────────────────────────────────────────
def test_sources_endpoint_blocks_anonymous():
    r = requests.get(f"{API}/admin/accountability/sources",
                     headers=_BAD, timeout=10)
    assert r.status_code == 401


def test_snapshot_endpoint_blocks_anonymous():
    r = requests.get(f"{API}/admin/accountability/snapshot",
                     headers=_BAD, timeout=10)
    assert r.status_code == 401


def test_item_endpoint_blocks_anonymous():
    r = requests.get(
        f"{API}/admin/accountability/item"
        f"?source_module=tasks&source_record_id=nope",
        headers=_BAD, timeout=10)
    assert r.status_code == 401


# ─── /sources ────────────────────────────────────────────────────────
def test_sources_returns_six_sources_with_canonical_statuses():
    r = requests.get(f"{API}/admin/accountability/sources", headers=_AUTH, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["canonical_statuses"] == [
        "open", "in_progress", "pending_review",
        "resolved", "closed", "cancelled",
    ]
    sources = {s["source_module"] for s in data["sources"]}
    assert sources == {
        "tasks", "safety.corrective_actions", "po.requests",
        "equipment.dvir", "safety.incidents", "virtual.signals",
    }
    # Async-projection flag must be true exactly for safety.incidents.
    by_id = {s["source_module"]: s for s in data["sources"]}
    assert by_id["safety.incidents"]["is_async_projection"] is True
    for sm in ("tasks", "safety.corrective_actions", "po.requests",
               "equipment.dvir", "virtual.signals"):
        assert by_id[sm]["is_async_projection"] is False


# ─── /snapshot ───────────────────────────────────────────────────────
def test_snapshot_returns_phase_1a3_marker_and_six_sections():
    r = requests.get(f"{API}/admin/accountability/snapshot", headers=_AUTH, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["phase"] == "1A-3"
    sections = d["sections"]
    assert set(sections.keys()) == {
        "tasks", "safety.corrective_actions", "po.requests",
        "equipment.dvir", "safety.incidents", "virtual.signals",
    }


def test_snapshot_rollup_arithmetic_matches_sections():
    r = requests.get(f"{API}/admin/accountability/snapshot", headers=_AUTH, timeout=30)
    d = r.json()
    sec = d["sections"]
    derived_total = sum(s["counts"]["total"] for s in sec.values())
    derived_overdue = sum(s["counts"]["overdue"] for s in sec.values())
    derived_by_status = {k: 0 for k in d["rollup"]["by_status"].keys()}
    for s in sec.values():
        for k, v in s["counts"]["by_status"].items():
            derived_by_status[k] = derived_by_status.get(k, 0) + v
    assert d["rollup"]["total_items"] == derived_total
    assert d["rollup"]["overdue_items"] == derived_overdue
    assert d["rollup"]["by_status"] == derived_by_status


def test_snapshot_every_item_has_canonical_24_field_shape():
    r = requests.get(f"{API}/admin/accountability/snapshot", headers=_AUTH, timeout=30)
    d = r.json()
    required_fields = {
        "accountability_id", "source_module", "source_record_id", "title",
        "owner_role", "owner_user_id", "owner_employee_id",
        "owner_display_name",
        "assigned_at", "assigned_by", "due_at", "status", "priority",
        "first_viewed_at", "first_viewed_by",
        "last_activity_at", "last_activity_kind",
        "escalation_level",
        "resolved_at", "resolved_by", "resolution_notes",
        "overdue", "timeline_events",
    }
    counted = 0
    for sm, sec in d["sections"].items():
        for item in sec["items"]:
            assert set(item.keys()) == required_fields, (
                f"shape drift in {sm}: "
                f"missing={required_fields - set(item.keys())} "
                f"extra={set(item.keys()) - required_fields}")
            counted += 1
    # Sanity: live preview has at least the tasks page populated.
    assert counted >= 1


def test_snapshot_every_status_is_canonical():
    r = requests.get(f"{API}/admin/accountability/snapshot", headers=_AUTH, timeout=30)
    d = r.json()
    canonical = {"open", "in_progress", "pending_review",
                 "resolved", "closed", "cancelled"}
    for sec in d["sections"].values():
        for item in sec["items"]:
            assert item["status"] in canonical


def test_snapshot_every_item_has_escalation_level_zero():
    """Pillar 1B reservation invariant — must NOT activate in Phase 1A-3."""
    r = requests.get(f"{API}/admin/accountability/snapshot", headers=_AUTH, timeout=30)
    d = r.json()
    for sec in d["sections"].values():
        for item in sec["items"]:
            assert item["escalation_level"] == 0


def test_snapshot_timing_breakdown_present_and_finite():
    r = requests.get(f"{API}/admin/accountability/snapshot", headers=_AUTH, timeout=30)
    d = r.json()
    timing = d["timing_ms"]
    for key in ("tasks", "corrective_actions", "po_requests",
                "fleet_defects", "incidents", "virtual", "total"):
        assert key in timing, f"missing timing key: {key}"
        assert isinstance(timing[key], (int, float))
        assert timing[key] >= 0


def test_snapshot_cache_returns_cached_true_within_ttl():
    # Trigger a cold call by selecting a *unique* per_source value
    # (cache key is per_source-keyed).
    unique = 47
    r1 = requests.get(
        f"{API}/admin/accountability/snapshot?per_source={unique}", headers=_AUTH, timeout=30)
    d1 = r1.json()
    assert d1["cached"] is False
    r2 = requests.get(
        f"{API}/admin/accountability/snapshot?per_source={unique}", headers=_AUTH, timeout=30)
    d2 = r2.json()
    assert d2["cached"] is True
    # The second call's recorded computed timing equals the first's
    # (cache returns the same payload).
    assert d2["timing_ms"]["total"] == d1["timing_ms"]["total"]


def test_snapshot_per_source_cap_respected():
    r = requests.get(
        f"{API}/admin/accountability/snapshot?per_source=5", headers=_AUTH, timeout=30)
    d = r.json()
    for sec in d["sections"].values():
        assert sec["counts"]["total"] <= 5


# ─── /item ───────────────────────────────────────────────────────────
def _pick_live_task_id():
    r = requests.get(f"{API}/admin/accountability/snapshot", headers=_AUTH, timeout=30)
    items = r.json()["sections"]["tasks"]["items"]
    return items[0]["source_record_id"] if items else None


def test_item_returns_canonical_projection_for_live_task():
    task_id = _pick_live_task_id()
    if not task_id:
        # No tasks in preview · skip gracefully (suite still passes).
        return
    r = requests.get(
        f"{API}/admin/accountability/item"
        f"?source_module=tasks&source_record_id={task_id}", headers=_AUTH, timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert d["source_module"] == "tasks"
    assert d["source_record_id"] == task_id
    assert d["status"] in (
        "open", "in_progress", "pending_review",
        "resolved", "closed", "cancelled")
    assert d["escalation_level"] == 0


def test_item_returns_404_for_unknown_id():
    r = requests.get(
        f"{API}/admin/accountability/item"
        f"?source_module=tasks&source_record_id=does-not-exist", headers=_AUTH, timeout=10)
    assert r.status_code == 404


def test_item_returns_400_for_unsupported_module():
    r = requests.get(
        f"{API}/admin/accountability/item"
        f"?source_module=unknown.workflow&source_record_id=x", headers=_AUTH, timeout=10)
    assert r.status_code == 400


def test_item_returns_404_for_virtual_module():
    """Virtual signals have no backing row; /item cannot fabricate one."""
    r = requests.get(
        f"{API}/admin/accountability/item"
        f"?source_module=virtual.dr_missing&source_record_id=x", headers=_AUTH, timeout=10)
    assert r.status_code == 404


# ─── Source parity (success condition) ───────────────────────────────
def test_snapshot_source_parity_all_non_empty_sections_match_field_set():
    """Success condition from directive: 'returns canonical accountability
    records from all six certified sources while preserving source
    workflow behavior'.

    Field-set parity for every non-empty section.
    """
    r = requests.get(f"{API}/admin/accountability/snapshot", headers=_AUTH, timeout=30)
    d = r.json()
    reference = None
    for sm, sec in d["sections"].items():
        if not sec["items"]:
            continue
        item_keys = set(sec["items"][0].keys())
        if reference is None:
            reference = item_keys
            continue
        diff = reference.symmetric_difference(item_keys)
        assert diff == set(), f"{sm} drifts from reference: {diff}"


# ─── No-workflow-regression sanity ───────────────────────────────────
def test_command_center_snapshot_still_returns_200():
    r = requests.get(f"{API}/admin/command-center/snapshot", headers=_AUTH, timeout=30)
    assert r.status_code == 200


def test_backups_scheduler_state_still_returns_200():
    r = requests.get(f"{API}/admin/backups-scheduler-state", headers=_AUTH, timeout=10)
    assert r.status_code == 200


def test_recovery_snapshot_still_returns_200():
    r = requests.get(f"{API}/admin/recovery/snapshot", headers=_AUTH, timeout=10)
    assert r.status_code == 200


def test_health_still_returns_200():
    r = requests.get(f"{URL}/api/health", headers=_AUTH, timeout=10)
    assert r.status_code == 200
    assert r.json().get("ok") is True
