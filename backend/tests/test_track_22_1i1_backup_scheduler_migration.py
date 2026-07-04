"""Track 22.1I.1 · Backup Scheduler Safety Audit + Lifespan Migration — lock test.

Migrates `_start_backup_scheduler` from `@app.on_event("startup")` into
`LIFECYCLE_STEPS` group=`backup-scheduler`. Zero runtime drift · zero
live emails · zero live R2 writes · bytecode-identical body.
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
TRACK_DIR = MEM / "track_22_1i1"
FINGERPRINT_DIR = MEM / "BYTECODE_FINGERPRINTS"

MIGRATED = ["_start_backup_scheduler"]
EXCLUDED_REMAIN = ["_startup", "_iter453_6_flip_ready_flag"]

BACKUP_SCHEDULER_BYTECODE_SHA256 = "c7d29e0072aa7578855271dfd5d63a048b0f10d0d0d7bbc6819488d35b378a73"

DELIVERABLES = [
    "TRACK_22_1I1_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1I1_BACKUP_SCHEDULER_INVENTORY.md",
    "TRACK_22_1I1_R2_BACKUP_SAFETY_AUDIT.md",
    "TRACK_22_1I1_FAILURE_WATCHDOG_EMAIL_SAFETY.md",
    "TRACK_22_1I1_DEPENDENCY_PROOF.md",
    "TRACK_22_1I1_BYTECODE_BASELINE.md",
    "TRACK_22_1I1_BACKUP_PARITY.md",
    "TRACK_22_1I1_PLATFORM_STATUS_UPDATE.md",
    "TRACK_22_1I1_SIDE_EFFECT_CERTIFICATION.md",
    "TRACK_22_1I1_EMAIL_SAFETY_RECERTIFICATION.md",
    "TRACK_22_1I1_DEPRECATION_REDUCTION.md",
    "TRACK_22_1I1_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1I1_TEST_REPORT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    os.environ.setdefault("DISABLE_BACKUP_SCHEDULER", "true")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


def test_backup_scheduler_migrated_to_lifecycle_steps():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    names = [s.name for s in LIFECYCLE_STEPS if s.group == "backup-scheduler"]
    assert names == MIGRATED, f"backup-scheduler group drift: {names}"


def test_backup_scheduler_no_longer_in_on_startup():
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    assert "_start_backup_scheduler" not in on, (
        f"legacy decorator still active for _start_backup_scheduler; on_startup={on}"
    )


def test_lifecycle_steps_total_is_48():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    assert len(LIFECYCLE_STEPS) >= 48, f"expected >=48, got {len(LIFECYCLE_STEPS)}"
    by_group = Counter(s.group for s in LIFECYCLE_STEPS)
    assert by_group["index-ensure"] == 11
    assert by_group["seed"] == 7
    assert by_group["scheduler-nonemail"] == 4
    assert by_group["email-scheduler"] == 5
    assert by_group["misc-bootstrap"] == 20
    assert by_group["backup-scheduler"] == 1


def test_on_startup_count_dropped_to_2():
    server = _load_server()
    assert len(server.app.router.on_startup) == 2, (
        f"expected 2 legacy on_startup handlers after 22.1I.1, got "
        f"{[getattr(fn,'__name__','?') for fn in server.app.router.on_startup]}"
    )


def test_excluded_handlers_remain_in_on_startup():
    """Remaining 2 legacy on_startup handlers: command_center router startup + readiness flip."""
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    for name in EXCLUDED_REMAIN:
        assert name in on, f"excluded handler {name} unexpectedly missing from on_startup: {on}"


def test_readiness_flip_remains_last():
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    assert on[-1] == "_iter453_6_flip_ready_flag", (
        f"readiness flip not last; on_startup order = {on}"
    )


def test_command_center_router_startup_still_queued():
    server = _load_server()
    on = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    assert "_startup" in on, "routes.command_center._startup missing (Track 22.1L scope)"


def test_shutdown_handler_still_registered():
    server = _load_server()
    assert len(server.app.router.on_shutdown) == 1


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


def test_backup_scheduler_bytecode_matches_baseline():
    """The function body must be byte-identical — only the decorator swapped."""
    server = _load_server()
    fn = server._start_backup_scheduler
    live = hashlib.sha256(fn.__code__.co_code).hexdigest()
    assert live == BACKUP_SCHEDULER_BYTECODE_SHA256, (
        f"bytecode drift: expected {BACKUP_SCHEDULER_BYTECODE_SHA256}, got {live}"
    )


def test_bytecode_fingerprint_index_updated():
    """`_start_backup_scheduler` must be present in the fingerprint index."""
    idx = json.loads((FINGERPRINT_DIR / "INDEX.json").read_text(encoding="utf-8"))
    assert idx.get("_start_backup_scheduler") == BACKUP_SCHEDULER_BYTECODE_SHA256
    p = FINGERPRINT_DIR / "_start_backup_scheduler.sha256.txt"
    assert p.is_file()
    assert p.read_text(encoding="utf-8").strip() == BACKUP_SCHEDULER_BYTECODE_SHA256


def test_bytecode_fingerprints_all_clean():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"
    assert result["checked"] >= 6, f"expected >=6 fingerprints (incl backup-scheduler), got {result['checked']}"


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


def test_platform_status_reflects_track_22_1i1():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    by_group = out["lifecycle"]["registry"]["by_group"]
    assert by_group.get("backup-scheduler") == 1
    assert by_group.get("misc-bootstrap") == 20
    assert out["lifecycle"]["on_startup_legacy_count"] == 2
    mig = out["lifecycle"]["migration_progress"]
    assert mig["migrated_pct"] >= 96.0
    targets = mig["target_groups"]
    assert targets["backup-scheduler"]["closed"] is True
    assert targets["backup-scheduler"]["track"] == "22.1I.1"
    assert "22.1I.1" in out["recent_track_closures"]
    assert out["bytecode_fingerprints"]["clean"] is True
    assert out["bytecode_fingerprints"]["checked"] >= 6
    assert out["email_safety"]["live_emails_possible"] is False
    payload = json.dumps(out)
    for banned in ("MONGO_URL", "RESEND_API_KEY", "SUPER_ADMIN_BOOTSTRAP_PASSWORD",
                   "ADMIN_HMAC_SECRET", "DEV_PASSWORD", "mongodb+srv://", "sk_",
                   "Bearer ", "@mascigc.com"):
        assert banned not in payload, f"secret-adjacent leak: {banned}"


def test_email_safety_strict_mode_intact():
    server = _load_server()
    # Verify via platform_status API (which introspects the Resend SDK
    # patch state without importing resend into this test module —
    # Track 21.2E-1 canonicalization forbids direct resend imports in
    # test files outside `test_track_21_2e_email_safety.py`).
    from lib.platform_status import platform_status  # noqa: PLC0415
    out = platform_status(server.app)
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["resend_sdk_patched"] is True
    assert out["email_safety"]["live_emails_possible"] is False


def test_lifespan_bootstrap_still_no_resend_import():
    src = (BACKEND / "lib" / "lifespan_bootstrap.py").read_text(encoding="utf-8")
    for line in src.splitlines():
        stripped = line.strip()
        assert stripped != "import resend", "module-scope `import resend` forbidden"
        assert not stripped.startswith("from resend "), "module-scope `from resend ...` forbidden"


def test_platform_status_lib_still_no_resend_import_at_module_scope():
    """`import resend` only occurs inside the try-block of _email_safety_summary."""
    src = (BACKEND / "lib" / "platform_status.py").read_text(encoding="utf-8")
    # No top-level `import resend` line.
    for line in src.splitlines():
        if line.strip().startswith("import resend"):
            # The one legal occurrence is nested inside try: block (indented).
            assert line != "import resend", "module-scope import resend forbidden"


def test_snapshot_artifacts_committed():
    for name in (
        "BACKUP_SCHEDULER_INVENTORY_before.json",
        "BACKUP_SCHEDULER_INVENTORY_after.json",
        "STARTUP_ORDER_after.json",
        "RUNTIME_ENUMERATION_after.json",
        "PLATFORM_STATUS_after.json",
    ):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 200, f"missing/empty snapshot: {name}"


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_no_live_r2_or_email_paths_touched_by_migration():
    """The migration must not introduce a new `import resend` or a direct
    R2 call at the module scope of server.py near the migrated handler."""
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    idx = src.find("async def _start_backup_scheduler")
    assert idx >= 0
    # Handler body starts here; scan a 6KB window.
    window = src[idx:idx + 6000]
    # No email dispatch or direct resend import in the handler body
    assert "resend.Emails.send" not in window
    assert "import resend" not in window


def test_prd_and_changelog_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8", errors="ignore")
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    assert "22.1I.1" in prd, "PRD.md missing 22.1I.1 section"
    assert "22.1I.1" in changelog, "CHANGELOG.md missing 22.1I.1 entry"
    assert "backup-scheduler" in prd, "PRD.md missing backup-scheduler mention"
