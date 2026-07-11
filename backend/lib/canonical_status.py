"""TRACK 28.11 · Canonical Operational Signal vocabulary.

Every diagnostics / OCC / system-health / governance surface must map its
raw signal through this module so summary counts, badges, and evidence
drawers speak the same language.

Canonical states (see `CanonicalStatus` below):
    HEALTHY         current evidence exists and every required threshold passed.
    ATTENTION       current evidence exists and a real, bounded issue needs operator attention.
    CRITICAL        current evidence proves a serious operational condition requiring immediate action.
    UNKNOWN         required evidence cannot currently be obtained.
    STALE           evidence exists but is too old to support a current conclusion.
    DISABLED        the capability is intentionally disabled and is not expected to operate.
    NOT_APPLICABLE  the capability does not apply to MASCI or the current deployment.

DISABLED and NOT_APPLICABLE must NOT be counted as failed, degraded, critical, or unknown.

Usage
-----
>>> from lib.canonical_status import to_canonical, summarize
>>> to_canonical("green")
'HEALTHY'
>>> to_canonical("disabled", mocked=True)
'NOT_APPLICABLE'
>>> summarize([{"canonical_status": "HEALTHY"}, {"canonical_status": "NOT_APPLICABLE"}])
{'healthy': 1, 'attention': 0, 'critical': 0, 'unknown': 0, 'stale': 0,
 'disabled': 0, 'not_applicable': 1, 'total_applicable': 1,
 'total_cards': 2, 'highest': 'HEALTHY'}
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

# ── Canonical vocabulary ────────────────────────────────────────────
HEALTHY = "HEALTHY"
ATTENTION = "ATTENTION"
CRITICAL = "CRITICAL"
UNKNOWN = "UNKNOWN"
STALE = "STALE"
DISABLED = "DISABLED"
NOT_APPLICABLE = "NOT_APPLICABLE"

CANONICAL_STATES = {
    HEALTHY, ATTENTION, CRITICAL, UNKNOWN, STALE, DISABLED, NOT_APPLICABLE,
}

# Severity ordering — highest legitimate status wins in a rollup.
# DISABLED / NOT_APPLICABLE / STALE are informational and never
# escalate the overall severity (a stale card is not automatically
# critical — the aggregator asks for STALE explicitly).
_SEVERITY = {
    HEALTHY: 0,
    NOT_APPLICABLE: 0,
    DISABLED: 0,
    STALE: 1,
    UNKNOWN: 2,
    ATTENTION: 3,
    CRITICAL: 4,
}

# Legacy → canonical mapping. Every historical value across the
# codebase (green/ok/pass/yellow/amber/watch/warning/red/critical/…)
# funnels through this dictionary. New raw values must be added here.
_LEGACY_MAP = {
    # Healthy family
    "green": HEALTHY,
    "ok": HEALTHY,
    "pass": HEALTHY,
    "passed": HEALTHY,
    "healthy": HEALTHY,
    "live": HEALTHY,
    "ready": HEALTHY,
    "go": HEALTHY,
    # Attention family
    "yellow": ATTENTION,
    "amber": ATTENTION,
    "watch": ATTENTION,
    "warning": ATTENTION,
    "warn": ATTENTION,
    "attention": ATTENTION,
    "degraded": ATTENTION,
    "advisory": ATTENTION,
    "at_risk": ATTENTION,
    # Critical family
    "red": CRITICAL,
    "critical": CRITICAL,
    "failed": CRITICAL,
    "fail": CRITICAL,
    "blocker": CRITICAL,
    "error": CRITICAL,
    "no-go": CRITICAL,
    "no_go": CRITICAL,
    # Unknown family
    "unknown": UNKNOWN,
    "unavailable": UNKNOWN,
    "loading": UNKNOWN,
    "none": UNKNOWN,
    "": UNKNOWN,
    # Stale
    "stale": STALE,
    "expired": STALE,
    # Disabled / Not applicable
    "disabled": DISABLED,
    "off": DISABLED,
    "stubbed": NOT_APPLICABLE,
    "mocked": NOT_APPLICABLE,
    "not_configured": DISABLED,
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
    """Convert any raw status value + hint flags to a canonical state.

    Order of precedence:
        1. `applicable=False` → NOT_APPLICABLE (tenant does not use)
        2. `enabled=False` AND `applicable=True` → DISABLED
        3. `mocked=True` AND raw in {disabled, stubbed} → NOT_APPLICABLE
           (an intentional stub for an unused capability)
        4. `stale=True` → STALE (evidence too old)
        5. Legacy lookup on the raw string
    """
    if not applicable:
        return NOT_APPLICABLE
    if mocked and str(raw or "").strip().lower() in {"disabled", "stubbed", "not_configured"}:
        return NOT_APPLICABLE
    if not enabled and applicable:
        return DISABLED
    if stale:
        return STALE
    if isinstance(raw, str) and raw.strip().upper() in CANONICAL_STATES:
        return raw.strip().upper()
    key = (str(raw or "")).strip().lower()
    return _LEGACY_MAP.get(key, UNKNOWN)


def severity(status: str) -> int:
    """Return the severity ordering of a canonical status."""
    return _SEVERITY.get(status, 0)


def highest(states: Iterable[str]) -> str:
    """Return the highest-severity canonical state in an iterable.

    Empty input returns HEALTHY. DISABLED / NOT_APPLICABLE / STALE
    never escalate above ATTENTION on their own — a rollup that is
    all-DISABLED reports HEALTHY (the aggregator surfaces the disabled
    count separately).
    """
    best = HEALTHY
    for s in states:
        if severity(s) > severity(best):
            best = s
    return best


def summarize(cards: List[Dict[str, Any]], *, status_key: str = "canonical_status") -> Dict[str, Any]:
    """Compute canonical counts + highest-legitimate severity from a
    list of card dicts. Every card must carry `canonical_status` (or
    the override key). Cards without one contribute UNKNOWN.

    Returns:
        {
            healthy: N,
            attention: N,
            critical: N,
            unknown: N,
            stale: N,
            disabled: N,
            not_applicable: N,
            total_applicable: (total - disabled - not_applicable),
            total_cards: N,
            highest: CanonicalStatus,
        }

    `total_applicable` excludes DISABLED and NOT_APPLICABLE — the
    caller can safely display "3/5 healthy" using
    `healthy / total_applicable`.
    """
    counts = {
        "healthy": 0, "attention": 0, "critical": 0,
        "unknown": 0, "stale": 0,
        "disabled": 0, "not_applicable": 0,
    }
    field_map = {
        HEALTHY: "healthy", ATTENTION: "attention", CRITICAL: "critical",
        UNKNOWN: "unknown", STALE: "stale",
        DISABLED: "disabled", NOT_APPLICABLE: "not_applicable",
    }
    highest_state = HEALTHY
    for c in cards:
        raw = (c or {}).get(status_key) or (c or {}).get("status")
        state = raw if raw in CANONICAL_STATES else to_canonical(raw)
        counts[field_map.get(state, "unknown")] += 1
        if severity(state) > severity(highest_state):
            highest_state = state
    total = len(cards)
    applicable = total - counts["disabled"] - counts["not_applicable"]
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
    """Evaluate freshness for a signal. Returns:
        {
            evidence_at_iso: str | None,
            evidence_age_seconds: int | None,
            max_age_seconds: int | None,
            fresh: bool | None,   (None if no policy)
            stale: bool,          (True only when policy set + age exceeded)
        }

    A `None` evidence_at with a set max_age_seconds → stale=True (no
    evidence beats stale evidence; the caller may render UNKNOWN
    instead by inspecting `evidence_at is None`).
    """
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
    "HEALTHY", "ATTENTION", "CRITICAL", "UNKNOWN", "STALE",
    "DISABLED", "NOT_APPLICABLE", "CANONICAL_STATES",
    "to_canonical", "severity", "highest", "summarize",
    "freshness_status",
]
