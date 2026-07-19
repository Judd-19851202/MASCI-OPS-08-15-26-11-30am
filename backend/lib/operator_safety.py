from __future__ import annotations

import os
from typing import Any, Mapping
from urllib.parse import urlparse

from fastapi import HTTPException


def current_runtime_target() -> dict[str, str]:
    return {
        "app_env": (os.environ.get("APP_ENV") or "").strip().lower(),
        "db_name": (os.environ.get("DB_NAME") or "").strip(),
    }


def require_destructive_confirmation(
    body: Mapping[str, Any] | None,
    *,
    expected_confirm: str,
    require_backup_ack: bool = True,
) -> None:
    payload = body or {}
    if str(payload.get("confirm") or "") != expected_confirm:
        raise HTTPException(
            status_code=400,
            detail=f'Pass {{"confirm": "{expected_confirm}"}} to authorize this destructive action.',
        )
    if require_backup_ack and payload.get("backup_ack") is not True:
        raise HTTPException(
            status_code=400,
            detail="Pass {\"backup_ack\": true} to acknowledge recovery/backups before destructive action.",
        )


def require_destructive_runtime_guard(
    *,
    expected_db_name: str | None = None,
    require_env: str | None = None,
) -> dict[str, str]:
    target = current_runtime_target()
    if require_env and target["app_env"] != require_env:
        raise HTTPException(
            status_code=409,
            detail=f"Destructive action blocked in APP_ENV={target['app_env'] or 'unknown'}; required {require_env}.",
        )
    if expected_db_name and target["db_name"] != expected_db_name:
        raise HTTPException(
            status_code=409,
            detail="Destructive action blocked because the active DB_NAME does not match the approved target.",
        )
    return target


def require_non_empty_destructive_scope(items: list[Any] | None, *, detail: str) -> None:
    if not items:
        raise HTTPException(status_code=400, detail=detail)


def redact_target_identity(mongo_url: str | None, db_name: str | None) -> str:
    parsed = urlparse(mongo_url or "")
    host = parsed.hostname or "unknown-host"
    db = db_name or "unknown-db"
    return f"mongodb://***@{host}/{db}"


def require_cli_execute(execute: bool) -> None:
    if not execute:
        raise RuntimeError("Refusing to mutate without explicit --execute.")


def require_cli_confirmation(confirm: str | None, *, expected: str) -> None:
    if (confirm or "").strip() != expected:
        raise RuntimeError(f'Refusing to mutate without --confirm "{expected}".')


def require_cli_backup_ack(backup_ack: bool) -> None:
    if backup_ack is not True:
        raise RuntimeError("Refusing to mutate without --backup-ack.")


def require_cli_runtime_guard(
    *,
    app_env: str,
    db_name: str,
    allow_production: bool,
    expected_db_name: str | None = None,
) -> None:
    normalized_env = (app_env or "").strip().lower()
    normalized_db = (db_name or "").strip()
    if expected_db_name and normalized_db != expected_db_name:
        raise RuntimeError(
            f"Refusing to mutate because DB_NAME={normalized_db or 'unknown'} does not match expected {expected_db_name}."
        )
    if normalized_env in {"production", "prod"} or normalized_db == "masci_safety":
        if not allow_production:
            raise RuntimeError(
                "Refusing to mutate against Production semantics without explicit --allow-production."
            )
