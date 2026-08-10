from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from lib.backup_paths import normalized_app_env


ENV_AWARE_FAMILIES = frozenset({
    "attachments",
    "backups",
    "documents",
    "exports",
    "photos",
    "promo-assets",
    "safety-docs",
    "signatures",
})


@dataclass(frozen=True)
class KeyOwnership:
    key: str
    family: Optional[str]
    owner_env: Optional[str]
    namespaced: bool
    relative_key: str

    @property
    def is_legacy(self) -> bool:
        return not self.namespaced


def current_app_env() -> str:
    return normalized_app_env(os.environ.get("APP_ENV"))


def describe_key_ownership(key: Optional[str]) -> KeyOwnership:
    cleaned = str(key or "").strip().lstrip("/")
    if not cleaned:
        return KeyOwnership(key="", family=None, owner_env=None, namespaced=False, relative_key="")
    parts = cleaned.split("/")
    family = parts[0] if parts else None
    if family in ENV_AWARE_FAMILIES and len(parts) >= 3 and parts[1] in {"preview", "production", "test"}:
        return KeyOwnership(
            key=cleaned,
            family=family,
            owner_env=parts[1],
            namespaced=True,
            relative_key="/".join(parts[2:]),
        )
    return KeyOwnership(
        key=cleaned,
        family=family,
        owner_env=None,
        namespaced=False,
        relative_key="/".join(parts[1:]) if len(parts) > 1 else "",
    )


def build_env_owned_key(family: str, suffix: str, *, app_env: Optional[str] = None) -> str:
    family_clean = str(family or "").strip().strip("/")
    if family_clean not in ENV_AWARE_FAMILIES:
        raise ValueError(f"Unsupported storage family for environment ownership: {family_clean}")
    suffix_clean = str(suffix or "").strip().lstrip("/")
    if not suffix_clean:
        raise ValueError("storage key suffix is required")
    current = describe_key_ownership(suffix_clean)
    if current.family == family_clean and current.namespaced:
        return current.key
    if suffix_clean.startswith(f"{family_clean}/"):
        suffix_clean = suffix_clean[len(family_clean) + 1 :]
    env = normalized_app_env(app_env or current_app_env())
    return f"{family_clean}/{env}/{suffix_clean}"


def current_env_owns_key(key: Optional[str], *, app_env: Optional[str] = None) -> bool:
    ownership = describe_key_ownership(key)
    if not ownership.namespaced:
        return False
    return ownership.owner_env == normalized_app_env(app_env or current_app_env())


def build_storage_ref(scheme: str, bucket: str, key: str) -> str:
    return f"{scheme}://{str(bucket or '').strip()}/{str(key or '').strip().lstrip('/')}"


__all__ = [
    "ENV_AWARE_FAMILIES",
    "KeyOwnership",
    "build_env_owned_key",
    "build_storage_ref",
    "current_app_env",
    "current_env_owns_key",
    "describe_key_ownership",
]