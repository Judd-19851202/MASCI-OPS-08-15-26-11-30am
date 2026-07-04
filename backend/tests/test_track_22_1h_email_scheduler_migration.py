"""Track 22.1H · Email-Capable Scheduler Handler Migration — lock test.

Enforces:
- 5 email-capable scheduler handlers registered in LIFECYCLE_STEPS with
  group="email-scheduler" (not in app.router.on_startup).
- app.router.on_startup handler count is 23 (was 29 pre-22.1H — includes
  the closure of a pre-existing double-registration of
  `_start_safety_digest_cron`).
- LIFECYCLE_STEPS total is 27.
- Zero route/OpenAPI/middleware/dep-chain drift.
- All 5 SHA-256 bytecode fingerprints still match live bytecode.
- No duplicate execution — no handler name appears more than once
  in either registry.
- Email safety envelope preserved: EMAIL_SAFETY_MODE=strict,
  auto_email_enabled() returns False in test env.
- Platform Ops API reports email-scheduler closed, migrated_pct climbs.
- All 12 Track 22.1H deliverables committed and non-empty.
- Ledgers record the track.
- Prior guardrails preserved.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_1h"

MIGRATED_EMAIL_SCHEDULERS = [
    "_start_safety_digest_cron",
    "_start_operator_digest_cron",
    "_start_po_digest_cron",
    "_start_backup_verification_cron",
    "_dispatch_reminder_scheduler_start",
]

DELIVERABLES = [
    "TRACK_22_1H_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1H_EMAIL_SCHEDULER_INVENTORY.md",
    "TRACK_22_1H_BYTECODE_BASELINE.md",
    "TRACK_22_1H_EMAIL_SAFETY_PRECHECK.md",
    "TRACK_22_1H_DEPENDENCY_PROOF.md",
    "TRACK_22_1H_SCHEDULER_PARITY.md",
    "TRACK_22_1H_PLATFORM_STATUS_UPDATE.md",
    "TRACK_22_1H_EMAIL_DISPATCH_PARITY.md",
    "TRACK_22_1H_SIDE_EFFECT_CERTIFICATION.md",
    "TRACK_22_1H_DEPRECATION_REDUCTION.md",
    "TRACK_22_1H_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1H_TEST_REPORT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    sys.path.insert(0, str(BACKEND))
    import server  # type: ignore
    return server


# --- Migration correctness ---------------------------------------------------
def test_lifecycle_steps_contains_5_email_schedulers():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    names = [s.name for s in LIFECYCLE_STEPS if s.group == "email-scheduler"]
    assert names == MIGRATED_EMAIL_SCHEDULERS, (
        f"LIFECYCLE_STEPS email-scheduler names drift.\n"
        f"expected: {MIGRATED_EMAIL_SCHEDULERS}\n"
        f"actual:   {names}"
    )


def test_lifecycle_steps_total_is_27():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    assert len(LIFECYCLE_STEPS) == 27, (
        f"expected 27 LIFECYCLE_STEPS (11 index-ensure + 7 seed + 4 scheduler-nonemail + 5 email-scheduler), got {len(LIFECYCLE_STEPS)}"
    )


def test_on_startup_no_longer_contains_email_schedulers():
    server = _load_server()
    startup_names = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    for name in MIGRATED_EMAIL_SCHEDULERS:
        assert name not in startup_names, (
            f"quarantine violation: {name} is still in app.router.on_startup"
        )


def test_startup_handler_count_is_23():
    server = _load_server()
    # 29 (22.1G close · included a pre-existing double-registration of
    # `_start_safety_digest_cron`) → 5 migrated + 1 dupe closure = 23.
    assert len(server.app.router.on_startup) == 23, (
        f"expected 23 on_startup handlers after Track 22.1H, got {len(server.app.router.on_startup)}"
    )


def test_no_duplicate_registrations():
    server = _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    on_names = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    ls_names = [s.name for s in LIFECYCLE_STEPS]
    on_dupes = {n: c for n, c in Counter(on_names).items() if c > 1}
    ls_dupes = {n: c for n, c in Counter(ls_names).items() if c > 1}
    assert on_dupes == {}, f"on_startup duplicates: {on_dupes}"
    assert ls_dupes == {}, f"LIFECYCLE_STEPS duplicates: {ls_dupes}"
    cross = set(on_names) & set(ls_names)
    assert cross == set(), f"handler present in both registries: {cross}"


# --- Runtime parity ----------------------------------------------------------
def test_runtime_snapshots_committed():
    for name in ("RUNTIME_ENUMERATION_before.json", "RUNTIME_ENUMERATION_after.json"):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 500, f"missing/empty: {name}"


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
    assert set(b_by) == set(a_by), f"route delta: added={set(a_by)-set(b_by)} removed={set(b_by)-set(a_by)}"
    for k in b_by.keys() & a_by.keys():
        assert b_by[k]["endpoint_qualname"] == a_by[k]["endpoint_qualname"], k
        assert b_by[k]["dependency_chain"] == a_by[k]["dependency_chain"], k


def test_bytecode_fingerprints_clean_and_include_all_5():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode  # type: ignore
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"
    assert result["checked"] == 5, f"expected 5 fingerprints checked, got {result['checked']}"
    ok_set = set(result["ok"])
    for name in ("_dispatch_auto_email",) + tuple(n for n in MIGRATED_EMAIL_SCHEDULERS if n != "_start_backup_verification_cron"):
        assert name in ok_set, f"fingerprint missing from ok list: {name}"


# --- Email safety ------------------------------------------------------------
def test_email_safety_strict_mode_active():
    server = _load_server()
    assert (os.environ.get("EMAIL_SAFETY_MODE") or "").lower() == "strict"
    # auto_email_enabled must be False in strict mode
    assert server.auto_email_enabled() is False


def test_migrated_handlers_have_no_module_scope_resend_import():
    """`lib/lifespan_bootstrap.py` and `lib/platform_status.py` still must not
    import ``resend`` at module scope. The migrated scheduler handler bodies
    live inside server.py — their handler-scope imports remain unchanged."""
    for rel in ("lib/lifespan_bootstrap.py", "lib/platform_status.py"):
        body = (BACKEND / rel).read_text(encoding="utf-8")
        tree = ast.parse(body)
        for node in tree.body:
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name != "resend", f"{rel} module-scope imports resend"
            if isinstance(node, ast.ImportFrom):
                assert node.module != "resend", f"{rel} module-scope imports resend"


# --- Platform Ops API --------------------------------------------------------
def test_platform_status_reflects_track_22_1h():
    server = _load_server()
    from lib.platform_status import platform_status  # type: ignore
    out = platform_status(server.app)
    by_group = out["lifecycle"]["registry"]["by_group"]
    assert by_group.get("index-ensure") == 11
    assert by_group.get("seed") == 7
    assert by_group.get("scheduler-nonemail") == 4
    assert by_group.get("email-scheduler") == 5
    assert out["lifecycle"]["on_startup_legacy_count"] == 23
    targets = out["lifecycle"]["migration_progress"]["target_groups"]
    assert targets["email-scheduler"]["closed"] is True
    assert targets["bootstrap-misc"]["closed"] is False
    assert "22.1H" in out["recent_track_closures"]
    assert out["bytecode_fingerprints"]["clean"] is True
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["live_emails_possible"] is False
    # No secret in payload.
    payload_json = json.dumps(out)
    for banned in ("MONGO_URL", "RESEND_API_KEY", "SUPER_ADMIN_BOOTSTRAP_PASSWORD",
                   "ADMIN_HMAC_SECRET", "DEV_PASSWORD", "mongodb+srv://", "sk_",
                   "Bearer ", "@mascigc.com"):
        assert banned not in payload_json, f"platform_status leaks: {banned}"


# --- Deliverables + ledgers --------------------------------------------------
def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_ledgers_record_track_22_1h():
    for name in ("PRD.md", "CHANGELOG.md", "TECHNICAL_DEBT_REGISTER.md"):
        body = (MEM / name).read_text(encoding="utf-8")
        assert "22.1H" in body or "22.1h" in body, f"{name} missing Track 22.1H"


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
        "test_track_22_1e_index_handler_migration.py",
        "test_track_22_1f_seed_handlers_and_platform_status.py",
        "test_track_22_1g_non_email_scheduler_migration.py",
    ):
        assert (BACKEND / "tests" / name).is_file()
