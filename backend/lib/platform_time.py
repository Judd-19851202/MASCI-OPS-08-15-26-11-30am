"""TRACK 27.03 · Canonical backend platform time formatter.

Server-side companion to `frontend/src/lib/platformTime.js`. Used by
PDF renderers, email builders, AI prompt assembly, export writers,
and any backend surface that emits a timestamp string an operator
will read.

Rules
-----
1. Storage is UTC (unchanged — Mongo, audit log, scheduler, etc.).
2. Display is local (this module).
3. Never call `.isoformat()`, `.strftime("%Y-%m-%dT%H:%M:%SZ")`, or
   `utcnow()` in a code path that produces operator-visible strings.
   Use `localize_timestamp()` / `display_timestamp()` instead.

Timezone resolution (highest priority first)
--------------------------------------------
1. Explicit `tz=` argument passed by the caller.
2. Actor / request timezone (extracted from headers or session).
3. Organization default (currently `America/New_York` — swap to
   a per-tenant record when that feature lands).
4. Never UTC.

Log lines and internal machine identifiers may remain UTC; those are
not operator-facing and are outside the scope of Track 27.03.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo


PLATFORM_DEFAULT_TZ = "America/New_York"


def _to_dt(value: Any) -> Optional[datetime]:
    """Coerce any accepted input into a timezone-aware datetime.

    Accepts: datetime, date, ISO string, epoch int/float, None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OSError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # Tolerate trailing "Z" (Python < 3.11 fromisoformat can't).
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def resolve_tz(tz: Optional[str] = None) -> ZoneInfo:
    """Return a ZoneInfo for the requested / default operator zone.
    Never raises — falls back to the platform default."""
    name = tz or PLATFORM_DEFAULT_TZ
    try:
        return ZoneInfo(name)
    except Exception:  # noqa: BLE001
        return ZoneInfo(PLATFORM_DEFAULT_TZ)


def localize_timestamp(
    value: Any, *, tz: Optional[str] = None,
    hour_format: str = "12", fallback: str = "—",
) -> str:
    """Full local date + time.  E.g. "Jul 9, 2026 · 2:53 PM"."""
    dt = _to_dt(value)
    if dt is None:
        return fallback
    local = dt.astimezone(resolve_tz(tz))
    hour_fmt = "%-I:%M %p" if hour_format == "12" else "%H:%M"
    return f"{local.strftime('%b %-d, %Y')} · {local.strftime(hour_fmt)}"


def display_timestamp(value: Any, *, tz: Optional[str] = None,
                      hour_format: str = "12", fallback: str = "—") -> str:
    """Alias for `localize_timestamp` — matches the frontend name.

    Kept as a distinct symbol so grep can prove PDF/email/AI paths
    switched off the raw `strftime` / `isoformat` habit.
    """
    return localize_timestamp(value, tz=tz, hour_format=hour_format, fallback=fallback)


def format_platform_date(value: Any, *, tz: Optional[str] = None,
                         fallback: str = "—") -> str:
    """Date only.  E.g. "Jul 9, 2026"."""
    dt = _to_dt(value)
    if dt is None:
        return fallback
    return dt.astimezone(resolve_tz(tz)).strftime("%b %-d, %Y")


def format_platform_time_only(value: Any, *, tz: Optional[str] = None,
                              hour_format: str = "12", fallback: str = "—") -> str:
    """Time only.  E.g. "2:53 PM" or "14:53"."""
    dt = _to_dt(value)
    if dt is None:
        return fallback
    hour_fmt = "%-I:%M %p" if hour_format == "12" else "%H:%M"
    return dt.astimezone(resolve_tz(tz)).strftime(hour_fmt)


def format_platform_stamp(value: Any, *, tz: Optional[str] = None,
                          hour_format: str = "12", fallback: str = "—") -> str:
    """Compact operator-visible stamp for PDF footers / export
    columns.  E.g. "2026-07-09 2:53 PM EDT"."""
    dt = _to_dt(value)
    if dt is None:
        return fallback
    local = dt.astimezone(resolve_tz(tz))
    hour_fmt = "%-I:%M %p" if hour_format == "12" else "%H:%M"
    zone = local.strftime("%Z") or ""
    return f"{local.strftime('%Y-%m-%d')} {local.strftime(hour_fmt)} {zone}".strip()


def organization_local_time(
    value: Any, *, tz: Optional[str] = None, fallback: str = "—",
) -> str:
    """Alias used by AI prompt assembly and audit viewers to make
    the caller's intent grep-able ('this is what the org sees')."""
    return localize_timestamp(value, tz=tz, fallback=fallback)
