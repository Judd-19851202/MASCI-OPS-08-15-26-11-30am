"""TRACK 16.04 + 16.05 · Transportation eligibility engine.

Pure function. No DB side effects. Phase 1 = base status truth table.
Phase 2 extends via the ``context`` bag to honor packet approval, rate
acknowledgement, expired/needs-correction documents, and the MASCI
Hauler Truck Readiness Inspection.
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


def _ctx_reasons(ctx: Dict[str, Any], record_type: str) -> list:
    """Phase 2 helper. Inspect the context bag and emit canonical
    reasons. Returns a list of reason dicts (possibly empty). Each
    reason can flip eligibility to a non-eligible state."""
    reasons = []

    # Packet readiness (carrier-level rolls up to drivers/trucks of that carrier).
    pkt = ctx.get("packet_status") if ctx else None
    if pkt in ("draft", "sent", "opened", "in_progress", "submitted",
               "pending_review", None):
        if pkt is not None:
            reasons.append({"code": f"packet_{pkt}",
                            "label": f"Carrier packet {pkt.replace('_', ' ')}",
                            "severity": "warn", "source": "packet"})
    elif pkt == "needs_correction":
        reasons.append({"code": "packet_needs_correction",
                        "label": "Carrier packet needs correction",
                        "severity": "block", "source": "packet"})
    elif pkt == "suspended":
        reasons.append({"code": "packet_suspended",
                        "label": "Carrier packet suspended",
                        "severity": "block", "source": "packet"})
    # pkt == "approved" emits no reason.

    # Rate acknowledgement.
    if ctx.get("rate_acknowledged") is False:
        reasons.append({"code": "rate_not_acknowledged",
                        "label": "Current MASCI rate schedule not acknowledged",
                        "severity": "block", "source": "rate"})

    # Document readiness (carrier or driver depending on record type).
    expired = int(ctx.get("expired_required_docs") or 0)
    if expired > 0:
        reasons.append({"code": "documents_expired",
                        "label": f"{expired} required document(s) expired",
                        "severity": "block", "source": "documents"})
    missing = int(ctx.get("missing_required_docs") or 0)
    if missing > 0:
        reasons.append({"code": "documents_missing",
                        "label": f"{missing} required document(s) missing",
                        "severity": "block", "source": "documents"})
    needs_corr = int(ctx.get("docs_needs_correction") or 0)
    if needs_corr > 0:
        reasons.append({"code": "documents_needs_correction",
                        "label": f"{needs_corr} document(s) need correction",
                        "severity": "block", "source": "documents"})

    # Truck readiness inspection (leased trucks only).
    if record_type == "truck":
        ir = ctx.get("inspection_result")
        if ctx.get("inspection_required", True) and (ctx.get("ownership") in
            (None, "leased_carrier", "owner_operator")):
            if ir is None:
                reasons.append({"code": "inspection_missing",
                                "label": "MASCI Hauler Readiness Inspection required",
                                "severity": "block", "source": "inspection"})
            elif ir == "not_ready":
                reasons.append({"code": "inspection_not_ready",
                                "label": "Truck readiness inspection: not ready",
                                "severity": "block", "source": "inspection"})
            elif ir == "expired":
                reasons.append({"code": "inspection_expired",
                                "label": "Truck readiness inspection expired",
                                "severity": "block", "source": "inspection"})
            elif ir == "pending_correction":
                reasons.append({"code": "inspection_pending_correction",
                                "label": "Truck readiness inspection: pending correction",
                                "severity": "block", "source": "inspection"})

    # Driver PPE acknowledgement.
    if record_type == "person":
        if ctx.get("ppe_issue") is True:
            reasons.append({"code": "ppe_issue",
                            "label": "Driver PPE compliance issue",
                            "severity": "block", "source": "ppe"})
        # Track 16.08 · orientation requirement (driver level).
        ostat = ctx.get("orientation_status")
        if ostat == "missing":
            reasons.append({"code": "orientation_missing",
                            "label": "Driver orientation not completed",
                            "severity": "block", "source": "orientation"})
        elif ostat == "expired":
            reasons.append({"code": "orientation_expired",
                            "label": "Driver orientation expired (annual refresher required)",
                            "severity": "block", "source": "orientation"})
        elif ostat == "quiz_failed":
            reasons.append({"code": "orientation_quiz_failed",
                            "label": "Orientation quiz not passed",
                            "severity": "block", "source": "orientation"})

    return reasons


def compute_transport_eligibility(
    record_type: str,
    record: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Phase 1 + Phase 2 truth table.

    record_type in {"carrier","person","truck"}.
    context may include:
      hr_lifecycle_active: bool
      packet_status: str (carrier packet status — rolls up to drivers/trucks of that carrier)
      rate_acknowledged: bool
      expired_required_docs: int
      missing_required_docs: int
      docs_needs_correction: int
      inspection_result: str (for truck only)
      inspection_required: bool (for truck only)
      ownership: str (truck only — determines whether inspection is required)
      ppe_issue: bool (person only)
    """
    ctx = context or {}
    reasons = []
    status = (record or {}).get("status") or "pending_review"
    safety_hold = bool((record or {}).get("safety_hold"))

    state = "eligible"

    # Phase 1 base truth table.
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

    # Phase 2 reasons (only applied if not already overridden by HR-lifecycle).
    ph2 = _ctx_reasons(ctx, record_type)
    if ph2:
        # Any Phase 2 reason with severity=block flips the state.
        blockers = [r for r in ph2 if r.get("severity") == "block"]
        if blockers:
            # If status was already not_dispatchable / suspended / expired,
            # keep that state but append the Phase 2 reasons for visibility.
            if state == "eligible":
                # Pick the most descriptive blocker family.
                first = blockers[0]
                src = first.get("source", "")
                if src == "inspection":
                    state = "needs_correction" if first["code"] == "inspection_pending_correction" else "not_dispatchable"
                    if first["code"] == "inspection_expired":
                        state = "expired"
                elif src == "documents":
                    if first["code"] == "documents_expired":
                        state = "expired"
                    elif first["code"] == "documents_needs_correction":
                        state = "needs_correction"
                    else:
                        state = "needs_correction"
                elif src == "packet":
                    state = "needs_correction" if first["code"] == "packet_needs_correction" else "suspended"
                elif src == "rate":
                    state = "pending_review"
                elif src == "ppe":
                    state = "not_dispatchable"
                else:
                    state = "not_dispatchable"
        reasons.extend(ph2)

    return {
        "state": state,
        "reasons": reasons,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "stale": False,
        "phase": 2,
    }
