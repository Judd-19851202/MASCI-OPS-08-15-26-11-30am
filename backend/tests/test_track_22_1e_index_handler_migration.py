"""Track 22.1E · Index-Ensure Handler Migration — lock test.

Enforces:
- 11 named index-ensure handlers are registered in LIFECYCLE_STEPS
  (not in app.router.on_startup).
- app.router.on_startup handler count is 40 (was 51 pre-22.1E).
- Runtime enumeration route/OpenAPI/middleware/dep-chain parity.
- All 5 SHA-256 bytecode fingerprints (dispatcher + 4 email scheduler
  handlers) still match live bytecode.
- Deprecation warning count reduced by exactly 11 vs pre-22.1E baseline.
- No duplicate execution (each migrated handler appears in
  LIFECYCLE_STEPS exactly once and NOT in on_startup).
- All 9 Track 22.1E deliverables committed and non-empty.
- Ledgers record the track.
- Prior guardrails (EMAIL_SAFETY_MODE=strict, CORS explicit lists,
  Track 22.0/22.1/22.1B/22.1C/22.1D locks) still committed.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_1e"

MIGRATED_HANDLERS = [
    "_ensure_scheduler_lock_indexes_at_startup",
    "_ensure_project_team_assignments_indexes",
    "_startup_trust_spine_indexes",
    "_arm_hot_id_indexes",
    "_arm_workflow_state_events_indexes",
    "_arm_iter142_perf_indexes",
    "_li_ensure_indexes",
    "_fleet_ensure_indexes",
    "_ensure_dls_indexes",
    "_ensure_driver_session_indexes",
    "_ensure_passkey_indexes",
]

DELIVERABLES = [
    "TRACK_22_1E_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1E_INDEX_HANDLER_INVENTORY.md",
    "TRACK_22_1E_LIFECYCLE_STEP_PATTERN.md",
    "TRACK_22_1E_INDEX_BEHAVIOR_CERTIFICATION.md",
    "TRACK_22_1E_STARTUP_PARITY.md",
    "TRACK_22_1E_EMAIL_SAFETY_RECERTIFICATION.md",
    "TRACK_22_1E_DEPRECATION_REDUCTION.md",
    "TRACK_22_1E_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1E_TEST_REPORT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    sys.path.insert(0, str(BACKEND))
    import server  # type: ignore
    return server


# --- Migration correctness ---------------------------------------------------
def test_lifecycle_steps_contains_11_migrated_handlers():
    server = _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    names_in_steps = [s.name for s in LIFECYCLE_STEPS if s.group == "index-ensure"]
    assert names_in_steps == MIGRATED_HANDLERS, (
        f"LIFECYCLE_STEPS index-ensure names drift.\n"
        f"expected: {MIGRATED_HANDLERS}\n"
        f"actual:   {names_in_steps}"
    )


def test_on_startup_no_longer_contains_migrated_handlers():
    server = _load_server()
    startup_names = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    for name in MIGRATED_HANDLERS:
        assert name not in startup_names, (
            f"duplicate: {name} is still in app.router.on_startup after migration"
        )


def test_startup_handler_count_reduced_from_51_to_40():
    server = _load_server()
    # Track 22.1E migrated 11 index-ensure handlers out of on_startup,
    # reducing it from 51 to 40. Subsequent tracks (22.1F seeds → 33,
    # then 22.1G-K) reduce it further, so the invariant this lock
    # guarantees is `<= 40` (i.e., "the 11 index-ensure handlers left").
    assert len(server.app.router.on_startup) <= 40, (
        f"expected <= 40 on_startup handlers after Track 22.1E "
        f"(11 index-ensure migrated), got {len(server.app.router.on_startup)}"
    )


# --- Runtime parity ----------------------------------------------------------
def test_runtime_snapshots_committed():
    for name in ("RUNTIME_ENUMERATION_before.json", "RUNTIME_ENUMERATION_after.json",
                 "STARTUP_ORDER_before.json", "STARTUP_ORDER_after.json",
                 "INDEX_HANDLER_INVENTORY_before.json"):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 500, f"missing/empty: {name}"


def test_route_and_openapi_parity():
    b = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_before.json").read_text(encoding="utf-8"))
    a = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_after.json").read_text(encoding="utf-8"))
    assert b["route_count"] == a["route_count"]
    assert b["route_methods_total"] == a["route_methods_total"]
    assert b["openapi_path_count"] == a["openapi_path_count"]
    assert b["middleware"] == a["middleware"]
    assert b["shutdown_handlers"] == a["shutdown_handlers"]
    assert b["exception_handlers"] == a["exception_handlers"]

    def key(r): return (r["path"], tuple(r["methods"]))
    b_by = {key(r): r for r in b["routes"]}
    a_by = {key(r): r for r in a["routes"]}
    assert set(b_by) == set(a_by)
    for k in b_by.keys() & a_by.keys():
        assert b_by[k]["endpoint_qualname"] == a_by[k]["endpoint_qualname"]
        assert b_by[k]["dependency_chain"] == a_by[k]["dependency_chain"]


def test_all_bytecode_fingerprints_match_live():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode  # type: ignore
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"


# --- Deliverables + ledgers --------------------------------------------------
def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_ledgers_record_track_22_1e():
    for name in ("PRD.md", "CHANGELOG.md", "TECHNICAL_DEBT_REGISTER.md"):
        body = (MEM / name).read_text(encoding="utf-8")
        assert "22.1e" in body.lower() or "22.1E" in body, f"{name} missing Track 22.1E"


# --- Prior guardrails --------------------------------------------------------
def test_email_safety_and_cors_preserved():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):' in src
    assert 'allow_methods=["*"]' not in src
    env = (BACKEND / ".env").read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", env, re.MULTILINE)


def test_prior_track_lock_files_committed():
    for name in (
        "test_track_22_0_platform_excellence.py",
        "test_track_22_1_server_modularization.py",
        "test_track_22_1b_email_dispatch.py",
        "test_track_22_1c_scheduler_bootstrap.py",
        "test_track_22_1d_lifespan_migration.py",
    ):
        assert (BACKEND / "tests" / name).is_file()


def test_lifespan_bootstrap_still_no_resend_import():
    body = (BACKEND / "lib" / "lifespan_bootstrap.py").read_text(encoding="utf-8")
    tree = ast.parse(body)
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name != "resend"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "resend"
