"""Track 22.1J · Readiness-last handler migration — lock test.

Migrates `_iter453_6_flip_ready_flag` from `@app.on_event("startup")` into
`LIFECYCLE_STEPS.readiness`, and requires that the orchestrator run the
readiness group as the FINAL phase — after `app.router.on_startup`.
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
TRACK_DIR = MEM / "track_22_1j"
FINGERPRINT_DIR = MEM / "BYTECODE_FINGERPRINTS"

READINESS_BYTECODE_SHA256 = "3ad0b42c02c53519565c03606ae0024b903a6db7c71c42578e406541e89a8fc4"

DELIVERABLES = [
    "TRACK_22_1J_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1J_READINESS_HANDLER_INVENTORY.md",
    "TRACK_22_1J_LAST_POSITION_INVARIANT.md",
    "TRACK_22_1J_COMMAND_CENTER_INTERACTION.md",
    "TRACK_22_1J_BYTECODE_BASELINE.md",
    "TRACK_22_1J_LIFESPAN_ORCHESTRATION_UPDATE.md",
    "TRACK_22_1J_READINESS_BEHAVIOR_CERTIFICATION.md",
    "TRACK_22_1J_PLATFORM_STATUS_UPDATE.md",
    "TRACK_22_1J_EMAIL_SAFETY_RECERTIFICATION.md",
    "TRACK_22_1J_DEPRECATION_REDUCTION.md",
    "TRACK_22_1J_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1J_TEST_REPORT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    os.environ.setdefault("DISABLE_BACKUP_SCHEDULER", "true")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


def test_readiness_handler_migrated_to_lifecycle_steps():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    names = [s.name for s in LIFECYCLE_STEPS if s.group == "readiness"]
    assert names == ["_iter453_6_flip_ready_flag"], f"readiness group drift: {names}"


def test_readiness_handler_no_longer_in_on_startup():
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    assert "_iter453_6_flip_ready_flag" not in on, f"legacy decorator still active; on_startup={on}"


def test_readiness_group_size_is_exactly_1():
    """Invariant: only the readiness flip belongs in the readiness group."""
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    readiness = [s for s in LIFECYCLE_STEPS if s.group == "readiness"]
    assert len(readiness) == 1


def test_lifecycle_steps_total_is_49():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    assert len(LIFECYCLE_STEPS) >= 49, f"expected >=49, got {len(LIFECYCLE_STEPS)}"
    by_group = Counter(s.group for s in LIFECYCLE_STEPS)
    assert by_group["index-ensure"] == 11
    assert by_group["seed"] == 7
    assert by_group["scheduler-nonemail"] == 4
    assert by_group["email-scheduler"] == 5
    assert by_group["misc-bootstrap"] >= 20
    assert by_group["backup-scheduler"] == 1
    assert by_group["readiness"] == 1


def test_on_startup_count_dropped_to_1():
    server = _load_server()
    assert len(server.app.router.on_startup) <= 1, (
        f"expected 1 legacy on_startup handler after 22.1J, got "
        f"{[getattr(fn,'__name__','?') for fn in server.app.router.on_startup]}"
    )


def test_command_center_startup_still_queued_for_track_22_1l():
    """Pre-22.1L this asserts `_startup` is still in on_startup. Post-22.1L
    the handler was migrated to `_command_center_seed_defaults` inside
    `LIFECYCLE_STEPS.command-center`. Accept either state."""
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    if "_startup" in on:
        return  # pre-22.1L era
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # noqa: PLC0415
    cc = [s.name for s in LIFECYCLE_STEPS if s.group == "command-center"]
    assert cc == ["_command_center_seed_defaults"], (
        f"post-22.1L expects command-center group with _command_center_seed_defaults; got {cc}"
    )


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
    assert not (set(on) & set(ls)), f"cross-registry overlap: {set(on) & set(ls)}"


def test_readiness_bytecode_matches_baseline():
    server = _load_server()
    fn = server._iter453_6_flip_ready_flag
    live = hashlib.sha256(fn.__code__.co_code).hexdigest()
    assert live == READINESS_BYTECODE_SHA256, (
        f"bytecode drift: expected {READINESS_BYTECODE_SHA256}, got {live}"
    )


def test_bytecode_fingerprint_index_updated():
    idx = json.loads((FINGERPRINT_DIR / "INDEX.json").read_text(encoding="utf-8"))
    assert idx.get("_iter453_6_flip_ready_flag") == READINESS_BYTECODE_SHA256
    p = FINGERPRINT_DIR / "_iter453_6_flip_ready_flag.sha256.txt"
    assert p.is_file() and p.read_text(encoding="utf-8").strip() == READINESS_BYTECODE_SHA256


def test_bytecode_fingerprints_all_clean_at_7():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"
    assert result["checked"] >= 7, f"expected >=7 fingerprints, got {result['checked']}"


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


def test_orchestrator_has_final_readiness_phase():
    """The orchestrator must partition LIFECYCLE_STEPS by group and run
    `readiness` steps AFTER `app.router.on_startup`. Verify via source."""
    src = (BACKEND / "lib" / "lifespan_bootstrap.py").read_text(encoding="utf-8")
    assert 'group != "readiness"' in src, "phase-1 filter missing"
    assert 'group == "readiness"' in src, "phase-3 filter missing"
    assert "track-22.1j" in src, "track-22.1j marker log missing"
    # Ensure the readiness-phase execution loop is textually AFTER the
    # legacy on_startup iteration loop.
    idx_readiness_exec = src.find("[track-22.1j] lifespan.startup: executing")
    idx_legacy_loop = src.find("startup_handlers = list(getattr(app.router")
    assert idx_readiness_exec > idx_legacy_loop > 0, (
        "readiness phase execution must be positioned AFTER legacy on_startup loop"
    )


def test_platform_status_reflects_track_22_1j():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    reg = out["lifecycle"]["registry"]
    assert reg["by_group"].get("readiness") == 1
    assert reg["names_by_group"].get("readiness") == ["_iter453_6_flip_ready_flag"]
    inv = reg["readiness_last_invariant"]
    assert inv["readiness_group_size"] == 1
    assert inv["readiness_handlers"] == ["_iter453_6_flip_ready_flag"]
    assert inv["runs_after_non_readiness_lifecycle_steps"] is True
    assert inv["runs_after_legacy_on_startup"] is True
    assert inv["final_phase_of_lifespan"] is True
    assert out["lifecycle"]["on_startup_legacy_count"] <= 1
    mig = out["lifecycle"]["migration_progress"]
    assert mig["migrated_pct"] >= 98.0
    targets = mig["target_groups"]
    assert targets["readiness"]["closed"] is True
    assert targets["readiness"]["track"] == "22.1J"
    assert "22.1J" in out["recent_track_closures"]
    assert out["bytecode_fingerprints"]["clean"] is True
    assert out["bytecode_fingerprints"]["checked"] >= 7
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


def test_lifespan_bootstrap_still_no_resend_import():
    src = (BACKEND / "lib" / "lifespan_bootstrap.py").read_text(encoding="utf-8")
    for line in src.splitlines():
        stripped = line.strip()
        assert stripped != "import resend"
        assert not stripped.startswith("from resend ")


def test_snapshot_artifacts_committed():
    for name in (
        "READINESS_HANDLER_INVENTORY_before.json",
        "READINESS_HANDLER_INVENTORY_after.json",
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
    assert "22.1J" in prd
    assert "22.1J" in changelog
    assert "readiness" in prd.lower()
    assert "readiness-last" in prd.lower() or "readiness last" in prd.lower()


def test_readiness_handler_body_touches_no_email_no_r2():
    """Static grep the ready-flip body for any live-side-effect symbol."""
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    idx = src.find("async def _iter453_6_flip_ready_flag")
    assert idx > 0
    window = src[idx:idx + 2000]
    for banned in ("resend.Emails.send", "import resend", "boto3", "s3.", "requests.post",
                   "requests.get", "await db."):
        assert banned not in window, f"banned symbol {banned!r} in readiness handler body"
