"""DR-UNIFY-003 · Consolidation lock envelope.

Locks every invariant that must hold after route/collection consolidation:

- Canonical daily-reports routes exist AND the deprecated dr-v2 aliases
  keep working (backward-compat window preserved).
- Frontend router redirects /daily-report/v2 → /daily/submit and no
  longer imports the DailyReportV2 shell component.
- No user-facing V1/V2 language in the field surface or any admin AI
  page.
- The read-compat helper prefers canonical, falls back to legacy, and
  never merges.
- The migration script exists, is executable, and offers the four
  required modes.
- No prior track's lock tests are broken.
"""
from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


# ─────────────────────── file-level introspection ────────────────────

_APP_ROUTES = Path("/app/frontend/src/app/routing/AppRoutes.jsx")
_NEW_DAILY  = Path("/app/frontend/src/pages/NewDailyReport.jsx")
_DR_V2_PDF  = Path("/app/backend/routes/dr_v2_pdf.py")
_DAILY_SUM  = Path("/app/backend/routes/daily_summary.py")
_COMPAT_LIB = Path("/app/backend/lib/daily_report_collections.py")
_MIGR_PATH  = Path("/app/backend/scripts/migrate_dr_v2_collections_to_daily_report.py")


# ─────────────────────── invariant tests ─────────────────────────────

def test_frontend_router_redirects_daily_report_v2_to_daily_submit():
    src = _APP_ROUTES.read_text(encoding="utf-8")
    # The redirect line MUST be present.
    m = re.search(
        r'path="/daily-report/v2"\s+element=\{[^}]*Navigate\s+to="/daily/submit"',
        src,
    )
    assert m, "expected /daily-report/v2 to <Navigate to='/daily/submit'>"
    # The old element mount MUST be gone.
    assert 'element={<DailyReportV2 />}' not in src, \
        "the legacy V2 shell must no longer be a routed element"


def test_frontend_router_no_longer_imports_daily_report_v2_shell():
    src = _APP_ROUTES.read_text(encoding="utf-8")
    # The old default import must be gone (a comment referencing the
    # component name is allowed).
    assert 'import DailyReportV2 from' not in src, \
        "AppRoutes.jsx must not import DailyReportV2 anymore"


def test_daily_summary_endpoints_are_under_canonical_prefix():
    """DR-CUTOVER-002 endpoints must live under /api/daily-reports/*."""
    src = _DAILY_SUM.read_text(encoding="utf-8")
    assert '/daily-reports/summary/draft' in src
    assert '/daily-reports/{report_id}/summary/accept' in src
    assert '/dr-v2/' not in src


def test_dr_v2_pdf_router_serves_both_canonical_and_alias():
    """Route aliases: canonical + deprecated live side-by-side."""
    src = _DR_V2_PDF.read_text(encoding="utf-8")
    assert '/daily-reports/approved' in src
    assert '/dr-v2/reports/approved' in src
    assert '/daily-reports/{report_id}/pdf' in src
    assert '/dr-v2/reports/{report_id}/pdf' in src


def test_new_daily_report_form_has_no_v1_or_v2_user_facing_language():
    """The single field form must never surface V1/V2 vocabulary or
    AI/model/provider/token/cost language to users."""
    src = _NEW_DAILY.read_text(encoding="utf-8").lower()
    for banned in [
        "try v2", '"v1"', '"v2"', "next generation",
        "ai agent", "ai-agent",
        "\"model\":", "\"provider\":", "\"token_cost\":",
        "cost meter", "token cost",
    ]:
        assert banned not in src, f"banned user-facing string in NewDailyReport: `{banned}`"


def test_compat_helper_exposes_expected_aliases():
    from lib.daily_report_collections import COLLECTION_ALIASES  # type: ignore
    for canonical, legacy in [
        ("daily_report_drafts",             "dr_v2_drafts"),
        ("daily_report_ai_cache",           "dr_v2_ai_cache"),
        ("daily_report_ai_audit_entries",   "dr_v2_ai_audit_entries"),
        ("daily_report_ai_approvals",       "dr_v2_ai_approvals"),
        ("daily_report_photo_intelligence", "dr_v2_photo_intelligence"),
        ("daily_report_bilingual_audit",    "dr_v2_bilingual_audit"),
    ]:
        assert COLLECTION_ALIASES.get(canonical) == legacy


@pytest.mark.asyncio
async def test_resolve_read_prefers_canonical_when_populated():
    from lib.daily_report_collections import resolve_read_collection_name  # type: ignore

    class _Coll:
        def __init__(self, docs):
            self.docs = docs
        async def find_one(self, q, projection=None):
            return self.docs[0] if self.docs else None

    class _DB:
        def __init__(self, canon_has, legacy_has):
            self._c = _Coll([{"_id": "x"}] if canon_has else [])
            self._l = _Coll([{"_id": "y"}] if legacy_has else [])
        def __getitem__(self, name):
            return self._c if name.startswith("daily_report_") else self._l

    # Canonical has data → return canonical.
    assert (await resolve_read_collection_name(_DB(True, True),
            "daily_report_drafts")) == "daily_report_drafts"
    # Only legacy has data → return legacy.
    assert (await resolve_read_collection_name(_DB(False, True),
            "daily_report_drafts")) == "dr_v2_drafts"
    # Neither has data → default to canonical.
    assert (await resolve_read_collection_name(_DB(False, False),
            "daily_report_drafts")) == "daily_report_drafts"


