"""Track 22.1C · Scheduler Bootstrap Extraction + Startup-Order Parity — lock test.

Enforces:
- Full startup/shutdown inventory JSON is committed.
- Runtime enumeration remained byte-equal to the Track 22.1B close snapshot.
- SHA-256 bytecode fingerprints for the 4 email-capable scheduler handlers
  + the Track 22.1B `_dispatch_auto_email` all match live bytecode.
- `backend/lib/scheduler_bootstrap.py` exists, does NOT `import resend`,
  and exports `verify_locked_bytecode(app)` + `load_fingerprint_index()`.
- All Track 22.1C deliverables committed and non-empty.
- Ledgers (PRD, CHANGELOG, Debt Register) record the track.
- Prior guardrails (EMAIL_SAFETY_MODE=strict, CORS explicit lists,
  prior lock-tests) survive.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_1c"
FP_DIR = MEM / "BYTECODE_FINGERPRINTS"

DELIVERABLES = [
    "TRACK_22_1C_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1C_SCHEDULER_ARCHITECTURE.md",
    "TRACK_22_1C_SCHEDULER_INVENTORY.md",
    "TRACK_22_1C_STARTUP_ORDER_PARITY.md",
    "TRACK_22_1C_EXTRACTION_PLAN.md",
    "TRACK_22_1C_SIDE_EFFECT_CERTIFICATION.md",
    "TRACK_22_1C_EMAIL_SAFETY.md",
    "TRACK_22_1C_ZERO_NOISE_REPORT.md",
    "TRACK_22_1C_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1C_TEST_REPORT.md",
]

LOCKED_HANDLERS = [
    "_start_safety_digest_cron",
    "_start_operator_digest_cron",
    "_start_po_digest_cron",
    "_dispatch_reminder_scheduler_start",
]


# --- Inventory snapshots ----------------------------------------------------
def test_startup_inventory_committed():
    for name in ("STARTUP_ORDER_before.json", "SCHEDULER_INVENTORY_before.json",
                 "RUNTIME_ENUMERATION_baseline.json"):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 500, f"missing/empty: {name}"


def test_inventory_counts_baseline():
    inv = json.loads((TRACK_DIR / "STARTUP_ORDER_before.json").read_text(encoding="utf-8"))
    assert inv["startup_handler_count"] == 51, f"expected 51 startup handlers, got {inv['startup_handler_count']}"
    assert inv["shutdown_handler_count"] == 1
    sched = json.loads((TRACK_DIR / "SCHEDULER_INVENTORY_before.json").read_text(encoding="utf-8"))
    assert sched["count"] >= 10, f"scheduler-capable handler count regressed: {sched['count']}"


# --- Runtime enumeration parity vs Track 22.1B close -----------------------
def test_runtime_enum_matches_22_1b_close():
    a = json.loads((MEM / "track_22_1b" / "RUNTIME_ENUMERATION_after.json").read_text(encoding="utf-8"))
    b = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_baseline.json").read_text(encoding="utf-8"))
    assert a["route_count"] == b["route_count"]
    assert a["route_methods_total"] == b["route_methods_total"]
    assert a["openapi_path_count"] == b["openapi_path_count"]
    assert a["middleware"] == b["middleware"]
    assert a["startup_handlers"] == b["startup_handlers"]
    assert a["shutdown_handlers"] == b["shutdown_handlers"]

    def key(r): return (r["path"], tuple(r["methods"]))
    a_by = {key(r): r for r in a["routes"]}
    b_by = {key(r): r for r in b["routes"]}
    assert set(a_by) == set(b_by)
    for k in a_by.keys() & b_by.keys():
        assert a_by[k]["endpoint_qualname"] == b_by[k]["endpoint_qualname"]
        assert a_by[k]["dependency_chain"] == b_by[k]["dependency_chain"]


# --- SHA-256 fingerprint index -----------------------------------------------
def test_fingerprint_index_present():
    idx_file = FP_DIR / "INDEX.json"
    assert idx_file.is_file(), "BYTECODE_FINGERPRINTS/INDEX.json missing"
    idx = json.loads(idx_file.read_text(encoding="utf-8"))
    # Must contain the Track 22.1B dispatcher fingerprint.
    assert "_dispatch_auto_email" in idx
    # Must contain all 4 email-capable scheduler handlers.
    for name in LOCKED_HANDLERS:
        assert name in idx, f"missing fingerprint for {name}"
    # Every stored fingerprint is a 64-hex-char sha256.
    for name, fp in idx.items():
        assert re.match(r"^[0-9a-f]{64}$", fp), f"bad fingerprint for {name}: {fp!r}"


def test_dispatcher_fingerprint_still_matches_track_22_1b():
    idx = json.loads((FP_DIR / "INDEX.json").read_text(encoding="utf-8"))
    stored_22_1b = (MEM / "track_22_1b" / "DISPATCHER_BYTECODE_FINGERPRINT.txt").read_text(encoding="utf-8").strip()
    assert idx["_dispatch_auto_email"] == stored_22_1b, (
        "Track 22.1B dispatcher fingerprint drift! "
        f"22.1B={stored_22_1b} 22.1C-index={idx['_dispatch_auto_email']}"
    )


def test_all_locked_handlers_match_live_bytecode():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    sys.path.insert(0, str(BACKEND))
    import server  # type: ignore
    from lib.scheduler_bootstrap import verify_locked_bytecode  # type: ignore

    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"bytecode drift detected: {result['drift']}"
    assert result["missing"] == [], f"locked handlers missing: {result['missing']}"
    assert len(result["ok"]) >= 5, f"too few fingerprints ok: {result}"


# --- New scheduler_bootstrap module -----------------------------------------
def test_scheduler_bootstrap_module_exists():
    p = BACKEND / "lib" / "scheduler_bootstrap.py"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    assert "verify_locked_bytecode" in src
    assert "load_fingerprint_index" in src


def test_scheduler_bootstrap_does_not_import_resend():
    """SDK-safety guardrail: any new lib module must not import resend at
    module scope to avoid disturbing the Track 21.2E patch order."""
    body = (BACKEND / "lib" / "scheduler_bootstrap.py").read_text(encoding="utf-8")
    tree = ast.parse(body)
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name != "resend"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "resend"


# --- Deliverables + ledgers -------------------------------------------------
def test_all_deliverables_present_and_non_empty():
    missing, empty = [], []
    for name in DELIVERABLES:
        p = MEM / name
        if not p.is_file():
            missing.append(name)
        elif p.stat().st_size < 200:
            empty.append(name)
    assert not missing, f"missing: {missing}"
    assert not empty, f"empty: {empty}"


def test_debt_register_records_track_22_1c():
    body = (MEM / "TECHNICAL_DEBT_REGISTER.md").read_text(encoding="utf-8")
    assert "22.1c" in body.lower() or "22.1C" in body or "Track 22.1C" in body


def test_prd_records_track_22_1c():
    body = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 22.1C" in body or "Track 22.1C" in body or "22.1c" in body.lower()


def test_changelog_records_track_22_1c():
    body = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 22.1C" in body or "Track 22.1C" in body or "22.1c" in body.lower()


# --- Prior guardrails preserved ---------------------------------------------
def test_email_safety_layers_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):' in src
    assert "_dispatch_auto_email" in src
    env = (BACKEND / ".env").read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", env, re.MULTILINE)


def test_cors_explicit_allow_lists_preserved():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'allow_methods=["*"]' not in src
    assert 'allow_headers=["*"]' not in src


def test_prior_track_lock_files_committed():
    for name in (
        "test_track_22_0_platform_excellence.py",
        "test_track_22_1_server_modularization.py",
        "test_track_22_1b_email_dispatch.py",
    ):
        assert (BACKEND / "tests" / name).is_file(), f"missing prior lock: {name}"
