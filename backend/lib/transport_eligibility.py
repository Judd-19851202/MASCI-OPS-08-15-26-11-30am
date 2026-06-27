"""TRACK 16.04 · Transportation eligibility engine (Phase 1 skeleton).

Pure function. No DB side effects. Future phases extend the truth
table with CDL / medical / Clearinghouse / orientation rules.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Phase-1 valid statuses across carriers/persons/trucks.
VALID_STATUSES = (
    "pending_review", "active", "needs_correction",
    "suspended", "expired", "inactive",
)
# Phase-1 derived eligibility states.
ELIGIBILITY_STATES = (
    "eligible", "pending_review", "needs_correction",
    "expired", "suspended", "not_dispatchable",
)


def compute_transport_eligibility(
    record_type: str,
    record: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Phase 1 truth table.

    record_type in {"carrier","person","truck"}.
    context may include {"hr_lifecycle_active": bool} for masci_employee
    persons so HR-terminated drivers compute not_dispatchable.
    """
    ctx = context or {}
    reasons = []
    status = (record or {}).get("status") or "pending_review"
    safety_hold = bool((record or {}).get("safety_hold"))

    state = "eligible"

    if status == "inactive":
        state = "not_dispatchable"
        reasons.append({"code": "record_inactive", "label": "Record is inactive",
                        "severity": "block", "source": "status"})
    elif safety_hold:
        state = "suspended"
        reasons.append({"code": "safety_hold", "label": "Safety hold engaged",
                        "severity": "block", "source": "safety"})
    elif status == "suspended":
        state = "suspended"
        reasons.append({"code": "status_suspended", "label": "Status: Suspended",
                        "severity": "block", "source": "status"})
    elif status == "expired":
        state = "expired"
        reasons.append({"code": "status_expired", "label": "Qualification expired",
                        "severity": "block", "source": "status"})
    elif status == "needs_correction":
        state = "needs_correction"
        reasons.append({"code": "needs_correction", "label": "Needs correction",
                        "severity": "warn", "source": "status"})
    elif status == "pending_review":
        state = "pending_review"
        reasons.append({"code": "pending_review", "label": "Pending review",
                        "severity": "warn", "source": "status"})

    # MASCI-employee person: HR-terminated/leave overrides everything to not_dispatchable.
    if record_type == "person" and (record or {}).get("kind") == "masci_employee":
        if ctx.get("hr_lifecycle_active") is False:
            state = "not_dispatchable"
            reasons = [{"code": "hr_lifecycle_inactive",
                        "label": "HR employment is not active",
                        "severity": "block", "source": "hr_lifecycle"}]

    return {
        "state": state,
        "reasons": reasons,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "stale": False,
        "phase": 1,
    }
