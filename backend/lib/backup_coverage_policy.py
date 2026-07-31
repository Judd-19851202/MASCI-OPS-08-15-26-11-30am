from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


POLICY_VERSION = "wp17a-1"


@dataclass(frozen=True)
class BackupCoveragePolicy:
    collection: str
    classification: str
    coverage_requirement: str
    retention_expectation: str
    restore_expectation: str
    owner: str
    reason: str
    blocking: bool


_EXPLICIT_POLICIES: Dict[str, BackupCoveragePolicy] = {
    "usage_events": BackupCoveragePolicy(
        collection="usage_events",
        classification="ttl_telemetry",
        coverage_requirement="do_not_require_for_complete_coverage",
        retention_expectation="ttl",
        restore_expectation="not_required",
        owner="backup-platform",
        reason="regenerable API telemetry",
        blocking=False,
    ),
    "health_monitor_runs": BackupCoveragePolicy(
        collection="health_monitor_runs",
        classification="ttl_telemetry",
        coverage_requirement="do_not_require_for_complete_coverage",
        retention_expectation="ttl",
        restore_expectation="not_required",
        owner="backup-platform",
        reason="regenerable scheduler health series",
        blocking=False,
    ),
    "job_photo_thumb_cache": BackupCoveragePolicy(
        collection="job_photo_thumb_cache",
        classification="cache",
        coverage_requirement="do_not_require_for_complete_coverage",
        retention_expectation="regenerable",
        restore_expectation="not_required",
        owner="backup-platform",
        reason="regenerable derivative photo cache",
        blocking=False,
    ),
    "backup_integrity_jobs": BackupCoveragePolicy(
        collection="backup_integrity_jobs",
        classification="operational_state",
        coverage_requirement="do_not_require_for_complete_coverage",
        retention_expectation="short_operational_history",
        restore_expectation="not_required",
        owner="backup-platform",
        reason="regenerable operator integrity job ledger",
        blocking=False,
    ),
    "motive_events": BackupCoveragePolicy(
        collection="motive_events",
        classification="ttl_telemetry",
        coverage_requirement="do_not_require_for_complete_coverage",
        retention_expectation="ttl",
        restore_expectation="not_required",
        owner="fleet-telemetry",
        reason="TTL telemetry is not a record of record for complete coverage",
        blocking=False,
    ),
    "digest_runs": BackupCoveragePolicy(
        collection="digest_runs",
        classification="ttl_telemetry",
        coverage_requirement="do_not_require_for_complete_coverage",
        retention_expectation="ttl",
        restore_expectation="not_required",
        owner="notifications",
        reason="TTL digest send-history is not a record of record for complete coverage",
        blocking=False,
    ),
    "r2_degraded_events": BackupCoveragePolicy(
        collection="r2_degraded_events",
        classification="ttl_telemetry",
        coverage_requirement="do_not_require_for_complete_coverage",
        retention_expectation="ttl",
        restore_expectation="not_required",
        owner="storage-runtime",
        reason="TTL degraded-upload telemetry is not a record of record for complete coverage",
        blocking=False,
    ),
    "system_health_events": BackupCoveragePolicy(
        collection="system_health_events",
        classification="ttl_telemetry",
        coverage_requirement="do_not_require_for_complete_coverage",
        retention_expectation="ttl",
        restore_expectation="not_required",
        owner="platform-health",
        reason="TTL system-health telemetry is not a record of record for complete coverage",
        blocking=False,
    ),
}


def backup_policy_for_collection(collection: str) -> BackupCoveragePolicy:
    name = str(collection or "").strip()
    if name.startswith("system."):
        return BackupCoveragePolicy(
            collection=name,
            classification="mongodb_internal",
            coverage_requirement="do_not_require_for_complete_coverage",
            retention_expectation="managed_by_mongodb",
            restore_expectation="not_required",
            owner="mongodb",
            reason="MongoDB internal system collection",
            blocking=False,
        )
    return _EXPLICIT_POLICIES.get(
        name,
        BackupCoveragePolicy(
            collection=name,
            classification="record_of_record",
            coverage_requirement="must_back_up",
            retention_expectation="per-domain-policy",
            restore_expectation="required",
            owner="application-domain",
            reason="default platform policy — collection is authoritative unless explicitly classified otherwise",
            blocking=True,
        ),
    )


def backup_explicit_exclusions() -> set[str]:
    return {
        policy.collection
        for policy in _EXPLICIT_POLICIES.values()
        if policy.coverage_requirement != "must_back_up"
    }


def backup_exclusion_details() -> Dict[str, Dict[str, str]]:
    details = {
        policy.collection: {
            "reason": policy.reason,
            "owner": policy.owner,
            "classification": policy.classification,
            "coverage_requirement": policy.coverage_requirement,
            "restore_expectation": policy.restore_expectation,
        }
        for policy in _EXPLICIT_POLICIES.values()
        if policy.coverage_requirement != "must_back_up"
    }
    details["system.*"] = {
        "reason": "MongoDB internal system collection",
        "owner": "mongodb",
        "classification": "mongodb_internal",
        "coverage_requirement": "do_not_require_for_complete_coverage",
        "restore_expectation": "not_required",
    }
    return details


def backup_policy_inventory() -> List[Dict[str, str]]:
    rows = []
    for name in sorted(_EXPLICIT_POLICIES):
        policy = _EXPLICIT_POLICIES[name]
        rows.append(
            {
                "collection": policy.collection,
                "classification": policy.classification,
                "coverage_requirement": policy.coverage_requirement,
                "retention_expectation": policy.retention_expectation,
                "restore_expectation": policy.restore_expectation,
                "owner": policy.owner,
                "reason": policy.reason,
                "blocking": "yes" if policy.blocking else "no",
            }
        )
    return rows
