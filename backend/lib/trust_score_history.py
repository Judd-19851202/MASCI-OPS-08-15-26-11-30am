"""TRACK 15.76B · Trust Score history persistence.

Persists a small snapshot every time the Operations Trust Center is
opened so the dashboard can render a real **24h / 7d / 30d trend**
sparkline without fabricating data.

Snapshots are de-duplicated by minute to avoid bloating the
collection. Old rows past 60 days are TTL-expired.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


COLLECTION = "trust_score_history"


async def ensure_indexes(db) -> None:
    try:
        await db[COLLECTION].create_index([("ts", -1)])
        # 60-day TTL.
        await db[COLLECTION].create_index(
            "ts_dt", expireAfterSeconds=60 * 24 * 3600
        )
    except Exception:
        pass


async def write_snapshot(
    db,
    *,
    score: int,
    band: str,
    categories: Dict[str, Any],
    summary: Dict[str, Any],
) -> None:
    """Best-effort snapshot writer. De-duplicated by minute."""
    now = datetime.now(timezone.utc)
    minute_key = now.strftime("%Y-%m-%dT%H:%M")
    try:
        existing = await db[COLLECTION].count_documents(
            {"minute_key": minute_key}, limit=1
        )
        if existing:
            return
        await db[COLLECTION].insert_one({
            "ts": now.isoformat(),
            "ts_dt": now,
            "minute_key": minute_key,
            "score": int(score),
            "band": band,
            "category_scores": {
                k: int(v.get("score", 0))
                for k, v in (categories or {}).items()
            },
            "summary": {
                k: summary.get(k)
                for k in (
                    "workflows_red", "workflows_amber",
                    "workflows_idle", "workflows_trusted",
                    "events_24h", "failed_24h",
                    "master_data_band",
                )
            },
        })
    except Exception:
        pass


async def read_trend(
    db, *, window_hours: int, bucket_minutes: int = 60
) -> List[Dict[str, Any]]:
    """Return ordered [{ts, score, band}, ...] for the requested window."""
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    out: List[Dict[str, Any]] = []
    try:
        cursor = db[COLLECTION].find(
            {"ts_dt": {"$gte": since}},
            {"_id": 0, "ts": 1, "score": 1, "band": 1},
            sort=[("ts", 1)],
        )
        async for r in cursor:
            out.append(r)
    except Exception:
        pass
    return out
