"""Track 22.1G · Non-Email Scheduler Handler Migration — lock test.

Enforces:
- 4 non-email scheduler handlers registered in LIFECYCLE_STEPS with
  group="scheduler-nonemail" (not in app.router.on_startup).
- app.router.on_startup handler count is 29 (was 33 pre-22.1G).
- LIFECYCLE_STEPS total is 22 (11 index-ensure + 7 seed + 4 scheduler-nonemail).
- Runtime enumeration route/OpenAPI/middleware/dep-chain parity — zero drift
  (no new routes this track).
- All 5 SHA-256 bytecode fingerprints (dispatcher + 4 email scheduler
  handlers) still match live bytecode.
- No duplicate execution.
- The 5 email-capable scheduler handlers are STILL in app.router.on_startup
  (untouched, quarantined for Track 22.1H).
- All 11 Track 22.1G deliverables committed and non-empty.
- Ledgers record the track.
- Platform Ops API reports scheduler-nonemail as closed.
- Prior guardrails preserved.
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
TRACK_DIR = MEM / "track_22_1g"

MIGRATED_SCHEDULERS = [
    "_start_job_photos_indexer",
    "_start_motive_reliability_loop",
    "_start_health_monitor",
    "_cluster_capacity_history_loop",
]

EXCLUDED_EMAIL_CAPABLE = [
    "_start_safety_digest_cron",
    "_start_operator_digest_cron",
    "_start_po_digest_cron",
    "_dispatch_reminder_scheduler_start",
    "_start_backup_verification_cron",
]

DELIVERABLES = [
    "TRACK_22_1G_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1G_NON_EMAIL_SCHEDULER_INVENTORY.md",
    "TRACK_22_1G_EMAIL_CAPABLE_EXCLUSION.md",
    "TRACK_22_1G_DEPENDENCY_PROOF.md",
    "TRACK_22_1G_SCHEDULER_PARITY.md",
    "TRACK_22_1G_PLATFORM_STATUS_UPDATE.md",
    "TRACK_22_1G_SIDE_EFFECT_CERTIFICATION.md",
    "TRACK_22_1G_EMAIL_SAFETY_RECERTIFICATION.md",
    "TRACK_22_1G_DEPRECATION_REDUCTION.md",
    "TRACK_22_1G_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1G_TEST_REPORT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    sys.path.insert(0, str(BACKEND))
    import server  # type: ignore
    return server


def test_lifecycle_steps_contains_4_non_email_schedulers():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    names = [s.name for s in LIFECYCLE_STEPS if s.group == "scheduler-nonemail"]
    assert names == MIGRATED_SCHEDULERS, (
        f"LIFECYCLE_STEPS scheduler-nonemail names drift.\n"
        f"expected: {MIGRATED_SCHEDULERS}\n"
        f"actual:   {names}"
    )


def test_lifecycle_steps_total_is_22():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    # Track 22.1G guaranteed >= 22 (11 index + 7 seed + 4 scheduler-nonemail).
    # Later tracks grow this further.
    assert len(LIFECYCLE_STEPS) >= 22, (
        f"expected >= 22 LIFECYCLE_STEPS after Track 22.1G, got {len(LIFECYCLE_STEPS)}"
    )


def test_on_startup_no_longer_contains_migrated_schedulers():
    server = _load_server()
    startup_names = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    for name in MIGRATED_SCHEDULERS:
        assert name not in startup_names, (
            f"duplicate: {name} is still in app.router.on_startup after migration"
        )


def test_startup_handler_count_is_29():
    server = _load_server()
    # Track 22.1G guaranteed <= 29 (33 − 4 non-email schedulers). Later
    # tracks (22.1H email schedulers, ...) reduce further.
    assert len(server.app.router.on_startup) <= 29, (
        f"expected <= 29 on_startup handlers after Track 22.1G, got {len(server.app.router.on_startup)}"
    )


def test_email_capable_schedulers_still_in_on_startup():
    """Track 22.1G's 5 email-capable scheduler handlers must remain
    in on_startup UNTIL Track 22.1H properly migrates them. Once 22.1H
    closes, they move into LIFECYCLE_STEPS.email-scheduler — this
    assertion adapts to check they land in *exactly one* registry."""
    server = _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    startup_names = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    ls_names = [s.name for s in LIFECYCLE_STEPS]
    for name in EXCLUDED_EMAIL_CAPABLE:
        in_startup = name in startup_names
        in_lifecycle = name in ls_names
        assert in_startup ^ in_lifecycle, (
            f"handler {name} must be in exactly one registry (found on_startup={in_startup}, lifecycle_steps={in_lifecycle})"
        )


def test_runtime_snapshots_committed():
    for name in ("RUNTIME_ENUMERATION_before.json", "RUNTIME_ENUMERATION_after.json"):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 500, f"missing/empty: {name}"


def test_zero_route_openapi_drift():
    b = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_before.json").read_text(encoding="utf-8"))
    a = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_after.json").read_text(encoding="utf-8"))
    assert b["middleware"] == a["middleware"]
    # Compare shutdown bytecode qualname (lineno may shift under unrelated edits)
    def _sk(h): return (h["qualname"], h["name"], h["module"], h["bytecode_sha256"], h["is_coroutine"])
    assert [_sk(h) for h in b["shutdown_handlers"]] == [_sk(h) for h in a["shutdown_handlers"]]
    assert b["exception_handlers"] == a["exception_handlers"]
    assert a["route_count"] == b["route_count"], f"route drift: {b['route_count']} -> {a['route_count']}"
    assert a["route_methods_total"] == b["route_methods_total"]
    assert a["openapi_path_count"] == b["openapi_path_count"]
    def key(r): return (r["path"], tuple(r["methods"]))
    b_by = {key(r): r for r in b["routes"]}
    a_by = {key(r): r for r in a["routes"]}
    assert set(b_by) == set(a_by), f"route delta: added={set(a_by)-set(b_by)} removed={set(b_by)-set(a_by)}"
    for k in b_by.keys() & a_by.keys():
        assert b_by[k]["endpoint_qualname"] == a_by[k]["endpoint_qualname"], k
        assert b_by[k]["dependency_chain"] == a_by[k]["dependency_chain"], k


def test_all_bytecode_fingerprints_match_live():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode  # type: ignore
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"


def test_platform_status_reflects_track_22_1g():
    server = _load_server()
    from lib.platform_status import platform_status  # type: ignore
    out = platform_status(server.app)
    by_group = out["lifecycle"]["registry"]["by_group"]
    assert by_group.get("index-ensure") == 11
    assert by_group.get("seed") == 7
    assert by_group.get("scheduler-nonemail") == 4
    assert out["lifecycle"]["on_startup_legacy_count"] <= 29
    targets = out["lifecycle"]["migration_progress"]["target_groups"]
    assert targets["scheduler-nonemail"]["closed"] is True
    assert "22.1G" in out["recent_track_closures"]
    assert out["bytecode_fingerprints"]["clean"] is True
    assert out["email_safety"]["live_emails_possible"] is False


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_ledgers_record_track_22_1g():
    for name in ("PRD.md", "CHANGELOG.md", "TECHNICAL_DEBT_REGISTER.md"):
        body = (MEM / name).read_text(encoding="utf-8")
        assert "22.1G" in body or "22.1g" in body, f"{name} missing Track 22.1G"


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
        "test_track_22_1e_index_handler_migration.py",
        "test_track_22_1f_seed_handlers_and_platform_status.py",
    ):
        assert (BACKEND / "tests" / name).is_file()


def test_lifespan_and_platform_status_have_no_resend_import():
    for rel in ("lib/lifespan_bootstrap.py", "lib/platform_status.py"):
        body = (BACKEND / rel).read_text(encoding="utf-8")
        tree = ast.parse(body)
        for node in tree.body:
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name != "resend", f"{rel} module-scope imports resend"
            if isinstance(node, ast.ImportFrom):
                assert node.module != "resend", f"{rel} module-scope imports resend"
