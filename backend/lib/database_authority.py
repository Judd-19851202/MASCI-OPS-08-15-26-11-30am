from __future__ import annotations

import atexit
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Mapping, Optional

from lib.runtime_identity import assert_runtime_identity_valid, runtime_identity_public_payload


AUTHORITY_ID = "database-authority-d3"
AUTHORITY_VERSION = "2026-07-19"

READ_ONLY = "READ_ONLY"
READ_WRITE = "READ_WRITE"
WRITE_RESTRICTED = "WRITE_RESTRICTED"
VALIDATION_READ_ONLY = "VALIDATION_READ_ONLY"
OPERATOR_CONTROLLED = "OPERATOR_CONTROLLED"


@dataclass
class DatabaseAuthorityPlan:
    authority_id: str
    authority_version: str
    client_kind: str
    db_name: str
    mongo_url: str
    app_env: str
    read_write_authority: str
    connection_options: Dict[str, Any]
    identity_payload: Dict[str, Any]
    lifecycle_owner: str


_SYNC_HELPER_LOCK = threading.Lock()
_SYNC_HELPERS: Dict[str, Any] = {}


def _truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _identity_parts(runtime_identity_bundle: Mapping[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    payload = runtime_identity_public_payload(runtime_identity_bundle)
    identity = (payload or {}).get("identity") or {}
    validation = (payload or {}).get("validation") or {}
    return identity, validation


def determine_read_write_authority(runtime_identity_bundle: Mapping[str, Any]) -> str:
    identity, _validation = _identity_parts(runtime_identity_bundle)
    ro_validation = ((identity.get("read_only_validation") or {}).get("requested") is True)
    mode = str(identity.get("read_write_mode") or "").strip().lower()
    if ro_validation:
        return VALIDATION_READ_ONLY
    if mode == "read_only":
        return READ_ONLY
    if mode == "write_restricted":
        return WRITE_RESTRICTED
    return READ_WRITE


def build_runtime_database_authority(
    *,
    runtime_identity_bundle: Mapping[str, Any],
    env: Mapping[str, str],
    lifecycle_owner: str = "server._bootstrap_runtime_db",
) -> DatabaseAuthorityPlan:
    assert_runtime_identity_valid(runtime_identity_bundle)
    identity, validation = _identity_parts(runtime_identity_bundle)
    mongo_url = (env.get("MONGO_URL") or "").strip()
    db_name = (identity.get("db_name") or env.get("DB_NAME") or "").strip()
    if not mongo_url:
        raise RuntimeError("DATABASE_AUTHORITY_MONGO_URL_MISSING")
    if not db_name:
        raise RuntimeError("DATABASE_AUTHORITY_DB_NAME_MISSING")
    if not validation.get("valid", False):
        raise RuntimeError(f"DATABASE_AUTHORITY_IDENTITY_{validation.get('status') or 'UNVERIFIABLE'}")
    return DatabaseAuthorityPlan(
        authority_id=AUTHORITY_ID,
        authority_version=AUTHORITY_VERSION,
        client_kind="AsyncIOMotorClient",
        db_name=db_name,
        mongo_url=mongo_url,
        app_env=str(identity.get("app_env") or "unknown"),
        read_write_authority=determine_read_write_authority(runtime_identity_bundle),
        connection_options={
            "tz_aware": True,
            "maxPoolSize": 50,
            "serverSelectionTimeoutMS": int((env.get("MONGO_SERVER_SELECTION_TIMEOUT_MS") or "30000").strip() or "30000"),
            "connectTimeoutMS": int((env.get("MONGO_CONNECT_TIMEOUT_MS") or "30000").strip() or "30000"),
            "socketTimeoutMS": int((env.get("MONGO_SOCKET_TIMEOUT_MS") or "30000").strip() or "30000"),
            "retryReads": True,
            "retryWrites": not _truthy(env.get("READ_ONLY_VALIDATION")),
            "appname": "masci-runtime-authority",
            "uuidRepresentation": "standard",
        },
        identity_payload=runtime_identity_public_payload(runtime_identity_bundle),
        lifecycle_owner=lifecycle_owner,
    )


def create_async_runtime_client(plan: DatabaseAuthorityPlan, *, client_factory: Callable[..., Any]) -> tuple[Any, Any]:
    client = client_factory(plan.mongo_url, **plan.connection_options)
    try:
        setattr(client, "_authority_db_name", plan.db_name)
    except Exception:
        pass
    return client, client[plan.db_name]


def build_sync_helper_client(
    *,
    runtime_identity_bundle: Mapping[str, Any],
    env: Mapping[str, str],
    helper_name: str,
    client_factory: Callable[..., Any],
    extra_options: Optional[Dict[str, Any]] = None,
) -> Any:
    plan = build_runtime_database_authority(
        runtime_identity_bundle=runtime_identity_bundle,
        env=env,
        lifecycle_owner=f"sync-helper:{helper_name}",
    )
    with _SYNC_HELPER_LOCK:
        existing = _SYNC_HELPERS.get(helper_name)
        if existing is not None:
            return existing
        options = {
            "serverSelectionTimeoutMS": plan.connection_options["serverSelectionTimeoutMS"],
            "connectTimeoutMS": plan.connection_options["connectTimeoutMS"],
            "socketTimeoutMS": plan.connection_options["socketTimeoutMS"],
            "maxPoolSize": 10,
            "retryReads": True,
            "retryWrites": False,
            "appname": f"masci-sync-helper:{helper_name}",
            "uuidRepresentation": "standard",
            **(extra_options or {}),
        }
        client = client_factory(plan.mongo_url, **options)
        _SYNC_HELPERS[helper_name] = client
        return client


def close_sync_helper_client(helper_name: str) -> None:
    with _SYNC_HELPER_LOCK:
        client = _SYNC_HELPERS.pop(helper_name, None)
    if client is not None:
        try:
            client.close()
        except Exception:
            pass


def close_all_sync_helper_clients() -> None:
    with _SYNC_HELPER_LOCK:
        names = list(_SYNC_HELPERS.keys())
    for name in names:
        close_sync_helper_client(name)


atexit.register(close_all_sync_helper_clients)


def database_authority_public_payload(
    plan: Optional[DatabaseAuthorityPlan],
    *,
    lifecycle_state: str,
    connection_state: str,
    last_successful_ping: Optional[str] = None,
    last_error_category: Optional[str] = None,
) -> Dict[str, Any]:
    if plan is None:
        return {
            "authority_id": AUTHORITY_ID,
            "authority_version": AUTHORITY_VERSION,
            "lifecycle_state": lifecycle_state,
            "connection_state": connection_state,
            "last_successful_ping": last_successful_ping,
            "last_error_category": last_error_category,
        }
    identity = (plan.identity_payload or {}).get("identity") or {}
    validation = (plan.identity_payload or {}).get("validation") or {}
    return {
        "authority_id": plan.authority_id,
        "authority_version": plan.authority_version,
        "client_kind": plan.client_kind,
        "app_env": plan.app_env,
        "db_name": plan.db_name,
        "mongo_hostname_redacted": identity.get("mongo_hostname_redacted"),
        "read_write_authority": plan.read_write_authority,
        "lifecycle_owner": plan.lifecycle_owner,
        "lifecycle_state": lifecycle_state,
        "connection_state": connection_state,
        "identity_status": validation.get("status"),
        "identity_valid": validation.get("valid"),
        "last_successful_ping": last_successful_ping,
        "last_error_category": last_error_category,
        "connection_options": {
            "serverSelectionTimeoutMS": plan.connection_options.get("serverSelectionTimeoutMS"),
            "connectTimeoutMS": plan.connection_options.get("connectTimeoutMS"),
            "socketTimeoutMS": plan.connection_options.get("socketTimeoutMS"),
            "maxPoolSize": plan.connection_options.get("maxPoolSize"),
            "retryReads": plan.connection_options.get("retryReads"),
            "retryWrites": plan.connection_options.get("retryWrites"),
            "appname": plan.connection_options.get("appname"),
            "uuidRepresentation": plan.connection_options.get("uuidRepresentation"),
        },
    }


def canonical_database_name_from_runtime_identity(runtime_identity_bundle: Mapping[str, Any]) -> str:
    identity, _validation = _identity_parts(runtime_identity_bundle)
    return str(identity.get("db_name") or "").strip()


def managed_database_names(runtime_identity_bundle: Mapping[str, Any]) -> list[str]:
    identity, _validation = _identity_parts(runtime_identity_bundle)
    names = [
        str(identity.get("db_name") or "").strip(),
        str(identity.get("approved_db_name") or "").strip(),
    ]
    preview_name = "masci_safety_preview"
    if preview_name not in names:
        names.append(preview_name)
    return [name for idx, name in enumerate(names) if name and name not in names[:idx]]


def authority_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "AUTHORITY_ID",
    "AUTHORITY_VERSION",
    "READ_ONLY",
    "READ_WRITE",
    "WRITE_RESTRICTED",
    "VALIDATION_READ_ONLY",
    "OPERATOR_CONTROLLED",
    "DatabaseAuthorityPlan",
    "build_runtime_database_authority",
    "create_async_runtime_client",
    "build_sync_helper_client",
    "close_sync_helper_client",
    "close_all_sync_helper_clients",
    "database_authority_public_payload",
    "canonical_database_name_from_runtime_identity",
    "managed_database_names",
    "determine_read_write_authority",
    "authority_timestamp",
]