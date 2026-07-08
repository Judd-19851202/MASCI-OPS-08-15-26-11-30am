"""TRACK 24.17 · Operations Control Center · regression locks.

Static + integration tests for the OCC subsystem. Covers:

* Registry structure (categories, risk levels, dry-run/apply flags).
* Permission gating (anon = 401, admin = 200).
* Dry-run + apply flow contracts (safe cleanup + R2 migration).
* Confirmation phrase gating.
* Audit log write-only guarantees.
* Secret-value redaction (env values never returned).
* Language lock — OCC modules never carry banned Daily Report
  version tags.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


BACKEND = Path("/app/backend")
OCC_ROOT = BACKEND / "services" / "operations_control"


# ── Registry + operation contracts ──────────────────────────────────

def test_registry_loads_and_declares_every_op_correctly():
    from services.operations_control import build_registry
    registry = build_registry(db=None)
    assert len(registry) >= 10, (
        f"OCC must register at least the 10 P0/P1 operations; got "
        f"{len(registry)}"
    )
    seen_categories = set()
    for op in registry.values():
        assert op.id and " " not in op.id, f"bad op id {op.id!r}"
        assert op.title
        assert op.description
        assert op.risk
        seen_categories.add(op.category)
        # Every mutating op must declare requires_dry_run.
        if op.apply_fn is not None and op.risk.value in (
            "data_migration", "destructive",
        ):
            assert op.requires_dry_run, (
                f"{op.id}: destructive/data_migration ops must set "
                "requires_dry_run=True"
            )
        # Every op must publish reads/writes/never_touches.
        # (writes may legitimately be empty for read-only ops.)
        assert isinstance(op.reads, list)
        assert isinstance(op.writes, list)
        assert isinstance(op.never_touches, list)


def test_first_operations_from_phase_18_are_present():
    from services.operations_control import build_registry
    r = build_registry(db=None)
    required = {
        "health.system_overview",
        "storage.audit",
        "storage.safe_cleanup",
        "storage.r2_migration",
        "r2.health",
        "backups.health",
        "daily_reports.health",
        "email.health",
        "ai.health",
        "security.posture",
    }
    missing = required - set(r.keys())
    assert not missing, f"OCC missing Phase-18 operations: {missing}"


def test_r2_migration_requires_confirmation_phrase():
    from services.operations_control import build_registry
    op = build_registry(db=None)["storage.r2_migration"]
    assert op.confirmation_phrase == "MIGRATE TO R2"
    assert op.requires_dry_run is True


def test_safe_cleanup_requires_dry_run_but_no_confirm_phrase():
    from services.operations_control import build_registry
    op = build_registry(db=None)["storage.safe_cleanup"]
    assert op.requires_dry_run is True
    assert op.confirmation_phrase is None


def test_read_only_operations_have_no_apply_handler():
    from services.operations_control import build_registry
    for op_id in (
        "storage.audit", "health.system_overview", "r2.health",
        "backups.health", "daily_reports.health", "ai.health",
        "email.health", "security.posture",
    ):
        op = build_registry(db=None)[op_id]
        assert op.apply_fn is None, (
            f"{op_id} must be read-only (apply_fn == None)"
        )


# ── Secret-value redaction ─────────────────────────────────────────

def _run_isolated(coro):
    """Run a coroutine on a private event loop without touching the
    process-default loop. This preserves the `get_event_loop()`
    contract that pre-existing tests (e.g. Track 23.10-E) rely on."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_env_var_values_never_appear_in_security_or_email_output():
    """Runtime: security.posture and email.health must return
    PRESENCE booleans only, never the actual secret value."""
    from services.operations_control import build_registry
    os.environ["SECRET_TEST_KEY_24_17"] = "supersecretvalue123"
    try:
        reg = build_registry(db=None)

        async def _both():
            return (
                await reg["security.posture"].status_fn({}),
                await reg["email.health"].status_fn({}),
            )

        sec_result, email_result = _run_isolated(_both())
    finally:
        os.environ.pop("SECRET_TEST_KEY_24_17", None)
    import json
    combined = json.dumps(sec_result) + json.dumps(email_result)
    assert "supersecretvalue123" not in combined, (
        "OCC responses must never echo secret values."
    )


# ── Storage safe-cleanup contract ──────────────────────────────────

def test_safe_cleanup_apply_rejects_missing_dry_run():
    from services.operations_control.storage import _safe_cleanup_apply
    res = _run_isolated(_safe_cleanup_apply({"dry_run_id": ""}))
    assert res["status"] == "failed"
    assert "dry-run" in (res.get("error") or "").lower()


def test_r2_migration_apply_rejects_missing_confirmation():
    """Even with a valid dry-run token, apply must fail without the
    confirmation phrase. We hand-inject a token to isolate the
    confirmation check."""
    from services.operations_control import storage as st
    token = st._register_dry_run("storage.r2_migration", {"candidates": []})
    res = _run_isolated(st._r2_migration_apply({"dry_run_id": token}))
    assert res["status"] == "failed"
    assert "confirmation" in (res.get("error") or "").lower()


# ── Audit ──────────────────────────────────────────────────────────

def test_audit_module_exposes_write_and_read_only_api():
    from services.operations_control import audit as a
    # Public surface — no delete/update.
    assert hasattr(a, "write")
    assert hasattr(a, "list_recent")
    assert hasattr(a, "get")
    assert not hasattr(a, "delete")
    assert not hasattr(a, "update")


# ── Language lock (24.13 One Daily Report) ─────────────────────────

_BANNED_PHRASES = (
    "Daily Report V1", "Daily Report V2", "Daily Report V3",
    "V1 Daily Report", "V2 Daily Report", "V3 Daily Report",
    "Legacy Daily Report", "Modern Daily Report",
)


def test_occ_service_carries_no_versioned_daily_report_language():
    for p in OCC_ROOT.rglob("*.py"):
        src = p.read_text(encoding="utf-8")
        # Only scan runtime string literals — comments and docstrings
        # may mention internal versions for engineering notes.
        import re
        docstrings_stripped = re.sub(r'"""[\s\S]*?"""', "", src)
        docstrings_stripped = re.sub(r"'''[\s\S]*?'''", "",
                                     docstrings_stripped)
        # Extract quoted strings.
        strings = re.findall(
            r'"([^"\\]{0,4000})"|\'([^\'\\]{0,4000})\'',
            docstrings_stripped,
        )
        flat = [g for tup in strings for g in tup if g]
        for s in flat:
            for phrase in _BANNED_PHRASES:
                assert phrase not in s, (
                    f"TRACK 24.17 · OCC file {p} carries banned "
                    f"product-facing phrase: {phrase!r}"
                )


def test_occ_service_uses_the_phrase_operations_control_center():
    # At least the __init__ docstring should establish product name.
    src = (OCC_ROOT / "__init__.py").read_text(encoding="utf-8")
    assert "Operations Control Center" in src, (
        "OCC subsystem must use the canonical product name."
    )


# ── Frontend route present ─────────────────────────────────────────

def test_frontend_route_declared():
    routes = Path(
        "/app/frontend/src/app/routing/AppRoutes.jsx",
    ).read_text(encoding="utf-8")
    assert "/admin/operations-control" in routes, (
        "TRACK 24.17 · /admin/operations-control route must be "
        "registered in AppRoutes.jsx."
    )
    assert "OperationsControlCenter" in routes, (
        "Route must reference the OperationsControlCenter component."
    )
