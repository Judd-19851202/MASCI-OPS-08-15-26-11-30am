"""DR-UNIFY-003 · Daily-report collection name compatibility layer.

The former V2 collections lived under ``dr_v2_*``. The DR-UNIFY-003
migration path renames them to ``daily_report_*``. While the rename
is being rolled out across deployments (and until DR-UNIFY-004 flips
the deployment cert switch), code that reads these collections must
work whether the data currently lives under the legacy name, the
canonical name, or split across both during the migration window.

The rules:
  1. **Reads** — return the canonical collection when it holds data;
     fall back to the legacy collection only when the canonical is
     empty (never merge — that would double-count).
  2. **Writes** — go to the canonical name.
  3. **Discovery** — a lightweight ``resolve_collection_name(db, key)``
     helper the app can call to decide which side to read from.
  4. **Idempotency** — safe to call repeatedly; a no-op when the
     canonical side has been populated (either by fresh writes or the
     migration script).

This module never mutates data. The migration itself lives in
``scripts/migrate_dr_v2_collections_to_daily_report.py``.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

# Canonical → legacy pairs. Order = read priority (canonical first).
COLLECTION_ALIASES: Dict[str, str] = {
    # canonical                     : legacy
    "daily_report_drafts":            "dr_v2_drafts",
    "daily_report_ai_cache":          "dr_v2_ai_cache",
    "daily_report_ai_audit_entries":  "dr_v2_ai_audit_entries",
    "daily_report_ai_approvals":      "dr_v2_ai_approvals",
    "daily_report_photo_intelligence":"dr_v2_photo_intelligence",
    "daily_report_bilingual_audit":   "dr_v2_bilingual_audit",
}


def legacy_name(canonical: str) -> Optional[str]:
    """Return the legacy collection name paired with ``canonical`` or
    ``None`` if no legacy mapping exists."""
    return COLLECTION_ALIASES.get(canonical)


def canonical_names() -> Iterable[str]:
    """Iterator over every canonical collection name known to the
    compat layer."""
    return COLLECTION_ALIASES.keys()


async def _collection_has_any_doc(db, name: str) -> bool:
    try:
        doc = await db[name].find_one({}, {"_id": 1})
        return doc is not None
    except Exception:  # noqa: BLE001
        return False


async def resolve_read_collection_name(db, canonical: str) -> str:
    """Return the collection name a *read* should target.

    Preference order:
      1. Canonical (``daily_report_*``) — if it holds any document.
      2. Legacy (``dr_v2_*``) — fallback during the migration window.
      3. Canonical name (default) — new writes will populate it.

    Never merges. Never mutates.
    """
    if await _collection_has_any_doc(db, canonical):
        return canonical
    legacy = legacy_name(canonical)
    if legacy and await _collection_has_any_doc(db, legacy):
        return legacy
    return canonical


def canonical_write_collection_name(canonical: str) -> str:
    """Return the collection name every *write* should target.

    Always the canonical name. Reserved as a function (not a passthrough)
    so callsites can be grepped for compliance during audits.
    """
    return canonical


__all__ = [
    "COLLECTION_ALIASES",
    "legacy_name",
    "canonical_names",
    "resolve_read_collection_name",
    "canonical_write_collection_name",
]
