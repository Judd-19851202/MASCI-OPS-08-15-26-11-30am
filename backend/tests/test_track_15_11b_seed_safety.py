"""TRACK 15.11B seed-script regression tests (no DB writes)."""
import argparse, importlib.util, sys
from pathlib import Path
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seed_track_15_11b_pm_cert.py"
spec = importlib.util.spec_from_file_location("seed_15_11b", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


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
