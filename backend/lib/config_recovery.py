from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from lib.backup_paths import canonical_backup_prefix_for_env, configured_backup_prefix
from lib.runtime_identity import build_runtime_identity_bundle, runtime_identity_public_payload


CONFIG_RECOVERY_SCHEMA_VERSION = "bcss-s1-2-config-recovery-v1"
CONFIG_RECOVERY_RUNBOOK_VERSION = "bcss-s1-2-runbook-v1"
CONFIG_RECOVERY_RUNBOOK_PATH = "/app/memory/S1_2_CONFIGURATION_RECOVERY_RUNBOOK.md"

_BOOT_REFUSAL_PATH = [
    "server._bootstrap_runtime_db",
    "lib.database_authority.build_runtime_database_authority",
    "lib.runtime_identity.assert_runtime_identity_valid",
]

_SECRET_KEYS = {
    "ADMIN_HMAC_SECRET",
    "MONGO_URL",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _first_present(source: Mapping[str, str], *keys: str) -> Optional[str]:
    for key in keys:
        value = (source.get(key) or "").strip()
        if value:
            return value
    return None


def _parse_int(value: Optional[str], default: int) -> int:
    try:
        return int((value or "").strip() or str(default))
    except (TypeError, ValueError):
        return int(default)


def _string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value)]


def _source_refs(*keys: str) -> List[str]:
    return [f"env:{key}" for key in keys]


def _safe_runtime_bundle(
    *,
    env: Optional[Mapping[str, str]] = None,
    runtime_identity_bundle: Optional[Mapping[str, Any]] = None,
    release_identity: Optional[Mapping[str, Any]] = None,
    domain_host_context: Optional[str] = None,
) -> Dict[str, Any]:
    if runtime_identity_bundle is not None:
        return dict(runtime_identity_bundle)
    return build_runtime_identity_bundle(
        env=dict(env or os.environ),
        release_identity=release_identity,
        domain_host_context=domain_host_context,
    )


def _inventory_entry(
    *,
    key: str,
    group: str,
    required: bool,
    secret: bool,
    source_reference: List[str],
    recovery_scope: List[str],
    rationale: str,
    effective_value: Any = None,
    explicit_present: bool = False,
    default_applied: bool = False,
    default_source: Optional[str] = None,
) -> Dict[str, Any]:
    present = bool(explicit_present or default_applied or effective_value not in (None, "", []))
    row = {
        "key": key,
        "group": group,
        "required": required,
        "secret": secret,
        "source_reference": source_reference,
        "recovery_scope": recovery_scope,
        "rationale": rationale,
        "present": present,
        "explicit_present": bool(explicit_present),
        "default_applied": bool(default_applied),
        "default_source": default_source,
    }
    if secret:
        row.update(
            {
                "presence": "present" if present else "missing",
                "secret_reference": source_reference[0] if source_reference else f"env:{key}",
                "value_exposed": False,
            }
        )
    else:
        row["effective_value"] = effective_value
    return row


