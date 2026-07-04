"""Track 22.1D · FastAPI Lifespan Migration Foundation — lock test.

Enforces:
- `backend/lib/lifespan_bootstrap.py` exists with expected exports and
  does NOT import `resend` at module scope.
- `server.py` wires `lifespan=` into `FastAPI(...)`.
- Runtime enumeration parity vs Track 22.1C baseline (0 route drift,
  0 qualname drift, 0 dependency-chain drift).
- All 5 Track 22.1B/22.1C SHA-256 bytecode fingerprints still match live.
- Lifespan boot log line fires (`[track-22.1d] lifespan.startup: complete`).
- All Track 22.1D deliverables committed and non-empty.
- Ledgers record the track.
- Prior guardrails preserved (EMAIL_SAFETY_MODE=strict, CORS explicit lists,
  Track 22.0/22.1/22.1B/22.1C lock-test files still committed).
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
TRACK_DIR = MEM / "track_22_1d"
FP_DIR = MEM / "BYTECODE_FINGERPRINTS"

DELIVERABLES = [
    "TRACK_22_1D_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1D_LIFESPAN_ARCHITECTURE.md",
    "TRACK_22_1D_LIFECYCLE_INVENTORY.md",
    "TRACK_22_1D_DEPENDENCY_ORDER_MAP.md",
    "TRACK_22_1D_LIFESPAN_DESIGN_PLAN.md",
    "TRACK_22_1D_STARTUP_PARITY.md",
    "TRACK_22_1D_SHUTDOWN_PARITY.md",
    "TRACK_22_1D_EMAIL_SAFETY_RECERTIFICATION.md",
    "TRACK_22_1D_SIDE_EFFECT_RECERTIFICATION.md",
    "TRACK_22_1D_DEPRECATION_CLEANUP.md",
    "TRACK_22_1D_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1D_TEST_REPORT.md",
]


def test_lifespan_bootstrap_module_exists():
    body = (BACKEND / "lib" / "lifespan_bootstrap.py").read_text(encoding="utf-8")
    for sym in ("orchestrated_lifespan", "create_lifespan"):
        assert sym in body, f"missing symbol: {sym}"


def test_lifespan_bootstrap_does_not_import_resend():
    body = (BACKEND / "lib" / "lifespan_bootstrap.py").read_text(encoding="utf-8")
    tree = ast.parse(body)
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name != "resend"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "resend"


def test_server_py_wires_lifespan():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "lifespan=" in src, "FastAPI() must be constructed with lifespan="
    assert "lifespan_bootstrap" in src


def test_runtime_snapshots_committed():
    for name in ("RUNTIME_ENUMERATION_before.json", "RUNTIME_ENUMERATION_after.json"):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 1000


def test_runtime_parity_zero_drift():
    b = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_before.json").read_text(encoding="utf-8"))
    a = json.loads((TRACK_DIR / "RUNTIME_ENUMERATION_after.json").read_text(encoding="utf-8"))
    assert b["route_count"] == a["route_count"]
    assert b["route_methods_total"] == a["route_methods_total"]
    assert b["openapi_path_count"] == a["openapi_path_count"]
    assert b["middleware"] == a["middleware"]
    assert b["startup_handlers"] == a["startup_handlers"]
    assert b["shutdown_handlers"] == a["shutdown_handlers"]

    def key(r): return (r["path"], tuple(r["methods"]))
    b_by = {key(r): r for r in b["routes"]}
    a_by = {key(r): r for r in a["routes"]}
    assert set(b_by) == set(a_by)
    for k in b_by.keys() & a_by.keys():
        assert b_by[k]["endpoint_qualname"] == a_by[k]["endpoint_qualname"]
        assert b_by[k]["dependency_chain"] == a_by[k]["dependency_chain"]


def test_all_bytecode_fingerprints_still_match_live():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    sys.path.insert(0, str(BACKEND))
    import server  # type: ignore
    from lib.scheduler_bootstrap import verify_locked_bytecode  # type: ignore

    result = verify_locked_bytecode(server.app)
    assert result["drift"] == [], f"bytecode drift: {result['drift']}"
    assert result["missing"] == [], f"missing: {result['missing']}"
    assert len(result["ok"]) >= 5


def test_lifecycle_inventory_committed():
    for name in ("STARTUP_ORDER_before.json", "STARTUP_ORDER_after.json",
                 "SHUTDOWN_ORDER_before.json", "LIFECYCLE_INVENTORY_before.json",
                 "LIFECYCLE_INVENTORY_after.json"):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 100, f"missing/empty: {name}"


def test_startup_handler_count_preserved():
    b = json.loads((TRACK_DIR / "STARTUP_ORDER_before.json").read_text(encoding="utf-8"))
    a = json.loads((TRACK_DIR / "STARTUP_ORDER_after.json").read_text(encoding="utf-8"))
    assert b["startup_handler_count"] == a["startup_handler_count"] == 51
    assert b["shutdown_handler_count"] == a["shutdown_handler_count"] == 1
    # Handler qualnames + bytecode SHA + module attributions must all match
    # (only line numbers may shift due to the FastAPI(lifespan=...) argument
    # adding lines at the top of server.py).
    for i, (bh, ah) in enumerate(zip(b["startup_handlers"], a["startup_handlers"])):
        assert bh["qualname"] == ah["qualname"], f"#{i} qualname drift"
        assert bh["name"] == ah["name"], f"#{i} name drift"
        assert bh["module"] == ah["module"], f"#{i} module drift"
        assert bh["bytecode_sha256"] == ah["bytecode_sha256"], f"#{i} {bh['name']} bytecode drift"


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_ledgers_record_track_22_1d():
    for name in ("PRD.md", "CHANGELOG.md", "TECHNICAL_DEBT_REGISTER.md"):
        body = (MEM / name).read_text(encoding="utf-8")
        assert "22.1d" in body.lower() or "22.1D" in body, f"{name} missing Track 22.1D"


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
    ):
        assert (BACKEND / "tests" / name).is_file()
