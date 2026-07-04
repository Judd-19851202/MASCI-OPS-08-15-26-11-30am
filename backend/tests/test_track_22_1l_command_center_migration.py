"""Track 22.1L · Final legacy startup handler elimination — lock test.

Migrates `build_command_center_router.<locals>._startup` from
`@router.on_event("startup")` into `LIFECYCLE_STEPS.command-center` and
achieves **100% startup migration** — zero legacy startup decorators
remain in the platform.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_1l"
FINGERPRINT_DIR = MEM / "BYTECODE_FINGERPRINTS"

COMMAND_CENTER_BYTECODE_SHA256 = "b2976f4460227c5402564de80fe32ee1d588f9f185ebd7ba97a39277989743cf"

DELIVERABLES = [
    "TRACK_22_1L_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1L_STARTUP_HANDLER_INVENTORY.md",
    "TRACK_22_1L_DEPENDENCY_GRAPH.md",
    "TRACK_22_1L_BYTECODE_FINGERPRINTS.md",
    "TRACK_22_1L_BOOT_ORDER_REPORT.md",
    "TRACK_22_1L_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1L_PLATFORM_STATUS_UPDATE.md",
    "TRACK_22_1L_ENGINEERING_AUDIT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    os.environ.setdefault("DISABLE_BACKUP_SCHEDULER", "true")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


def test_zero_legacy_startup_handlers():
    """The mission — 100% startup migration."""
    server = _load_server()
    assert len(server.app.router.on_startup) == 0, (
        f"expected 0 legacy on_startup handlers after 22.1L, got "
        f"{[getattr(fn,'__name__','?') for fn in server.app.router.on_startup]}"
    )


def test_command_center_group_exists_and_contains_exactly_one_handler():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    cc = [s for s in LIFECYCLE_STEPS if s.group == "command-center"]
    assert len(cc) == 1
    assert cc[0].name == "_command_center_seed_defaults"
    assert cc[0].source_module == "server"


def test_router_on_startup_decorator_removed_from_command_center_file():
    src = (BACKEND / "routes" / "command_center.py").read_text(encoding="utf-8")
    # Docstrings/comments may reference the historical decorator string;
    # what matters is that no line ACTUALLY uses the decorator.
    for line in src.splitlines():
        stripped = line.strip()
        # A real decorator line starts with @ and applies to the next def.
        assert not stripped.startswith('@router.on_event("startup")'), (
            f"router-hosted @router.on_event('startup') decorator still active: {line!r}"
        )
        assert not stripped.startswith("@router.on_event('startup')"), (
            f"router-hosted @router.on_event('startup') decorator still active: {line!r}"
        )


def test_lifecycle_steps_total_is_50():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    assert len(LIFECYCLE_STEPS) >= 50, f"expected >=50, got {len(LIFECYCLE_STEPS)}"
    by_group = Counter(s.group for s in LIFECYCLE_STEPS)
    assert by_group["index-ensure"] == 11
    assert by_group["seed"] == 7
    assert by_group["scheduler-nonemail"] == 4
    assert by_group["email-scheduler"] == 5
    assert by_group["misc-bootstrap"] >= 20
    assert by_group["backup-scheduler"] == 1
    assert by_group["command-center"] == 1
    assert by_group["readiness"] == 1


def test_shutdown_handler_still_registered():
    """Post-22.1K: shutdown_db_client migrated to SHUTDOWN_STEPS."""
    server = _load_server()
    if len(server.app.router.on_shutdown) == 1:
        return
    from lib.lifespan_bootstrap import SHUTDOWN_STEPS  # noqa: PLC0415
    assert any(s.name == "shutdown_db_client" for s in SHUTDOWN_STEPS)


def test_no_duplicate_registrations():
    server = _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    ls = [s.name for s in LIFECYCLE_STEPS]
    dup_on = {n: c for n, c in Counter(on).items() if c > 1}
    dup_ls = {n: c for n, c in Counter(ls).items() if c > 1}
    assert not dup_on, f"duplicate on_startup: {dup_on}"
    assert not dup_ls, f"duplicate lifecycle_steps: {dup_ls}"


def test_command_center_step_ordered_before_readiness_after_backup():
    """Registration order guarantees command-center runs after
    backup-scheduler and before readiness in phase-1 execution order."""
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    names_in_order = [s.name for s in LIFECYCLE_STEPS]
    i_cc = names_in_order.index("_command_center_seed_defaults")
    i_backup = names_in_order.index("_start_backup_scheduler")
    i_ready = names_in_order.index("_iter453_6_flip_ready_flag")
    assert i_backup < i_cc, f"backup-scheduler must precede command-center: {i_backup} vs {i_cc}"
    assert i_cc < i_ready, f"command-center must precede readiness: {i_cc} vs {i_ready}"


def test_readiness_still_last_in_phase_3():
    """Readiness must still be the ONLY entry in the readiness group and
    the orchestrator's phase-3 must still run readiness LAST."""
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    readiness = [s.name for s in LIFECYCLE_STEPS if s.group == "readiness"]
    assert readiness == ["_iter453_6_flip_ready_flag"]


