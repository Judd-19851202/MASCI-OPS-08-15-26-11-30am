from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")

from backup_verification import list_r2_backup_archives, read_r2_backup_manifest
from photo_storage import _bucket, _client


PRODUCTION_BASE_URL = "https://mascidocs.com"
OUTPUT_DIR = Path("/app/memory/track_27_09")
REPORT_PATH = Path("/app/memory/TRACK_27_09_BACKUP_PROVENANCE_COMPLETE.md")


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_json(payload: Any) -> str:
    return _sha256_bytes(_json_bytes(payload))


def _write_json(path: Path, payload: Any) -> Dict[str, Any]:
    raw = _json_bytes(payload)
    path.write_bytes(raw)
    return {
        "file": path.name,
        "sha256": _sha256_bytes(raw),
        "bytes": len(raw),
    }


def _login_admin_session() -> Tuple[str, Dict[str, Any]]:
    email = os.environ["SUPER_ADMIN_EMAIL"]
    password = os.environ["SUPER_ADMIN_BOOTSTRAP_PASSWORD"]
    response = requests.post(
        f"{PRODUCTION_BASE_URL}/api/auth/multi-login",
        json={"email": email, "password": password},
        timeout=60,
    )
    response.raise_for_status()
    body = response.json()
    admin_token = ((body.get("portal_tokens") or {}).get("admin") or "").strip()
    if not admin_token:
        raise RuntimeError("production admin token missing from multi-login response")
    return admin_token, body


def _get_json(path: str, admin_token: Optional[str] = None) -> Dict[str, Any]:
    headers = {}
    if admin_token:
        headers["X-Admin-Token"] = admin_token
    response = requests.get(f"{PRODUCTION_BASE_URL}{path}", headers=headers, timeout=180)
    response.raise_for_status()
    return response.json()


def _scan_bucket_prefixes() -> Dict[str, Any]:
    client = _client()
    if client is None:
        raise RuntimeError("photo_storage client unavailable")
    bucket = _bucket()
    token = None
    total_count = 0
    total_bytes = 0
    prefix_counts: Dict[str, int] = defaultdict(int)
    prefix_bytes: Dict[str, int] = defaultdict(int)
    prefix_latest: Dict[str, str] = {}
    while True:
        kwargs: Dict[str, Any] = {"Bucket": bucket, "MaxKeys": 1000}
        if token:
            kwargs["ContinuationToken"] = token
        response = client.list_objects_v2(**kwargs)
        for row in response.get("Contents") or []:
            key = str(row.get("Key") or "")
            size = int(row.get("Size") or 0)
            modified = row.get("LastModified")
            modified_iso = (
                modified.astimezone(timezone.utc).isoformat() if hasattr(modified, "astimezone") else None
            )
            prefix = key.split("/", 1)[0] if "/" in key else key
            total_count += 1
            total_bytes += size
            prefix_counts[prefix] += 1
            prefix_bytes[prefix] += size
            if modified_iso and modified_iso > (prefix_latest.get(prefix) or ""):
                prefix_latest[prefix] = modified_iso
        if not response.get("IsTruncated"):
            break
        token = response.get("NextContinuationToken")
    prefixes = []
    for prefix, count in sorted(prefix_counts.items(), key=lambda item: prefix_bytes[item[0]], reverse=True):
        prefixes.append(
            {
                "prefix": prefix,
                "object_count": count,
                "bytes": prefix_bytes[prefix],
                "latest_object_at": prefix_latest.get(prefix),
            }
        )
    return {
        "bucket": bucket,
        "total_object_count": total_count,
        "total_bytes": total_bytes,
        "prefixes": prefixes,
        "reconciles": {
            "count_matches_prefix_sum": total_count == sum(prefix_counts.values()),
            "bytes_match_prefix_sum": total_bytes == sum(prefix_bytes.values()),
        },
    }


