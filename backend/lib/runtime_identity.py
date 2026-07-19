from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional
from urllib.parse import parse_qsl, unquote, urlparse


DEFAULT_APPROVED_PRODUCTION_CLUSTER = "MASCI-prod"
DEFAULT_APPROVED_PRODUCTION_HOSTNAME = "masci-prod.1nduwmg.mongodb.net"
DEFAULT_APPROVED_PRODUCTION_DB = "masci_safety"
DEFAULT_APPROVED_PRODUCTION_USER = "masci_prod_user"

STATUS_VERIFIED = "VERIFIED"
STATUS_MISMATCH = "MISMATCH"
STATUS_UNVERIFIABLE = "UNVERIFIABLE"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
STATUS_DEGRADED = "DEGRADED"


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


def _sha_prefix(*parts: Optional[str]) -> str:
    raw = "|".join((part or "") for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


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
    db_name: str
    mongo_scheme: str
    mongo_hostname_redacted: str
    mongo_hostname: Optional[str]
    mongo_username: Optional[str]
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
    query_duplicates: Dict[str, list[str]]
    parse_error: Optional[str]
    is_atlas: bool
    is_local: bool

    def to_safe_dict(self) -> Dict[str, Any]:
        return {
            "app_env": self.app_env,
            "db_name": self.db_name,
            "mongo_scheme": self.mongo_scheme,
            "mongo_hostname_redacted": self.mongo_hostname_redacted,
            "mongo_user": self.mongo_username,
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
            "query_duplicates": self.query_duplicates,
            "is_atlas": self.is_atlas,
            "is_local": self.is_local,
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
    db_name = _safe_text(source.get("DB_NAME")) or ""
    parsed = parse_mongo_url(source.get("MONGO_URL"))
    approved_hostname = _safe_text(source.get("APPROVED_PRODUCTION_MONGO_HOST")) or DEFAULT_APPROVED_PRODUCTION_HOSTNAME
    approved_db_name = _safe_text(source.get("APPROVED_PRODUCTION_DB_NAME")) or DEFAULT_APPROVED_PRODUCTION_DB
    approved_username = _safe_text(source.get("APPROVED_PRODUCTION_DB_USER")) or DEFAULT_APPROVED_PRODUCTION_USER
    approved_cluster_identifier = _safe_text(source.get("APPROVED_PRODUCTION_CLUSTER_ID")) or DEFAULT_APPROVED_PRODUCTION_CLUSTER
    release_commit = _safe_text(str(release.get("commit") or ""))
    release_source_hash = _safe_text(str(release.get("source_hash") or ""))
    source_identity = release_source_hash or release_commit or "unknown-release"
    return RuntimeIdentity(
        app_env=app_env,
        db_name=db_name,
        mongo_scheme=parsed.scheme,
        mongo_hostname_redacted=parsed.hostname_redacted,
        mongo_hostname=parsed.hostname,
        mongo_username=parsed.username,
        effective_database=parsed.path_database,
        enforce_db_isolation=_truthy(source.get("ENFORCE_DB_ISOLATION")),
        release_commit=release_commit,
        release_source_hash=release_source_hash,
        preview_distinction="production" if app_env == "production" else "preview",
        scheduler_authority="enabled" if _truthy(source.get("SCHEDULER_ENABLED")) else "disabled",
        read_write_mode="read_only" if _truthy(source.get("READ_ONLY_MODE")) else "read_write",
        domain_host_context=domain_host_context or _safe_text(source.get("APP_DOMAIN")) or _safe_text(source.get("REACT_APP_BACKEND_URL")),
        source_identity=source_identity,
        approved_cluster_identifier=approved_cluster_identifier,
        approved_hostname=approved_hostname,
        approved_db_name=approved_db_name,
        approved_username=approved_username,
        identity_fingerprint=_sha_prefix(app_env, db_name, parsed.hostname or parsed.hostname_redacted, parsed.username, source_identity),
        query_duplicates=parsed.query_duplicates,
        parse_error=parsed.parse_error,
        is_atlas=parsed.is_atlas,
        is_local=parsed.is_local,
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
    if identity.effective_database and identity.db_name and identity.effective_database != identity.db_name:
        errors.append("path_db_mismatch")
        mismatch_category = mismatch_category or "DATABASE_NAME_MISMATCH"

    if identity.app_env == "production":
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
    else:
        if identity.db_name == identity.approved_db_name:
            errors.append("preview_using_production_db_name")
            mismatch_category = mismatch_category or "PREVIEW_PRODUCTION_DB_REFUSED"
        if identity.mongo_hostname == identity.approved_hostname:
            errors.append("preview_pointing_to_production_cluster")
            mismatch_category = mismatch_category or "PREVIEW_PRODUCTION_CLUSTER_REFUSED"
        if identity.mongo_username == identity.approved_username:
            errors.append("preview_using_production_user")
            mismatch_category = mismatch_category or "PREVIEW_PRODUCTION_USER_REFUSED"
        if identity.db_name and "preview" not in identity.db_name.lower():
            warnings.append("preview_db_name_not_explicitly_preview")

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
    "STATUS_DEGRADED",
    "STATUS_MISMATCH",
    "STATUS_NOT_APPLICABLE",
    "STATUS_UNVERIFIABLE",
    "STATUS_VERIFIED",
    "assert_runtime_identity_valid",
    "build_runtime_identity_bundle",
    "parse_mongo_url",
    "runtime_identity_public_payload",
]