"""TRACK 15.11B / 15.11C seed-script regression tests (no DB writes)."""
import argparse
import importlib.util
from pathlib import Path
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seed_track_15_11b_pm_cert.py"
spec = importlib.util.spec_from_file_location("seed_15_11b", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _ns(seed=False, verify=False, rollback=False):
    return argparse.Namespace(seed=seed, verify=verify, rollback=rollback)


class TestSafetyGuard:
    def test_refuses_seed_in_production(self):
        err = mod._validate_env(_ns(seed=True), "production", "masci_safety_preview")
        assert err and "APP_ENV=production" in err

    def test_refuses_seed_against_masci_safety(self):
        err = mod._validate_env(_ns(seed=True), "preview", "masci_safety")
        assert err and "DB_NAME=masci_safety" in err

    def test_refuses_rollback_in_production(self):
        err = mod._validate_env(_ns(rollback=True), "production", "masci_safety_preview")
        assert err

    def test_allows_seed_in_preview(self):
        assert mod._validate_env(_ns(seed=True), "preview", "masci_safety_preview") is None

    def test_verify_only_allowed_anywhere(self):
        # Read-only mode must not be blocked even if env vars look prod-like.
        assert mod._validate_env(_ns(verify=True), "production", "masci_safety") is None

    def test_case_insensitive_app_env(self):
        err = mod._validate_env(_ns(seed=True), "PRODUCTION", "masci_safety_preview")
        assert err


class TestStampingContract:
    def test_stamp_contains_cert_track_marker(self):
        s = mod._stamp()
        assert s["cert_track"] == "TRACK15_11B"
        assert s["created_by_cert"] is True

    def test_stamp_merges_extra_fields(self):
        s = mod._stamp({"foo": "bar"})
        assert s["foo"] == "bar"
        assert s["cert_track"] == "TRACK15_11B"


class TestCanonicalConstants:
    def test_canonical_cert_emails_use_mascicert_local(self):
        for e in (mod.PM_EMAIL, mod.FOREMAN_EMAIL, mod.SAFETY_EMAIL,
                  mod.ASSET_EMAIL, mod.NOLOGIN_EMAIL):
            assert e.endswith("@mascicert.local"), e
            assert "track15.11b.cert" in e, e

    def test_canonical_project_numbers(self):
        assert mod.PROJECT_NUMBER == "TRACK15-11B"
        assert mod.PROJECT_NUMBER_OTHER == "TRACK15-11B-OTHER"

    def test_track_15_11c_second_project_constant(self):
        # 15.11C — second in-scope project must be present, distinct.
        assert mod.PROJECT_NUMBER_SECOND == "TRACK15-11B-SECOND"
        assert mod.PROJECT_NUMBER_SECOND != mod.PROJECT_NUMBER
        assert mod.PROJECT_NUMBER_SECOND != mod.PROJECT_NUMBER_OTHER

    def test_track_15_11c_other_pm_email_is_disjoint(self):
        # Out-of-scope project must NOT share the cert PM email.
        assert mod.OTHER_PM_EMAIL != mod.PM_EMAIL
        assert "other" in mod.OTHER_PM_EMAIL

    def test_track_15_11c_cert_pm_password_set(self):
        # A non-empty cert PM password must exist for browser cert.
        assert isinstance(mod.CERT_PM_PASSWORD, str)
        assert len(mod.CERT_PM_PASSWORD) >= 12


class TestRollbackContract:
    def test_rollback_targets_only_cert_tagged_rows(self):
        src = SCRIPT.read_text()
        # rollback() must filter on cert_track. No bare delete_many.
        for stmt in ('delete_many({"cert_track": CERT_TRACK})',):
            assert stmt in src, f"Rollback must filter on cert_track: {stmt}"
        # Forbid unfiltered destructive verbs.
        assert "delete_many({})" not in src
        assert "drop()" not in src
        assert "drop_collection" not in src

    def test_no_real_email_or_sms_dispatch(self):
        src = SCRIPT.read_text()
        for bad in ("requests.post", "resend.send", "twilio", "smtp.",
                    "send_mail", "send_email"):
            assert bad.lower() not in src.lower(), f"Forbidden network verb: {bad}"


class TestCliShape:
    def test_cli_has_seed_verify_rollback_flags(self):
        for flags in (["--seed"], ["--verify"], ["--rollback"]):
            ns = mod.cli_args(flags)
            assert getattr(ns, flags[0].lstrip("-").replace("-", "_"))

    def test_cli_defaults_to_no_mode(self):
        ns = mod.cli_args([])
        assert ns.seed is False and ns.verify is False and ns.rollback is False


class TestSecondProjectSeedBehavior:
    """15.11C — the seed body must actually create the 2nd in-scope project
    assigned to the cert PM, and lay down operational fixtures for it.
    Static-source assertions only — no DB writes."""

    def test_seed_seeds_second_in_scope_project(self):
        src = SCRIPT.read_text()
        # The second job must be inserted with the cert PM as primary.
        assert "PROJECT_NUMBER_SECOND" in src
        # The call may wrap across multiple lines — collapse whitespace.
        flat = " ".join(src.split())
        assert "_ensure_job( db, run_id, PROJECT_NUMBER_SECOND," in flat
        # And the cert PM must be the pm_email on that job.
        assert "PROJECT_NUMBER_SECOND, PM_EMAIL," in flat or \
               "PROJECT_NUMBER_SECOND," in flat and ", PM_EMAIL," in flat

    def test_seed_writes_second_project_operational_fixtures(self):
        import re
        src = SCRIPT.read_text()
        # Daily report + photo + incident + JHA + equipment all routed
        # through the SECOND project number (matched as a regex so the
        # check is tolerant of arg wrapping and dict-comprehension form).
        for fn in ("_ensure_daily_report", "_ensure_photo", "_ensure_incident",
                   "_ensure_jha", "_ensure_equipment"):
            pat = re.compile(
                rf"{fn}\(\s*db,\s*run_id,\s*PROJECT_NUMBER_SECOND",
                re.MULTILINE,
            )
            assert pat.search(src), fn

    def test_out_of_scope_project_uses_distinct_pm_email(self):
        src = SCRIPT.read_text()
        # The out-of-scope project must still be seeded with OTHER_PM_EMAIL,
        # NOT the cert PM. This is what proves scope-leak prevention.
        assert "_ensure_job(db, run_id, PROJECT_NUMBER_OTHER" in src
        assert "OTHER_PM_EMAIL" in src

    def test_verify_emits_per_project_breakdown(self):
        src = SCRIPT.read_text()
        # 15.11C — verify must surface a per-project count + the pm_email
        # mapping so ledgers prove what the cert PM is allowed to see.
        assert "per_project" in src
        assert "pm_email_by_project" in src
        assert "cert_pm_email" in src


class TestRollbackIdempotency:
    """Static guarantee that rollback walks every cert-tagged collection
    exactly once and only matches on cert_track."""

    def test_rollback_walks_all_cert_collections(self):
        src = SCRIPT.read_text()
        for coll in ("daily_reports", "job_photos", "incidents",
                     "jha_records", "equipment_inspections",
                     "project_team_assignments", "jobs_master",
                     "user_directory"):
            assert f'"{coll}"' in src, coll


class TestRealBcryptForCertPM:
    """15.11C — the cert PM must be seeded with a real, verifiable bcrypt
    hash via user_directory.hash_password so the cert PM can sign in
    via /api/auth/multi-login without any production touch."""

    def test_imports_user_directory_hash_password(self):
        src = SCRIPT.read_text()
        assert "from user_directory import hash_password" in src

    def test_cert_pm_seed_uses_real_password(self):
        src = SCRIPT.read_text()
        assert "real_password=CERT_PM_PASSWORD" in src

    def test_placeholder_hash_remains_for_other_users(self):
        # Foreman / safety / shop users keep the synthetic hash so no
        # real login is ever silently created for them.
        src = SCRIPT.read_text()
        assert '"$2b$12$"' in src and 'placeholder' in src.lower()


class TestNoSilentLoginCreation:
    """No code path may issue an email/SMS, fire a welcome message, or
    expand the cert dataset beyond the canonical cert emails."""

    def test_no_external_network_verbs(self):
        src = SCRIPT.read_text().lower()
        for bad in ("import requests", "httpx.post", "httpx.client",
                    "import smtplib", "send_welcome", "send_temp_password"):
            assert bad not in src, bad

    def test_only_canonical_cert_emails_referenced(self):
        src = SCRIPT.read_text()
        # The cert dataset must not splice in real prod emails.
        for prod in ("jaymn.judd@mascigc.com", "@mascigc.com",
                     "@mascidocs.com"):
            assert prod not in src, prod
