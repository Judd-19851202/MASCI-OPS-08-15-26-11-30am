"""Track 22.1F · Seed Handler Migration + Platform Operations API — lock test.

Enforces:
- 7 seed handlers registered in LIFECYCLE_STEPS with group="seed"
  (not in app.router.on_startup).
- app.router.on_startup handler count is 33 (was 40 pre-22.1F).
- LIFECYCLE_STEPS total is 18 (11 index-ensure + 7 seed).
- Runtime enumeration route/OpenAPI/middleware/dep-chain parity except
  for the single new admin route GET /api/admin/platform/status
  (intentional Platform Operations API foundation).
- All 5 SHA-256 bytecode fingerprints (dispatcher + 4 email scheduler
  handlers) still match live bytecode.
- No duplicate execution (each migrated seed appears in LIFECYCLE_STEPS
  exactly once and NOT in on_startup).
- Platform Status API: admin-gated, returns non-secret metadata only,
  read-only, no side effects, no live email possible.
- All 9 Track 22.1F deliverables committed and non-empty.
- Ledgers record the track.
- lib/platform_status.py does not import resend.
- Prior guardrails (EMAIL_SAFETY_MODE=strict, CORS explicit lists,
  Track 22.0/22.1/22.1B/22.1C/22.1D/22.1E locks) still committed.
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
TRACK_DIR = MEM / "track_22_1f"

MIGRATED_SEEDS = [
    "_seed_field_leadership_equipment_catalog",
    "_seed_shop_users",
    "_seed_hr_users",
    "_seed_field_leadership_users",
    "_seed_safety_users",
    "_bootstrap_user_directory",
    "_seed_phase1",
]

DELIVERABLES = [
    "TRACK_22_1F_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1F_SEED_HANDLER_INVENTORY.md",
    "TRACK_22_1F_SEED_DEPENDENCY_PROOF.md",
    "TRACK_22_1F_SEED_PARITY.md",
    "TRACK_22_1F_PLATFORM_STATUS_API.md",
    "TRACK_22_1F_PLATFORM_STATUS_SECURITY.md",
    "TRACK_22_1F_EMAIL_SAFETY.md",
    "TRACK_22_1F_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1F_TEST_REPORT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    sys.path.insert(0, str(BACKEND))
    import server  # type: ignore
    return server


# --- Migration correctness ---------------------------------------------------
def test_lifecycle_steps_contains_7_seed_handlers():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    seed_names = [s.name for s in LIFECYCLE_STEPS if s.group == "seed"]
    assert seed_names == MIGRATED_SEEDS, (
        f"LIFECYCLE_STEPS seed names drift.\n"
        f"expected: {MIGRATED_SEEDS}\n"
        f"actual:   {seed_names}"
    )


def test_lifecycle_steps_total_is_18():
    _load_server()
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS  # type: ignore
    assert len(LIFECYCLE_STEPS) == 18, (
        f"expected 18 LIFECYCLE_STEPS (11 index-ensure + 7 seed), got {len(LIFECYCLE_STEPS)}"
    )


def test_on_startup_no_longer_contains_migrated_seeds():
    server = _load_server()
    startup_names = [getattr(fn, "__name__", "") for fn in server.app.router.on_startup]
    for name in MIGRATED_SEEDS:
        assert name not in startup_names, (
            f"duplicate: {name} is still in app.router.on_startup after migration"
        )


def test_startup_handler_count_reduced_from_40_to_33():
    server = _load_server()
    assert len(server.app.router.on_startup) == 33, (
        f"expected 33 on_startup handlers after 7-seed migration, got {len(server.app.router.on_startup)}"
    )


# --- Runtime parity ----------------------------------------------------------
def test_runtime_snapshots_committed():
    for name in (
        "RUNTIME_ENUMERATION_before.json",
        "RUNTIME_ENUMERATION_after.json",
        "SEED_HANDLER_INVENTORY_before.json",
    ):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 500, f"missing/empty: {name}"


def test_route_and_openapi_parity_delta_is_only_platform_status():
    b = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_before.json").read_text(encoding="utf-8"))
    a = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_after.json").read_text(encoding="utf-8"))
    # Middleware unchanged; shutdown handler qualname + bytecode unchanged
    # (lineno may shift by the +Platform-Status route delta — that's expected).
    assert b["middleware"] == a["middleware"]
    def _shutdown_key(h): return (h["qualname"], h["name"], h["module"], h["bytecode_sha256"], h["is_coroutine"])
    assert [_shutdown_key(h) for h in b["shutdown_handlers"]] == [_shutdown_key(h) for h in a["shutdown_handlers"]]
    assert b["exception_handlers"] == a["exception_handlers"]
    # Route delta: exactly one intentional add.
    assert a["route_count"] == b["route_count"] + 1, (
        f"route_count drift: {b['route_count']} -> {a['route_count']} (expected +1 for platform/status)"
    )
    assert a["route_methods_total"] == b["route_methods_total"] + 1
    assert a["openapi_path_count"] == b["openapi_path_count"] + 1
    # Verify the added route is exactly /api/admin/platform/status GET.
    def key(r): return (r["path"], tuple(r["methods"]))
    b_by = {key(r): r for r in b["routes"]}
    a_by = {key(r): r for r in a["routes"]}
    added = set(a_by) - set(b_by)
    removed = set(b_by) - set(a_by)
    assert removed == set(), f"routes removed: {removed}"
    assert added == {("/api/admin/platform/status", ("GET",))}, f"unexpected route add: {added}"
    # No qualname / dependency-chain drift on shared routes.
    for k in b_by.keys() & a_by.keys():
        assert b_by[k]["endpoint_qualname"] == a_by[k]["endpoint_qualname"], k
        assert b_by[k]["dependency_chain"] == a_by[k]["dependency_chain"], k


def test_all_bytecode_fingerprints_match_live():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode  # type: ignore
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"


# --- Platform Status API -----------------------------------------------------
def test_platform_status_module_exists_and_has_no_resend_import():
    p = BACKEND / "lib" / "platform_status.py"
    assert p.is_file(), "backend/lib/platform_status.py missing"
    body = p.read_text(encoding="utf-8")
    tree = ast.parse(body)
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name != "resend", "platform_status.py must not import resend at module scope"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "resend"


def test_platform_status_route_admin_gated():
    server = _load_server()
    found = None
    for r in server.app.routes:
        if hasattr(r, "endpoint") and getattr(r, "path", "") == "/api/admin/platform/status":
            found = r
            break
    assert found is not None, "/api/admin/platform/status route missing"
    assert "GET" in (found.methods or set())
    dep_qualnames = [getattr(d.call, "__qualname__", "") for d in (found.dependant.dependencies or [])] if getattr(found, "dependant", None) else []
    assert any("require_admin_strict" in q for q in dep_qualnames), (
        f"platform/status must be gated by require_admin_strict; deps={dep_qualnames}"
    )


def test_platform_status_payload_shape_no_secrets():
    server = _load_server()
    from lib.platform_status import platform_status  # type: ignore
    out = platform_status(server.app)
    # Required top-level fields.
    for k in ("service", "attestation_version", "routes", "middleware", "lifecycle",
              "bytecode_fingerprints", "email_safety", "readiness",
              "recommended_next_actions", "recent_track_closures"):
        assert k in out, f"platform_status missing key: {k}"
    # Lifecycle counts sane.
    assert out["lifecycle"]["registry"]["by_group"].get("index-ensure") == 11
    assert out["lifecycle"]["registry"]["by_group"].get("seed") == 7
    assert out["lifecycle"]["on_startup_legacy_count"] == 33
    # Bytecode fingerprint status clean.
    assert out["bytecode_fingerprints"]["clean"] is True
    assert out["bytecode_fingerprints"]["drift_count"] == 0
    # Email safety in test env.
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["live_emails_possible"] is False
    # No secret-looking keys in the payload.
    payload_json = json.dumps(out)
    for banned in ("MONGO_URL", "RESEND_API_KEY", "SUPER_ADMIN_BOOTSTRAP_PASSWORD",
                   "ADMIN_HMAC_SECRET", "DEV_PASSWORD", "mongodb+srv://", "sk_",
                   "Bearer ", "@mascigc.com"):
        assert banned not in payload_json, f"platform_status payload leaks secret token: {banned}"


# --- Deliverables + ledgers --------------------------------------------------
def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_ledgers_record_track_22_1f():
    for name in ("PRD.md", "CHANGELOG.md", "TECHNICAL_DEBT_REGISTER.md"):
        body = (MEM / name).read_text(encoding="utf-8")
        assert "22.1F" in body or "22.1f" in body, f"{name} missing Track 22.1F"


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