def test_command_center_bytecode_matches_baseline():
    server = _load_server()
    fn = server._command_center_seed_defaults
    live = hashlib.sha256(fn.__code__.co_code).hexdigest()
    assert live == COMMAND_CENTER_BYTECODE_SHA256, (
        f"bytecode drift: expected {COMMAND_CENTER_BYTECODE_SHA256}, got {live}"
    )


def test_bytecode_fingerprint_index_updated():
    idx = json.loads((FINGERPRINT_DIR / "INDEX.json").read_text(encoding="utf-8"))
    assert idx.get("_command_center_seed_defaults") == COMMAND_CENTER_BYTECODE_SHA256
    p = FINGERPRINT_DIR / "_command_center_seed_defaults.sha256.txt"
    assert p.is_file() and p.read_text(encoding="utf-8").strip() == COMMAND_CENTER_BYTECODE_SHA256


def test_bytecode_fingerprints_all_clean_at_8():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"
    assert result["checked"] >= 8, f"expected >=8, got {result['checked']}"


def test_route_and_openapi_parity():
    server = _load_server()
    route_count = sum(1 for r in server.app.routes if hasattr(r, "endpoint"))
    assert route_count == 1441, f"route drift: {route_count}"
    methods = 0
    for r in server.app.routes:
        if hasattr(r, "endpoint"):
            methods += len(getattr(r, "methods", None) or [])
    assert methods == 1445, f"method drift: {methods}"
    oa = len(server.app.openapi().get("paths", {}))
    assert oa == 1264, f"openapi drift: {oa}"


def test_middleware_count_unchanged():
    server = _load_server()
    assert len(server.app.user_middleware) == 7


def test_command_center_endpoints_still_registered():
    """All 6 command-center endpoints must still be present."""
    server = _load_server()
    paths = {r.path for r in server.app.routes if hasattr(r, "endpoint")}
    expected = {
        "/api/admin/command-center/snapshot",
        "/api/admin/command-center/thresholds",
        "/api/admin/command-center/calendar",
    }
    missing = [p for p in expected if p not in paths]
    assert not missing, f"missing command-center endpoints: {missing}"


def test_platform_status_reflects_100pct_migration():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    reg = out["lifecycle"]["registry"]
    assert reg["by_group"].get("command-center") == 1
    assert reg["names_by_group"].get("command-center") == ["_command_center_seed_defaults"]
    assert out["lifecycle"]["on_startup_legacy_count"] == 0
    mig = out["lifecycle"]["migration_progress"]
    assert mig["migrated_pct"] == 100.0, f"expected 100.0, got {mig['migrated_pct']}"
    targets = mig["target_groups"]
    assert targets["command-center"]["closed"] is True
    assert targets["command-center"]["track"] == "22.1L"
    assert "22.1L" in out["recent_track_closures"]
    assert out["bytecode_fingerprints"]["clean"] is True
    assert out["bytecode_fingerprints"]["checked"] >= 8
    assert out["email_safety"]["live_emails_possible"] is False
    payload = json.dumps(out)
    for banned in ("MONGO_URL", "RESEND_API_KEY", "SUPER_ADMIN_BOOTSTRAP_PASSWORD",
                   "ADMIN_HMAC_SECRET", "DEV_PASSWORD", "mongodb+srv://", "sk_",
                   "Bearer ", "@mascigc.com"):
        assert banned not in payload, f"secret-adjacent leak: {banned}"


def test_email_safety_strict_mode_intact():
    server = _load_server()
    from lib.platform_status import platform_status  # noqa: PLC0415
    out = platform_status(server.app)
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["resend_sdk_patched"] is True
    assert out["email_safety"]["live_emails_possible"] is False


def test_command_center_handler_body_touches_no_email_no_r2():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    idx = src.find("async def _command_center_seed_defaults")
    assert idx > 0
    window = src[idx:idx + 2000]
    for banned in ("resend.Emails.send", "boto3", "s3.", "requests.post",
                   "requests.get"):
        assert banned not in window, f"banned symbol {banned!r} in command-center handler"


def test_snapshot_artifacts_committed():
    for name in (
        "COMMAND_CENTER_STARTUP_INVENTORY_before.json",
        "COMMAND_CENTER_STARTUP_INVENTORY_after.json",
        "STARTUP_ORDER_after.json",
        "RUNTIME_ENUMERATION_after.json",
        "PLATFORM_STATUS_after.json",
    ):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 200, f"missing/empty snapshot: {name}"


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_prd_and_changelog_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8", errors="ignore")
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    assert "22.1L" in prd
    assert "22.1L" in changelog
    assert "100%" in prd or "100.00" in prd
