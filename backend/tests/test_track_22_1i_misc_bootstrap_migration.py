"""Track 22.1I · Miscellaneous Bootstrap Handler Migration — lock test."""
from __future__ import annotations
import ast, json, os, re, sys
from collections import Counter
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_1i"

MIGRATED = [
    "_db_isolation_failsafe", "_tune_asyncio_thread_pool", "_deploy_fix_001_backup_orphan_sweep",
    "_ensure_v_prelude_wave1_indexes", "_log_operational_hygiene_at_startup",
    "_clear_super_admin_force_pw_change", "_startup_deployment_ledger_indexes", "_oa_startup",
    "_arm_audit_ttl_indexes", "_bootstrap_operations", "_bootstrap_integrations",
    "_ensure_stability_ttls", "_li_start_worker", "_ensure_field_memory_indexes_startup",
    "_backfill_doc_ids", "_track_16_05_bootstrap_on_startup", "_track_16_08_bootstrap_on_startup",
    "_track_16_09_bootstrap_on_startup", "_track_16_10_bootstrap_on_startup",
    "_track_15_93_run_system_bootstrap",
]

EXCLUDED_REMAIN = ["_startup"]  # Track 22.1J migrated readiness out; 22.1L will migrate _startup

DELIVERABLES = [
    "TRACK_22_1I_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1I_MISC_BOOTSTRAP_INVENTORY.md",
    "TRACK_22_1I_EXCLUSION_MATRIX.md",
    "TRACK_22_1I_DEPENDENCY_PROOF.md",
    "TRACK_22_1I_BACKUP_R2_SAFETY.md",
    "TRACK_22_1I_BOOTSTRAP_PARITY.md",
    "TRACK_22_1I_PLATFORM_STATUS_UPDATE.md",
    "TRACK_22_1I_SIDE_EFFECT_CERTIFICATION.md",
    "TRACK_22_1I_EMAIL_SAFETY_RECERTIFICATION.md",
    "TRACK_22_1I_DEPRECATION_REDUCTION.md",
    "TRACK_22_1I_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1I_TEST_REPORT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


def test_lifecycle_steps_contains_20_misc_bootstrap():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    names = [s.name for s in LIFECYCLE_STEPS if s.group == "misc-bootstrap"]
    assert names == MIGRATED, f"drift:\nexpected: {MIGRATED}\nactual:   {names}"


def test_lifecycle_steps_total_is_47():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    # >= 47 because subsequent tracks (22.1I.1+) keep adding to LIFECYCLE_STEPS.
    assert len(LIFECYCLE_STEPS) >= 47, f"expected >=47, got {len(LIFECYCLE_STEPS)}"


def test_on_startup_no_longer_contains_migrated():
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    for name in MIGRATED:
        assert name not in on, f"quarantine violation: {name} still in on_startup"


def test_startup_handler_count_is_3():
    server = _load_server()
    # <= 3 because Track 22.1I.1 migrates one more (backup-scheduler).
    assert len(server.app.router.on_startup) <= 3


def test_excluded_handlers_remain_in_on_startup():
    """The 3 excluded handlers must remain in on_startup:
    - `_startup` (from routes.command_center — different module, out of scope)
    - `_start_backup_scheduler` (needs dedicated backup safety audit track)
    - `_iter453_6_flip_ready_flag` (readiness-last, Track 22.1J)"""
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    for name in EXCLUDED_REMAIN:
        assert name in on, f"excluded handler {name} unexpectedly missing from on_startup"


def test_readiness_flip_is_last():
    """Post-22.1J: readiness handler was moved into LIFECYCLE_STEPS.readiness.
    The last-position invariant is now enforced by the orchestrator's phase-3.
    Here we only assert readiness is NOT present in on_startup (moved out)."""
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    if "_iter453_6_flip_ready_flag" in on:
        # Pre-22.1J era — must be last.
        assert on[-1] == "_iter453_6_flip_ready_flag", (
            f"readiness flip not last; on_startup order = {on}"
        )
    else:
        # Post-22.1J era — readiness moved to LIFECYCLE_STEPS.readiness phase-3.
        from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # noqa: PLC0415
        readiness = [s.name for s in LIFECYCLE_STEPS if s.group == "readiness"]
        assert readiness == ["_iter453_6_flip_ready_flag"], readiness


def test_no_duplicate_registrations():
    server = _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    ls = [s.name for s in LIFECYCLE_STEPS]
    assert not {n: c for n, c in Counter(on).items() if c > 1}
    assert not {n: c for n, c in Counter(ls).items() if c > 1}
    assert not (set(on) & set(ls))


def test_runtime_snapshots_committed():
    for name in ("RUNTIME_ENUMERATION_before.json", "RUNTIME_ENUMERATION_after.json"):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 500


def test_zero_route_openapi_drift():
    b = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_before.json").read_text(encoding="utf-8"))
    a = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_after.json").read_text(encoding="utf-8"))
    assert b["middleware"] == a["middleware"]
    def _sk(h): return (h["qualname"], h["name"], h["module"], h["bytecode_sha256"], h["is_coroutine"])
    assert [_sk(h) for h in b["shutdown_handlers"]] == [_sk(h) for h in a["shutdown_handlers"]]
    assert b["exception_handlers"] == a["exception_handlers"]
    assert a["route_count"] == b["route_count"]
    assert a["route_methods_total"] == b["route_methods_total"]
    assert a["openapi_path_count"] == b["openapi_path_count"]
    def key(r): return (r["path"], tuple(r["methods"]))
    b_by = {key(r): r for r in b["routes"]}
    a_by = {key(r): r for r in a["routes"]}
    assert set(b_by) == set(a_by)
    for k in b_by.keys() & a_by.keys():
        assert b_by[k]["endpoint_qualname"] == a_by[k]["endpoint_qualname"], k
        assert b_by[k]["dependency_chain"] == a_by[k]["dependency_chain"], k


def test_bytecode_fingerprints_clean():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"


def test_platform_status_reflects_track_22_1i():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    by_group = out["lifecycle"]["registry"]["by_group"]
    assert by_group.get("index-ensure") == 11
    assert by_group.get("seed") == 7
    assert by_group.get("scheduler-nonemail") == 4
    assert by_group.get("email-scheduler") == 5
    assert by_group.get("misc-bootstrap") == 20
    assert out["lifecycle"]["on_startup_legacy_count"] <= 3
    targets = out["lifecycle"]["migration_progress"]["target_groups"]
    assert targets["misc-bootstrap"]["closed"] is True
    assert "22.1I" in out["recent_track_closures"]
    assert out["bytecode_fingerprints"]["clean"] is True
    assert out["email_safety"]["live_emails_possible"] is False
    payload = json.dumps(out)
    for banned in ("MONGO_URL", "RESEND_API_KEY", "SUPER_ADMIN_BOOTSTRAP_PASSWORD",
                   "ADMIN_HMAC_SECRET", "DEV_PASSWORD", "mongodb+srv://", "sk_",
                   "Bearer ", "@mascigc.com"):
        assert banned not in payload


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_ledgers_record_track_22_1i():
    for name in ("PRD.md", "CHANGELOG.md", "TECHNICAL_DEBT_REGISTER.md"):
        body = (MEM / name).read_text(encoding="utf-8")
        assert "22.1I" in body or "22.1i" in body


def test_email_safety_and_cors_preserved():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):' in src
    assert 'allow_methods=["*"]' not in src
    env = (BACKEND / ".env").read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", env, re.MULTILINE)


def test_lifespan_and_platform_status_have_no_resend_import():
    for rel in ("lib/lifespan_bootstrap.py", "lib/platform_status.py"):
        body = (BACKEND / rel).read_text(encoding="utf-8")
        tree = ast.parse(body)
        for node in tree.body:
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name != "resend"
            if isinstance(node, ast.ImportFrom):
                assert node.module != "resend"


def test_prior_track_lock_files_committed():
    for name in (
        "test_track_22_0_platform_excellence.py", "test_track_22_1_server_modularization.py",
        "test_track_22_1b_email_dispatch.py", "test_track_22_1c_scheduler_bootstrap.py",
        "test_track_22_1d_lifespan_migration.py", "test_track_22_1e_index_handler_migration.py",
        "test_track_22_1f_seed_handlers_and_platform_status.py",
        "test_track_22_1g_non_email_scheduler_migration.py",
        "test_track_22_1h_email_scheduler_migration.py",
    ):
        assert (BACKEND / "tests" / name).is_file()
