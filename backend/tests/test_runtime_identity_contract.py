from __future__ import annotations

from lib.runtime_identity import (
    STATUS_DEGRADED,
    STATUS_MISMATCH,
    STATUS_NOT_APPLICABLE,
    STATUS_VERIFIED,
    assert_runtime_identity_valid,
    build_runtime_identity_bundle,
    is_read_only_validation_active_bundle,
    parse_mongo_url,
    runtime_identity_public_payload,
)


def _bundle(env: dict[str, str]):
    return build_runtime_identity_bundle(
        env=env,
        release_identity={"commit": "abc123", "source_hash": "deadbeef"},
        domain_host_context="preview.example.test",
    )


def test_production_identity_passes_with_approved_target() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety?retryWrites=true&w=majority",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
    })
    assert bundle["validation"].valid is True
    assert bundle["validation"].status == STATUS_VERIFIED
    assert_runtime_identity_valid(bundle)


def test_wrong_cluster_correct_db_hard_fails() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@wrong-cluster.mongodb.net/masci_safety?retryWrites=true&w=majority",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].status == STATUS_MISMATCH
    assert bundle["validation"].mismatch_category == "CLUSTER_HOST_MISMATCH"


def test_preview_cluster_refused_in_production() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-preview.mongodb.net/masci_safety",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
    })
    assert bundle["validation"].valid is False


def test_local_mongo_refused_in_production() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety",
        "ENFORCE_DB_ISOLATION": "true",
    })
    assert "local_mongo_refused" in bundle["validation"].errors


def test_production_db_refused_in_preview() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety",
        "ENFORCE_DB_ISOLATION": "false",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "PREVIEW_PRODUCTION_DB_REFUSED"


def test_preview_prod_hostname_with_preview_user_and_preview_db_passes() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
    })
    assert bundle["validation"].valid is True


def test_preview_prod_hostname_with_production_user_still_hard_fails() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "PREVIEW_PRODUCTION_USER_REFUSED"


def test_preview_local_preview_database_passes() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety_preview",
        "ENFORCE_DB_ISOLATION": "false",
    })
    assert bundle["validation"].valid is True


def test_ro_validation_requested_but_incomplete_hard_fails() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "READ_ONLY_VALIDATION": "true",
        "READ_ONLY_MODE": "true",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "READ_ONLY_VALIDATION_INCOMPLETE"
    assert "zero_write_proof_missing" in bundle["validation"].errors


def test_ro_validation_fully_valid_allows_boot_in_read_only_mode() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "READ_ONLY_VALIDATION": "true",
        "READ_ONLY_MODE": "true",
        "READ_ONLY_VALIDATION_DB_AUTHORITY": "read_only",
        "SESSION_TIMEOUTS_ENABLED": "false",
        "SCHEDULER_ENABLED": "false",
        "AUTO_EMAIL_REPORTS": "false",
        "MAINTAINX_WRITE_ENABLED": "false",
        "MAINTAINX_SYNC_ENABLED": "false",
        "AI_GATEWAY_ENABLED": "false",
        "DR_V2_AI_ENABLED": "false",
        "ODS_ENABLED": "false",
        "READ_ONLY_VALIDATION_TRUST_SPINE_DISABLED": "true",
        "READ_ONLY_VALIDATION_WEBHOOKS_DISABLED": "true",
        "READ_ONLY_VALIDATION_ZERO_WRITE_PROVEN": "true",
        "APP_DOMAIN": "preview-readonly.example.test",
    })
    assert bundle["validation"].valid is True
    assert is_read_only_validation_active_bundle(bundle) is True
    assert bundle["identity"].read_only_validation["http_mutation_barrier_active"] is True
    assert bundle["identity"].read_only_validation["startup_write_suppressed"] is True


def test_unknown_hostname_hard_fails() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb:///masci_safety",
        "ENFORCE_DB_ISOLATION": "true",
    })
    assert bundle["validation"].valid is False


def test_credentials_redacted_in_public_payload() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://user%40domain.com:p%40ss%2Fword@masci-prod.1nduwmg.mongodb.net/masci_safety",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
    })
    payload = runtime_identity_public_payload(bundle)
    text = str(payload)
    assert "mongodb+srv://" not in text
    assert "p%40ss" not in text
    assert "word" not in text


def test_ipv6_options_and_query_parameters_parse() -> None:
    parsed = parse_mongo_url("mongodb://user:pass@[::1]:27017/masci_safety_preview?retryWrites=true&authSource=admin")  # secret-scan: allow-line
    assert parsed.scheme == "mongodb"
    assert parsed.hostname == "::1"
    assert parsed.path_database == "masci_safety_preview"


