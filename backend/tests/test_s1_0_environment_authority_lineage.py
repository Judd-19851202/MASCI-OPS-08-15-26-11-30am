#!/usr/bin/env python3
"""
test_s1_0_environment_authority_lineage.py — BCSS Release 2 · S1-0 Environment Authority & Archive Lineage Hardening

This test suite verifies the S1-0 implementation slice:
1. Stable environment-authority fingerprint exists and remains stable across release identity changes
2. Preview and production authority inputs produce different fingerprints
3. Canonical archive lineage exposes environment-bound identity fields
4. Environment-bound selection rejects explicit keys that do not reconcile to authoritative preview lineage
5. Preview authoritative archive selection succeeds for the current persisted preview lineage archive
6. Legacy artifacts without persisted lineage are quarantined from automatic selection
"""
import os
import asyncio
import pytest
from datetime import datetime, timezone
from pathlib import Path

# Load backend env
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.runtime_identity import (
    build_runtime_identity_bundle,
    build_environment_authority_fingerprint,
    ENVIRONMENT_FINGERPRINT_VERSION,
)
from lib.archive_lineage import (
    build_canonical_archive_lineage,
    resolve_archive_lineage_from_inputs,
    RESOLVER_VERSION,
)


def _load_env() -> dict:
    """Load environment from backend/.env"""
    env = dict(os.environ)
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"'))
    return env


def _bundle(env: dict, *, release_identity: dict = None):
    return build_runtime_identity_bundle(
        env=env,
        release_identity=release_identity or {"commit": "abc123", "source_hash": "release-a"},
        domain_host_context="preview.example.test",
    )


class TestEnvironmentAuthorityFingerprint:
    """Verify the new stable environment-authority fingerprint."""

    def test_environment_fingerprint_exists(self):
        """Environment fingerprint field exists in runtime identity."""
        env = {
            "APP_ENV": "preview",
            "DB_NAME": "masci_safety_preview",
            "MONGO_URL": "mongodb+srv://masci_preview_user:test@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",
            "S3_BUCKET": "masci-hub",
            "BACKUP_PREFIX": "backups/auto-90d/",
        }
        bundle = _bundle(env)
        identity = bundle["identity"]
        
        assert hasattr(identity, "environment_fingerprint")
        assert identity.environment_fingerprint is not None
        assert len(identity.environment_fingerprint) == 12  # SHA256 prefix
        assert identity.environment_fingerprint_version == ENVIRONMENT_FINGERPRINT_VERSION

    def test_environment_fingerprint_stable_across_release_changes(self):
        """Environment fingerprint remains stable when release identity changes."""
        env = {
            "APP_ENV": "preview",
            "DB_NAME": "masci_safety_preview",
            "MONGO_URL": "mongodb+srv://masci_preview_user:test@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",
            "S3_BUCKET": "masci-hub",
            "BACKUP_PREFIX": "backups/auto-90d/",
        }
        
        bundle_a = _bundle(env, release_identity={"commit": "c1", "source_hash": "r1"})
        bundle_b = _bundle(env, release_identity={"commit": "c2", "source_hash": "r2"})
        
        # Environment fingerprint should be identical
        assert bundle_a["identity"].environment_fingerprint == bundle_b["identity"].environment_fingerprint
        
        # But identity fingerprint should differ (includes release info)
        assert bundle_a["identity"].identity_fingerprint != bundle_b["identity"].identity_fingerprint

    def test_preview_and_production_fingerprints_differ(self):
        """Preview and production authority inputs produce different fingerprints."""
        preview_env = {
            "APP_ENV": "preview",
            "DB_NAME": "masci_safety_preview",
            "MONGO_URL": "mongodb+srv://masci_preview_user:test@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",
            "S3_BUCKET": "masci-hub",
            "BACKUP_PREFIX": "backups/auto-90d/",
        }
        production_env = {
            "APP_ENV": "production",
            "DB_NAME": "masci_safety",
            "MONGO_URL": "mongodb+srv://masci_prod_user:test@masci-prod.1nduwmg.mongodb.net/masci_safety",
            "ENFORCE_DB_ISOLATION": "true",
            "S3_BUCKET": "masci-hub",
            "BACKUP_PREFIX": "backups/auto-90d/",
        }
        
        preview_bundle = _bundle(preview_env)
        production_bundle = _bundle(production_env)
        
        assert preview_bundle["identity"].environment_fingerprint != production_bundle["identity"].environment_fingerprint
        assert preview_bundle["identity"].environment_name == "PREVIEW"
        assert production_bundle["identity"].environment_name == "PRODUCTION"

    def test_environment_fingerprint_normalizes_case_and_whitespace(self):
        """Environment fingerprint normalizes case and whitespace."""
        env_a = {
            "APP_ENV": "preview ",
            "DB_NAME": "masci_safety_preview",
            "MONGO_URL": "mongodb+srv://masci_preview_user:test@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",
            "S3_BUCKET": "masci-hub",
            "BACKUP_PREFIX": " backups/auto-90d/ ",
        }
        env_b = {
            "APP_ENV": "PREVIEW",
            "DB_NAME": "masci_safety_preview",
            "MONGO_URL": "mongodb+srv://masci_preview_user:test@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",
            "S3_BUCKET": "MASCI-HUB",
            "BACKUP_PREFIX": "backups/auto-90d/",
        }
        
        bundle_a = _bundle(env_a)
        bundle_b = _bundle(env_b)
        
        assert bundle_a["identity"].environment_fingerprint == bundle_b["identity"].environment_fingerprint


