"""
masci/identity.py — Track 14.0-HR-IDENTITY backend display formatter.

Single source of truth for rendering an employee's display name across
PDFs, CSV exports, notifications, and any other server-side surface.

Display rule (matches frontend `formatEmployeeIdentity` exactly):
    * "<legal_first> <legal_last> (<preferred>)" when preferred_name set.
    * "<legal_first> <legal_last>" otherwise.
    * Fall back to legacy denormalised `name` / `full_name` /
      `display_name` / `employee_name` when no legal parts are stored.

Never replace legal identity. Never hide it. Never show only nickname.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional


def _str(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def format_employee_identity(obj: Optional[Mapping[str, Any]]) -> str:
    """Format "Legal First Last (Preferred)" for an employee-like dict.

    Accepts anything carrying any subset of:
        legal_first_name · legal_middle_name · legal_last_name ·
        preferred_name · name · full_name · display_name · employee_name
    """
    if not obj:
        return ""
    first = _str(obj.get("legal_first_name"))
    last = _str(obj.get("legal_last_name"))
    preferred = _str(obj.get("preferred_name"))

    legal = ""
    if first or last:
        legal = " ".join(p for p in (first, last) if p)
    else:
        # `display_identity` is the backend-precomputed label and
        # takes precedence over the other denormalised aliases.
        for k in ("display_identity", "name", "full_name", "display_name", "employee_name"):
            v = _str(obj.get(k))
            if v:
                legal = v
                break

    if not legal and not preferred:
        return ""
    if preferred and legal and preferred.lower() != legal.lower():
        return f"{legal} ({preferred})"
    return legal or preferred


def format_legal_name(obj: Optional[Mapping[str, Any]]) -> str:
    """Legal name only — no preferred suffix. Use where space is tight."""
    if not obj:
        return ""
    first = _str(obj.get("legal_first_name"))
    last = _str(obj.get("legal_last_name"))
    if first or last:
        return " ".join(p for p in (first, last) if p)
    for k in ("display_identity", "name", "full_name", "display_name", "employee_name"):
        v = _str(obj.get(k))
        if v:
            return v
    return ""


def identity_search_blob(obj: Optional[Mapping[str, Any]]) -> str:
    """Substring-searchable lowercase blob for an employee record.

    Lets a single ``q in blob`` match resolve "James", "Jimmy",
    "Fisher", "James Fisher", "Jimmy Fisher", "James Michael Fisher"
    to the same employee.
    """
    if not obj:
        return ""
    first = _str(obj.get("legal_first_name"))
    middle = _str(obj.get("legal_middle_name"))
    last = _str(obj.get("legal_last_name"))
    preferred = _str(obj.get("preferred_name"))
    parts: list = [
        first, middle, last, preferred,
        # Pre-joined variants so "James Fisher" / "Jimmy Fisher" /
        # "James Michael Fisher" all become substring-findable even
        # though the legal name pieces are stored separately.
        " ".join(p for p in (first, last) if p),
        " ".join(p for p in (first, middle, last) if p),
        " ".join(p for p in (preferred, last) if p),
        obj.get("name"),
        obj.get("full_name"),
        obj.get("display_name"),
        obj.get("employee_name"),
    ]
    return " ".join(_str(p) for p in parts if _str(p)).lower()
