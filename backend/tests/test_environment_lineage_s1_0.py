from __future__ import annotations

from lib.runtime_identity import build_runtime_identity_bundle


def _bundle(env: dict[str, str], *, release_identity: dict[str, str] | None = None):
    return build_runtime_identity_bundle(
        env=env,
        release_identity=release_identity or {"commit": "abc123", "source_hash": "release-a"},
        domain_host_context="preview.example.test",
    )


def test_environment_fingerprint_stable_across_release_changes() -> None:
    env = {
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "S3_BUCKET": "masci-hub",
        "BACKUP_PREFIX": "backups/auto-90d/preview/",
    }
    a = _bundle(env, release_identity={"commit": "c1", "source_hash": "r1"})
    b = _bundle(env, release_identity={"commit": "c2", "source_hash": "r2"})
    assert a["identity"].environment_fingerprint == b["identity"].environment_fingerprint
    assert a["identity"].identity_fingerprint != b["identity"].identity_fingerprint


def test_environment_fingerprint_normalizes_case_and_whitespace() -> None:
    a = _bundle({
        "APP_ENV": "preview ",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "S3_BUCKET": "masci-hub",
        "BACKUP_PREFIX": " backups/auto-90d/preview/ ",
    })
    b = _bundle({
        "APP_ENV": "PREVIEW",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "S3_BUCKET": "MASCI-HUB",
        "BACKUP_PREFIX": "backups/auto-90d/preview/",
    })
    assert a["identity"].environment_fingerprint == b["identity"].environment_fingerprint


def test_preview_and_production_environment_fingerprints_differ() -> None:
    preview = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "S3_BUCKET": "masci-hub",
        "BACKUP_PREFIX": "backups/auto-90d/preview/",
    })
    production = _bundle({
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "S3_BUCKET": "masci-hub",
        "BACKUP_PREFIX": "backups/auto-90d/production/",
    })
    assert preview["identity"].environment_fingerprint != production["identity"].environment_fingerprint


def test_environment_fingerprint_contains_no_release_hash_material() -> None:
    bundle = _bundle({
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "S3_BUCKET": "masci-hub",
        "BACKUP_PREFIX": "backups/auto-90d/preview/",
    })
    fp = bundle["identity"].environment_fingerprint
    assert "release" not in fp
    assert "r1" not in fp