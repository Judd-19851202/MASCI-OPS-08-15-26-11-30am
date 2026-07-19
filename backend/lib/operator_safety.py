from __future__ import annotations

import os
from typing import Any, Mapping

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
