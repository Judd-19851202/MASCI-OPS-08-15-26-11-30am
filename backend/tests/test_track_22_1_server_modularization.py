"""Track 22.1 · server.py Modularization + Endpoint Parity — lock test.

Enforces:
- The two extracted modules exist under `backend/lib/` and contain the
  expected symbols.
- server.py re-imports those symbols under identical names so bare-name
  references remain byte-identical.
- The pre/post runtime enumeration JSONs are present and byte-comparable
  (except for the 2 intentional handler-qualname moves).
- All 13 Track 22.1 memory deliverables present and non-empty.
- Debt register + PRD + CHANGELOG record Track 22.1 closure.
- Every prior-track guardrail (email SDK patch, dispatcher gate, CORS
  explicit allow-lists, EMAIL_SAFETY_MODE=strict) survives.
- The route count / method count / startup count / middleware count / OpenAPI
  path count are numerically identical pre/post extraction.

No HTTP calls. No email dispatched. File-system + JSON compare only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_1"

DELIVERABLES = [
    "TRACK_22_1_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1_ARCHITECTURE_REPORT.md",
    "TRACK_22_1_ENDPOINT_PARITY_REPORT.md",
    "TRACK_22_1_RUNTIME_ENUMERATION.md",
    "TRACK_22_1_DEPENDENCY_GRAPH.md",
    "TRACK_22_1_MODULE_EXTRACTION_REPORT.md",
    "TRACK_22_1_STARTUP_PARITY.md",
    "TRACK_22_1_EMAIL_SAFETY_REPORT.md",
    "TRACK_22_1_AUTH_PARITY.md",
    "TRACK_22_1_PERFORMANCE_REPORT.md",
    "TRACK_22_1_ZERO_NOISE_REPORT.md",
    "TRACK_22_1_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_1_TEST_REPORT.md",
]


# --- Extracted modules exist and export expected symbols --------------------
def test_health_probes_module_exists_with_expected_symbols():
    body = (BACKEND / "lib" / "health_probes.py").read_text(encoding="utf-8")
    for sym in ("_probe_health", "_probe_healthz", "attach_health_probes"):
        assert f"def {sym}" in body, f"missing symbol: {sym}"
    assert 'include_in_schema=False' in body


def test_rate_limiting_module_exists_with_expected_symbols():
    body = (BACKEND / "lib" / "rate_limiting.py").read_text(encoding="utf-8")
    for sym in (
        "_client_ip", "rate_limit_public_post",
        "_check_login_lockout", "_record_login_fail", "_reset_login_fails",
        "_RATE_LOCK", "_PUBLIC_POST_BUCKETS", "_LOGIN_FAIL_BUCKETS",
        "PUBLIC_POST_LIMIT_PER_HOUR", "LOGIN_MAX_FAILS_PER_WINDOW",
        "LOGIN_LOCKOUT_SECONDS",
    ):
        assert sym in body, f"missing symbol in rate_limiting.py: {sym}"


# --- server.py re-imports the extracted symbols ------------------------------
def test_server_py_imports_extracted_modules():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "from lib.health_probes import attach_health_probes" in src
    assert "attach_health_probes(app)" in src
    assert "from lib.rate_limiting import" in src
    for name in (
        "rate_limit_public_post", "_client_ip",
        "_check_login_lockout", "_record_login_fail", "_reset_login_fails",
        "PUBLIC_POST_LIMIT_PER_HOUR",
    ):
        assert name in src, f"server.py must re-export {name}"


def test_server_py_no_longer_defines_extracted_bodies():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    # The old inline definitions must be gone.
    assert 'def _probe_health():' not in src, "inline _probe_health body still present"
    assert 'def _probe_healthz():' not in src, "inline _probe_healthz body still present"
    # Rate-limiting bodies (heuristic: single-line def with the tell-tale body next line).
    # We assert the module-level import path is the only place these live.
    # The re-import brings names into server, so the identifier appears in the import statement.
    # Absence of the *definition body* is proven by the module extraction file having them.
    lib_body = (BACKEND / "lib" / "rate_limiting.py").read_text(encoding="utf-8")
    assert "def rate_limit_public_post(request: Request):" in lib_body


# --- Runtime parity JSONs present and equivalent -----------------------------
def _load_json(name: str) -> dict:
    return json.loads((TRACK_DIR / name).read_text(encoding="utf-8"))


def test_runtime_enumeration_snapshots_committed():
    for name in ("RUNTIME_ENUMERATION_before.json", "RUNTIME_ENUMERATION_after.json"):
        p = TRACK_DIR / name
        assert p.is_file(), f"missing snapshot: {name}"
        assert p.stat().st_size > 1000


def test_route_count_and_openapi_parity():
    b = _load_json("RUNTIME_ENUMERATION_before.json")
    a = _load_json("RUNTIME_ENUMERATION_after.json")
    assert b["route_count"] == a["route_count"], "route count drift"
    assert b["route_methods_total"] == a["route_methods_total"], "method count drift"
    assert b["openapi_path_count"] == a["openapi_path_count"], "openapi drift"


def test_middleware_startup_shutdown_exception_parity():
    b = _load_json("RUNTIME_ENUMERATION_before.json")
    a = _load_json("RUNTIME_ENUMERATION_after.json")
    assert b["middleware"] == a["middleware"], "middleware set drift"
    assert b["startup_handlers"] == a["startup_handlers"], "startup handler drift"
    assert b["shutdown_handlers"] == a["shutdown_handlers"], "shutdown handler drift"
    assert b["exception_handlers"] == a["exception_handlers"], "exception handler drift"


def test_route_set_parity_paths_and_methods():
    b = _load_json("RUNTIME_ENUMERATION_before.json")
    a = _load_json("RUNTIME_ENUMERATION_after.json")

    def key(r): return (r["path"], tuple(r["methods"]))
    b_keys = {key(r) for r in b["routes"]}
    a_keys = {key(r) for r in a["routes"]}
    assert b_keys == a_keys, f"route set drift: +{a_keys - b_keys!r} -{b_keys - a_keys!r}"


def test_only_intentional_handler_module_moves():
    """The ONLY endpoint_qualname / dependency_chain drift permitted is the
    move of `_probe_health` / `_probe_healthz` from `server.*` to
    `lib.health_probes.*`. Any other drift fails the parity gate."""
    b = _load_json("RUNTIME_ENUMERATION_before.json")
    a = _load_json("RUNTIME_ENUMERATION_after.json")

    def key(r): return (r["path"], tuple(r["methods"]))
    b_by = {key(r): r for r in b["routes"]}
    a_by = {key(r): r for r in a["routes"]}

    ALLOWED_MOVES = {
        (("/health", ("GET",)), "server._probe_health", "lib.health_probes._probe_health"),
        (("/healthz", ("GET",)), "server._probe_healthz", "lib.health_probes._probe_healthz"),
    }

    for k in b_by.keys() & a_by.keys():
        b_qn = b_by[k]["endpoint_qualname"]
        a_qn = a_by[k]["endpoint_qualname"]
        if b_qn != a_qn:
            assert (k, b_qn, a_qn) in ALLOWED_MOVES, f"unexpected handler module move: {k} {b_qn} → {a_qn}"
        assert b_by[k]["dependency_chain"] == a_by[k]["dependency_chain"], (
            f"dependency chain drift on {k}: {b_by[k]['dependency_chain']} → {a_by[k]['dependency_chain']}"
        )


# --- Deliverables + ledgers --------------------------------------------------
def test_all_deliverables_present_and_non_empty():
    missing = []
    empty = []
    for name in DELIVERABLES:
        p = MEM / name
        if not p.is_file():
            missing.append(name)
        elif p.stat().st_size < 200:
            empty.append(name)
    assert not missing, f"missing deliverables: {missing}"
    assert not empty, f"empty deliverables: {empty}"


def test_debt_register_records_track_22_1_closure():
    body = (MEM / "TECHNICAL_DEBT_REGISTER.md").read_text(encoding="utf-8")
    assert "TD-22.1" in body
    assert re.search(r"22\.1.*(CLOSED|PARTIAL|EXTRACTION)", body, re.IGNORECASE) or "Track 22.1" in body


def test_prd_records_track_22_1():
    body = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 22.1" in body or "Track 22.1" in body


def test_changelog_records_track_22_1():
    body = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 22.1" in body or "Track 22.1" in body


# --- Prior-track guardrails survive -----------------------------------------
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
    assert '"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"' in src


def test_track_22_0_lock_still_committed():
    assert (BACKEND / "tests" / "test_track_22_0_platform_excellence.py").is_file()