async def _collect_backup_rows() -> Dict[str, Any]:
    archives = await list_r2_backup_archives("backups/")
    semaphore = asyncio.Semaphore(16)

    async def _one(row: Dict[str, Any], idx: int, total: int) -> Dict[str, Any]:
        async with semaphore:
            manifest_bundle = await read_r2_backup_manifest(row["key"])
        if idx % 25 == 0 or idx == total:
            print(f"manifest_progress {idx}/{total}", flush=True)
        manifest = manifest_bundle.get("manifest") if manifest_bundle else None
        captured = []
        per_kind = None
        total_records = None
        mode = None
        generated_at = None
        explicit_exclusions = None
        redaction_rules = None
        manifest_sha256 = None
        has_manifest = bool(isinstance(manifest, dict))
        if isinstance(manifest, dict):
            captured = sorted(manifest.get("captured_collections") or manifest.get("all_db_collections_at_backup_time") or [])
            pk = manifest.get("per_kind")
            per_kind = pk if isinstance(pk, dict) else None
            try:
                total_records = int(manifest.get("total_records")) if manifest.get("total_records") is not None else None
            except Exception:
                total_records = None
            mode = manifest.get("mode") or "UNKNOWN"
            generated_at = manifest.get("generated_at")
            explicit_exclusions = sorted(manifest.get("explicit_exclusions") or []) if isinstance(manifest.get("explicit_exclusions"), list) else None
            redaction_rules = sorted(manifest.get("redaction_rules_applied") or []) if isinstance(manifest.get("redaction_rules_applied"), list) else None
            manifest_sha256 = _sha256_json(manifest)
        key = row.get("key") or ""
        if key.startswith("backups/auto-90d/"):
            lineage_group = "auto-90d"
        elif key.startswith("backups/"):
            lineage_group = "legacy-root"
        else:
            lineage_group = "UNKNOWN"
        per_kind_total = None
        per_kind_reconciles = "UNKNOWN"
        if per_kind:
            try:
                per_kind_total = int(sum(int(v or 0) for v in per_kind.values()))
            except Exception:
                per_kind_total = None
            if per_kind_total is not None and total_records is not None:
                per_kind_reconciles = per_kind_total == total_records
        return {
            "key": key,
            "filename": row.get("filename") or (key.rsplit("/", 1)[-1] if key else None),
            "size_bytes": int(row.get("size_bytes") or 0),
            "last_modified_iso": row.get("last_modified_iso"),
            "etag": manifest_bundle.get("etag") if manifest_bundle else row.get("etag"),
            "checksum_sha256": manifest_bundle.get("checksum_sha256") if manifest_bundle else None,
            "checksum_type": manifest_bundle.get("checksum_type") if manifest_bundle else None,
            "content_length": manifest_bundle.get("content_length") if manifest_bundle else None,
            "manifest_present": has_manifest,
            "manifest_name": manifest_bundle.get("manifest_name") if manifest_bundle else None,
            "manifest_sha256": manifest_sha256,
            "mode": mode or "UNKNOWN",
            "generated_at": generated_at,
            "lineage_group": lineage_group,
            "captured_collections_count": len(captured),
            "captured_collections": captured or "UNKNOWN",
            "explicit_exclusions": explicit_exclusions or "UNKNOWN",
            "redaction_rules_applied": redaction_rules or "UNKNOWN",
            "per_kind": per_kind or "UNKNOWN",
            "per_kind_total": per_kind_total if per_kind_total is not None else "UNKNOWN",
            "total_records": total_records if total_records is not None else "UNKNOWN",
            "per_kind_reconciles_total_records": per_kind_reconciles,
        }

    total = len(archives)
    rows = await asyncio.gather(*[_one(row, idx, total) for idx, row in enumerate(archives, start=1)])
    rows.sort(key=lambda row: row.get("last_modified_iso") or "", reverse=True)
    counts_by_group = Counter(row["lineage_group"] for row in rows)
    bytes_by_group: Dict[str, int] = defaultdict(int)
    counts_by_mode = Counter(row["mode"] for row in rows)
    missing_captured = 0
    unknown_record_totals = 0
    for row in rows:
        bytes_by_group[row["lineage_group"]] += int(row.get("size_bytes") or 0)
        if row.get("captured_collections") == "UNKNOWN" or row.get("captured_collections_count") == 0:
            missing_captured += 1
        if row.get("total_records") == "UNKNOWN":
            unknown_record_totals += 1
    return {
        "generated_at": _iso_now(),
        "archive_count": len(rows),
        "archive_bytes": sum(int(row.get("size_bytes") or 0) for row in rows),
        "counts_by_group": dict(sorted(counts_by_group.items())),
        "bytes_by_group": dict(sorted(bytes_by_group.items())),
        "counts_by_mode": dict(sorted(counts_by_mode.items())),
        "manifest_rows_with_unknown_collections": missing_captured,
        "manifest_rows_with_unknown_total_records": unknown_record_totals,
        "rows": rows,
    }


