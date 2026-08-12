from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional
from lib.backup_paths import canonical_backup_prefix_for_env, configured_backup_prefix
from urllib.parse import parse_qsl, unquote, urlparse


DEFAULT_APPROVED_PRODUCTION_CLUSTER = "MASCI-prod"
DEFAULT_APPROVED_PRODUCTION_HOSTNAME = "masci-prod.1nduwmg.mongodb.net"
DEFAULT_APPROVED_PRODUCTION_DB = "masci_safety"
DEFAULT_APPROVED_PRODUCTION_USER = "masci_prod_user"
DEFAULT_APPROVED_PREVIEW_DB = "masci_safety_preview"

STATUS_VERIFIED = "VERIFIED"
STATUS_MISMATCH = "MISMATCH"
STATUS_UNVERIFIABLE = "UNVERIFIABLE"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
STATUS_DEGRADED = "DEGRADED"
ENVIRONMENT_FINGERPRINT_VERSION = "env-authority-v1"


def _normalized_env(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    if raw in {"prod"}:
        return "production"
    if raw in {"dev", "development", "stage", "staging"}:
        return "preview"
    return raw or "preview"


def _truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_text(value: Optional[str]) -> Optional[str]:
    text = (value or "").strip()
    return text or None


def _split_csv(value: Optional[str]) -> tuple[str, ...]:
    if not value:
        return tuple()
    return tuple(part.strip().lower() for part in value.split(",") if part.strip())


def _is_preview_db_name(db_name: Optional[str]) -> bool:
    return bool((db_name or "").strip().lower().endswith("_preview"))


def _read_only_validation_requested(source: Mapping[str, str]) -> bool:
    mode = (source.get("READ_ONLY_VALIDATION_MODE") or "").strip().lower()
    return (
        _truthy(source.get("READ_ONLY_VALIDATION"))
        or _truthy(source.get("READ_ONLY_VALIDATION_REQUESTED"))
        or mode in {"read_only_validation", "enabled"}
    )


def _sha_prefix(*parts: Optional[str]) -> str:
    raw = "|".join((part or "") for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _normalized_environment_name(value: Optional[str]) -> str:
    env = _normalized_env(value)
    if env == "production":
        return "PRODUCTION"
    if env == "preview":
        return "PREVIEW"
    return (env or "UNKNOWN").upper()


def _cluster_fingerprint(hostname: Optional[str]) -> Optional[str]:
    safe = _safe_text((hostname or "").lower())
    if not safe:
        return None
    return _sha_prefix("cluster", safe)


def _normalize_storage_value(value: Optional[str], *, default: str = "UNRESOLVED") -> str:
    safe = _safe_text(value)
    if not safe:
        return default
    return safe.strip().lower()


def _normalized_binding_env(value: Optional[str]) -> Optional[str]:
    raw = _safe_text(value)
    if not raw:
        return None
    normalized = raw.lower()
    if normalized in {"prod", "production"}:
        return "production"
    if normalized in {"preview", "dev", "development", "stage", "staging", "test", "testing", "nonprod", "non-production"}:
        return "preview"
    if normalized in {"shared", "common"}:
        return "shared"
    return normalized


def _hostname_from_url(value: Optional[str]) -> Optional[str]:
    raw = _safe_text(value)
    if not raw:
        return None
    try:
        parsed = urlparse(raw)
        if parsed.hostname:
            return parsed.hostname.lower()
    except Exception:  # noqa: BLE001
        return raw.lower()
    return raw.lower()


def _contains_non_production_marker(value: Optional[str]) -> bool:
    safe = _safe_text(value)
    if not safe:
        return False
    lower = safe.lower()
    return any(marker in lower for marker in ("preview", "staging", "stage", "dev", "test", "localhost", "127.0.0.1"))


def build_environment_authority_fingerprint(
    *,
    environment_name: Optional[str],
    cluster_fingerprint: Optional[str],
    database_name: Optional[str],
    runtime_user_identity: Optional[str],
    backup_bucket: Optional[str],
    backup_prefix: Optional[str],
) -> str:
    return _sha_prefix(
        ENVIRONMENT_FINGERPRINT_VERSION,
        _normalized_environment_name(environment_name),
        _normalize_storage_value(cluster_fingerprint),
        _normalize_storage_value(database_name),
        _normalize_storage_value(runtime_user_identity),
        _normalize_storage_value(backup_bucket),
        _normalize_storage_value(backup_prefix),
    )


def _parse_duplicate_query_values(query: str) -> Dict[str, list[str]]:
    duplicates: Dict[str, list[str]] = {}
    grouped: Dict[str, list[str]] = {}
    for key, value in parse_qsl(query, keep_blank_values=True):
        grouped.setdefault(key, []).append(value)
    for key, values in grouped.items():
        normalized = {value.strip() for value in values}
        if len(values) > 1 and len(normalized) > 1:
            duplicates[key] = values
    return duplicates


@dataclass(frozen=True)
class ParsedMongoUrl:
    raw_present: bool
    scheme: str
    hostname: Optional[str]
    hostname_redacted: str
    username: Optional[str]
    path_database: Optional[str]
    query_duplicates: Dict[str, list[str]]
    parse_error: Optional[str]
    is_atlas: bool
    is_local: bool


def parse_mongo_url(mongo_url: Optional[str]) -> ParsedMongoUrl:
    raw = _safe_text(mongo_url)
    if not raw:
        return ParsedMongoUrl(False, "", None, "<missing>", None, None, {}, "missing_mongo_url", False, False)

    try:
        parsed = urlparse(raw)
    except Exception as exc:  # noqa: BLE001
        return ParsedMongoUrl(True, "", None, "<unparseable>", None, None, {}, f"unparseable_url:{type(exc).__name__}", False, False)

    scheme = (parsed.scheme or "").strip().lower()
    hostname = (parsed.hostname or "").strip().lower() or None
    username = unquote(parsed.username) if parsed.username else None
    path_database = parsed.path.lstrip("/").strip() or None
    parse_error = None
    if scheme not in {"mongodb", "mongodb+srv"}:
        parse_error = "unsupported_or_missing_scheme"
    elif not hostname:
        parse_error = "missing_hostname"
    return ParsedMongoUrl(
        raw_present=True,
        scheme=scheme,
        hostname=hostname,
        hostname_redacted=hostname or "<unknown-host>",
        username=username,
        path_database=path_database,
        query_duplicates=_parse_duplicate_query_values(parsed.query),
        parse_error=parse_error,
        is_atlas=bool(hostname and hostname.endswith("mongodb.net")),
        is_local=bool(hostname and hostname in {"localhost", "127.0.0.1", "::1"}),
    )


@dataclass(frozen=True)
class RuntimeIdentity:
    app_env: str
    environment_name: str
    db_name: str
    mongo_scheme: str
    mongo_hostname_redacted: str
    mongo_hostname: Optional[str]
    mongo_username: Optional[str]
    cluster_fingerprint: Optional[str]
    effective_database: Optional[str]
    enforce_db_isolation: bool
    release_commit: Optional[str]
    release_source_hash: Optional[str]
    preview_distinction: str
    scheduler_authority: str
    read_write_mode: str
    domain_host_context: Optional[str]
    source_identity: str
    approved_cluster_identifier: str
    approved_hostname: str
    approved_db_name: str
    approved_username: str
    identity_fingerprint: str
    environment_fingerprint: str
    environment_fingerprint_version: str
    backup_bucket: Optional[str]
    backup_prefix: Optional[str]
    storage_endpoint_host_redacted: Optional[str]
    maintainx_base_url_host: Optional[str]
    query_duplicates: Dict[str, list[str]]
    parse_error: Optional[str]
    is_atlas: bool
    is_local: bool
    read_only_validation: Dict[str, Any]
    environment_separation: Dict[str, Any]

    def to_safe_dict(self) -> Dict[str, Any]:
        return {
            "app_env": self.app_env,
            "environment_name": self.environment_name,
            "db_name": self.db_name,
            "mongo_scheme": self.mongo_scheme,
            "mongo_hostname_redacted": self.mongo_hostname_redacted,
            "mongo_user": self.mongo_username,
            "cluster_fingerprint": self.cluster_fingerprint,
            "effective_database": self.effective_database,
            "enforce_db_isolation": self.enforce_db_isolation,
            "release_commit": self.release_commit,
            "release_source_hash": self.release_source_hash,
            "preview_distinction": self.preview_distinction,
            "scheduler_authority": self.scheduler_authority,
            "read_write_mode": self.read_write_mode,
            "domain_host_context": self.domain_host_context,
            "source_identity": self.source_identity,
            "approved_cluster_identifier": self.approved_cluster_identifier,
            "approved_hostname": self.approved_hostname,
            "approved_db_name": self.approved_db_name,
            "approved_username": self.approved_username,
            "identity_fingerprint": self.identity_fingerprint,
            "environment_fingerprint": self.environment_fingerprint,
            "environment_fingerprint_version": self.environment_fingerprint_version,
            "backup_bucket": self.backup_bucket,
            "backup_prefix": self.backup_prefix,
            "storage_endpoint_host_redacted": "<configured>" if self.storage_endpoint_host_redacted else None,
            "maintainx_base_url_host": "<configured>" if self.maintainx_base_url_host else None,
            "query_duplicates": self.query_duplicates,
            "is_atlas": self.is_atlas,
            "is_local": self.is_local,
            "read_only_validation": self.read_only_validation,
            "environment_separation": self.environment_separation,
        }


@dataclass(frozen=True)
class RuntimeIdentityValidation:
    status: str
    valid: bool
    mismatch_category: Optional[str]
    remediation_owner: str
    remediation_action: str
    detail: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_safe_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "valid": self.valid,
            "mismatch_category": self.mismatch_category,
            "remediation_owner": self.remediation_owner,
            "remediation_action": self.remediation_action,
            "detail": self.detail,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def build_runtime_identity(*, env: Optional[Mapping[str, str]] = None, release_identity: Optional[Mapping[str, Any]] = None, domain_host_context: Optional[str] = None) -> RuntimeIdentity:
    source = env or os.environ
    release = release_identity or {}
    app_env = _normalized_env(source.get("APP_ENV"))
    environment_name = _normalized_environment_name(app_env)
    db_name = _safe_text(source.get("DB_NAME")) or ""
    parsed = parse_mongo_url(source.get("MONGO_URL"))
    cluster_fingerprint = _cluster_fingerprint(parsed.hostname or parsed.hostname_redacted)
    approved_hostname = _safe_text(source.get("APPROVED_PRODUCTION_MONGO_HOST")) or DEFAULT_APPROVED_PRODUCTION_HOSTNAME
    approved_db_name = _safe_text(source.get("APPROVED_PRODUCTION_DB_NAME")) or DEFAULT_APPROVED_PRODUCTION_DB
    approved_username = _safe_text(source.get("APPROVED_PRODUCTION_DB_USER")) or DEFAULT_APPROVED_PRODUCTION_USER
    approved_cluster_identifier = _safe_text(source.get("APPROVED_PRODUCTION_CLUSTER_ID")) or DEFAULT_APPROVED_PRODUCTION_CLUSTER
    approved_preview_db_name = _safe_text(source.get("APPROVED_PREVIEW_DB_NAME")) or DEFAULT_APPROVED_PREVIEW_DB
    approved_preview_hosts = _split_csv(source.get("APPROVED_PREVIEW_MONGO_HOSTS")) or (
        "localhost",
        "127.0.0.1",
        "::1",
    )
    resolved_domain_host = domain_host_context or _safe_text(source.get("APP_DOMAIN")) or _safe_text(source.get("REACT_APP_BACKEND_URL"))
    read_only_validation_requested = _read_only_validation_requested(source)
    read_only_mode = _truthy(source.get("READ_ONLY_MODE"))
    session_writes_suppressed = not _truthy(source.get("SESSION_TIMEOUTS_ENABLED"))
    scheduler_disabled = not _truthy(source.get("SCHEDULER_ENABLED"))
    email_disabled = not _truthy(source.get("AUTO_EMAIL_REPORTS"))
    maintainx_disabled = (
        not _truthy(source.get("MAINTAINX_WRITE_ENABLED"))
        and not _truthy(source.get("MAINTAINX_SYNC_ENABLED"))
    )
    ai_disabled = (
        _truthy(source.get("READ_ONLY_VALIDATION_AI_DISABLED"))
        or (
            not _truthy(source.get("AI_GATEWAY_ENABLED"))
            and not _truthy(source.get("DR_V2_AI_ENABLED"))
        )
    )
    ods_disabled = not _truthy(source.get("ODS_ENABLED"))
    trust_spine_disabled = _truthy(source.get("READ_ONLY_VALIDATION_TRUST_SPINE_DISABLED"))
    webhooks_disabled = _truthy(source.get("READ_ONLY_VALIDATION_WEBHOOKS_DISABLED"))
    zero_write_proven = _truthy(source.get("READ_ONLY_VALIDATION_ZERO_WRITE_PROVEN"))
    db_authority = (_safe_text(source.get("READ_ONLY_VALIDATION_DB_AUTHORITY")) or "unknown").lower()
    non_production_domain = bool(resolved_domain_host and "mascidocs.com" not in resolved_domain_host.lower())
    read_only_validation_errors: list[str] = []
    if read_only_validation_requested:
        if not read_only_mode:
            read_only_validation_errors.append("read_only_mode_not_enabled")
        if db_authority not in {"read_only", "readonly", "read-only"}:
            read_only_validation_errors.append("database_authority_not_proven_read_only")
        if not session_writes_suppressed:
            read_only_validation_errors.append("session_writes_not_suppressed")
        if not scheduler_disabled:
            read_only_validation_errors.append("schedulers_not_disabled")
        if not email_disabled:
            read_only_validation_errors.append("email_not_disabled")
        if not maintainx_disabled:
            read_only_validation_errors.append("maintainx_not_disabled")
        if not ai_disabled:
            read_only_validation_errors.append("ai_not_disabled")
        if not ods_disabled:
            read_only_validation_errors.append("ods_not_disabled")
        if not trust_spine_disabled:
            read_only_validation_errors.append("trust_spine_not_disabled")
        if not webhooks_disabled:
            read_only_validation_errors.append("webhooks_not_disabled")
        if not non_production_domain:
            read_only_validation_errors.append("domain_not_non_production")
        if not zero_write_proven:
            read_only_validation_errors.append("zero_write_proof_missing")
    read_only_validation = {
        "requested": read_only_validation_requested,
        "active": bool(read_only_validation_requested and not read_only_validation_errors),
        "db_authority": db_authority,
        "read_only_mode": read_only_mode,
        "startup_write_suppressed": bool(read_only_validation_requested),
        "http_mutation_barrier_active": bool(read_only_validation_requested),
        "session_writes_suppressed": session_writes_suppressed,
        "scheduler_disabled": scheduler_disabled,
        "backup_scheduler_disabled": scheduler_disabled,
        "email_disabled": email_disabled,
        "ai_disabled": ai_disabled,
        "ods_disabled": ods_disabled,
        "trust_spine_disabled": trust_spine_disabled,
        "maintainx_disabled": maintainx_disabled,
        "webhooks_disabled": webhooks_disabled,
        "non_production_domain": non_production_domain,
        "zero_write_proven": zero_write_proven,
        "approved_preview_db_name": approved_preview_db_name,
        "approved_preview_hosts": list(approved_preview_hosts),
        "errors": list(read_only_validation_errors),
    }
    release_commit = _safe_text(str(release.get("commit") or ""))
    release_source_hash = _safe_text(str(release.get("source_hash") or ""))
    source_identity = release_source_hash or release_commit or "unknown-release"
    backup_bucket = _safe_text(source.get("BACKUP_BUCKET") or source.get("R2_BUCKET") or source.get("S3_BUCKET"))
    backup_prefix = _safe_text(configured_backup_prefix(source))
    storage_endpoint_host = _hostname_from_url(source.get("S3_ENDPOINT_URL") or source.get("R2_ENDPOINT"))
    maintainx_base_url_host = _hostname_from_url(source.get("MAINTAINX_BASE_URL"))
    environment_separation = {
        "fail_closed": True,
        "dev_endpoints_enabled": _truthy(source.get("DEV_ENDPOINTS_ENABLED")),
        "preview_validation_identities_enabled": _truthy(source.get("ENABLE_PREVIEW_VALIDATION_IDENTITIES")),
        "preview_only_backfill_enabled": _truthy(source.get("PREVIEW_ONLY_BACKFILL_ENABLED") or source.get("ALLOW_PREVIEW_ONLY_BACKFILL")),
        "storage_binding_env": _normalized_binding_env(source.get("STORAGE_BINDING_ENV") or source.get("R2_BINDING_ENV") or source.get("S3_BINDING_ENV") or source.get("BACKUP_BINDING_ENV")),
        "storage_credential_binding_env": _normalized_binding_env(source.get("STORAGE_CREDENTIAL_BINDING_ENV") or source.get("R2_CREDENTIAL_BINDING_ENV") or source.get("S3_CREDENTIAL_BINDING_ENV")),
        "maintainx_binding_env": _normalized_binding_env(source.get("MAINTAINX_BINDING_ENV") or source.get("INTEGRATION_BINDING_ENV")),
        "resend_binding_env": _normalized_binding_env(source.get("RESEND_BINDING_ENV") or source.get("EMAIL_BINDING_ENV")),
        "admin_binding_env": _normalized_binding_env(source.get("SUPER_ADMIN_BINDING_ENV") or source.get("ADMIN_CREDENTIAL_BINDING_ENV")),
        "storage_namespace_has_non_production_marker": any(
            _contains_non_production_marker(item)
            for item in (backup_bucket, backup_prefix, storage_endpoint_host)
        ),
        "maintainx_endpoint_has_non_production_marker": _contains_non_production_marker(maintainx_base_url_host),
        "storage_endpoint_present": bool(storage_endpoint_host),
        "storage_endpoint_authority_label": "configured" if storage_endpoint_host else "missing",
        "maintainx_endpoint_present": bool(maintainx_base_url_host),
        "maintainx_endpoint_authority_label": "configured" if maintainx_base_url_host else "missing",
    }
    environment_fingerprint = build_environment_authority_fingerprint(
        environment_name=environment_name,
        cluster_fingerprint=cluster_fingerprint,
        database_name=db_name,
        runtime_user_identity=parsed.username,
        backup_bucket=backup_bucket,
        backup_prefix=backup_prefix,
    )
    return RuntimeIdentity(
        app_env=app_env,
        environment_name=environment_name,
        db_name=db_name,
        mongo_scheme=parsed.scheme,
        mongo_hostname_redacted=parsed.hostname_redacted,
        mongo_hostname=parsed.hostname,
        mongo_username=parsed.username,
        cluster_fingerprint=cluster_fingerprint,
        effective_database=parsed.path_database,
        enforce_db_isolation=_truthy(source.get("ENFORCE_DB_ISOLATION")),
        release_commit=release_commit,
        release_source_hash=release_source_hash,
        preview_distinction="production" if app_env == "production" else "preview",
        scheduler_authority="enabled" if _truthy(source.get("SCHEDULER_ENABLED")) else "disabled",
        read_write_mode="read_only" if _truthy(source.get("READ_ONLY_MODE")) else "read_write",
        domain_host_context=resolved_domain_host,
        source_identity=source_identity,
        approved_cluster_identifier=approved_cluster_identifier,
        approved_hostname=approved_hostname,
        approved_db_name=approved_db_name,
        approved_username=approved_username,
        identity_fingerprint=_sha_prefix(app_env, db_name, parsed.hostname or parsed.hostname_redacted, parsed.username, source_identity),
        environment_fingerprint=environment_fingerprint,
        environment_fingerprint_version=ENVIRONMENT_FINGERPRINT_VERSION,
        backup_bucket=backup_bucket,
        backup_prefix=backup_prefix,
        storage_endpoint_host_redacted=storage_endpoint_host,
        maintainx_base_url_host=maintainx_base_url_host,
        query_duplicates=parsed.query_duplicates,
        parse_error=parsed.parse_error,
        is_atlas=parsed.is_atlas,
        is_local=parsed.is_local,
        read_only_validation=read_only_validation,
        environment_separation=environment_separation,
    )


def validate_runtime_identity(identity: RuntimeIdentity) -> RuntimeIdentityValidation:
    errors: list[str] = []
    warnings: list[str] = []
    mismatch_category: Optional[str] = None

    if identity.parse_error:
        errors.append(f"mongo_url:{identity.parse_error}")
        mismatch_category = mismatch_category or "MONGO_URL_PARSE_ERROR"
    if identity.query_duplicates:
        errors.append("duplicate_query_values")
        mismatch_category = mismatch_category or "DUPLICATE_CONFIG_VALUES"
    if not identity.db_name:
        errors.append("missing_db_name")
        mismatch_category = mismatch_category or "DB_NAME_MISSING"
    expected_backup_prefix = canonical_backup_prefix_for_env(identity.app_env)
    if identity.backup_prefix and identity.backup_prefix != expected_backup_prefix:
        errors.append("backup_prefix_unapproved_for_environment")
        mismatch_category = mismatch_category or "BACKUP_PREFIX_MISMATCH"
    if identity.effective_database and identity.db_name and identity.effective_database != identity.db_name:
        errors.append("path_db_mismatch")
        mismatch_category = mismatch_category or "DATABASE_NAME_MISMATCH"

    preview_hosts = tuple(identity.read_only_validation.get("approved_preview_hosts") or ())
    preview_db_name = identity.read_only_validation.get("approved_preview_db_name") or DEFAULT_APPROVED_PREVIEW_DB
    preview_host_allowed = bool(
        identity.mongo_hostname
        and (
            identity.mongo_hostname in preview_hosts
            or any(marker in identity.mongo_hostname for marker in ("preview", "staging", "dev", "test"))
        )
    )
    preview_target_uses_production = any(
        (
            identity.db_name == identity.approved_db_name,
            identity.mongo_username == identity.approved_username,
        )
    )
    environment_separation = identity.environment_separation or {}

    def _binding_refused(binding_key: str, expected_env: str, error_code: str, category: str) -> None:
        nonlocal mismatch_category
        binding_value = environment_separation.get(binding_key)
        if binding_value and binding_value not in {expected_env, "shared"}:
            errors.append(error_code)
            mismatch_category = mismatch_category or category

    if identity.app_env == "production":
        if identity.read_only_validation.get("requested"):
            errors.append("read_only_validation_not_permitted_in_production")
            mismatch_category = mismatch_category or "READ_ONLY_VALIDATION_NOT_PERMITTED"
        if not identity.enforce_db_isolation:
            errors.append("db_isolation_not_enforced")
            mismatch_category = mismatch_category or "ISOLATION_NOT_ENFORCED"
        if identity.is_local:
            errors.append("local_mongo_refused")
            mismatch_category = mismatch_category or "LOCAL_MONGO_REFUSED"
        if identity.db_name != identity.approved_db_name:
            errors.append("production_db_name_unapproved")
            mismatch_category = mismatch_category or "DATABASE_NAME_MISMATCH"
        if not identity.mongo_hostname:
            errors.append("hostname_unverifiable")
            mismatch_category = mismatch_category or "HOST_UNVERIFIABLE"
        elif identity.mongo_hostname != identity.approved_hostname:
            errors.append("production_hostname_unapproved")
            mismatch_category = mismatch_category or "CLUSTER_HOST_MISMATCH"
        if identity.mongo_username and identity.mongo_username != identity.approved_username:
            errors.append("production_user_unapproved")
            mismatch_category = mismatch_category or "DATABASE_USER_MISMATCH"
        elif not identity.mongo_username:
            warnings.append("database_user_unavailable")
        if not identity.is_atlas:
            errors.append("atlas_identity_unproven")
            mismatch_category = mismatch_category or "CLUSTER_HOST_MISMATCH"
        if environment_separation.get("dev_endpoints_enabled"):
            errors.append("dev_endpoints_enabled_in_production")
            mismatch_category = mismatch_category or "PREVIEW_SURFACE_ENABLED_IN_PRODUCTION"
        if environment_separation.get("preview_validation_identities_enabled"):
            errors.append("preview_validation_identities_enabled_in_production")
            mismatch_category = mismatch_category or "PREVIEW_SURFACE_ENABLED_IN_PRODUCTION"
        if environment_separation.get("preview_only_backfill_enabled"):
            errors.append("preview_only_backfill_enabled_in_production")
            mismatch_category = mismatch_category or "PREVIEW_BACKFILL_ENABLED_IN_PRODUCTION"
        if environment_separation.get("storage_namespace_has_non_production_marker"):
            errors.append("preview_storage_namespace_refused")
            mismatch_category = mismatch_category or "STORAGE_NAMESPACE_ENV_MISMATCH"
        if environment_separation.get("maintainx_endpoint_has_non_production_marker"):
            errors.append("preview_integration_endpoint_refused")
            mismatch_category = mismatch_category or "INTEGRATION_ENDPOINT_ENV_MISMATCH"
        _binding_refused("storage_binding_env", "production", "storage_binding_env_unapproved", "STORAGE_BINDING_ENV_MISMATCH")
        _binding_refused("storage_credential_binding_env", "production", "storage_credentials_binding_env_unapproved", "STORAGE_CREDENTIAL_ENV_MISMATCH")
        _binding_refused("maintainx_binding_env", "production", "maintainx_binding_env_unapproved", "INTEGRATION_BINDING_ENV_MISMATCH")
        _binding_refused("resend_binding_env", "production", "resend_binding_env_unapproved", "INTEGRATION_CREDENTIAL_ENV_MISMATCH")
        _binding_refused("admin_binding_env", "production", "admin_credentials_binding_env_unapproved", "ADMIN_CREDENTIAL_ENV_MISMATCH")
    else:
        preview_db_name_is_valid = identity.db_name == preview_db_name
        preview_user_is_valid = bool(identity.mongo_username and identity.mongo_username != identity.approved_username)
        preview_host_is_shared_but_expected = identity.mongo_hostname == identity.approved_hostname and preview_db_name_is_valid and preview_user_is_valid

        if preview_target_uses_production:
            if identity.read_only_validation.get("requested") and identity.read_only_validation.get("active"):
                warnings.append("read_only_validation_active")
            elif identity.read_only_validation.get("requested"):
                errors.append("read_only_validation_incomplete")
                errors.extend(identity.read_only_validation.get("errors") or [])
                mismatch_category = mismatch_category or "READ_ONLY_VALIDATION_INCOMPLETE"
            else:
                if identity.db_name == identity.approved_db_name:
                    errors.append("preview_using_production_db_name")
                    mismatch_category = mismatch_category or "PREVIEW_PRODUCTION_DB_REFUSED"
                if identity.mongo_username == identity.approved_username:
                    errors.append("preview_using_production_user")
                    mismatch_category = mismatch_category or "PREVIEW_PRODUCTION_USER_REFUSED"
                if identity.mongo_hostname == identity.approved_hostname and not preview_host_is_shared_but_expected:
                    errors.append("preview_pointing_to_production_cluster")
                    mismatch_category = mismatch_category or "PREVIEW_PRODUCTION_CLUSTER_REFUSED"
        else:
            if identity.read_only_validation.get("requested"):
                errors.append("read_only_validation_not_required_for_non_production_target")
                mismatch_category = mismatch_category or "READ_ONLY_VALIDATION_NOT_REQUIRED"
            if identity.db_name != preview_db_name:
                errors.append("preview_db_name_unapproved")
                mismatch_category = mismatch_category or "PREVIEW_TARGET_UNAPPROVED"
            if not (identity.is_local or preview_host_allowed or preview_host_is_shared_but_expected):
                errors.append("preview_hostname_unapproved")
                mismatch_category = mismatch_category or "PREVIEW_TARGET_UNAPPROVED"
        if identity.db_name and not _is_preview_db_name(identity.db_name):
            warnings.append("preview_db_name_not_explicitly_preview")
        _binding_refused("storage_binding_env", "preview", "preview_using_production_storage_binding", "PREVIEW_PRODUCTION_STORAGE_REFUSED")
        _binding_refused("storage_credential_binding_env", "preview", "preview_using_production_storage_credentials", "PREVIEW_PRODUCTION_STORAGE_CREDENTIALS_REFUSED")
        _binding_refused("maintainx_binding_env", "preview", "preview_using_production_integration_binding", "PREVIEW_PRODUCTION_INTEGRATION_REFUSED")
        _binding_refused("resend_binding_env", "preview", "preview_using_production_integration_credentials", "PREVIEW_PRODUCTION_INTEGRATION_CREDENTIALS_REFUSED")
        _binding_refused("admin_binding_env", "preview", "preview_using_production_admin_credentials", "PREVIEW_PRODUCTION_ADMIN_CREDENTIALS_REFUSED")

    if errors:
        return RuntimeIdentityValidation(
            status=STATUS_MISMATCH if identity.mongo_hostname or identity.db_name else STATUS_UNVERIFIABLE,
            valid=False,
            mismatch_category=mismatch_category,
            remediation_owner="platform-ops",
            remediation_action="Correct runtime identity inputs before startup proceeds.",
            detail=f"env={identity.app_env} host={identity.mongo_hostname_redacted} db={identity.db_name or '<missing>'} expected_host={identity.approved_hostname} expected_db={identity.approved_db_name}",
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    return RuntimeIdentityValidation(
        status=STATUS_VERIFIED if identity.app_env == "production" else (STATUS_DEGRADED if warnings else STATUS_NOT_APPLICABLE),
        valid=True,
        mismatch_category=None,
        remediation_owner="platform-ops",
        remediation_action="No action required.",
        detail=f"env={identity.app_env} host={identity.mongo_hostname_redacted} db={identity.db_name or '<missing>'} fingerprint={identity.identity_fingerprint}",
        errors=tuple(),
        warnings=tuple(warnings),
    )


def build_runtime_identity_bundle(*, env: Optional[Mapping[str, str]] = None, release_identity: Optional[Mapping[str, Any]] = None, domain_host_context: Optional[str] = None) -> Dict[str, Any]:
    identity = build_runtime_identity(env=env, release_identity=release_identity, domain_host_context=domain_host_context)
    validation = validate_runtime_identity(identity)
    return {"identity": identity, "validation": validation}


def is_read_only_validation_requested_from_env(env: Optional[Mapping[str, str]] = None) -> bool:
    return _read_only_validation_requested(env or os.environ)


def is_read_only_validation_active_bundle(bundle: Optional[Mapping[str, Any]]) -> bool:
    if not bundle:
        return False
    identity = bundle.get("identity")
    if identity is None:
        return False
    contract = getattr(identity, "read_only_validation", None) or {}
    return bool(contract.get("active"))


def runtime_identity_public_payload(bundle: Mapping[str, Any]) -> Dict[str, Any]:
    identity = bundle["identity"]
    validation = bundle["validation"]
    return {
        "status": validation.status,
        "valid": validation.valid,
        "mismatch_category": validation.mismatch_category,
        "identity": identity.to_safe_dict(),
        "validation": validation.to_safe_dict(),
    }


def assert_runtime_identity_valid(bundle: Mapping[str, Any]) -> None:
    validation: RuntimeIdentityValidation = bundle["validation"]
    identity: RuntimeIdentity = bundle["identity"]
    if validation.valid:
        return
    raise RuntimeError(
        "Runtime identity contract refusal: "
        f"env={identity.app_env} host={identity.mongo_hostname_redacted} db={identity.db_name or '<missing>'} "
        f"expected_host={identity.approved_hostname} expected_db={identity.approved_db_name} "
        f"category={validation.mismatch_category or 'UNKNOWN'} owner={validation.remediation_owner}"
    )


__all__ = [
    "ENVIRONMENT_FINGERPRINT_VERSION",
    "STATUS_DEGRADED",
    "STATUS_MISMATCH",
    "STATUS_NOT_APPLICABLE",
    "STATUS_UNVERIFIABLE",
    "STATUS_VERIFIED",
    "assert_runtime_identity_valid",
    "build_environment_authority_fingerprint",
    "build_runtime_identity_bundle",
    "is_read_only_validation_active_bundle",
    "is_read_only_validation_requested_from_env",
    "parse_mongo_url",
    "runtime_identity_public_payload",
]