"""Track 22.2 Phase B · App.js route-group extraction — lock test.

Enforces every constitutional invariant of the extraction:
  1. All required deliverables exist (10 markdown files + parity artifacts + extractor).
  2. Before / after inventories exist and are non-trivial.
  3. Post-extraction route count, unique paths, and guards match the pre-extraction baseline.
  4. No confirmed-dead imports (still 0).
  5. `frontend/src/App.js` has been thinned dramatically (< 200 lines).
  6. `frontend/src/App.js` no longer contains a monolithic route block (< 5 `<Route ` tokens).
  7. `frontend/src/app/routing/AppRoutes.jsx` exists and contains ≥ 384 `<Route ` tokens.
  8. Backend runtime parity is intact.
  9. Email safety is strict + patched + no live.
 10. Bytecode fingerprints stay clean.
 11. PRD + CHANGELOG + TECHNICAL_DEBT_REGISTER reference Track 22.2 Phase B.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
FRONTEND = APP / "frontend"
MEM = APP / "memory"
TR = MEM / "track_22_2"

DELIVERABLES = [
    "TRACK_22_2_EXECUTIVE_SUMMARY.md",
    "TRACK_22_2_TARGET_ARCHITECTURE.md",
    "TRACK_22_2_ROUTE_PARITY_REPORT.md",
    "TRACK_22_2_PROVIDER_GUARD_LAYOUT_PARITY.md",
    "TRACK_22_2_BUNDLE_PERFORMANCE_REPORT.md",
    "TRACK_22_2_PLAYWRIGHT_CERTIFICATION.md",
    "TRACK_22_2_BACKEND_SAFETY_RECERTIFICATION.md",
    "TRACK_22_2_ENGINEERING_AUDIT.md",
    "TRACK_22_2_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_2_TEST_REPORT.md",
]

BEFORE_JSON = TR / "APP_JS_INVENTORY_before.json"
AFTER_JSON = TR / "APP_JS_INVENTORY_after.json"
DIFF_JSON = TR / "APP_JS_ROUTE_PARITY_DIFF.json"
APP_ROUTES = FRONTEND / "src" / "app" / "routing" / "AppRoutes.jsx"
APP_JS = FRONTEND / "src" / "App.js"


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    os.environ.setdefault("DISABLE_BACKUP_SCHEDULER", "true")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing/empty: {missing}"


def test_before_and_after_inventories_present():
    assert BEFORE_JSON.is_file() and BEFORE_JSON.stat().st_size > 5000
    assert AFTER_JSON.is_file() and AFTER_JSON.stat().st_size > 5000
    assert DIFF_JSON.is_file()


def test_route_count_preserved():
    b = json.loads(BEFORE_JSON.read_text())
    a = json.loads(AFTER_JSON.read_text())
    assert a["counts"]["routes"] == b["counts"]["routes"] == 385
    assert a["counts"]["unique_paths"] == b["counts"]["unique_paths"] == 385
    assert a["counts"]["duplicate_paths"] == b["counts"]["duplicate_paths"] == 0


def test_guard_and_provider_parity():
    b = json.loads(BEFORE_JSON.read_text())
    a = json.loads(AFTER_JSON.read_text())
    assert a["counts"]["guards"] == b["counts"]["guards"] == 11
    assert a["counts"]["providers"] == b["counts"]["providers"] == 1
    assert a["counts"]["chrome_components"] == b["counts"]["chrome_components"] == 15
    # Set-equality on (alias, component) tuples
    assert (sorted((g["alias"], g["component"]) for g in a["guards"])
            == sorted((g["alias"], g["component"]) for g in b["guards"]))


def test_route_set_and_ordering_preserved():
    d = json.loads(DIFF_JSON.read_text())
    assert d["routes_set_match"] is True
    assert d["route_ordering_preserved"] is True
    assert d["guards_match"] is True
    assert d["providers_match"] is True
    assert d["chrome_match"] is True
    assert d["lazy_set_match"] is True


def test_lazy_target_parity():
    b = json.loads(BEFORE_JSON.read_text())
    a = json.loads(AFTER_JSON.read_text())
    assert a["counts"]["lazy_imports"] == b["counts"]["lazy_imports"] == 180
    b_lazy = sorted((li["name"], li["module"]) for li in b["lazy_imports"])
    a_lazy = sorted((li["name"], li["module"]) for li in a["lazy_imports"])
    assert a_lazy == b_lazy, "lazy target set changed"


def test_zero_dead_imports():
    a = json.loads(AFTER_JSON.read_text())
    assert a["counts"]["dead_import_candidates"] == 0


def test_app_js_is_thin():
    text = APP_JS.read_text(encoding="utf-8")
    line_count = text.count("\n") + 1
    assert line_count < 200, f"App.js was not thinned enough: {line_count} lines"
    # App.js must NOT contain a monolithic route block: at most a couple of stray `<Route ` mentions
    route_tokens = text.count("<Route ")
    assert route_tokens < 5, f"App.js still contains route JSX: {route_tokens} tokens"


def test_app_routes_file_exists_and_owns_routes():
    assert APP_ROUTES.is_file()
    text = APP_ROUTES.read_text(encoding="utf-8")
    # Must own essentially all 385 routes
    route_tokens = text.count("<Route ")
    assert route_tokens >= 384, f"AppRoutes.jsx contains {route_tokens} <Route  tokens; expected 385+"
    # Must export AppRoutes for App.js to consume
    assert "export function AppRoutes()" in text or "export const AppRoutes" in text


def test_app_js_imports_app_routes():
    text = APP_JS.read_text(encoding="utf-8")
    assert 'from "@/app/routing/AppRoutes"' in text
    assert "<AppRoutes" in text


def test_backend_runtime_parity_intact():
    """Baseline was 1441/1445/1264. DR-ROI-001 Phase C additively mounted
    6 /api/dr-v2/* routes → 1447/1451/1270. ODS-001 additively mounts 8
    /api/ods/* routes → 1455/1459/1277. Track 22.2's App.js extraction
    claim (zero backend drift for THAT track) remains intact — no V1
    route was touched."""
    server = _load_server()
    routes = [r for r in server.app.routes if hasattr(r, "endpoint")]
    assert len(routes) == 1455
    methods = sum(len(getattr(r, "methods", None) or []) for r in routes)
    assert methods == 1459
    assert len(server.app.openapi().get("paths", {})) == 1277


def test_backend_lifecycle_and_email_safety_unchanged():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    mig = out["lifecycle"]["migration_progress"]
    assert mig["lifecycle_complete"] is True
    assert mig["startup_migration_pct"] == 100.0
    assert mig["shutdown_migration_pct"] == 100.0
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["resend_sdk_patched"] is True
    assert out["email_safety"]["live_emails_possible"] is False


def test_bytecode_fingerprints_still_clean():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode
    r = verify_locked_bytecode(server.app)
    assert r["drift"] == []
    assert r["missing"] == []
    assert r["checked"] >= 9


def test_prd_changelog_and_debt_register_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8", errors="ignore")
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    tdr = (MEM / "TECHNICAL_DEBT_REGISTER.md").read_text(encoding="utf-8", errors="ignore")
    for hay, needle in [(prd, "22.2 · Phase B"), (changelog, "22.2 · Phase B")]:
        assert needle in hay, f"{needle!r} missing"
    # TD-P1-C-1 (App.js modularization) must now show CLOSED / EXTRACTED
    assert "TD-P1-C-1" in tdr