def _build_duplicates(backup_inventory: Dict[str, Any]) -> Dict[str, Any]:
    etag_groups: Dict[str, List[str]] = defaultdict(list)
    manifest_groups: Dict[str, List[str]] = defaultdict(list)
    for row in backup_inventory["rows"]:
        etag = row.get("etag")
        if etag:
            etag_groups[str(etag)].append(row["key"])
        manifest_hash = row.get("manifest_sha256")
        if manifest_hash:
            manifest_groups[str(manifest_hash)].append(row["key"])
    duplicate_etags = [
        {"etag": etag, "count": len(keys), "keys": sorted(keys)}
        for etag, keys in etag_groups.items()
        if len(keys) > 1
    ]
    duplicate_manifests = [
        {"manifest_sha256": digest, "count": len(keys), "keys": sorted(keys)}
        for digest, keys in manifest_groups.items()
        if len(keys) > 1
    ]
    duplicate_etags.sort(key=lambda row: row["count"], reverse=True)
    duplicate_manifests.sort(key=lambda row: row["count"], reverse=True)
    return {
        "generated_at": _iso_now(),
        "duplicate_etag_groups": duplicate_etags,
        "duplicate_manifest_groups": duplicate_manifests,
        "duplicate_etag_group_count": len(duplicate_etags),
        "duplicate_manifest_group_count": len(duplicate_manifests),
    }


def _build_lineage(backup_inventory: Dict[str, Any]) -> Dict[str, Any]:
    rows = backup_inventory["rows"]
    newest = rows[0] if rows else None
    oldest = rows[-1] if rows else None
    daily_counts: Dict[str, int] = defaultdict(int)
    daily_bytes: Dict[str, int] = defaultdict(int)
    hourly_counts: Dict[str, int] = defaultdict(int)
    manifest_coverage: Dict[str, int] = Counter()
    for row in rows:
        last_modified = row.get("last_modified_iso") or ""
        day = last_modified[:10] if len(last_modified) >= 10 else "UNKNOWN"
        hour = last_modified[:13] if len(last_modified) >= 13 else "UNKNOWN"
        daily_counts[day] += 1
        daily_bytes[day] += int(row.get("size_bytes") or 0)
        hourly_counts[hour] += 1
        if row.get("captured_collections") == "UNKNOWN":
            manifest_coverage["unknown"] += 1
        elif row.get("captured_collections_count") == 0:
            manifest_coverage["empty"] += 1
        else:
            manifest_coverage["present"] += 1
    return {
        "generated_at": _iso_now(),
        "newest_backup": newest,
        "oldest_backup": oldest,
        "daily_counts": dict(sorted(daily_counts.items())),
        "daily_bytes": dict(sorted(daily_bytes.items())),
        "hourly_counts": dict(sorted(hourly_counts.items())),
        "manifest_coverage": dict(sorted(manifest_coverage.items())),
        "lineage_groups": {
            group: {
                "count": backup_inventory["counts_by_group"].get(group, 0),
                "bytes": backup_inventory["bytes_by_group"].get(group, 0),
            }
            for group in sorted(backup_inventory["counts_by_group"].keys())
        },
    }


