"""DR-ROI-001 · Phase C · Agent result cache (MongoDB).

Cache key: (report_id, agent, evidence_hash). We only rerun an agent
when the evidence hash changes. This is the "only recompute what
changed" invariant from the phase directive.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


COLLECTION = "dr_v2_ai_cache"


async def read_cache(db, *, report_id: str, agent: str, evidence_hash: str) -> Optional[Dict[str, Any]]:
    doc = await db[COLLECTION].find_one(
        {"report_id": report_id, "agent": agent, "evidence_hash": evidence_hash},
        {"_id": 0},
    )
    return doc


async def write_cache(
    db, *, report_id: str, agent: str, evidence_hash: str, result: Dict[str, Any]
) -> None:
    await db[COLLECTION].update_one(
        {"report_id": report_id, "agent": agent, "evidence_hash": evidence_hash},
        {
            "$set": {
                "report_id": report_id,
                "agent": agent,
                "evidence_hash": evidence_hash,
                "result": result,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )


async def ensure_indexes(db) -> None:
    """Idempotent index creation. Called by the DR-V2 route registration."""
    try:
        await db[COLLECTION].create_index(
            [("report_id", 1), ("agent", 1), ("evidence_hash", 1)],
            unique=True,
            name="dr_v2_ai_cache_unique_key",
        )
        # 24h TTL — cached AI outputs expire so old models don't linger
        await db[COLLECTION].create_index(
            "cached_at", expireAfterSeconds=86400, name="dr_v2_ai_cache_ttl"
        )
    except Exception:  # noqa: BLE001 — index creation is best-effort at boot
        pass
