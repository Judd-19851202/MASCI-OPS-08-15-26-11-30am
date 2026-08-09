from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def retirement_recommendation(
    agg_row: Dict[str, Any],
    *,
    ttl_days: int,
    now: datetime | None = None,
) -> str:
    current = now or datetime.now(timezone.utc)
    last = agg_row.get("last_observed_at")
    if isinstance(last, str):
        try:
            last = datetime.fromisoformat(last.replace("Z", "+00:00"))
        except ValueError:
            last = None
    if isinstance(last, datetime):
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        age = (current - last).total_seconds()
        if age > ttl_days * 24 * 60 * 60:
            return "SAFE_TO_RETIRE"
    role = str(agg_row.get("last_role") or "").lower()
    env = str(agg_row.get("last_env") or "").lower()
    if env in ("preview", "unknown", "test") and role in ("anonymous", "bearer"):
        return "SAFE_TO_RETIRE"
    return "REVIEW_BEFORE_RETIRE"