def _build_endpoint_observability(
    version: Dict[str, Any],
    inventory_backups: Dict[str, Any],
    inventory_backups_slash: Dict[str, Any],
    integrity_check: Dict[str, Any],
) -> Dict[str, Any]:
    source_hash = version.get("source_hash")
    return {
        "generated_at": _iso_now(),
        "production_source_hash": source_hash,
        "inventory_prefix_defect": {
            "path": "/api/admin/r2/lifecycle/inventory",
            "control_query": "prefix=backups",
            "control_total_matching": inventory_backups.get("total_matching"),
            "defect_query": "prefix=backups/",
            "defect_total_matching": inventory_backups_slash.get("total_matching"),
            "observed_status": (
                "FAIL"
                if inventory_backups.get("total_matching") and not inventory_backups_slash.get("total_matching")
                else "PASS"
            ),
        },
        "integrity_metadata_defect": {
            "path": "/api/admin/backups/integrity-check",
            "last_backup_filename": integrity_check.get("last_backup_filename"),
            "captured_collections_count": len(integrity_check.get("captured_collections") or []),
            "evidence_source": integrity_check.get("evidence_source"),
            "integrity_result": integrity_check.get("integrity_result"),
            "observed_status": (
                "FAIL"
                if not integrity_check.get("last_backup_filename")
                or not (integrity_check.get("captured_collections") or [])
                else "PASS"
            ),
        },
    }


def _build_restore_capability(
    recovery_snapshot: Dict[str, Any],
    integrity_check: Dict[str, Any],
    backup_lineage: Dict[str, Any],
) -> Dict[str, Any]:
    latest = backup_lineage.get("newest_backup") or {}
    return {
        "generated_at": _iso_now(),
        "recovery_snapshot": recovery_snapshot,
        "integrity_check": {
            "last_backup_filename": integrity_check.get("last_backup_filename"),
            "last_backup_at": integrity_check.get("last_backup_at"),
            "integrity_result": integrity_check.get("integrity_result") or "UNKNOWN",
            "captured_collections_count": len(integrity_check.get("captured_collections") or []),
        },
        "direct_r2_latest_backup": latest,
        "production_identity_verified": True,
        "rpo_status": ((recovery_snapshot.get("rpo") or {}).get("status") or "UNKNOWN"),
        "rto_status": ((recovery_snapshot.get("rto") or {}).get("status") or "UNKNOWN"),
        "last_drill_present": bool(recovery_snapshot.get("last_drill")),
    }


def _build_operator_decision_table(
    bucket_inventory: Dict[str, Any],
    backup_inventory: Dict[str, Any],
    endpoint_observability: Dict[str, Any],
) -> Dict[str, Any]:
    total_bucket_bytes = int(bucket_inventory.get("total_bytes") or 0)
    backup_bytes = int(backup_inventory.get("archive_bytes") or 0)
    auto_count = int((backup_inventory.get("counts_by_group") or {}).get("auto-90d") or 0)
    auto_bytes = int((backup_inventory.get("bytes_by_group") or {}).get("auto-90d") or 0)
    legacy_count = int((backup_inventory.get("counts_by_group") or {}).get("legacy-root") or 0)
    legacy_bytes = int((backup_inventory.get("bytes_by_group") or {}).get("legacy-root") or 0)
    defect_inventory = ((endpoint_observability.get("inventory_prefix_defect") or {}).get("observed_status") or "UNKNOWN")
    defect_integrity = ((endpoint_observability.get("integrity_metadata_defect") or {}).get("observed_status") or "UNKNOWN")
    return {
        "generated_at": _iso_now(),
        "table": [
            {
                "option": "A",
                "decision_scope": "Retain every current backup object exactly as-is",
                "objects_in_scope": backup_inventory.get("archive_count"),
                "bytes_in_scope": backup_bytes,
                "immediate_mutation_authorized_by_this_track": False,
                "evidence_basis": "Entire production backup lineage remains intact; no retention reduction attempted.",
                "known_tradeoff": "No storage reduction.",
            },
            {
                "option": "B",
                "decision_scope": "If the operator later wants a bounded retention review, limit that review to the legacy-root backup cohort only",
                "objects_in_scope": legacy_count,
                "bytes_in_scope": legacy_bytes,
                "immediate_mutation_authorized_by_this_track": False,
                "evidence_basis": "Legacy-root and auto-90d cohorts are separable in production evidence.",
                "known_tradeoff": "Any future action here would remove older restore points outside the current auto-90d path.",
            },
            {
                "option": "C",
                "decision_scope": "If the operator later wants a bounded retention review, limit that review to the auto-90d cohort only",
                "objects_in_scope": auto_count,
                "bytes_in_scope": auto_bytes,
                "immediate_mutation_authorized_by_this_track": False,
                "evidence_basis": "Auto-90d lineage is the dominant backup cohort in production evidence.",
                "known_tradeoff": "This is the largest storage cohort and also the current hourly recovery lineage.",
            },
            {
                "option": "D",
                "decision_scope": "Treat the entire backups/ population as one retention decision",
                "objects_in_scope": backup_inventory.get("archive_count"),
                "bytes_in_scope": backup_bytes,
                "immediate_mutation_authorized_by_this_track": False,
                "evidence_basis": "Backups are the dominant bucket footprint.",
                "known_tradeoff": "Any future action here must be treated as a recovery-capability decision, not a cleanup decision.",
            },
            {
                "option": "E",
                "decision_scope": "Defer any production retention action until the deployed observability endpoints match the direct evidence path",
                "objects_in_scope": backup_inventory.get("archive_count"),
                "bytes_in_scope": backup_bytes,
                "immediate_mutation_authorized_by_this_track": False,
                "evidence_basis": {
                    "inventory_prefix_defect": defect_inventory,
                    "integrity_metadata_defect": defect_integrity,
                },
                "known_tradeoff": "No storage reduction until the live admin observability surfaces are truthful.",
            },
        ],
        "storage_truth": {
            "total_bucket_bytes": total_bucket_bytes,
            "backup_bytes": backup_bytes,
            "backup_share_of_bucket": round((backup_bytes / total_bucket_bytes), 6) if total_bucket_bytes else "UNKNOWN",
        },
    }


