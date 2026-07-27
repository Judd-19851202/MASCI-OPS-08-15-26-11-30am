from __future__ import annotations

from lib.backup_paths import backup_prefix_search_order
from lib.hourly_activation import build_hourly_activation_state


def test_reclaimable_stale_jobs_do_not_block_hourly_activation() -> None:
    state = build_hourly_activation_state(
        requested_raw="true",
        environment="production",
        scheduler_healthy=True,
        persistence_available=True,
        backup_active=False,
        restore_active=False,
        stale_job_count=1,
        reclaimable_stale_job_count=1,
        stale_lock_present=False,
        resource_preflight={"ok": True, "reasons": []},
        r2_configured=True,
        retention_valid=True,
        retention_reason="approved_tiered_retention",
    )

    assert state["activation_status"] == "ACTIVE"
    assert state["blocking_stale_job_count"] == 0
    assert state["reclaimable_stale_job_count"] == 1
    assert state["r2_hourly_effective"] is True


def test_production_prefix_search_order_does_not_fall_back_to_legacy_prefix() -> None:
    prefixes = backup_prefix_search_order("production", explicit_prefix="backups/production/auto-90d/")
    assert prefixes == ["backups/production/auto-90d/"]


def test_preview_prefix_search_order_is_environment_scoped() -> None:
    prefixes = backup_prefix_search_order("preview", explicit_prefix="backups/preview/auto-90d/")
    assert prefixes == ["backups/preview/auto-90d/"]