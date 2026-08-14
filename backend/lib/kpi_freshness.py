"""WAVE 6 — Canonical FRESHNESS / TIME authority (governed age-state machine).

One governed owner for "is this data CURRENT?" so no surface can claim CURRENT merely
because data exists. Freshness comes from the correct authority timestamp + age threshold.

Governed enum (matches TRUTH_FRESHNESS_HEALTH_REGISTER):
  CURRENT      observed within fresh_within
  AGING        older than fresh_within, within stale_after
  STALE        older than stale_after
  UNKNOWN      no/malformed/absent timestamp  (NEVER CURRENT)
  FUTURE       timestamp is in the future beyond tolerance (clock/ingest anomaly; NOT CURRENT)
  SCAN_FAILED  the producing scan failed (caller passes scan_failed=True; NEVER CURRENT/STALE-only)

Time doctrine: all comparisons in UTC. Callers pass tz-aware or ISO-Z timestamps; naive
datetimes are treated as UTC. Missing/unknown NEVER silently becomes CURRENT or STALE.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union

CURRENT = "CURRENT"
AGING = "AGING"
STALE = "STALE"
UNKNOWN = "UNKNOWN"
FUTURE = "FUTURE"
SCAN_FAILED = "SCAN_FAILED"

_FUTURE_TOLERANCE_S = 120  # allow small clock skew before calling a timestamp FUTURE


def _to_utc(value: Union[str, datetime, None]) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def freshness_state(
    observed_at: Union[str, datetime, None],
    *,
    fresh_within_s: float,
    stale_after_s: float,
    now: Optional[datetime] = None,
    scan_failed: bool = False,
) -> str:
    """Return the governed freshness enum. Unknown/missing/failed never -> CURRENT."""
    if scan_failed:
        return SCAN_FAILED
    dt = _to_utc(observed_at)
    if dt is None:
        return UNKNOWN
    now = (now.astimezone(timezone.utc) if isinstance(now, datetime) and now.tzinfo
           else (now.replace(tzinfo=timezone.utc) if isinstance(now, datetime) else datetime.now(timezone.utc)))
    age = (now - dt).total_seconds()
    if age < -_FUTURE_TOLERANCE_S:
        return FUTURE
    if age <= fresh_within_s:
        return CURRENT
    if age <= stale_after_s:
        return AGING
    return STALE


def is_current(state: str) -> bool:
    return state == CURRENT


__all__ = ["freshness_state", "is_current", "CURRENT", "AGING", "STALE",
           "UNKNOWN", "FUTURE", "SCAN_FAILED"]
