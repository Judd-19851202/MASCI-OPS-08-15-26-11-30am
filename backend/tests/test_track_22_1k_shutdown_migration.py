"""Track 22.1K · Final lifecycle completion — permanent CI guardrail.

Fails if ANY new `@app.on_event("startup")` or `@app.on_event("shutdown")` or
`@router.on_event("startup")` or `@router.on_event("shutdown")` decorator is
introduced anywhere under `backend/**/*.py` — including new files.

Post-Track 22.1K the platform runs on a UNIFIED LIFECYCLE ARCHITECTURE:
  - Startup handlers live in `LIFECYCLE_STEPS`
  - Shutdown handlers live in `SHUTDOWN_STEPS`
  - Zero legacy `@app.on_event(...)` / `@router.on_event(...)` decorators exist.

This lock test enforces "no new legacy decorators" indefinitely.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_1k"
FINGERPRINT_DIR = MEM / "BYTECODE_FINGERPRINTS"

SHUTDOWN_BYTECODE_SHA256 = "a7db2b0122a4d9405610d78c2b44de8cd8314531ae688d554116b83e332e7c9b"

DELIVERABLES = [
    "TRACK_22_1K_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1K_LIFECYCLE_FINALIZATION_REPORT.md",
    "TRACK_22_1K_SHUTDOWN_ARCHITECTURE.md",
    "TRACK_22_1K_GRACEFUL_SHUTDOWN_REPORT.md",
    "TRACK_22_1K_TASK_INVENTORY.md",
    "TRACK_22_1K_BYTECODE_FINGERPRINTS.md",
    "TRACK_22_1K_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1K_PLATFORM_STATUS_UPDATE.md",
    "TRACK_22_1K_TEST_REPORT.md",
]

# Regex that matches an ACTIVE decorator (line starts with `@`) — ignores
# comments, docstrings, log-message strings that mention the historical decorator.
_STARTUP_DECORATOR = re.compile(r'^\s*@(?:app|router)\.on_event\(\s*[\'\"]startup[\'\"]', re.M)
_SHUTDOWN_DECORATOR = re.compile(r'^\s*@(?:app|router)\.on_event\(\s*[\'\"]shutdown[\'\"]', re.M)


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    os.environ.setdefault("DISABLE_BACKUP_SCHEDULER", "true")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


# ---------------------------------------------------------------------------
# ZERO-LEGACY GUARDRAILS (permanent)
# ---------------------------------------------------------------------------

def _scan_for_legacy_decorators(event_kind: str) -> list[str]:
    """AST-walk every backend/**/*.py and return locations where any
    `@app.on_event("<event_kind>")` or `@router.on_event("<event_kind>")`
    decorator is applied to a function/async def. Docstrings, comments,
    and string literals do NOT trigger a hit."""
    import ast  # noqa: PLC0415
    offenders: list[str] = []
    for py in BACKEND.rglob("*.py"):
        if "test_track_22_1" in py.name:
            continue
        try:
            src = py.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src, filename=str(py))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                # Match @X.on_event("<event_kind>") where X is a Name.
                if not (isinstance(dec, ast.Call)
                        and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr == "on_event"
                        and isinstance(dec.func.value, ast.Name)
                        and dec.func.value.id in {"app", "router"}):
                    continue
                if not dec.args:
                    continue
                arg = dec.args[0]
                if isinstance(arg, ast.Constant) and arg.value == event_kind:
                    offenders.append(f"{py.relative_to(APP)}:{dec.lineno}")
    return offenders


def test_no_legacy_startup_decorators_anywhere_in_backend():
    """PERMANENT · fails CI if ANY file introduces @(app|router).on_event('startup')."""
    offenders = _scan_for_legacy_decorators("startup")
    assert not offenders, (
        f"ZERO-LEGACY RULE VIOLATED — new @(app|router).on_event('startup') decorator(s) detected:\n  "
        + "\n  ".join(offenders)
    )


def test_no_legacy_shutdown_decorators_anywhere_in_backend():
    """PERMANENT · fails CI if ANY file introduces @(app|router).on_event('shutdown')."""
    offenders = _scan_for_legacy_decorators("shutdown")
    assert not offenders, (
        f"ZERO-LEGACY RULE VIOLATED — new @(app|router).on_event('shutdown') decorator(s) detected:\n  "
        + "\n  ".join(offenders)
    )


def test_app_router_on_startup_is_empty():
    server = _load_server()
    assert len(server.app.router.on_startup) == 0


def test_app_router_on_shutdown_is_empty():
    server = _load_server()
    assert len(server.app.router.on_shutdown) == 0


# ---------------------------------------------------------------------------
# SHUTDOWN REGISTRY
# ---------------------------------------------------------------------------

def test_shutdown_step_registered():
    _load_server()
    from lib.lifespan_bootstrap import SHUTDOWN_STEPS
    names = [s.name for s in SHUTDOWN_STEPS]
    assert "shutdown_db_client" in names, f"shutdown_db_client missing: {names}"


def test_shutdown_step_count_is_1():
    _load_server()
    from lib.lifespan_bootstrap import SHUTDOWN_STEPS
    assert len(SHUTDOWN_STEPS) == 1


def test_shutdown_step_group_is_shutdown():
    _load_server()
    from lib.lifespan_bootstrap import SHUTDOWN_STEPS
    step = next(s for s in SHUTDOWN_STEPS if s.name == "shutdown_db_client")
    assert step.group == "shutdown"


def test_shutdown_db_client_bytecode_matches_baseline():
    server = _load_server()
    fn = server.shutdown_db_client
    live = hashlib.sha256(fn.__code__.co_code).hexdigest()
    assert live == SHUTDOWN_BYTECODE_SHA256, (
        f"bytecode drift: expected {SHUTDOWN_BYTECODE_SHA256}, got {live}"
    )


def test_bytecode_fingerprint_index_updated():
    idx = json.loads((FINGERPRINT_DIR / "INDEX.json").read_text(encoding="utf-8"))
    assert idx.get("shutdown_db_client") == SHUTDOWN_BYTECODE_SHA256
    p = FINGERPRINT_DIR / "shutdown_db_client.sha256.txt"
    assert p.is_file() and p.read_text(encoding="utf-8").strip() == SHUTDOWN_BYTECODE_SHA256


def test_bytecode_fingerprints_all_clean_at_9():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"
    assert result["checked"] >= 9, f"expected >=9, got {result['checked']}"


# ---------------------------------------------------------------------------
# ORCHESTRATOR SHAPE
# ---------------------------------------------------------------------------

def test_orchestrator_has_shutdown_phase_4():
    src = (BACKEND / "lib" / "lifespan_bootstrap.py").read_text(encoding="utf-8")
    assert "SHUTDOWN_STEPS" in src, "shutdown registry missing"
    assert "track-22.1k" in src, "phase-4 marker log missing"
    # Phase 4a (SHUTDOWN_STEPS) must be textually AFTER `yield`.
    idx_yield = src.find("yield")
    idx_shutdown_phase = src.find("[track-22.1k] lifespan.shutdown: executing")
    assert idx_shutdown_phase > idx_yield > 0, "phase-4 must be positioned AFTER yield"


def test_register_shutdown_step_decorator_exposed():
    """The public API for future shutdown migrations must exist."""
    from lib.lifespan_bootstrap import register_shutdown_step, SHUTDOWN_STEPS  # noqa: F401
    assert callable(register_shutdown_step)


# ---------------------------------------------------------------------------
# PLATFORM STATUS API
# ---------------------------------------------------------------------------

def test_platform_status_reflects_lifecycle_complete():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    mig = out["lifecycle"]["migration_progress"]
    assert mig["startup_migration_pct"] == 100.0
    assert mig["shutdown_migration_pct"] == 100.0
    assert mig["lifecycle_complete"] is True
    assert mig["on_startup_legacy_count"] == 0
    assert mig["on_shutdown_legacy_count"] == 0
    assert mig["shutdown_steps_count"] == 1
    targets = mig["target_groups"]
    assert targets["shutdown"]["closed"] is True
    assert targets["shutdown"]["track"] == "22.1K"
    reg = out["lifecycle"]["registry"]
    sr = reg["shutdown_registry"]
    assert sr["total"] == 1
    assert sr["names"] == ["shutdown_db_client"]
    assert sr["graceful_shutdown_supported"] is True
    assert "22.1K" in out["recent_track_closures"]
    assert out["bytecode_fingerprints"]["clean"] is True
    assert out["bytecode_fingerprints"]["checked"] >= 9
    assert out["email_safety"]["live_emails_possible"] is False


def test_platform_status_top_recommendation_is_lifecycle_complete():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    top = out["recommended_next_actions"][0]
    assert top["priority"] == "P0"
    assert "LIFECYCLE ARCHITECTURE COMPLETE" in top["action"]


def test_platform_status_no_secret_leaks():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    payload = json.dumps(out)
    for banned in ("MONGO_URL", "RESEND_API_KEY", "SUPER_ADMIN_BOOTSTRAP_PASSWORD",
                   "ADMIN_HMAC_SECRET", "DEV_PASSWORD", "mongodb+srv://", "sk_",
                   "Bearer ", "@mascigc.com"):
        assert banned not in payload, f"secret-adjacent leak: {banned}"


# ---------------------------------------------------------------------------
# PARITY
# ---------------------------------------------------------------------------

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


def test_email_safety_strict_mode_intact():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["resend_sdk_patched"] is True
    assert out["email_safety"]["live_emails_possible"] is False


# ---------------------------------------------------------------------------
# ORPHAN TASK ELIMINATION (audit F2)
# ---------------------------------------------------------------------------

def test_no_get_event_loop_create_task_at_module_scope_in_job_photos():
    """The pre-22.1K orphan task creation was removed and replaced with a
    proper LIFECYCLE_STEP registration. Uses AST to distinguish real code
    from historical references inside comments/docstrings."""
    import ast  # noqa: PLC0415
    src = (BACKEND / "routes" / "job_photos.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    def _uses_forbidden_call(node: ast.AST) -> bool:
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            fn = child.func
            # Match ...create_task(_ensure_thumb_cache_indexes(...))
            if not (isinstance(fn, ast.Attribute) and fn.attr == "create_task"):
                continue
            if not child.args:
                continue
            inner = child.args[0]
            if not (isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id == "_ensure_thumb_cache_indexes"):
                continue
            # Also require the outer to look like `asyncio.get_event_loop().create_task(...)`.
            outer_value = fn.value
            if (isinstance(outer_value, ast.Call)
                    and isinstance(outer_value.func, ast.Attribute)
                    and outer_value.func.attr == "get_event_loop"):
                return True
        return False

    assert not _uses_forbidden_call(tree), (
        "orphan-task fire-and-forget `asyncio.get_event_loop().create_task"
        "(_ensure_thumb_cache_indexes(...))` re-introduced in routes/job_photos.py"
    )
    # And the replacement lifecycle step registration must be present.
    assert "_job_photos_ensure_thumb_cache_indexes" in src


def test_job_photos_thumb_cache_registered_as_lifecycle_step():
    """The replacement must actually be in LIFECYCLE_STEPS after import."""
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    names = [s.name for s in LIFECYCLE_STEPS]
    assert "_job_photos_ensure_thumb_cache_indexes" in names, (
        f"replacement step not registered: {names[-8:]}"
    )


# ---------------------------------------------------------------------------
# DELIVERABLES
# ---------------------------------------------------------------------------

def test_snapshot_artifacts_committed():
    for name in (
        "SHUTDOWN_HANDLER_INVENTORY_before.json",
        "SHUTDOWN_HANDLER_INVENTORY_after.json",
        "STARTUP_ORDER_after.json",
        "RUNTIME_ENUMERATION_after.json",
        "PLATFORM_STATUS_after.json",
        "TASK_INVENTORY.json",
    ):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 200, f"missing/empty snapshot: {name}"


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_prd_and_changelog_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8", errors="ignore")
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    assert "22.1K" in prd
    assert "22.1K" in changelog
    # PRD must attest to the unified lifecycle.
    assert ("100%" in prd or "100.00" in prd) and ("shutdown" in prd.lower())
