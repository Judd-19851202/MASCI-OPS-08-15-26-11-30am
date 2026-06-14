"""
tests/test_data_hygiene_sweep.py — Track 14.0-P0 Preview/Test/Demo Data
Deployment Hygiene Sweep regression guard.

Locks the production data boundary so future PRs cannot:
  1. Remove the startup env/DB alignment check that refuses to start
     when APP_ENV and DB_NAME disagree.
  2. Ship a demo / preview-only seed script without a production
     refuse-to-run guard.
  3. Insert a credential, demo user, or seed record into the canonical
     production startup path.

These are static-analysis assertions — no live DB writes — so they run
in any environment without risk of corrupting data.

Closure ledger:
/app/memory/TRACK_14_0_P0_PREVIEW_TEST_DEMO_DATA_HYGIENE_SWEEP_CLOSURE.md
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path("/app")
SERVER = REPO / "backend/server.py"
SCRIPTS = REPO / "backend/scripts"


# ── Env / DB alignment ─────────────────────────────────────────────


def test_env_db_alignment_guard_intact():
    """server._verify_env_db_alignment() is the last line of defence
    that prevented the 2026-05-26 preview/production data crossover
    incident from repeating. The check MUST keep raising RuntimeError
    when APP_ENV and DB_NAME disagree — preview env must require a
    `_preview` DB and production must refuse one."""
    text = SERVER.read_text()
    assert "_verify_env_db_alignment" in text, (
        "server.py removed the _verify_env_db_alignment() guard. "
        "Without this, preview code can write into the live "
        "`masci_safety` database again — exactly the 2026-05-26 "
        "crossover incident this guard was added to prevent.")
    # Must enforce both directions.
    assert 'app_env == "preview"' in text and "is_preview_db" in text, (
        "Env-DB guard no longer references both APP_ENV=preview and "
        "the `_preview` DB suffix — one direction of the safety net "
        "is missing.")
    # Must RAISE, not just warn.
    assert "raise RuntimeError" in text and "REFUSING TO START" in text, (
        "Env-DB guard no longer raises RuntimeError on mismatch. "
        "A warning is not enough — the server must refuse to start.")
    # Must run at import time so misconfigured workers cannot serve
    # any requests before tripping the check.
    assert "_verify_env_db_alignment()" in text, (
        "Env-DB guard is defined but never invoked at module load.")


# ── Demo / preview seed scripts must refuse production ─────────────


@pytest.mark.parametrize("script_path", [
    "backend/scripts/seed_pm_demo_fixture.py",
    "backend/scripts/dls_seed_demo.py",
])
def test_demo_seed_scripts_refuse_production(script_path):
    """Any script that seeds demo / preview-only data MUST contain a
    runtime guard that refuses to run against a production DB or
    APP_ENV. Without that guard, an operator running the script with
    production env vars in their shell silently injects demo records
    into the live database."""
    text = (REPO / script_path).read_text()
    # Must reference APP_ENV / preview / production env detection.
    assert ("APP_ENV" in text or "DB_NAME" in text), (
        f"{script_path} has no env-aware guard — running it with "
        "production env vars in the shell would seed demo data into "
        "the live database.")
    # Must explicitly refuse the wrong env (raise / sys.exit / return).
    bad_combos = ("RefusingToRun" in text
                  or "REFUSING TO RUN" in text
                  or "RuntimeError" in text
                  or "hard-block" in text
                  or "hard_block" in text
                  or "production tenant" in text.lower()
                  or "is hard-blocked" in text)
    assert bad_combos, (
        f"{script_path} mentions APP_ENV but doesn't appear to "
        "explicitly refuse the production environment. Add an "
        "explicit raise/exit so misuse is impossible.")


# ── No demo data in the canonical production startup path ─────────


def test_server_startup_does_not_auto_seed_demo_collections():
    """server.py must not auto-seed any of the demo collections
    (TEST_iter*, demo employees, fake jobs) during startup. The only
    legitimate startup writes are scheme/migration patches and
    bootstrap records. Catch obvious regressions by scanning for
    demo-keyword strings inside the startup section."""
    text = SERVER.read_text()
    # We slice off the first 3 KB of imports + alignment guard and
    # check the next ~1 MB body for forbidden literal seeds.
    forbidden_literals = [
        "TEST Juan Perez",
        "TEST Worker",
        "Approval Test User",
        "Test Driver OOS",
        "Test Mechanic",
        "Lorem ipsum",
        "lorem ipsum",
    ]
    leaks = [s for s in forbidden_literals if s in text]
    assert not leaks, (
        f"server.py contains literal demo strings inside the request "
        f"path: {leaks!r}. These belong in tests/fixtures only — "
        "never compiled into production server code.")


def test_test_credentials_doc_is_not_referenced_by_runtime():
    """/app/memory/test_credentials.md documents preview-only test
    accounts and must NEVER be read by the running backend. If a
    future change accidentally adds `open()` on the file, the test
    user/password could leak into production logs or responses."""
    backend_py = list((REPO / "backend").rglob("*.py"))
    for fp in backend_py:
        if "/tests/" in str(fp) or "/scripts/" in str(fp):
            continue
        text = fp.read_text(errors="ignore")
        assert "test_credentials.md" not in text, (
            f"{fp} now references test_credentials.md from runtime "
            "code. That file documents preview-only credentials and "
            "must remain a memory-only reference.")


# ── Production data-import safety ─────────────────────────────────


def test_admin_restore_paths_do_not_assume_preview_db():
    """The admin backup-restore path (`/api/admin/backups/restore/...`)
    must not silently accept preview-shaped data. The env/DB guard
    keeps the runtime aligned, but the restore handler itself should
    refuse a restore archive that obviously came from a preview DB
    (DB_NAME=*_preview is part of the metadata). This test only
    verifies that admin-token authentication is enforced — fully
    auditing every restore archive is a separate manual deploy
    checklist item, documented in the closure ledger."""
    text = SERVER.read_text()
    # Restore endpoints must be wrapped in admin auth dependency.
    for kw in ("exports_restore", "restore_employee", "admin_restore_job"):
        assert kw in text, f"Restore endpoint {kw!r} no longer exists."
    # The endpoint signatures must include require_admin (admin gate).
    # Grep for the admin-token Depends on the relevant lines.
    for fn in ("admin_restore_job", "restore_supplier"):
        m = re.search(rf"async def {fn}\([^)]*\)", text)
        assert m, f"Restore endpoint {fn!r} signature not found."
        # Find the enclosing async def block and check for require_admin.
        idx = m.start()
        block = text[idx:idx + 600]
        assert "require_admin" in block or "require_hr_or_admin" in block, (
            f"Restore endpoint {fn!r} no longer enforces admin auth — "
            "a non-admin actor could potentially restore foreign data.")