def test_url_encoded_credentials_do_not_break_parsing() -> None:
    parsed = parse_mongo_url("mongodb+srv://masci_prod_user%40tenant:p%40ss%2Fword@masci-prod.1nduwmg.mongodb.net/masci_safety")  # secret-scan: allow-line
    assert parsed.username == "masci_prod_user@tenant"
    assert parsed.hostname == "masci-prod.1nduwmg.mongodb.net"


def test_duplicate_query_values_are_surfaced() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety?retryWrites=true&retryWrites=false",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "DUPLICATE_CONFIG_VALUES"


def test_normal_preview_remains_bootable() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety_preview",
        "ENFORCE_DB_ISOLATION": "false",
    })
    assert bundle["validation"].valid is True
    assert bundle["validation"].status in {STATUS_NOT_APPLICABLE, STATUS_DEGRADED}


def test_production_refuses_preview_surface_flags() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "DEV_ENDPOINTS_ENABLED": "true",
        "ENABLE_PREVIEW_VALIDATION_IDENTITIES": "true",
        "PREVIEW_ONLY_BACKFILL_ENABLED": "true",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "PREVIEW_SURFACE_ENABLED_IN_PRODUCTION"
    assert "dev_endpoints_enabled_in_production" in bundle["validation"].errors
    assert "preview_validation_identities_enabled_in_production" in bundle["validation"].errors
    assert "preview_only_backfill_enabled_in_production" in bundle["validation"].errors


def test_production_refuses_preview_storage_namespace_and_endpoint() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "S3_BUCKET": "masci-preview-hub",
        "BACKUP_PREFIX": "backups/preview/auto-90d/",
        "S3_ENDPOINT_URL": "https://preview-r2.example.test",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "BACKUP_PREFIX_MISMATCH"
    assert "backup_prefix_unapproved_for_environment" in bundle["validation"].errors
    assert "preview_storage_namespace_refused" in bundle["validation"].errors


def test_production_refuses_preview_integration_endpoint_and_binding_markers() -> None:
    bundle = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "MAINTAINX_BASE_URL": "https://preview-maintainx.example.test/v1",
        "MAINTAINX_BINDING_ENV": "preview",
        "RESEND_BINDING_ENV": "preview",
        "ADMIN_CREDENTIAL_BINDING_ENV": "preview",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "INTEGRATION_ENDPOINT_ENV_MISMATCH"
    assert "preview_integration_endpoint_refused" in bundle["validation"].errors
    assert "maintainx_binding_env_unapproved" in bundle["validation"].errors
    assert "resend_binding_env_unapproved" in bundle["validation"].errors
    assert "admin_credentials_binding_env_unapproved" in bundle["validation"].errors


def test_preview_refuses_production_storage_and_admin_credentials() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety_preview",
        "ENFORCE_DB_ISOLATION": "false",
        "STORAGE_BINDING_ENV": "production",
        "STORAGE_CREDENTIAL_BINDING_ENV": "production",
        "ADMIN_CREDENTIAL_BINDING_ENV": "production",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "PREVIEW_PRODUCTION_STORAGE_REFUSED"
    assert "preview_using_production_storage_binding" in bundle["validation"].errors
    assert "preview_using_production_storage_credentials" in bundle["validation"].errors
    assert "preview_using_production_admin_credentials" in bundle["validation"].errors


def test_preview_refuses_production_integration_credentials() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety_preview",
        "ENFORCE_DB_ISOLATION": "false",
        "MAINTAINX_BINDING_ENV": "production",
        "RESEND_BINDING_ENV": "production",
    })
    assert bundle["validation"].valid is False
    assert bundle["validation"].mismatch_category == "PREVIEW_PRODUCTION_INTEGRATION_REFUSED"
    assert "preview_using_production_integration_binding" in bundle["validation"].errors
    assert "preview_using_production_integration_credentials" in bundle["validation"].errors


def test_environment_separation_contract_is_fail_closed_and_public() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety_preview",
        "ENFORCE_DB_ISOLATION": "false",
        "STORAGE_BINDING_ENV": "preview",
        "MAINTAINX_BINDING_ENV": "shared",
        "ADMIN_CREDENTIAL_BINDING_ENV": "preview",
    })
    identity = bundle["identity"]
    payload = runtime_identity_public_payload(bundle)
    separation = identity.environment_separation
    assert separation["fail_closed"] is True
    assert separation["storage_binding_env"] == "preview"
    assert separation["maintainx_binding_env"] == "shared"
    assert payload["identity"]["environment_separation"]["fail_closed"] is True