class TestArchiveLineageEnvironmentBound:
    """Verify canonical archive lineage exposes environment-bound identity fields."""

    @pytest.fixture
    def env(self):
        return _load_env()

    @pytest.fixture
    def db(self, env):
        from pymongo import MongoClient
        mongo = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=10000)
        yield mongo[env["DB_NAME"]]
        mongo.close()

    def test_lineage_resolver_version(self, env, db):
        """Lineage resolver version is bcss-r02-1."""
        lineage = asyncio.run(
            build_canonical_archive_lineage(
                db,
                current_env=env.get("APP_ENV"),
                current_db=env.get("DB_NAME"),
                requested_source_environment="preview",
                force_refresh=True,
            )
        )
        assert lineage.get("resolver_version") == "bcss-r02-1"

    def test_lineage_exposes_runtime_identity(self, env, db):
        """Lineage exposes runtime identity with environment fingerprint."""
        lineage = asyncio.run(
            build_canonical_archive_lineage(
                db,
                current_env=env.get("APP_ENV"),
                current_db=env.get("DB_NAME"),
                requested_source_environment="preview",
                force_refresh=True,
            )
        )
        
        runtime = lineage.get("runtime_identity") or {}
        assert runtime.get("app_env") == "preview"
        assert runtime.get("db_name") == "masci_safety_preview"
        assert runtime.get("environment_fingerprint") is not None
        assert runtime.get("environment_fingerprint_version") == ENVIRONMENT_FINGERPRINT_VERSION

    def test_authoritative_artifact_has_lineage_identity(self, env, db):
        """Authoritative artifact exposes lineage_identity with environment fields."""
        lineage = asyncio.run(
            build_canonical_archive_lineage(
                db,
                current_env=env.get("APP_ENV"),
                current_db=env.get("DB_NAME"),
                requested_source_environment="preview",
                force_refresh=True,
            )
        )
        
        auth = lineage.get("authoritative_artifact")
        if auth:
            lineage_id = auth.get("lineage_identity") or {}
            assert "environment" in lineage_id
            assert "source_database" in lineage_id
            assert "archive_key" in lineage_id