def _build_configuration_inventory(
    source: Mapping[str, str],
    *,
    runtime_identity_payload: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    identity = (runtime_identity_payload.get("identity") or {}) if isinstance(runtime_identity_payload, dict) else {}
    validation = (runtime_identity_payload.get("validation") or {}) if isinstance(runtime_identity_payload, dict) else {}
    read_only_validation = identity.get("read_only_validation") or {}

    backup_prefix_explicit = _first_present(source, "BACKUP_PREFIX", "R2_BACKUP_PREFIX", "S3_BACKUP_PREFIX")
    backup_prefix_effective = str(identity.get("backup_prefix") or configured_backup_prefix(dict(source)))
    backup_prefix_defaulted = not bool(backup_prefix_explicit)
    backup_prefix_default_source = (
        f"derived:{canonical_backup_prefix_for_env(identity.get('app_env'))}"
        if backup_prefix_defaulted
        else None
    )
    app_domain_value = _first_present(source, "APP_DOMAIN", "REACT_APP_BACKEND_URL")

    inventory = [
        _inventory_entry(
            key="APP_ENV",
            group="runtime",
            required=True,
            secret=False,
            source_reference=_source_refs("APP_ENV"),
            recovery_scope=["runtime_boot", "environment_separation", "archive_lineage"],
            rationale="Selects Preview vs Production authority and canonical backup prefix.",
            effective_value=identity.get("app_env") or (source.get("APP_ENV") or "").strip().lower(),
            explicit_present=bool((source.get("APP_ENV") or "").strip()),
        ),
        _inventory_entry(
            key="DB_NAME",
            group="runtime",
            required=True,
            secret=False,
            source_reference=_source_refs("DB_NAME"),
            recovery_scope=["runtime_boot", "environment_separation", "archive_lineage"],
            rationale="Pins the canonical database identity that Preview recovery is allowed to touch.",
            effective_value=identity.get("db_name") or (source.get("DB_NAME") or "").strip(),
            explicit_present=bool((source.get("DB_NAME") or "").strip()),
        ),
        _inventory_entry(
            key="MONGO_URL",
            group="database",
            required=True,
            secret=True,
            source_reference=_source_refs("MONGO_URL"),
            recovery_scope=["runtime_boot", "database_connectivity", "environment_separation"],
            rationale="MongoDB connection secret used to reach the canonical Preview database.",
            explicit_present=bool((source.get("MONGO_URL") or "").strip()),
        ),
        _inventory_entry(
            key="ENFORCE_DB_ISOLATION",
            group="safety",
            required=True,
            secret=False,
            source_reference=_source_refs("ENFORCE_DB_ISOLATION"),
            recovery_scope=["runtime_boot", "environment_separation"],
            rationale="Fail-closed guard that prevents runtime startup with contradictory database targets.",
            effective_value=bool(identity.get("enforce_db_isolation")),
            explicit_present=bool((source.get("ENFORCE_DB_ISOLATION") or "").strip()),
        ),
        _inventory_entry(
            key="APPROVED_PREVIEW_DB_NAME",
            group="authority",
            required=True,
            secret=False,
            source_reference=_source_refs("APPROVED_PREVIEW_DB_NAME"),
            recovery_scope=["environment_separation", "preview_target_validation"],
            rationale="Approved Preview database name used by the fail-closed validator.",
            effective_value=read_only_validation.get("approved_preview_db_name"),
            explicit_present=bool((source.get("APPROVED_PREVIEW_DB_NAME") or "").strip()),
            default_applied=not bool((source.get("APPROVED_PREVIEW_DB_NAME") or "").strip()),
            default_source="runtime_identity_default",
        ),
        _inventory_entry(
            key="APPROVED_PREVIEW_MONGO_HOSTS",
            group="authority",
            required=True,
            secret=False,
            source_reference=_source_refs("APPROVED_PREVIEW_MONGO_HOSTS"),
            recovery_scope=["environment_separation", "preview_target_validation"],
            rationale="Allowed Preview Mongo hosts when a dedicated Preview cluster is used.",
            effective_value=_string_list(read_only_validation.get("approved_preview_hosts")),
            explicit_present=bool((source.get("APPROVED_PREVIEW_MONGO_HOSTS") or "").strip()),
            default_applied=not bool((source.get("APPROVED_PREVIEW_MONGO_HOSTS") or "").strip()),
            default_source="runtime_identity_default",
        ),
        _inventory_entry(
            key="APPROVED_PRODUCTION_MONGO_HOST",
            group="authority",
            required=True,
            secret=False,
            source_reference=_source_refs("APPROVED_PRODUCTION_MONGO_HOST"),
            recovery_scope=["environment_separation", "production_blend_detection"],
            rationale="Production host reference used to reject Preview-to-Production blending.",
            effective_value=identity.get("approved_hostname"),
            explicit_present=bool((source.get("APPROVED_PRODUCTION_MONGO_HOST") or "").strip()),
            default_applied=not bool((source.get("APPROVED_PRODUCTION_MONGO_HOST") or "").strip()),
            default_source="runtime_identity_default",
        ),
        _inventory_entry(
            key="APPROVED_PRODUCTION_DB_NAME",
            group="authority",
            required=True,
            secret=False,
            source_reference=_source_refs("APPROVED_PRODUCTION_DB_NAME"),
            recovery_scope=["environment_separation", "production_blend_detection"],
            rationale="Production database reference used to reject Preview-to-Production blending.",
            effective_value=identity.get("approved_db_name"),
            explicit_present=bool((source.get("APPROVED_PRODUCTION_DB_NAME") or "").strip()),
            default_applied=not bool((source.get("APPROVED_PRODUCTION_DB_NAME") or "").strip()),
            default_source="runtime_identity_default",
        ),
        _inventory_entry(
            key="APPROVED_PRODUCTION_DB_USER",
            group="authority",
            required=True,
            secret=False,
            source_reference=_source_refs("APPROVED_PRODUCTION_DB_USER"),
            recovery_scope=["environment_separation", "production_blend_detection"],
            rationale="Production database user reference used to reject Preview-to-Production blending.",
            effective_value=identity.get("approved_username"),
            explicit_present=bool((source.get("APPROVED_PRODUCTION_DB_USER") or "").strip()),
            default_applied=not bool((source.get("APPROVED_PRODUCTION_DB_USER") or "").strip()),
            default_source="runtime_identity_default",
        ),
        _inventory_entry(
            key="S3_ENDPOINT_URL",
            group="backup_storage",
            required=True,
            secret=False,
            source_reference=_source_refs("S3_ENDPOINT_URL", "R2_ENDPOINT"),
            recovery_scope=["backup_archive_read", "backup_archive_write", "verification_read_path"],
            rationale="R2/S3-compatible endpoint required to read canonical backup archives and sidecars.",
            effective_value=_first_present(source, "S3_ENDPOINT_URL", "R2_ENDPOINT"),
            explicit_present=bool(_first_present(source, "S3_ENDPOINT_URL", "R2_ENDPOINT")),
        ),
        _inventory_entry(
            key="S3_BUCKET",
            group="backup_storage",
            required=True,
            secret=False,
            source_reference=_source_refs("BACKUP_BUCKET", "R2_BUCKET", "S3_BUCKET"),
            recovery_scope=["backup_archive_read", "backup_archive_write", "lineage_validation"],
            rationale="Canonical bucket identifier used by the backup archive and sidecar readers.",
            effective_value=identity.get("backup_bucket") or _first_present(source, "BACKUP_BUCKET", "R2_BUCKET", "S3_BUCKET"),
            explicit_present=bool(_first_present(source, "BACKUP_BUCKET", "R2_BUCKET", "S3_BUCKET")),
        ),
        _inventory_entry(
            key="S3_ACCESS_KEY",
            group="backup_storage",
            required=True,
            secret=True,
            source_reference=_source_refs("S3_ACCESS_KEY", "R2_ACCESS_KEY_ID"),
            recovery_scope=["backup_archive_read", "backup_archive_write"],
            rationale="Access-key reference used to authenticate against the R2 bucket.",
            explicit_present=bool(_first_present(source, "S3_ACCESS_KEY", "R2_ACCESS_KEY_ID")),
        ),
        _inventory_entry(
            key="S3_SECRET_KEY",
            group="backup_storage",
            required=True,
            secret=True,
            source_reference=_source_refs("S3_SECRET_KEY", "R2_SECRET_ACCESS_KEY"),
            recovery_scope=["backup_archive_read", "backup_archive_write"],
            rationale="Secret-key reference used to authenticate against the R2 bucket.",
            explicit_present=bool(_first_present(source, "S3_SECRET_KEY", "R2_SECRET_ACCESS_KEY")),
        ),
        _inventory_entry(
            key="BACKUP_PREFIX",
            group="backup_storage",
            required=True,
            secret=False,
            source_reference=_source_refs("BACKUP_PREFIX", "R2_BACKUP_PREFIX", "S3_BACKUP_PREFIX"),
            recovery_scope=["archive_lineage", "backup_archive_read", "verification_read_path"],
            rationale="Canonical archive prefix used for Preview lineage selection and sidecar lookups.",
            effective_value=backup_prefix_effective,
            explicit_present=bool(backup_prefix_explicit),
            default_applied=backup_prefix_defaulted,
            default_source=backup_prefix_default_source,
        ),
        _inventory_entry(
            key="BACKUP_R2_HOURLY",
            group="backup_policy",
            required=False,
            secret=False,
            source_reference=_source_refs("BACKUP_R2_HOURLY"),
            recovery_scope=["backup_schedule"],
            rationale="Signals whether the hourly complete R2 cadence is expected to be active.",
            effective_value=_truthy(source.get("BACKUP_R2_HOURLY")),
            explicit_present=bool((source.get("BACKUP_R2_HOURLY") or "").strip()),
        ),
        _inventory_entry(
            key="SCHEDULER_ENABLED",
            group="backup_policy",
            required=False,
            secret=False,
            source_reference=_source_refs("SCHEDULER_ENABLED"),
            recovery_scope=["backup_schedule", "verification_automation"],
            rationale="Scheduler authority drives automatic backup and verification cadence.",
            effective_value=str(identity.get("scheduler_authority") or "disabled") == "enabled",
            explicit_present=bool((source.get("SCHEDULER_ENABLED") or "").strip()),
        ),
        _inventory_entry(
            key="BACKUP_R2_MANIFEST_TIMEOUT_SECONDS",
            group="verification_policy",
            required=True,
            secret=False,
            source_reference=_source_refs("BACKUP_R2_MANIFEST_TIMEOUT_SECONDS"),
            recovery_scope=["verification_read_path"],
            rationale="Bounded timeout used when reading direct manifest evidence from R2.",
            effective_value=_parse_int(source.get("BACKUP_R2_MANIFEST_TIMEOUT_SECONDS"), 30),
            explicit_present=bool((source.get("BACKUP_R2_MANIFEST_TIMEOUT_SECONDS") or "").strip()),
            default_applied=not bool((source.get("BACKUP_R2_MANIFEST_TIMEOUT_SECONDS") or "").strip()),
            default_source="backup_verification_default",
        ),
        _inventory_entry(
            key="BACKUP_AGE_TARGET_HOURS",
            group="verification_policy",
            required=True,
            secret=False,
            source_reference=_source_refs("BACKUP_AGE_TARGET_HOURS"),
            recovery_scope=["recovery_snapshot", "freshness_posture"],
            rationale="Freshness threshold used by the recovery snapshot posture summary.",
            effective_value=_parse_int(source.get("BACKUP_AGE_TARGET_HOURS"), 24),
            explicit_present=bool((source.get("BACKUP_AGE_TARGET_HOURS") or "").strip()),
            default_applied=not bool((source.get("BACKUP_AGE_TARGET_HOURS") or "").strip()),
            default_source="recovery_snapshot_default",
        ),
        _inventory_entry(
            key="BACKUP_VERIFICATION_MAX_AGE_HOURS",
            group="verification_policy",
            required=True,
            secret=False,
            source_reference=_source_refs("BACKUP_VERIFICATION_MAX_AGE_HOURS"),
            recovery_scope=["backup_verification", "freshness_posture"],
            rationale="Maximum acceptable age used by the canonical backup verification report.",
            effective_value=_parse_int(source.get("BACKUP_VERIFICATION_MAX_AGE_HOURS"), 36),
            explicit_present=bool((source.get("BACKUP_VERIFICATION_MAX_AGE_HOURS") or "").strip()),
            default_applied=not bool((source.get("BACKUP_VERIFICATION_MAX_AGE_HOURS") or "").strip()),
            default_source="backup_verification_default",
        ),
        _inventory_entry(
            key="BACKUP_RPO_TARGET_MINUTES",
            group="recovery_objectives",
            required=True,
            secret=False,
            source_reference=_source_refs("BACKUP_RPO_TARGET_MINUTES"),
            recovery_scope=["recovery_snapshot", "operator_expectations"],
            rationale="Recovery point objective presented by the recovery dashboard.",
            effective_value=_parse_int(source.get("BACKUP_RPO_TARGET_MINUTES"), 60),
            explicit_present=bool((source.get("BACKUP_RPO_TARGET_MINUTES") or "").strip()),
            default_applied=not bool((source.get("BACKUP_RPO_TARGET_MINUTES") or "").strip()),
            default_source="recovery_snapshot_default",
        ),
        _inventory_entry(
            key="BACKUP_RTO_TARGET_MINUTES",
            group="recovery_objectives",
            required=True,
            secret=False,
            source_reference=_source_refs("BACKUP_RTO_TARGET_MINUTES"),
            recovery_scope=["recovery_snapshot", "operator_expectations"],
            rationale="Recovery time objective presented by the recovery dashboard.",
            effective_value=_parse_int(source.get("BACKUP_RTO_TARGET_MINUTES"), 15),
            explicit_present=bool((source.get("BACKUP_RTO_TARGET_MINUTES") or "").strip()),
            default_applied=not bool((source.get("BACKUP_RTO_TARGET_MINUTES") or "").strip()),
            default_source="recovery_snapshot_default",
        ),
        _inventory_entry(
            key="ADMIN_HMAC_SECRET",
            group="access_continuity",
            required=True,
            secret=True,
            source_reference=_source_refs("ADMIN_HMAC_SECRET"),
            recovery_scope=["admin_access_continuity", "operator_verification"],
            rationale="Stable admin token signing secret required for admin continuity across restarts.",
            explicit_present=bool((source.get("ADMIN_HMAC_SECRET") or "").strip()),
        ),
        _inventory_entry(
            key="APP_DOMAIN_OR_BACKEND_URL",
            group="operator_surface",
            required=False,
            secret=False,
            source_reference=_source_refs("APP_DOMAIN", "REACT_APP_BACKEND_URL"),
            recovery_scope=["operator_runbook", "read_only_validation"],
            rationale="Operator-visible endpoint reference used by the runbook and read-only validation mode.",
            effective_value=app_domain_value,
            explicit_present=bool(app_domain_value),
        ),
        _inventory_entry(
            key="RUNTIME_IDENTITY_STATUS",
            group="derived_authority",
            required=True,
            secret=False,
            source_reference=["derived:runtime_identity_public_payload"],
            recovery_scope=["environment_separation", "bootstrap_refusal"],
            rationale="Derived validator status proving whether Preview configuration is internally consistent.",
            effective_value=validation.get("status") or runtime_identity_payload.get("status"),
            explicit_present=True,
        ),
    ]
    return inventory


def _build_secret_inventory(configuration_inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in configuration_inventory:
        if row.get("key") not in _SECRET_KEYS:
            continue
        out.append(
            {
                "key": row.get("key"),
                "group": row.get("group"),
                "required": row.get("required"),
                "presence": row.get("presence"),
                "secret_reference": row.get("secret_reference"),
                "source_reference": row.get("source_reference") or [],
                "recovery_scope": row.get("recovery_scope") or [],
                "rationale": row.get("rationale"),
                "value_exposed": False,
            }
        )
    return out


def _build_environment_separation(runtime_identity_payload: Mapping[str, Any]) -> Dict[str, Any]:
    validation = (runtime_identity_payload.get("validation") or {}) if isinstance(runtime_identity_payload, dict) else {}
    identity = (runtime_identity_payload.get("identity") or {}) if isinstance(runtime_identity_payload, dict) else {}
    errors = list(validation.get("errors") or [])
    warnings = list(validation.get("warnings") or [])
    return {
        "status": "PASS" if validation.get("valid") else "FAIL",
        "fail_closed": True,
        "runtime_identity_status": validation.get("status") or runtime_identity_payload.get("status"),
        "mismatch_category": validation.get("mismatch_category"),
        "blocking_conditions": errors,
        "warnings": warnings,
        "boot_refusal_path": list(_BOOT_REFUSAL_PATH),
        "enforced_dimensions": [
            "app_env",
            "db_name",
            "mongo_hostname",
            "mongo_user",
            "backup_prefix",
            "environment_fingerprint",
        ],
        "preview_target": {
            "app_env": identity.get("app_env"),
            "db_name": identity.get("db_name"),
            "backup_prefix": identity.get("backup_prefix"),
            "environment_fingerprint": identity.get("environment_fingerprint"),
        },
        "refusal_contract": "Runtime database bootstrap refuses contradictory Preview/Production configuration before the DB handle becomes active.",
    }


def _build_validator(
    configuration_inventory: List[Dict[str, Any]],
    secret_reference_inventory: List[Dict[str, Any]],
    *,
    runtime_identity_payload: Mapping[str, Any],
    environment_separation: Mapping[str, Any],
) -> Dict[str, Any]:
    identity = (runtime_identity_payload.get("identity") or {}) if isinstance(runtime_identity_payload, dict) else {}
    validation = (runtime_identity_payload.get("validation") or {}) if isinstance(runtime_identity_payload, dict) else {}

    def _entry(key: str) -> Dict[str, Any]:
        for row in configuration_inventory:
            if row.get("key") == key:
                return row
        return {}

    checks: List[Dict[str, Any]] = []
    blocking_issues: List[str] = []
    warnings: List[str] = []

    def _add_check(check_id: str, ok: bool, *, severity: str, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        checks.append({"check_id": check_id, "status": status, "severity": severity, "detail": detail})
        if not ok and severity == "blocking":
            blocking_issues.append(f"{check_id}:{detail}")
        elif not ok:
            warnings.append(f"{check_id}:{detail}")

    missing_required_config = sorted(
        row.get("key")
        for row in configuration_inventory
        if row.get("required") and row.get("secret") is False and not row.get("present")
    )
    missing_required_secret_refs = sorted(
        row.get("key")
        for row in secret_reference_inventory
        if row.get("required") and row.get("presence") != "present"
    )
    defaulted_keys = sorted(row.get("key") for row in configuration_inventory if row.get("default_applied"))
    expected_preview_prefix = canonical_backup_prefix_for_env(identity.get("app_env"))
    effective_backup_prefix = str(_entry("BACKUP_PREFIX").get("effective_value") or "")
    expected_preview_db = str((identity.get("read_only_validation") or {}).get("approved_preview_db_name") or "")
    preview_db = str(identity.get("db_name") or "")

    _add_check(
        "runtime_identity_valid",
        bool(validation.get("valid")),
        severity="blocking",
        detail=(validation.get("detail") or "runtime identity must remain valid for Preview recovery certification"),
    )
    _add_check(
        "environment_separation_fail_closed",
        environment_separation.get("status") == "PASS" and environment_separation.get("fail_closed") is True,
        severity="blocking",
        detail="Preview/Production blend detection must pass and remain fail-closed.",
    )
    _add_check(
        "required_configuration_inventory_present",
        not missing_required_config,
        severity="blocking",
        detail="missing=" + (", ".join(missing_required_config) if missing_required_config else "none"),
    )
    _add_check(
        "required_secret_references_present",
        not missing_required_secret_refs,
        severity="blocking",
        detail="missing=" + (", ".join(missing_required_secret_refs) if missing_required_secret_refs else "none"),
    )
    _add_check(
        "preview_backup_prefix_canonical",
        bool(identity.get("app_env") != "preview" or effective_backup_prefix == expected_preview_prefix),
        severity="blocking",
        detail=f"effective={effective_backup_prefix or '<missing>'} expected={expected_preview_prefix}",
    )
    _add_check(
        "preview_database_identity_canonical",
        bool(identity.get("app_env") != "preview" or (preview_db and preview_db == expected_preview_db)),
        severity="blocking",
        detail=f"effective={preview_db or '<missing>'} expected={expected_preview_db or '<missing>'}",
    )
    _add_check(
        "bootstrap_refusal_path_registered",
        True,
        severity="info",
        detail=" -> ".join(_BOOT_REFUSAL_PATH),
    )
    checks.append(
        {
            "check_id": "safe_defaults_documented",
            "status": "PASS",
            "severity": "info",
            "detail": ", ".join(defaulted_keys) if defaulted_keys else "none",
        }
    )

    blocking_issues.extend(str(error) for error in (validation.get("errors") or []))
    warnings.extend(str(warning) for warning in (validation.get("warnings") or []))
    overall_status = "PASS" if not blocking_issues else "FAIL"
    return {
        "overall_status": overall_status,
        "certification_ready": overall_status == "PASS",
        "evidence_confidence": "HIGH" if overall_status == "PASS" else "LOW",
        "blocking_issues": sorted(dict.fromkeys(blocking_issues)),
        "warnings": sorted(dict.fromkeys(warnings)),
        "checks": checks,
        "required_configuration_keys": sorted(
            row.get("key") for row in configuration_inventory if row.get("required") and row.get("secret") is False
        ),
        "required_secret_keys": sorted(
            row.get("key") for row in secret_reference_inventory if row.get("required")
        ),
    }


def build_configuration_recovery_runbook(*, app_env: Optional[str]) -> Dict[str, Any]:
    env_label = str(app_env or "unknown")
    return {
        "runbook_version": CONFIG_RECOVERY_RUNBOOK_VERSION,
        "runbook_path": CONFIG_RECOVERY_RUNBOOK_PATH,
        "scope": env_label,
        "steps": [
            {
                "step": 1,
                "title": "Confirm bounded Preview scope",
                "action": "Verify APP_ENV, DB_NAME, and backup prefix via /api/admin/recovery/configuration-recovery.",
                "pass_condition": "validator.overall_status == PASS and environment_separation.status == PASS",
            },
            {
                "step": 2,
                "title": "Recover configuration inventory",
                "action": "Use configuration_inventory to rebuild non-secret runtime values and defaults without copying secret material into evidence.",
                "pass_condition": "All required non-secret entries are present or safely defaulted.",
            },
            {
                "step": 3,
                "title": "Recover secret references",
                "action": "Use secret_reference_inventory to identify which secret slots must be rehydrated from the Preview secret store.",
                "pass_condition": "Every required secret reference shows presence=present and value_exposed=false.",
            },
            {
                "step": 4,
                "title": "Enforce fail-closed separation",
                "action": "If runtime identity validation fails, stop before DB bootstrap and correct the conflicting Preview/Production configuration.",
                "pass_condition": "No Preview/Production blend errors remain; boot_refusal_path stays active.",
            },
            {
                "step": 5,
                "title": "Re-verify recovery posture",
                "action": "Re-check /api/health, /api/admin/recovery/snapshot, and the configuration package before declaring Preview config recovery ready.",
                "pass_condition": "Health is reachable and the recovery snapshot carries configuration_recovery.status == PASS.",
            },
        ],
    }


def build_configuration_recovery_package(
    *,
    env: Optional[Mapping[str, str]] = None,
    runtime_identity_bundle: Optional[Mapping[str, Any]] = None,
    release_identity: Optional[Mapping[str, Any]] = None,
    domain_host_context: Optional[str] = None,
) -> Dict[str, Any]:
    source = dict(env or os.environ)
    bundle = _safe_runtime_bundle(
        env=source,
        runtime_identity_bundle=runtime_identity_bundle,
        release_identity=release_identity,
        domain_host_context=domain_host_context,
    )
    runtime_identity_payload = runtime_identity_public_payload(bundle)
    configuration_inventory = _build_configuration_inventory(source, runtime_identity_payload=runtime_identity_payload)
    secret_reference_inventory = _build_secret_inventory(configuration_inventory)
    environment_separation = _build_environment_separation(runtime_identity_payload)
    validator = _build_validator(
        configuration_inventory,
        secret_reference_inventory,
        runtime_identity_payload=runtime_identity_payload,
        environment_separation=environment_separation,
    )
    runbook = build_configuration_recovery_runbook(
        app_env=((runtime_identity_payload.get("identity") or {}).get("app_env")),
    )
    return {
        "schema_version": CONFIG_RECOVERY_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "certification_slice": "S1-2",
        "scope": "preview_only",
        "runtime_identity": runtime_identity_payload,
        "inventory_counts": {
            "configuration_items": len(configuration_inventory),
            "secret_reference_items": len(secret_reference_inventory),
        },
        "configuration_inventory": configuration_inventory,
        "secret_reference_inventory": secret_reference_inventory,
        "environment_separation": environment_separation,
        "validator": validator,
        "recovery_runbook": runbook,
        "evidence_refs": [
            "/api/health",
            "/api/admin/recovery/snapshot",
            "/api/admin/recovery/configuration-recovery",
        ],
        "external_dependencies": [],
    }


def build_configuration_recovery_summary(package: Mapping[str, Any]) -> Dict[str, Any]:
    validator = package.get("validator") or {}
    environment_separation = package.get("environment_separation") or {}
    runtime_identity = ((package.get("runtime_identity") or {}).get("identity") or {}) if isinstance(package.get("runtime_identity"), dict) else {}
    inventory_counts = package.get("inventory_counts") or {}
    runbook = package.get("recovery_runbook") or {}
    secret_inventory = package.get("secret_reference_inventory") or []
    return {
        "status": validator.get("overall_status") or "FAIL",
        "environment": runtime_identity.get("app_env"),
        "db_name": runtime_identity.get("db_name"),
        "environment_separation_status": environment_separation.get("status"),
        "blocking_issue_count": len(validator.get("blocking_issues") or []),
        "warning_count": len(validator.get("warnings") or []),
        "configuration_item_count": inventory_counts.get("configuration_items", 0),
        "secret_reference_count": inventory_counts.get("secret_reference_items", 0),
        "all_secret_refs_present": all(row.get("presence") == "present" for row in secret_inventory),
        "runbook_path": runbook.get("runbook_path"),
        "evidence_confidence": validator.get("evidence_confidence") or "LOW",
    }


__all__ = [
    "CONFIG_RECOVERY_RUNBOOK_PATH",
    "CONFIG_RECOVERY_RUNBOOK_VERSION",
    "CONFIG_RECOVERY_SCHEMA_VERSION",
    "build_configuration_recovery_package",
    "build_configuration_recovery_runbook",
    "build_configuration_recovery_summary",
]