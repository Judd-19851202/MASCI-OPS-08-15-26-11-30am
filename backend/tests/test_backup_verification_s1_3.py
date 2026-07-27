from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lib.archive_lineage import resolve_archive_lineage_from_inputs


def _runtime_identity() -> dict:
    return {
        "app_env": "preview",
        "db_name": "masci_safety_preview",
        "environment_name": "PREVIEW",
        "cluster_fingerprint": "cluster-preview-001",
        "runtime_user_identity": "masci_preview_user",
        "backup_bucket": "masci-hub",
        "backup_prefix": "backups/preview/auto-90d/",
        "environment_fingerprint": "env-preview-001",
        "environment_fingerprint_version": "env-authority-v1",
    }


def _direct_manifest(archive_key: str, backup_id: str) -> dict:
    filename = archive_key.rsplit("/", 1)[-1]
    return {
        "manifest_name": f"{filename}.manifest.json",
        "manifest_key": f"backups/preview/auto-90d/manifests/{filename}.manifest.json",
        "checksum_key": f"backups/preview/auto-90d/checksums/{filename}.sha256",
        "checksum_sidecar": f"abc123  {filename}\n",
        "read_mode": "SIDECAR",
        "manifest": {
            "manifest_version": "27.11c-1",
            "backup_id": backup_id,
            "backup_type": "complete-r2",
            "classification": "COMPLETE",
            "coverage_complete": True,
            "integrity_result": "PASS",
            "environment": "preview",
            "app_env": "preview",
            "environment_fingerprint": "env-preview-001",
            "environment_fingerprint_version": "env-authority-v1",
            "database_name": "masci_safety_preview",
            "db_name": "masci_safety_preview",
            "source_database_identity": "masci_safety_preview",
            "source_cluster_fingerprint": "cluster-preview-001",
            "source_runtime_user_identity": "masci_preview_user",
            "backup_bucket": "masci-hub",
            "backup_prefix": "backups/preview/auto-90d/",
            "archive_key": archive_key,
            "backup_started_at": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(),
            "backup_completed_at": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
            "generated_at": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        },
    }


