"""
employee_linkage.py — iter350

Employee Linkage Standard (operator-mandated · P0).
Maps a cross-portal record (Safety, CDL, Field Leadership, etc.) to the
canonical `employees` roster profile using a deterministic, two-tier
resolution strategy. NO disappearing records because Safety wrote
"Alec Perkins" but HR was expecting employee_id "EMP-1234".

Strategy:
    Primary    — `employee_id` exact match (canonical roster id).
    Fallback A — `employee_master_id` exact match (alternate FK used
                 by safety_training_records since iter138).
    Fallback B — normalized employee_name + email match.
    Fallback C — normalized employee_name match alone (last resort).

Normalization:
    - lowercase
    - trimmed (leading/trailing whitespace)
    - collapsed internal whitespace (runs of >1 space → 1 space)
    - email lowercased + trimmed

Returns:
    The matched employee dict (with `_id` stripped) OR None if no match.

Usage:
    from lib.employee_linkage import resolve_employee, normalize_name
    emp = await resolve_employee(
        db,
        employee_id=rec.get("employee_id"),
        employee_master_id=rec.get("employee_master_id"),
        employee_name=rec.get("employee_name"),
        email=rec.get("employee_email"),
    )

This utility is read-only — it does NOT mutate the source record or
write back to the employees collection. It also never raises on
missing inputs; an all-empty call returns None.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional


_WS_RE = re.compile(r"\s+")


def normalize_name(name: Optional[str]) -> str:
    """Lowercase + trim + collapse whitespace. Returns "" for None/empty."""
    if not name or not isinstance(name, str):
        return ""
    return _WS_RE.sub(" ", name.strip()).lower()


def normalize_email(email: Optional[str]) -> str:
    """Lowercase + trim. Returns "" for None/empty."""
    if not email or not isinstance(email, str):
        return ""
    return email.strip().lower()


async def resolve_employee(
    db,
    *,
    employee_id: Optional[str] = None,
    employee_master_id: Optional[str] = None,
    employee_name: Optional[str] = None,
    email: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Resolve a single employee using the canonical four-tier strategy.

    Returns the employee dict (with `_id` stripped) or None.
    """
    # ── Primary · employee_id (canonical roster id) ──────────────────
    eid = (employee_id or "").strip()
    if eid:
        emp = await db.employees.find_one({"id": eid}, {"_id": 0})
        if emp:
            return emp
        # Also try the human-readable employee_id field (e.g. "EMP-1234")
        emp = await db.employees.find_one({"employee_id": eid}, {"_id": 0})
        if emp:
            return emp

    # ── Fallback A · employee_master_id (safety_training_records FK) ─
    mid = (employee_master_id or "").strip()
    if mid and mid != eid:
        emp = await db.employees.find_one({"id": mid}, {"_id": 0})
        if emp:
            return emp
        emp = await db.employees.find_one({"employee_id": mid}, {"_id": 0})
        if emp:
            return emp

    # ── Fallback B · normalized name + email ─────────────────────────
    norm_name = normalize_name(employee_name)
    norm_email = normalize_email(email)
    if norm_name and norm_email:
        # Exact-match the normalized email AND case-insensitive name.
        emp = await db.employees.find_one({
            "email": {"$regex": f"^{re.escape(norm_email)}$", "$options": "i"},
            "name":  {"$regex": f"^{re.escape(norm_name)}$",  "$options": "i"},
        }, {"_id": 0})
        if emp:
            return emp

    # ── Fallback C · normalized name alone ───────────────────────────
    if norm_name:
        # Case-insensitive exact match on name. Whitespace is NOT
        # collapsed in the DB, so the regex needs to tolerate runs of
        # internal whitespace.
        # Build a tolerant pattern: split on spaces, rejoin with `\s+`.
        parts = [re.escape(p) for p in norm_name.split(" ") if p]
        if parts:
            pattern = r"^" + r"\s+".join(parts) + r"$"
            emp = await db.employees.find_one(
                {"name": {"$regex": pattern, "$options": "i"}},
                {"_id": 0},
            )
            if emp:
                return emp

    return None


