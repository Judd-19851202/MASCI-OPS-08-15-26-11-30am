"""Checkpoint D2 · Canonical runtime truth vocabulary.

Every runtime truth surface must map its local/raw signal through this
module so health, trust, admin, and governance payloads expose one
shared status language.

Approved canonical statuses:
    VERIFIED
    MISMATCH
    UNVERIFIABLE
    DEGRADED
    NOT_APPLICABLE
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

VERIFIED = "VERIFIED"
MISMATCH = "MISMATCH"
UNVERIFIABLE = "UNVERIFIABLE"
DEGRADED = "DEGRADED"
NOT_APPLICABLE = "NOT_APPLICABLE"

HEALTHY = VERIFIED
ATTENTION = DEGRADED
CRITICAL = MISMATCH
UNKNOWN = UNVERIFIABLE
STALE = DEGRADED
DISABLED = NOT_APPLICABLE

CANONICAL_STATES = {
    VERIFIED,
    MISMATCH,
    UNVERIFIABLE,
    DEGRADED,
    NOT_APPLICABLE,
}

_SEVERITY = {
    NOT_APPLICABLE: 0,
    VERIFIED: 1,
    DEGRADED: 2,
    UNVERIFIABLE: 3,
    MISMATCH: 4,
}

_LEGACY_MAP = {
    "green": VERIFIED,
    "ok": VERIFIED,
    "pass": VERIFIED,
    "passed": VERIFIED,
    "healthy": VERIFIED,
    "live": VERIFIED,
    "ready": VERIFIED,
    "go": VERIFIED,
    "configured": VERIFIED,
    "reachable": VERIFIED,
    "live_verified": VERIFIED,
    "active": VERIFIED,
    "verified": VERIFIED,
    "yellow": DEGRADED,
    "amber": DEGRADED,
    "watch": DEGRADED,
    "warning": DEGRADED,
    "warn": DEGRADED,
    "attention": DEGRADED,
    "degraded": DEGRADED,
    "advisory": DEGRADED,
    "at_risk": DEGRADED,
    "partial": DEGRADED,
    "partial_config": DEGRADED,
    "configured_via_universal": DEGRADED,
    "idle": DEGRADED,
    "stale": DEGRADED,
    "expired": DEGRADED,
    "red": MISMATCH,
    "critical": MISMATCH,
    "failed": MISMATCH,
    "fail": MISMATCH,
    "blocker": MISMATCH,
    "error": MISMATCH,
    "no-go": MISMATCH,
    "no_go": MISMATCH,
    "missing_config": MISMATCH,
    "missing_secret": MISMATCH,
    "unreachable": MISMATCH,
    "not_connected": MISMATCH,
    "mismatch": MISMATCH,
    "unknown": UNVERIFIABLE,
    "unavailable": UNVERIFIABLE,
    "loading": UNVERIFIABLE,
    "none": UNVERIFIABLE,
    "": UNVERIFIABLE,
    "disabled": NOT_APPLICABLE,
    "off": NOT_APPLICABLE,
    "stubbed": NOT_APPLICABLE,
    "mocked": NOT_APPLICABLE,
    "not_configured": NOT_APPLICABLE,
    "not_applicable": NOT_APPLICABLE,
    "n/a": NOT_APPLICABLE,
}


def to_canonical(
    raw: Any,
    *,
    mocked: bool = False,
    applicable: bool = True,
    enabled: bool = True,
    stale: bool = False,
) -> str:
    if not applicable:
        return NOT_APPLICABLE
    if mocked and str(raw or "").strip().lower() in {"disabled", "stubbed", "not_configured"}:
        return NOT_APPLICABLE
    if not enabled and applicable:
        return NOT_APPLICABLE
    if stale:
        return DEGRADED
    if isinstance(raw, str) and raw.strip().upper() in CANONICAL_STATES:
        return raw.strip().upper()
    key = (str(raw or "")).strip().lower()
    return _LEGACY_MAP.get(key, UNVERIFIABLE)


def severity(status: str) -> int:
    return _SEVERITY.get(status, 0)


def highest(states: Iterable[str]) -> str:
    best = NOT_APPLICABLE
    for s in states:
        if severity(s) > severity(best):
            best = s
    return best


def summarize(cards: List[Dict[str, Any]], *, status_key: str = "canonical_status") -> Dict[str, Any]:
    counts = {
        "verified": 0,
        "mismatch": 0,
        "unverifiable": 0,
        "degraded": 0,
        "not_applicable": 0,
    }
    field_map = {
        VERIFIED: "verified",
        MISMATCH: "mismatch",
        UNVERIFIABLE: "unverifiable",
        DEGRADED: "degraded",
        NOT_APPLICABLE: "not_applicable",
    }
    highest_state = NOT_APPLICABLE
    for c in cards:
        raw = (c or {}).get(status_key) or (c or {}).get("status")
        state = raw if raw in CANONICAL_STATES else to_canonical(raw)
        counts[field_map.get(state, "unverifiable")] += 1
        if severity(state) > severity(highest_state):
            highest_state = state
    total = len(cards)
    applicable = total - counts["not_applicable"]
    return {
        **counts,
        "total_applicable": applicable,
        "total_cards": total,
        "highest": highest_state,
    }


def freshness_status(
    *,
    evidence_at: Optional[datetime | int | float | str],
    max_age_seconds: Optional[int],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    dt: Optional[datetime] = None
    if isinstance(evidence_at, datetime):
        dt = evidence_at if evidence_at.tzinfo else evidence_at.replace(tzinfo=timezone.utc)
    elif isinstance(evidence_at, (int, float)):
        try:
            dt = datetime.fromtimestamp(float(evidence_at), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            dt = None
    elif isinstance(evidence_at, str):
        try:
            iso = evidence_at.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            dt = None
    age = int((now - dt).total_seconds()) if dt else None
    if max_age_seconds is None:
        stale = False
        fresh = None
    elif age is None:
        stale = True
        fresh = False
    else:
        stale = age > max_age_seconds
        fresh = not stale
    return {
        "evidence_at_iso": dt.isoformat() if dt else None,
        "evidence_age_seconds": age,
        "max_age_seconds": max_age_seconds,
        "fresh": fresh,
        "stale": stale,
    }


__all__ = [
    "VERIFIED",
    "MISMATCH",
    "UNVERIFIABLE",
    "DEGRADED",
    "NOT_APPLICABLE",
    "CANONICAL_STATES",
    "to_canonical",
    "severity",
    "highest",
    "summarize",
    "freshness_status",
]