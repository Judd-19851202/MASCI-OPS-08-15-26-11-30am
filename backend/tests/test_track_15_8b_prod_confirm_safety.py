"""TRACK 15.8B — regression tests for the --prod-confirm safety guard
on the leaked PM offboarding cleanup script.

These are pure unit tests for `validate_safety()` plus a few subprocess
checks against the script's CLI surface. They MUST NOT touch any
database. The cleanup script's mutating path (`_get_db`, `scan`,
`apply_plan`) is exercised by `test_track_15_2_pm_add_member_runtime.py`
and `test_track_15_1_offboarding_pm_scoping.py`; this file is solely
about the new TRACK 15.8B production-mutation safety guard.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Import the script as a module so we can call validate_safety() directly.
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / (
    "track_15_2_backfill_leaked_pm_offboarding.py"
)
assert SCRIPT_PATH.exists(), SCRIPT_PATH

# Add scripts dir to sys.path so we can import by module name.
sys.path.insert(0, str(SCRIPT_PATH.parent))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "track_15_2_backfill_leaked_pm_offboarding", SCRIPT_PATH,
)
cleanup_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup_mod)


def _ns(**kw) -> argparse.Namespace:
    """Build a namespace with sane defaults for validate_safety()."""
    defaults = dict(apply=False, dry_run_explicit=False,
                    prod_confirm=False, max_rows=200)
    defaults.update(kw)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------- safety
class TestProdConfirmSafetyGuard:
    """validate_safety() rules per TRACK 15.8B."""

    def test_dry_run_always_safe_no_env(self):
        # Dry-run with nothing set is safe.
        err = cleanup_mod.validate_safety(_ns(), app_env=None, db_name=None)
        assert err is None

    def test_dry_run_safe_even_against_production(self):
        # Dry-run against production target is safe — it's read-only.
        err = cleanup_mod.validate_safety(
            _ns(), app_env="production", db_name="masci_safety",
        )
        assert err is None

    def test_dry_run_with_prod_confirm_is_noop(self):
        # --prod-confirm without --apply is a no-op (still safe).
        err = cleanup_mod.validate_safety(
            _ns(prod_confirm=True),
            app_env="production", db_name="masci_safety",
        )
        assert err is None

    def test_preview_apply_without_prod_confirm_allowed(self):
        # Preview-pod apply (e.g. pre-deploy gate) works without --prod-confirm.
        err = cleanup_mod.validate_safety(
            _ns(apply=True),
            app_env="preview", db_name="masci_safety_preview",
        )
        assert err is None

    def test_prod_apply_without_prod_confirm_refused_by_app_env(self):
        # APP_ENV=production alone is enough to require --prod-confirm.
        err = cleanup_mod.validate_safety(
            _ns(apply=True),
            app_env="production", db_name="masci_safety",
        )
        assert err is not None
        assert "Refusing production mutation without --prod-confirm" in err

    def test_prod_apply_without_prod_confirm_refused_by_db_name(self):
        # DB_NAME=masci_safety alone (without APP_ENV set) is also refused.
        err = cleanup_mod.validate_safety(
            _ns(apply=True),
            app_env=None, db_name="masci_safety",
        )
        assert err is not None
        assert "Refusing production mutation without --prod-confirm" in err

    def test_prod_confirm_with_wrong_app_env_refused(self):
        # --prod-confirm + APP_ENV=preview → refuse.
        err = cleanup_mod.validate_safety(
            _ns(apply=True, prod_confirm=True),
            app_env="preview", db_name="masci_safety",
        )
        assert err is not None
        assert "APP_ENV=production" in err

    def test_prod_confirm_with_wrong_db_name_refused(self):
        # --prod-confirm + DB_NAME=staging → refuse.
        err = cleanup_mod.validate_safety(
            _ns(apply=True, prod_confirm=True),
            app_env="production", db_name="masci_safety_staging",
        )
        assert err is not None
        assert "DB_NAME=masci_safety" in err

    def test_prod_confirm_with_correct_env_allowed(self):
        # Happy path: --apply + --prod-confirm + APP_ENV=production
        # + DB_NAME=masci_safety. ALL four must be present. Allowed.
        err = cleanup_mod.validate_safety(
            _ns(apply=True, prod_confirm=True),
            app_env="production", db_name="masci_safety",
        )
        assert err is None

    def test_prod_confirm_app_env_case_insensitive(self):
        # APP_ENV="PRODUCTION" should still satisfy the guard.
        err = cleanup_mod.validate_safety(
            _ns(apply=True, prod_confirm=True),
            app_env="PRODUCTION", db_name="masci_safety",
        )
        assert err is None


# ---------------------------------------------------- CLI subprocess checks
class TestCliBehavior:
    """End-to-end: invoke the script and verify exit codes."""

    def test_help_lists_prod_confirm_flag(self):
        out = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert out.returncode == 0
        assert "--prod-confirm" in out.stdout
        assert "--apply" in out.stdout
        assert "--dry-run" in out.stdout

    def test_prod_apply_without_prod_confirm_exits_2(self):
        env = os.environ.copy()
        env["APP_ENV"] = "production"
        env["DB_NAME"] = "masci_safety"
        env["MONGO_URL"] = "mongodb://localhost:27017"
        out = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--apply"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert out.returncode == 2
        assert ("Refusing production mutation without --prod-confirm"
                in out.stderr)

    def test_prod_confirm_wrong_db_exits_2(self):
        env = os.environ.copy()
        env["APP_ENV"] = "production"
        env["DB_NAME"] = "wrong_db"
        env["MONGO_URL"] = "mongodb://localhost:27017"
        out = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--apply", "--prod-confirm"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert out.returncode == 2
        assert "DB_NAME=masci_safety" in out.stderr

    def test_prod_confirm_wrong_env_exits_2(self):
        env = os.environ.copy()
        env["APP_ENV"] = "preview"
        env["DB_NAME"] = "masci_safety"
        env["MONGO_URL"] = "mongodb://localhost:27017"
        out = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--apply", "--prod-confirm"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert out.returncode == 2
        assert "APP_ENV=production" in out.stderr


# ----------------------------------------- contract guards (predicate / verbs)
class TestPredicateAndVerbContracts:
    """Track 15.2's narrow predicate and expire-not-delete contracts
    must survive Track 15.8B's safety-flag patch."""

    def test_predicate_is_four_clause_and(self):
        src = SCRIPT_PATH.read_text()
        # Must filter on linked_source_module = hr.offboarding
        assert '"linked_source_module": "hr.offboarding"' in src
        # Must filter on recipient_role = pm
        assert '"recipient_role": "pm"' in src
        # Must only touch un-targeted rows
        assert '"recipient_user_id": None' in src
        # Must require resolvable employee id
        assert '"linked_employee_id": {"$ne": None}' in src

    def test_no_hard_delete_calls(self):
        src = SCRIPT_PATH.read_text()
        # Notifications collection must NEVER be hard-deleted.
        assert "notifications.delete_one" not in src
        assert "notifications.delete_many" not in src
        # The expire verb must be the one used.
        assert '"expires_at": now' in src

    def test_audit_event_on_every_apply(self):
        src = SCRIPT_PATH.read_text()
        assert "audit_events.insert_one" in src
        assert "track_15_2.pm_offboarding_cleanup" in src

    def test_idempotency_flag_is_set(self):
        src = SCRIPT_PATH.read_text()
        assert "_track_15_2_cleaned_at" in src

    def test_max_rows_cap_default_is_200(self):
        # Sanity: the default cap from cli_args.
        ns = cleanup_mod.cli_args([])
        assert ns.max_rows == 200

    def test_apply_default_is_false(self):
        ns = cleanup_mod.cli_args([])
        assert ns.apply is False
        assert ns.prod_confirm is False
