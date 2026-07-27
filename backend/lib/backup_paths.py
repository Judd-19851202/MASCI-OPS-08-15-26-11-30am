from __future__ import annotations

import os
from typing import Iterable, List, Optional


LEGACY_COMPLETE_BACKUP_PREFIX = "backups/auto-90d/"


def normalized_app_env(raw: Optional[str]) -> str:
    env = str(raw or "").strip().lower()
    return env if env in {"preview", "production", "test"} else "preview"


def canonical_backup_prefix_for_env(app_env: Optional[str]) -> str:
    env = normalized_app_env(app_env)
    if env == "production":
        return "backups/production/auto-90d/"
    if env == "test":
        return "backups/test/auto-90d/"
    return "backups/preview/auto-90d/"


def configured_backup_prefix(env: Optional[dict] = None) -> str:
    source = env or os.environ
    explicit = (
        source.get("BACKUP_PREFIX")
        or source.get("R2_BACKUP_PREFIX")
        or source.get("S3_BACKUP_PREFIX")
        or ""
    ).strip()
    return explicit or canonical_backup_prefix_for_env(source.get("APP_ENV"))


def backup_prefix_search_order(app_env: Optional[str], *, explicit_prefix: Optional[str] = None) -> List[str]:
    canonical = (explicit_prefix or canonical_backup_prefix_for_env(app_env)).strip().rstrip("/") + "/"
    prefixes: List[str] = [canonical]
    legacy = LEGACY_COMPLETE_BACKUP_PREFIX.strip().rstrip("/") + "/"
    if legacy != canonical:
        prefixes.append(legacy)
    return prefixes


def dedupe_prefixes(prefixes: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in prefixes:
        prefix = str(raw or "").strip().rstrip("/") + "/"
        if not prefix or prefix in seen:
            continue
        seen.add(prefix)
        out.append(prefix)
    return out


def manifest_sidecar_key_for_archive(archive_key: str) -> str:
    cleaned = str(archive_key or "").strip().lstrip("/")
    prefix, _, filename = cleaned.rpartition("/")
    if not filename:
        raise ValueError("archive key missing filename")
    return f"{prefix}/manifests/{filename}.manifest.json" if prefix else f"manifests/{filename}.manifest.json"


def checksum_sidecar_key_for_archive(archive_key: str) -> str:
    cleaned = str(archive_key or "").strip().lstrip("/")
    prefix, _, filename = cleaned.rpartition("/")
    if not filename:
        raise ValueError("archive key missing filename")
    return f"{prefix}/checksums/{filename}.sha256" if prefix else f"checksums/{filename}.sha256"


__all__ = [
    "LEGACY_COMPLETE_BACKUP_PREFIX",
    "backup_prefix_search_order",
    "canonical_backup_prefix_for_env",
    "checksum_sidecar_key_for_archive",
    "configured_backup_prefix",
    "dedupe_prefixes",
    "manifest_sidecar_key_for_archive",
    "normalized_app_env",
]