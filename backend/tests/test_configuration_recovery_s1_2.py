from __future__ import annotations

import json

from lib.backup_paths import canonical_backup_prefix_for_env
from lib.config_recovery import build_configuration_recovery_package, build_configuration_recovery_summary


def _preview_env(**overrides: str) -> dict[str, str]:
    env = {
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "S3_ENDPOINT_URL": "https://example-r2.test",
        "S3_BUCKET": "masci-hub",
        "S3_ACCESS_KEY": "AKIA-PREVIEW-SECRET",
        "S3_SECRET_KEY": "preview-secret-key-value",
        "ADMIN_HMAC_SECRET": "preview-admin-hmac-secret",
    }
    env.update(overrides)
    return env


def test_configuration_recovery_redacts_secret_values() -> None:
    env = _preview_env()
    package = build_configuration_recovery_package(env=env, domain_host_context="preview.example.test")
    text = json.dumps(package, sort_keys=True)

    assert "mongodb+srv://" not in text
    assert "preview-secret-key-value" not in text
    assert "preview-admin-hmac-secret" not in text
    assert package["validator"]["overall_status"] == "PASS"


def test_configuration_recovery_records_safe_defaults() -> None:
    env = _preview_env()
    package = build_configuration_recovery_package(env=env, domain_host_context="preview.example.test")
    rows = {row["key"]: row for row in package["configuration_inventory"]}

    assert rows["BACKUP_PREFIX"]["default_applied"] is True
    assert rows["BACKUP_PREFIX"]["effective_value"] == canonical_backup_prefix_for_env("preview")
    assert rows["BACKUP_VERIFICATION_MAX_AGE_HOURS"]["default_applied"] is True
    assert rows["BACKUP_VERIFICATION_MAX_AGE_HOURS"]["effective_value"] == 36


def test_configuration_recovery_fails_closed_on_preview_production_blend() -> None:
    env = _preview_env(
        DB_NAME="masci_safety",
        MONGO_URL="mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety",  # secret-scan: allow-line
    )
    package = build_configuration_recovery_package(env=env, domain_host_context="preview.example.test")

    assert package["validator"]["overall_status"] == "FAIL"
    assert package["environment_separation"]["status"] == "FAIL"
    assert package["environment_separation"]["fail_closed"] is True
    assert any(
        issue in package["validator"]["blocking_issues"]
        for issue in [
            "preview_using_production_db_name",
            "preview_using_production_user",
        ]
    )


def test_configuration_recovery_summary_reports_pass() -> None:
    package = build_configuration_recovery_package(env=_preview_env(), domain_host_context="preview.example.test")
    summary = build_configuration_recovery_summary(package)

    assert summary["status"] == "PASS"
    assert summary["all_secret_refs_present"] is True
    assert summary["environment"] == "preview"