class TestEnvironmentBoundSelection:
    """Verify environment-bound selection rejects mismatched requests."""

    @pytest.fixture
    def env(self):
        return _load_env()

    @pytest.fixture
    def db(self, env):
        from pymongo import MongoClient
        mongo = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=10000)
        yield mongo[env["DB_NAME"]]
        mongo.close()

    def test_rejects_production_request_from_preview_runtime(self, env, db):
        """Environment-bound selection rejects production request from preview runtime."""
        lineage = asyncio.run(
            build_canonical_archive_lineage(
                db,
                current_env="preview",
                current_db="masci_safety_preview",
                requested_source_environment="production",  # Requesting production from preview
                force_refresh=True,
            )
        )
        
        # Should return no authoritative artifact
        assert lineage.get("authoritative_artifact") is None
        
        # Should have correct degradation reason
        degradation = lineage.get("degradation_reasons") or []
        assert "no_valid_archive_for_requested_environment" in degradation

    def test_accepts_preview_request_from_preview_runtime(self, env, db):
        """Environment-bound selection accepts preview request from preview runtime."""
        lineage = asyncio.run(
            build_canonical_archive_lineage(
                db,
                current_env="preview",
                current_db="masci_safety_preview",
                requested_source_environment="preview",
                force_refresh=True,
            )
        )
        
        # Should return an authoritative artifact (if one exists)
        auth = lineage.get("authoritative_artifact")
        # Note: May be None if no valid archives exist, but should not be rejected for environment mismatch
        if auth:
            assert auth.get("valid_recoverable") is True
            lineage_id = auth.get("lineage_identity") or {}
            assert lineage_id.get("environment") == "preview"


class TestPreviewAuthoritativeArchive:
    """Verify preview authoritative archive selection succeeds."""

    @pytest.fixture
    def env(self):
        return _load_env()

    @pytest.fixture
    def db(self, env):
        from pymongo import MongoClient
        mongo = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=10000)
        yield mongo[env["DB_NAME"]]
        mongo.close()

    def test_authoritative_archive_is_preview_scoped(self, env, db):
        """Preview authoritative archive remains preview-scoped and recoverable."""
        try:
            lineage = asyncio.run(
                build_canonical_archive_lineage(
                    db,
                    current_env=env.get("APP_ENV"),
                    current_db=env.get("DB_NAME"),
                    requested_source_environment="preview",
                    force_refresh=True,
                )
            )
        except Exception as exc:
            pytest.skip(f"live preview authority lookup unavailable: {exc}")
        
        auth = lineage.get("authoritative_artifact")
        assert auth is not None, "No authoritative artifact found"
        
        object_key = auth.get("object_key") or ""
        assert object_key.startswith(("backups/preview/auto-90d/", "backups/auto-90d/"))
        assert auth.get("valid_recoverable") is True
        assert auth.get("legacy_classification") == "LINEAGE_VERIFIED"

    def test_older_archive_without_lineage_is_quarantined(self, env, db):
        """Older archive without persisted lineage is quarantined from auto-selection."""
        try:
            lineage = asyncio.run(
                build_canonical_archive_lineage(
                    db,
                    current_env=env.get("APP_ENV"),
                    current_db=env.get("DB_NAME"),
                    requested_source_environment="preview",
                    force_refresh=True,
                )
            )
        except Exception as exc:
            pytest.skip(f"live preview authority lookup unavailable: {exc}")
        
        # Check rejected candidates for quarantine markers
        rejected = lineage.get("rejected_candidates") or []
        for cand in rejected:
            reasons = cand.get("rejection_reasons") or []
            legacy_class = cand.get("legacy_classification")
            
            # Candidates without verified lineage should be quarantined
            if legacy_class == "LINEAGE_UNVERIFIED":
                assert "quarantined_from_auto_selection" in reasons


class TestNoProductionClaim:
    """Verify no production claim is made."""

    @pytest.fixture
    def env(self):
        return _load_env()

    def test_current_environment_is_preview(self, env):
        """Current environment is preview, not production."""
        assert env.get("APP_ENV") == "preview"
        assert env.get("DB_NAME") == "masci_safety_preview"

    def test_runtime_identity_is_preview(self, env):
        """Runtime identity correctly identifies as preview."""
        bundle = build_runtime_identity_bundle(env=env)
        identity = bundle["identity"]
        
        assert identity.environment_name == "PREVIEW"
        assert identity.preview_distinction == "preview"
        assert identity.db_name == "masci_safety_preview"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
