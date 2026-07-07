"""TRACK 24.2 · Phase 3 · Shared MongoDB regex safety helper.

Every `$regex` query in this codebase interpolates user-controlled input
into a regex pattern. Without `re.escape()` this is a NoSQL / ReDoS
injection surface — any user with a session token can construct a
regex meta-character payload that either (a) alters the intended
semantics of the query, or (b) triggers catastrophic backtracking on
the Mongo server (denial-of-service).

Track 24.0 audit flagged this. Track 24.1 escaped the highest-risk
sites individually. Track 24.2 lifts the pattern into a single helper
so the entire platform can be swept consistently and future endpoints
cannot regress.

Usage:

    from lib.mongo_query import safe_regex

    if q:
        needle = safe_regex(q)              # {"$regex": "…", "$options": "i"}
        query["$or"] = [
            {"name":     needle},
            {"employee": needle},
        ]

    if unit_number:
        query["unit_number"] = safe_regex(unit_number, anchor="exact")

Options:
  * `anchor="none"` (default) — substring match: `re.escape(x)`
  * `anchor="prefix"`         — starts-with:    `^re.escape(x)`
  * `anchor="exact"`          — full match:     `^re.escape(x)$`
  * `case_insensitive` (default True)  — sets the "i" Mongo option.

The helper always returns the exact Mongo shape
`{"$regex": str, "$options": str}` so callers can drop it in wherever
they previously interpolated a raw string.
"""
from __future__ import annotations

import re as _re
from typing import Dict, Literal


AnchorKind = Literal["none", "prefix", "exact"]


def safe_regex(
    needle: str,
    *,
    anchor: AnchorKind = "none",
    case_insensitive: bool = True,
) -> Dict[str, str]:
    """Return a Mongo `$regex` clause with ReDoS/injection-safe input.

    Args:
        needle:            User-controlled input. Metacharacters are
                           escaped so `.*` matches the literal string
                           `.*` instead of "everything".
        anchor:            "none" (substring), "prefix" (^…), or
                           "exact" (^…$). Default "none".
        case_insensitive:  Adds the "i" Mongo option (default True).

    Returns:
        `{"$regex": "<escaped>", "$options": "i" | ""}` — drop-in
        replacement for legacy `{"$regex": f"{x}", ...}` patterns.
    """
    if needle is None:
        needle = ""
    escaped = _re.escape(str(needle).strip())
    if anchor == "exact":
        pattern = f"^{escaped}$"
    elif anchor == "prefix":
        pattern = f"^{escaped}"
    else:
        pattern = escaped
    return {
        "$regex": pattern,
        "$options": "i" if case_insensitive else "",
    }


__all__ = ["safe_regex"]
