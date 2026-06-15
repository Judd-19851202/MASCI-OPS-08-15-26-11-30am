"""
identity_lookup_sync.py — sync employee lookup for PDF / report rendering.

Used by WeasyPrint render paths that run inside a `to_thread()` pool
and cannot await Motor coroutines. Resolves a list of `employee_id`s
to their HR records via a quick PyMongo round-trip.

Doctrine: SAFETY-MEETING-CERT (2026-06-15).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List


def lookup_employees_sync(employee_ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """Return `{employee_id: employee_doc}` for each id supplied.

    Best-effort: returns an empty mapping on any failure so the calling
    renderer can fall back to typed values. NEVER raises.
    """
    ids: List[str] = [str(i).strip() for i in (employee_ids or []) if str(i).strip()]
    if not ids:
        return {}
    try:
        from pymongo import MongoClient

        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        if not mongo_url or not db_name:
            return {}
        # Reuse a module-level client across calls (cheaper than per-call).
        global _CLIENT
        try:
            _CLIENT
        except NameError:
            _CLIENT = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)  # noqa: F841
        client = _CLIENT  # type: ignore[name-defined]
        db = client[db_name]
        rows = list(db.employees.find({"id": {"$in": ids}}, {"_id": 0}))
        return {r["id"]: r for r in rows if r.get("id")}
    except Exception:
        return {}
