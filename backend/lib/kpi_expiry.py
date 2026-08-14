"""Wave 5 — CANONICAL EXPIRY / EXPIRING-RATE contract (KPI-EXPIRING-RATE).

The MASCI OPS codebase computes "expired / expiring-soon" buckets in many places
(driver qualifications, safety training, document expirations, trench certs, transport).
Left ungoverned, each site could pick a different boundary, timezone, or missing-date
rule. This module fixes ONE governed convention so the same expiration date yields the
same bucket everywhere.

GOVERNED CONVENTION (do not diverge without an explicit governed reason):
  * Reference date = TODAY in UTC (`datetime.now(timezone.utc).date()`), date-only.
  * days = (expiration_date_utc - today_utc).days  (timestamps are floored to whole days).
  * EXPIRED       -> days < 0   (an item expiring TODAY is NOT yet expired; still valid today).
  * EXPIRING (<=N) -> 0 <= days <= N   (horizon end is INCLUSIVE; today counts as expiring-soon).
  * CURRENT       -> days > max(horizons).
  * MISSING       -> no/blank/unparseable date  (its OWN bucket; NEVER counted as expired,
                     expiring, OR current, and EXCLUDED from the eligible-rate denominator).

RATE SEMANTICS (owner-governed, single answer — components must NOT decide independently):
  * mode="expiring_soon" -> expiring_soon_count / eligible_total   (upcoming renewals load).
  * mode="at_risk"       -> (expired + expiring_soon) / eligible_total  (total non-compliant risk).
  eligible_total = records that HAVE a usable expiration date (missing excluded).
  Empty eligible population -> None (UNKNOWN rate, never 0).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Iterable, List, Optional

# Governed default horizon buckets (days). Callers may pass a subset/superset explicitly.
DEFAULT_HORIZONS = (7, 30, 60, 90)

STATUS_EXPIRED = "Expired"
STATUS_EXPIRING = "Expiring Soon"
STATUS_CURRENT = "Current"
STATUS_MISSING = "Not Applicable"

RATE_MODE_EXPIRING_SOON = "expiring_soon"
RATE_MODE_AT_RISK = "at_risk"
RATE_MODES = (RATE_MODE_EXPIRING_SOON, RATE_MODE_AT_RISK)


def _today_utc(now: Optional[datetime] = None) -> date:
    if now is not None:
        return now.astimezone(timezone.utc).date() if now.tzinfo else now.date()
    return datetime.now(timezone.utc).date()


def _to_date(value: Any) -> Optional[date]:
    """Parse a date/datetime/ISO-string to a UTC date. None/blank/invalid -> None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return (value.astimezone(timezone.utc) if value.tzinfo else value).date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        if "T" in s or " " in s:
            dt = datetime.fromisoformat(s.replace(" ", "T"))
            return (dt.astimezone(timezone.utc) if dt.tzinfo else dt).date()
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def expiry_days(value: Any, *, now: Optional[datetime] = None) -> Optional[int]:
    """Whole days until expiration (UTC date). None if missing/unparseable.
    Negative => already expired; 0 => expires today (still valid today)."""
    d = _to_date(value)
    if d is None:
        return None
    return (d - _today_utc(now)).days


def expiry_status(value: Any, *, horizon_days: int = 60, now: Optional[datetime] = None) -> str:
    """Governed status label: Expired / Expiring Soon / Current / Not Applicable."""
    days = expiry_days(value, now=now)
    if days is None:
        return STATUS_MISSING
    if days < 0:
        return STATUS_EXPIRED
    if days <= horizon_days:
        return STATUS_EXPIRING
    return STATUS_CURRENT


def expiry_bucket(value: Any, *, horizons: Iterable[int] = DEFAULT_HORIZONS,
                  now: Optional[datetime] = None) -> str:
    """Finest governed bucket: 'EXPIRED' | 'EXPIRING_{n}' (smallest matching) | 'CURRENT' | 'MISSING'."""
    days = expiry_days(value, now=now)
    if days is None:
        return "MISSING"
    if days < 0:
        return "EXPIRED"
    for h in sorted(set(horizons)):
        if days <= h:
            return f"EXPIRING_{h}"
    return "CURRENT"


def classify_expiries(values: Iterable[Any], *, horizons: Iterable[int] = DEFAULT_HORIZONS,
                      now: Optional[datetime] = None) -> dict:
    """Count a population of expiration dates into governed buckets.
    Returns counts incl. per-horizon expiring_{n}d (CUMULATIVE: <=n days), expired, current,
    missing, and eligible_total (records with a usable date)."""
    hs = sorted(set(horizons))
    out = {"total": 0, "expired": 0, "current": 0, "missing": 0, "eligible_total": 0}
    for h in hs:
        out[f"expiring_{h}d"] = 0
    for v in values:
        out["total"] += 1
        days = expiry_days(v, now=now)
        if days is None:
            out["missing"] += 1
            continue
        out["eligible_total"] += 1
        if days < 0:
            out["expired"] += 1
            continue
        matched = False
        for h in hs:
            if days <= h:
                out[f"expiring_{h}d"] += 1
                matched = True
        if not matched:
            out["current"] += 1
    return out


def expiring_rate(values: Iterable[Any], *, mode: str, horizon_days: int = 30,
                  now: Optional[datetime] = None, ndigits: int = 1) -> Optional[float]:
    """Governed expiring RATE (percentage). Caller MUST pass an explicit mode.
    eligible_total excludes missing dates; empty eligible population -> None (unknown)."""
    if mode not in RATE_MODES:
        raise ValueError(f"expiring_rate requires an explicit mode {RATE_MODES}; got {mode!r}")
    values = list(values)
    counts = classify_expiries(values, horizons=(horizon_days,), now=now)
    eligible = counts["eligible_total"]
    if eligible <= 0:
        return None
    expiring_soon = counts[f"expiring_{horizon_days}d"]
    numerator = expiring_soon if mode == RATE_MODE_EXPIRING_SOON else (expiring_soon + counts["expired"])
    return round(100.0 * numerator / eligible, ndigits)