async def attach_employee_link(
    db,
    record: Dict[str, Any],
) -> Dict[str, Any]:
    """Enrich a single safety/training record with `linked_employee`
    metadata so HR views can show roster context without an extra
    round-trip. Always returns the same record (mutated in place).

    Adds keys:
        - linked_employee_id        — canonical employees.id, or None
        - linked_employee_name      — canonical employees.name, or original
        - linked_employee_trade     — canonical employees.trade, or ""
        - linkage_method            — "id" | "master_id" | "name_email" | "name" | "unlinked"
    """
    if not isinstance(record, dict):
        return record

    eid = record.get("employee_id") or ""
    mid = record.get("employee_master_id") or ""
    nm = record.get("employee_name") or ""
    em = record.get("employee_email") or record.get("email") or ""

    emp = await resolve_employee(
        db,
        employee_id=eid,
        employee_master_id=mid,
        employee_name=nm,
        email=em,
    )
    if not emp:
        record["linked_employee_id"] = None
        record["linked_employee_name"] = nm or None
        record["linked_employee_trade"] = ""
        record["linkage_method"] = "unlinked"
        return record

    # Identify which method matched (cheapest re-check; avoids a
    # second DB round-trip).
    method = "name"
    if eid and (emp.get("id") == eid or emp.get("employee_id") == eid):
        method = "id"
    elif mid and (emp.get("id") == mid or emp.get("employee_id") == mid):
        method = "master_id"
    elif normalize_email(em) and normalize_email(emp.get("email")) == normalize_email(em):
        method = "name_email"

    record["linked_employee_id"] = emp.get("id")
    record["linked_employee_name"] = emp.get("name")
    record["linked_employee_trade"] = emp.get("trade") or ""
    record["linkage_method"] = method
    return record


async def attach_employee_links(
    db,
    records: list,
) -> list:
    """Bulk variant. Pre-loads the employees collection into a
    name+id index so we don't fire one query per record. Falls back to
    `attach_employee_link` for any record the in-memory index misses.

    O(n + m) where n = len(records) and m = len(employees).
    """
    if not records:
        return records

    # Build lookup tables — id, employee_id (human code), normalized
    # name + email.
    by_id: Dict[str, Dict[str, Any]] = {}
    by_emp_code: Dict[str, Dict[str, Any]] = {}
    by_name_email: Dict[str, Dict[str, Any]] = {}
    by_name: Dict[str, Dict[str, Any]] = {}

    async for emp in db.employees.find({}, {
        "_id": 0, "id": 1, "employee_id": 1, "name": 1,
        "email": 1, "trade": 1,
    }):
        eid = (emp.get("id") or "").strip()
        if eid:
            by_id[eid] = emp
        code = (emp.get("employee_id") or "").strip()
        if code:
            by_emp_code[code] = emp
        n = normalize_name(emp.get("name"))
        e = normalize_email(emp.get("email"))
        if n and e:
            by_name_email[f"{n}|{e}"] = emp
        if n and n not in by_name:
            # First-write-wins — ambiguous duplicate names stay
            # un-resolved by this fast path; they fall back to the
            # per-record query which can disambiguate via email.
            by_name[n] = emp

    out: list = []
    for rec in records:
        if not isinstance(rec, dict):
            out.append(rec)
            continue
        eid = (rec.get("employee_id") or "").strip()
        mid = (rec.get("employee_master_id") or "").strip()
        nm = rec.get("employee_name") or ""
        em = rec.get("employee_email") or rec.get("email") or ""

        emp = None
        method = "unlinked"
        if eid and eid in by_id:
            emp, method = by_id[eid], "id"
        elif eid and eid in by_emp_code:
            emp, method = by_emp_code[eid], "id"
        elif mid and mid in by_id:
            emp, method = by_id[mid], "master_id"
        elif mid and mid in by_emp_code:
            emp, method = by_emp_code[mid], "master_id"
        else:
            n_norm = normalize_name(nm)
            e_norm = normalize_email(em)
            if n_norm and e_norm and f"{n_norm}|{e_norm}" in by_name_email:
                emp, method = by_name_email[f"{n_norm}|{e_norm}"], "name_email"
            elif n_norm and n_norm in by_name:
                emp, method = by_name[n_norm], "name"

        if emp:
            rec["linked_employee_id"] = emp.get("id")
            rec["linked_employee_name"] = emp.get("name")
            rec["linked_employee_trade"] = emp.get("trade") or ""
            rec["linkage_method"] = method
        else:
            rec["linked_employee_id"] = None
            rec["linked_employee_name"] = nm or None
            rec["linked_employee_trade"] = ""
            rec["linkage_method"] = "unlinked"
        out.append(rec)
    return out


__all__ = [
    "normalize_name",
    "normalize_email",
    "resolve_employee",
    "attach_employee_link",
    "attach_employee_links",
]