def test_direct_sidecar_evidence_grants_high_confidence() -> None:
    archive_key = "backups/preview/auto-90d/MASCI_complete_backup_2026-07-27_105000Z.zip"
    backup_id = "backup-direct-001"
    archive = {
        "filename": archive_key.rsplit("/", 1)[-1],
        "key": archive_key,
        "last_modified_iso": datetime.now(timezone.utc).isoformat(),
        "size_bytes": 1024,
        "etag": "etag-ignored",
    }
    row = {
        "filename": archive["filename"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": True,
        "mode": "complete-r2",
        "records": 100,
        "size_bytes": 1024,
        "archive_lineage": {
            "backup_id": backup_id,
            "archive_key": archive_key,
            "checksum_sha256": "abc123",
            "environment": "preview",
            "environment_fingerprint": "env-preview-001",
            "environment_fingerprint_version": "env-authority-v1",
            "source_cluster_fingerprint": "cluster-preview-001",
            "database_name": "masci_safety_preview",
            "source_database_identity": "masci_safety_preview",
            "backup_bucket": "masci-hub",
            "backup_prefix": "backups/preview/auto-90d/",
            "manifest_key": f"backups/preview/auto-90d/manifests/{archive['filename']}.manifest.json",
            "checksum_key": f"backups/preview/auto-90d/checksums/{archive['filename']}.sha256",
            "created_at": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(),
            "uploaded_at": (datetime.now(timezone.utc) - timedelta(minutes=9)).isoformat(),
        },
    }

    result = resolve_archive_lineage_from_inputs(
        runtime_identity=_runtime_identity(),
        archive_rows=[archive],
        recent_rows=[row],
        manifest_bundles={archive["filename"]: _direct_manifest(archive_key, backup_id)},
    )
    authoritative = result["authoritative_artifact"]

    assert authoritative is not None
    assert authoritative["direct_evidence_status"] == "VERIFIED"
    assert authoritative["integrity_status"] == "PASS"
    assert authoritative["completeness_status"] == "COMPLETE"
    assert authoritative["authoritative_time_source"] == "COMPLETED_ARCHIVE_TIME"
    assert authoritative["lineage_confidence"] == "HIGH"
    assert result["lineage_confidence"] == "HIGH"


def test_direct_sidecar_checksum_mismatch_fails_closed() -> None:
    archive_key = "backups/preview/auto-90d/MASCI_complete_backup_2026-07-27_105500Z.zip"
    backup_id = "backup-direct-002"
    archive = {
        "filename": archive_key.rsplit("/", 1)[-1],
        "key": archive_key,
        "last_modified_iso": datetime.now(timezone.utc).isoformat(),
        "size_bytes": 2048,
        "etag": "etag-ignored",
    }
    row = {
        "filename": archive["filename"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": True,
        "mode": "complete-r2",
        "records": 100,
        "size_bytes": 2048,
        "archive_lineage": {
            "backup_id": backup_id,
            "archive_key": archive_key,
            "checksum_sha256": "different-checksum",
            "environment": "preview",
            "environment_fingerprint": "env-preview-001",
            "environment_fingerprint_version": "env-authority-v1",
            "source_cluster_fingerprint": "cluster-preview-001",
            "database_name": "masci_safety_preview",
            "source_database_identity": "masci_safety_preview",
            "backup_bucket": "masci-hub",
            "backup_prefix": "backups/preview/auto-90d/",
            "manifest_key": f"backups/preview/auto-90d/manifests/{archive['filename']}.manifest.json",
            "checksum_key": f"backups/preview/auto-90d/checksums/{archive['filename']}.sha256",
        },
    }

    result = resolve_archive_lineage_from_inputs(
        runtime_identity=_runtime_identity(),
        archive_rows=[archive],
        recent_rows=[row],
        manifest_bundles={archive["filename"]: _direct_manifest(archive_key, backup_id)},
    )
    rejected = result["rejected_candidates"][0]

    assert result["authoritative_artifact"] is None
    assert rejected["direct_evidence_status"] == "FAILED"
    assert rejected["integrity_status"] == "FAIL"
    assert "direct_checksum_lineage_mismatch" in rejected["rejection_reasons"]


def test_legacy_inline_manifest_remains_medium_confidence() -> None:
    archive_key = "backups/auto-90d/MASCI_complete_backup_legacy.zip"
    archive = {
        "filename": "MASCI_complete_backup_legacy.zip",
        "key": archive_key,
        "last_modified_iso": datetime.now(timezone.utc).isoformat(),
        "size_bytes": 4096,
        "etag": "etag-legacy",
    }
    row = {
        "filename": archive["filename"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": True,
        "mode": "complete-r2",
        "records": 120,
        "size_bytes": 4096,
        "archive_lineage": {
            "archive_key": archive_key,
            "checksum_sha256": "legacy-checksum",
            "environment": "preview",
            "database_name": "masci_safety_preview",
            "created_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            "uploaded_at": (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat(),
        },
    }
    manifest_bundle = {
        "manifest_name": "MANIFEST.json",
        "manifest_key": None,
        "checksum_key": None,
        "checksum_sidecar": None,
        "read_mode": "INLINE_ZIP",
        "manifest": {
            "manifest_version": "27.11c-1",
            "backup_type": "complete-r2",
            "classification": "COMPLETE",
            "coverage_complete": True,
            "integrity_result": "PASS",
            "environment": "preview",
            "db_name": "masci_safety_preview",
            "backup_completed_at": (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat(),
            "generated_at": (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat(),
        },
    }

    result = resolve_archive_lineage_from_inputs(
        runtime_identity=_runtime_identity(),
        archive_rows=[archive],
        recent_rows=[row],
        manifest_bundles={archive["filename"]: manifest_bundle},
    )
    authoritative = result["authoritative_artifact"]

    assert authoritative is not None
    assert authoritative["direct_evidence_status"] == "LEGACY"
    assert authoritative["integrity_status"] == "UNVERIFIED"
    assert authoritative["authoritative_time_source"] == "PROVIDER_DURABLE_COMPLETION_TIME"
    assert authoritative["lineage_confidence"] == "MEDIUM"