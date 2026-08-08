from __future__ import annotations

from typing import Any, Dict, Optional


CLOSED_CORRECTIVE_ACTION_STATUSES = (
    "Closed",
    "Completed",
    "Cancelled",
    "Canceled",
    "closed",
    "completed",
    "cancelled",
    "canceled",
)


def normalize_corrective_action_due_date(value: Optional[str]) -> Optional[str]:
    raw = "" if value is None else str(value).strip()
    if not raw:
        return None
    return raw[:10]


def open_corrective_action_query(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    query: Dict[str, Any] = {"status": {"$nin": list(CLOSED_CORRECTIVE_ACTION_STATUSES)}}
    if extra:
        query.update(extra)
    return query


def overdue_corrective_action_query(*, today_iso: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    query = open_corrective_action_query({"due_date": {"$nin": [None, ""], "$lt": today_iso}})
    if extra:
        query.update(extra)
    return query


__all__ = [
    "CLOSED_CORRECTIVE_ACTION_STATUSES",
    "normalize_corrective_action_due_date",
    "open_corrective_action_query",
    "overdue_corrective_action_query",
]