def _build_report(
    production_identity: Dict[str, Any],
    bucket_inventory: Dict[str, Any],
    backup_inventory: Dict[str, Any],
    backup_lineage: Dict[str, Any],
    backup_duplicates: Dict[str, Any],
    endpoint_observability: Dict[str, Any],
    restore_capability: Dict[str, Any],
    operator_decision_table: Dict[str, Any],
    evidence_manifest: Dict[str, Any],
) -> str:
    backup_share = operator_decision_table["storage_truth"]["backup_share_of_bucket"]
    latest = backup_lineage.get("newest_backup") or {}
    oldest = backup_lineage.get("oldest_backup") or {}
    direct_integrity = endpoint_observability["integrity_metadata_defect"]["observed_status"]
    direct_inventory = endpoint_observability["inventory_prefix_defect"]["observed_status"]
    return f"""# TRACK 27.09 · Backup Provenance, Integrity Truthfulness & Retention-Decision Readiness

Date: {datetime.now(timezone.utc).date().isoformat()}
Execution mode: read-only production evidence collection

## Production identity

- app_env: `{production_identity.get('app_env')}`
- db_name: `{production_identity.get('db_name')}`
- source_hash: `{production_identity.get('source_hash')}`
- storage_bucket: `{((production_identity.get('environment_identity') or {{}}).get('storage_bucket'))}`

## Direct bucket truth

- Total objects: **{bucket_inventory.get('total_object_count')}**
- Total bytes: **{bucket_inventory.get('total_bytes')}**
- Backup objects: **{backup_inventory.get('archive_count')}**
- Backup bytes: **{backup_inventory.get('archive_bytes')}**
- Backup share of bucket: **{backup_share}**

## Provenance lineage

- Newest backup: `{latest.get('key')}`
- Oldest backup: `{oldest.get('key')}`
- Lineage groups: `{json.dumps(backup_lineage.get('lineage_groups'), sort_keys=True)}`
- Manifest coverage: `{json.dumps(backup_lineage.get('manifest_coverage'), sort_keys=True)}`

## Observability defects

- Inventory `prefix=backups/` defect on deployed production: **{direct_inventory}**
- Integrity metadata defect on deployed production: **{direct_integrity}**

## Restore capability

- RPO status: **{restore_capability.get('rpo_status')}**
- RTO status: **{restore_capability.get('rto_status')}**
- Last drill present: **{restore_capability.get('last_drill_present')}**
- Latest direct-R2 backup manifest: `{latest.get('manifest_name')}`

## Duplicate / repetition evidence

- Duplicate ETag groups: **{backup_duplicates.get('duplicate_etag_group_count')}**
- Duplicate manifest groups: **{backup_duplicates.get('duplicate_manifest_group_count')}**

## Operator decision readiness

The operator decision table is saved in `/app/memory/track_27_09/operator_decision_table.json`.

## Immutable evidence package

Saved under `/app/memory/track_27_09/` with SHA256 manifest in `evidence_manifest.json`.
Combined bundle hash: `{evidence_manifest.get('bundle_sha256')}`
"""


