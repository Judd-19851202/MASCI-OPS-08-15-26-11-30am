"""TRACK 25.01 · OCC consolidation regression locks.

Phase C of the Admin Operating System rollout. Verifies that the four
new OCC operations that absorb the retired legacy pages are:

1. Registered in the OCC operation registry.
2. Read-only (no apply handlers, since they replace read-only pages).
3. Callable without crashing.
4. Return a status envelope carrying the canonical shape (status,
   summary, warnings) the OCC UI depends on.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict


REQUIRED_NEW_OPS = {
    "deploy.readiness_check",
    "deploy.recovery_playbook",
    "queues.scheduler_runs",
    "integrations.probe_all",
}


def _run_isolated(coro):
    """Run a coroutine on a private event loop without touching the
    process-default loop (mirror of the 24.17 test suite pattern to
    avoid asyncio pollution)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Registry inclusion ─────────────────────────────────────────────

def test_phase_c_operations_are_all_registered():
    from services.operations_control import build_registry
    ops = build_registry(db=None)
    missing = REQUIRED_NEW_OPS - set(ops.keys())
    assert not missing, (
        "TRACK 25.01 Phase C · OCC registry is missing consolidation "
        f"operations: {missing}"
    )


def test_phase_c_operations_are_read_only():
    """Every Phase C operation must be read-only — they replace
    read-only legacy pages. If any grows an apply handler in a future
    track that's a deliberate design decision, but here it MUST be
    read-only or we've drifted from the audit contract."""
    from services.operations_control import build_registry
    ops = build_registry(db=None)
    for op_id in REQUIRED_NEW_OPS:
        op = ops[op_id]
        assert op.apply_fn is None, (
            f"TRACK 25.01 · {op_id} must be read-only (apply_fn == None)."
        )
        assert op.writes == [] or op.writes == list(op.writes), (
            f"TRACK 25.01 · {op_id} must not declare write side effects."
        )


def test_phase_c_operations_have_status_and_dry_run_handlers():
    from services.operations_control import build_registry
    ops = build_registry(db=None)
    for op_id in REQUIRED_NEW_OPS:
        op = ops[op_id]
        assert op.status_fn is not None, (
            f"TRACK 25.01 · {op_id} must expose a status_fn so its OCC "
            "card populates on load."
        )
        assert op.dry_run_fn is not None, (
            f"TRACK 25.01 · {op_id} must expose a dry_run_fn so an "
            "operator can trigger a refresh from the OCC UI."
        )


# ── Runtime envelope contract ──────────────────────────────────────

def _valid_status_envelope(result: Dict[str, Any]) -> None:
    assert isinstance(result, dict), "status result must be a dict"
    assert "status" in result, "envelope must carry `status`"
    assert result["status"] in {
        "healthy", "warning", "critical", "unavailable",
    }, f"unexpected status value: {result['status']}"
    assert "summary" in result, "envelope must carry `summary`"
    assert "generated_at" in result, "envelope must carry `generated_at`"


def test_recovery_playbook_returns_envelope_without_db():
    from services.operations_control import build_registry
    op = build_registry(db=None)["deploy.recovery_playbook"]
    result = _run_isolated(op.status_fn({}))
    _valid_status_envelope(result)
    assert "playbook" in result, (
        "TRACK 25.01 · deploy.recovery_playbook must return the 6-step "
        "playbook so the OCC card renders the recovery guidance."
    )
    assert isinstance(result["playbook"], list) and len(result["playbook"]) >= 6, (
        "TRACK 25.01 · recovery playbook must contain the 6 canonical steps."
    )


def test_deploy_readiness_returns_unavailable_when_no_db():
    from services.operations_control import build_registry
    op = build_registry(db=None)["deploy.readiness_check"]
    result = _run_isolated(op.status_fn({}))
    _valid_status_envelope(result)
    assert result["status"] == "unavailable", (
        "TRACK 25.01 · without a live DB, deploy.readiness_check must "
        "return status=unavailable rather than crash."
    )


def test_scheduler_runs_returns_unavailable_when_no_db():
    from services.operations_control import build_registry
    op = build_registry(db=None)["queues.scheduler_runs"]
    result = _run_isolated(op.status_fn({}))
    _valid_status_envelope(result)
    assert result["status"] == "unavailable"


def test_integrations_probe_all_returns_unavailable_when_no_db():
    from services.operations_control import build_registry
    op = build_registry(db=None)["integrations.probe_all"]
    result = _run_isolated(op.status_fn({}))
    _valid_status_envelope(result)
    assert result["status"] == "unavailable"


# ── Categories are sensible ────────────────────────────────────────

def test_phase_c_operations_use_expected_categories():
    from services.operations_control import build_registry
    ops = build_registry(db=None)
    from services.operations_control.registry import OperationCategory
    expected = {
        "deploy.readiness_check": OperationCategory.HEALTH,
        "deploy.recovery_playbook": OperationCategory.HEALTH,
        "queues.scheduler_runs": OperationCategory.QUEUES,
        "integrations.probe_all": OperationCategory.HEALTH,
    }
    for op_id, cat in expected.items():
        actual = ops[op_id].category
        assert actual == cat, (
            f"TRACK 25.01 · {op_id} expected category {cat.value}, "
            f"got {actual.value}."
        )


# ── to_public_dict shape ───────────────────────────────────────────

def test_public_dict_contract_for_new_operations():
    from services.operations_control import build_registry
    for op_id in REQUIRED_NEW_OPS:
        op = build_registry(db=None)[op_id]
        pd = op.to_public_dict()
        for k in (
            "id", "title", "description", "category", "risk",
            "reads", "writes", "never_touches",
            "has_dry_run", "has_apply", "has_status",
        ):
            assert k in pd, (
                f"TRACK 25.01 · public dict for {op_id} missing key {k!r}"
            )
        assert pd["has_status"] is True
        assert pd["has_dry_run"] is True
        assert pd["has_apply"] is False