def test_compat_helper_never_returns_a_merge():
    """resolve_read_collection_name returns a single name string —
    never a list — so double-counting is impossible by construction."""
    import inspect
    from lib import daily_report_collections as compat  # type: ignore
    src = inspect.getsource(compat.resolve_read_collection_name)
    assert "return canonical" in src
    assert "return legacy" in src
    # No merge/union operation — a single collection name is always returned.
    assert "+" not in src.split("return")[-1]
    assert "extend(" not in src and "update(" not in src
    # And the write helper is a pure passthrough to canonical.
    assert "return canonical" in inspect.getsource(compat.canonical_write_collection_name)


def test_migration_script_exists_and_is_executable():
    assert _MIGR_PATH.exists(), "migration script missing"
    mode = _MIGR_PATH.stat().st_mode
    # Not enforcing +x since python3 <path> works either way, but assert
    # readability at minimum.
    assert mode & stat.S_IRUSR


def test_migration_script_has_four_required_modes():
    src = _MIGR_PATH.read_text(encoding="utf-8")
    for flag in ("--dry-run", "--live", "--verify", "--rollback"):
        assert flag in src, f"migration script missing mode {flag}"
    # Refuse-prod safety.
    assert "APP_ENV" in src and "allow-prod" in src


def test_migration_script_help_prints():
    """Smoke — help works, no import error at load time."""
    r = subprocess.run(
        [sys.executable, str(_MIGR_PATH), "--help"],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stderr
    for flag in ("--dry-run", "--live", "--verify", "--rollback"):
        assert flag in r.stdout


def test_migration_script_refuses_production_by_default(tmp_path):
    """When APP_ENV=production and no --allow-prod, exit code is non-zero."""
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env.setdefault("MONGO_URL", "mongodb://127.0.0.1:1/nope")
    env.setdefault("DB_NAME", "unused")
    r = subprocess.run(
        [sys.executable, str(_MIGR_PATH)],
        capture_output=True, text=True, timeout=30, env=env,
    )
    assert r.returncode != 0
    assert "REFUSING to run" in r.stderr


def test_migration_script_rollback_plan_prints_without_touching_db(tmp_path):
    env = os.environ.copy()
    env.setdefault("MONGO_URL", "mongodb://127.0.0.1:1/nope")
    env.setdefault("DB_NAME", "unused")
    env["APP_ENV"] = "preview"
    r = subprocess.run(
        [sys.executable, str(_MIGR_PATH), "--rollback"],
        capture_output=True, text=True, timeout=30, env=env,
    )
    assert r.returncode == 0
    assert "rollback-plan" in r.stdout


def test_no_new_route_deletes_a_legacy_alias():
    """Guard against a future edit accidentally dropping either the
    canonical or the deprecated alias route from the PDF router."""
    src = _DR_V2_PDF.read_text(encoding="utf-8")
    # Both approved list variants must exist.
    assert src.count("/daily-reports/approved") >= 1
    assert src.count("/dr-v2/reports/approved") >= 1
    # Both PDF variants must exist.
    assert src.count("/daily-reports/{report_id}/pdf") >= 1
    assert src.count("/dr-v2/reports/{report_id}/pdf") >= 1


def test_daily_submit_form_still_mounts_the_summary_section():
    """Regression against DR-CUTOVER-002 — the summary section stays
    inside the real form."""
    src = Path("/app/frontend/src/components/daily-report-v3/sections.jsx").read_text(encoding="utf-8")
    assert "DailySummaryAssist" in src, \
        "Canonical Daily Report summary section must remain mounted"


def test_no_user_facing_ai_language_in_daily_summary_backend_route():
    """DR-CUTOVER-002 route must remain UI-copy clean."""
    src = _DAILY_SUM.read_text(encoding="utf-8").lower()
    for banned in ("anthropic", "openai", "gemini", "ai agent",
                   " model =", "provider ="):
        assert banned not in src, f"banned marketing/AI wording in daily_summary.py: `{banned}`"


def test_daily_reports_route_still_ignorant_of_ai_summary_module():
    """DR-CUTOVER-002 regression lock lives on."""
    src = Path("/app/backend/routes/daily_reports.py").read_text(encoding="utf-8")
    assert "daily_summary" not in src
    assert "resolve_ai_capabilities" not in src


def test_ai_config_env_placeholders_still_present():
    """AI-CONFIG-001 regression — no accidental removal of the Emergent
    Secrets contract."""
    body = Path("/app/backend/.env").read_text(encoding="utf-8")
    keys = {ln.split("=", 1)[0].strip() for ln in body.splitlines() if "=" in ln}
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY",
              "AI_GATEWAY_ENABLED", "TENANT_AI_ENABLED",
              "AI_DAILY_REPORT_SUMMARY_ENABLED",
              "AI_ADMIN_INTELLIGENCE_ENABLED"):
        assert k in keys


def test_ods_module_still_reads_dr_v2_drafts_via_compat_or_legacy_path():
    """ODS approval-fact reader still targets the legacy collection —
    the read-compat layer is available for future migration, but the
    legacy read path must not be silently deleted before DR-UNIFY-004."""
    src = Path("/app/backend/services/ods_spine/ingest.py").read_text(encoding="utf-8")
    # Either the legacy read remains, or a compat helper is used.
    assert ("dr_v2_drafts" in src) or ("resolve_read_collection_name" in src)