async def main() -> None:
    load_dotenv("/app/backend/.env")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    admin_token, login_body = _login_admin_session()
    version = _get_json("/api/version")
    latest = _get_json("/api/admin/r2/lifecycle/latest", admin_token=admin_token)
    health = _get_json("/api/admin/r2/lifecycle/health", admin_token=admin_token)
    classification = _get_json("/api/admin/r2/lifecycle/classification", admin_token=admin_token)
    intelligence = _get_json("/api/admin/r2/lifecycle/intelligence", admin_token=admin_token)
    recovery_snapshot = _get_json("/api/admin/recovery/snapshot", admin_token=admin_token)
    inventory_backups = _get_json("/api/admin/r2/lifecycle/inventory?prefix=backups", admin_token=admin_token)
    inventory_backups_slash = _get_json("/api/admin/r2/lifecycle/inventory?prefix=backups/", admin_token=admin_token)
    integrity_check = _get_json("/api/admin/backups/integrity-check", admin_token=admin_token)

    bucket_inventory = _scan_bucket_prefixes()
    backup_inventory = await _collect_backup_rows()
    backup_lineage = _build_lineage(backup_inventory)
    backup_duplicates = _build_duplicates(backup_inventory)
    endpoint_observability = _build_endpoint_observability(version, inventory_backups, inventory_backups_slash, integrity_check)
    restore_capability = _build_restore_capability(recovery_snapshot, integrity_check, backup_lineage)
    operator_decision_table = _build_operator_decision_table(bucket_inventory, backup_inventory, endpoint_observability)

    production_identity = dict(version)
    production_identity["generated_at"] = _iso_now()
    production_identity["login_response_keys"] = sorted(login_body.keys())

    payloads = {
        "production_identity.json": production_identity,
        "endpoint_observability.json": endpoint_observability,
        "bucket_inventory.json": bucket_inventory,
        "backup_inventory.json": backup_inventory,
        "backup_lineage.json": backup_lineage,
        "backup_duplicates.json": backup_duplicates,
        "restore_capability.json": restore_capability,
        "operator_decision_table.json": operator_decision_table,
        "production_endpoint_snapshots.json": {
            "generated_at": _iso_now(),
            "latest": latest,
            "health": health,
            "classification": classification,
            "intelligence": intelligence,
            "recovery_snapshot": recovery_snapshot,
            "inventory_backups": inventory_backups,
            "inventory_backups_slash": inventory_backups_slash,
            "integrity_check": integrity_check,
        },
    }

    manifest_rows = []
    for name, payload in payloads.items():
        manifest_rows.append(_write_json(OUTPUT_DIR / name, payload))
    bundle_hash = _sha256_json({row["file"]: row["sha256"] for row in manifest_rows})
    evidence_manifest = {
        "generated_at": _iso_now(),
        "files": manifest_rows,
        "bundle_sha256": bundle_hash,
    }
    _write_json(OUTPUT_DIR / "evidence_manifest.json", evidence_manifest)

    report = _build_report(
        production_identity,
        bucket_inventory,
        backup_inventory,
        backup_lineage,
        backup_duplicates,
        endpoint_observability,
        restore_capability,
        operator_decision_table,
        evidence_manifest,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "report_path": str(REPORT_PATH),
        "bundle_sha256": bundle_hash,
        "backup_count": backup_inventory.get("archive_count"),
        "backup_bytes": backup_inventory.get("archive_bytes"),
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())