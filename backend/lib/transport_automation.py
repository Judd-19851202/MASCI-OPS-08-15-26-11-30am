"""TRACK 16.10 · Transportation Automation Engine.

The proactive transportation operating system. Pure async runner; safe
in dry-run; idempotent across the deterministic event_key space.

Public API:
    run_transportation_automation(db, *, now=None, dry_run=False)

The runner:
* scans every transportation-tracked compliance item
* computes due-date + reminder-window for each
* dedupes via ``transport_automation_events`` (event_key uniqueness)
* materialises one Action Queue row per actionable event
* recomputes eligibility for affected entities (pure compute, never
  mutates source documents)
* fans out email notifications through the existing Email Routing v2
  + ``fsi_email_sender`` primitives (NO new sender, NO SMS / push)
* tolerates missing route config — audits ``needs_configuration`` and
  carries on
* writes a single ``transport_automation_runs`` row per run
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

TENANT = "masci"

# -- reminder windows + severity ---------------------------------------------
REMINDER_WINDOWS: Tuple[Tuple[str, int, str], ...] = (
    # (window_key, days_threshold, severity)
    ("30_days", 30, "info"),
    ("14_days", 14, "advisory"),
    ("7_days", 7, "advisory"),
    ("1_day", 1, "action_required"),
    ("due_today", 0, "action_required"),
    ("overdue", -1, "urgent"),
)

# After being overdue once we re-notify every 7 days.
OVERDUE_REPEAT_DAYS = 7


def _now_iso(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        if isinstance(s, datetime):
            return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


def _reminder_for(due: datetime, now: datetime) -> Optional[Tuple[str, str]]:
    """Return (window_key, severity) for a given due-date / now.

    Returns None if the item is more than 30 days out — nothing to do yet.
    For overdue items, ``window_key`` is ``overdue`` (severity ``urgent``)
    on the first day past due AND then re-emitted every ``OVERDUE_REPEAT_DAYS``.
    """
    days = (due.date() - now.date()).days
    if days > 30:
        return None
    if days <= 0:
        # First-day past due → overdue. After that, repeat every 7 days
        # by using a deterministic event_key that includes the
        # overdue-bucket index.
        return ("overdue", "urgent")
    if days <= 1:
        return ("1_day", "action_required")
    if days <= 7:
        return ("7_days", "advisory")
    if days <= 14:
        return ("14_days", "advisory")
    return ("30_days", "info")


def overdue_bucket(due: datetime, now: datetime) -> int:
    """How many OVERDUE_REPEAT_DAYS buckets past due. 0 = first bucket."""
    days_past = (now.date() - due.date()).days
    if days_past <= 0:
        return 0
    return days_past // OVERDUE_REPEAT_DAYS


def make_event_key(*, item_kind: str, entity_id: str, window: str,
                    due_iso: str, overdue_bucket_idx: int = 0) -> str:
    """Deterministic event key. Identical inputs ⇒ identical hash ⇒
    dedupe is automatic across runs."""
    parts = [item_kind, entity_id, window, due_iso]
    if window == "overdue":
        parts.append(f"bucket{overdue_bucket_idx}")
    raw = ":".join(parts)
    h = hashlib.sha1(raw.encode()).hexdigest()[:16]
    return f"{item_kind}:{entity_id}:{window}:{h}"


def kind_to_route(kind: str, severity: str, window: str) -> str:
    """Map (kind, severity, window) to a Track 16.09 / 16.10 route key."""
    if kind == "truck_inspection":
        return ("TRANSPORT_ANNUAL_INSPECTION_OVERDUE" if window == "overdue"
                else "TRANSPORT_ANNUAL_INSPECTION_REMINDER")
    if kind == "orientation":
        return ("TRANSPORT_ORIENTATION_OVERDUE" if window == "overdue"
                else "TRANSPORT_ORIENTATION_EXPIRING")
    if kind == "carrier_packet":
        return "TRANSPORT_PACKET_PENDING_REVIEW"
    if kind == "carrier_packet_correction":
        return "TRANSPORT_PACKET_NEEDS_CORRECTION"
    if kind == "eligibility_changed":
        return "TRANSPORT_ELIGIBILITY_CHANGED"
    if kind == "override_approved":
        return "TRANSPORT_OVERRIDE_APPROVED"
    if kind == "override_expiring":
        return "TRANSPORT_OVERRIDE_EXPIRING"
    if kind in ("driver_cdl", "driver_medical", "driver_doc",
                 "driver_clearinghouse"):
        return ("TRANSPORT_DOC_OVERDUE" if window == "overdue"
                else "TRANSPORT_DOC_EXPIRING")
    if kind.startswith("carrier_"):
        return ("TRANSPORT_DOC_OVERDUE" if window == "overdue"
                else "TRANSPORT_DOC_EXPIRING")
    return "TRANSPORT_DOC_EXPIRING"


# ============================================================================
# Compliance scanners — each returns a list of action dicts.
# Each action dict shape:
#   { item_kind, entity_type, entity_id, entity_label, due_date }
# ============================================================================
async def _scan_truck_inspections(db) -> List[Dict[str, Any]]:
    """Find every transport_truck with an annual readiness inspection
    that has a known expires_at."""
    items: List[Dict[str, Any]] = []
    trucks = await db.transport_trucks.find(
        {"tenant": TENANT}).to_list(2000)
    truck_map = {t["id"]: t for t in trucks}
    cur = db.transport_truck_inspections.find({"tenant": TENANT})
    inspections = await cur.to_list(5000)
    # Latest active inspection per truck.
    latest_by_truck: Dict[str, Dict[str, Any]] = {}
    for ins in inspections:
        tid = ins.get("truck_id")
        if not tid:
            continue
        prev = latest_by_truck.get(tid)
        if (not prev) or (ins.get("performed_at") or "") > (prev.get("performed_at") or ""):
            latest_by_truck[tid] = ins
    for tid, t in truck_map.items():
        if t.get("kind") != "leased_truck":
            continue  # MASCI's own trucks tracked elsewhere
        ins = latest_by_truck.get(tid)
        if not ins or not ins.get("valid_until"):
            # Missing inspection — surface as immediate action.
            items.append({
                "item_kind": "truck_inspection",
                "entity_type": "truck", "entity_id": tid,
                "entity_label": t.get("unit_number") or t.get("license_plate") or tid,
                "due_date": _now_iso(),
                "status_note": "missing",
            })
            continue
        items.append({
            "item_kind": "truck_inspection",
            "entity_type": "truck", "entity_id": tid,
            "entity_label": t.get("unit_number") or t.get("license_plate") or tid,
            "due_date": ins["valid_until"],
        })
    return items


async def _scan_orientation(db) -> List[Dict[str, Any]]:
    """Surface drivers whose orientation expires soon / is expired /
    is missing."""
    items: List[Dict[str, Any]] = []
    persons = await db.transport_persons.find(
        {"tenant": TENANT}).to_list(2000)
    try:
        from lib.transport_orientation_status import (
            derive_orientation_status,
        )
    except Exception:  # noqa: BLE001
        return items
    for p in persons:
        os_ = await derive_orientation_status(db, p["id"])
        status = os_["orientation_status"]
        if status == "current" and os_.get("latest_expires_at"):
            items.append({
                "item_kind": "orientation",
                "entity_type": "person", "entity_id": p["id"],
                "entity_label": f"{p.get('first_name','')} {p.get('last_name','')}".strip() or p["id"],
                "due_date": os_["latest_expires_at"],
            })
        elif status in ("missing", "expired"):
            items.append({
                "item_kind": "orientation",
                "entity_type": "person", "entity_id": p["id"],
                "entity_label": f"{p.get('first_name','')} {p.get('last_name','')}".strip() or p["id"],
                "due_date": _now_iso(),
                "status_note": status,
            })
    return items


async def _scan_driver_documents(db) -> List[Dict[str, Any]]:
    """Surface driver CDL / Medical / Clearinghouse expirations."""
    items: List[Dict[str, Any]] = []
    docs = await db.driver_documents.find(
        {"tenant": TENANT}).to_list(5000)
    for d in docs:
        if not d.get("expires_at"):
            continue
        kind = d.get("doc_kind") or "driver_doc"
        item_kind = {"cdl": "driver_cdl",
                      "medical_card": "driver_medical",
                      "clearinghouse": "driver_clearinghouse"}.get(kind, "driver_doc")
        items.append({
            "item_kind": item_kind,
            "entity_type": "person",
            "entity_id": d.get("transport_person_id") or d.get("driver_id") or "unknown",
            "entity_label": d.get("doc_label") or d.get("doc_kind") or "Driver document",
            "due_date": d["expires_at"],
        })
    return items


async def _scan_carrier_documents(db) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    docs = await db.carrier_documents.find(
        {"tenant": TENANT}).to_list(5000)
    for d in docs:
        if not d.get("expires_at"):
            continue
        items.append({
            "item_kind": f"carrier_{(d.get('doc_kind') or 'doc')}",
            "entity_type": "carrier", "entity_id": d.get("carrier_id") or "unknown",
            "entity_label": d.get("doc_label") or d.get("doc_kind") or "Carrier document",
            "due_date": d["expires_at"],
        })
    return items


async def _scan_packets(db) -> List[Dict[str, Any]]:
    """Pending-review packets older than 7 days, and needs-correction
    packets surface immediately."""
    items: List[Dict[str, Any]] = []
    pkts = await db.transport_packet_submissions.find(
        {"tenant": TENANT}).to_list(2000)
    now = datetime.now(timezone.utc)
    for pkt in pkts:
        st = pkt.get("status")
        if st == "needs_correction":
            items.append({
                "item_kind": "carrier_packet_correction",
                "entity_type": "carrier",
                "entity_id": pkt.get("carrier_id") or "unknown",
                "entity_label": pkt.get("carrier_label") or pkt.get("carrier_id") or "Carrier",
                "due_date": _now_iso(),
            })
        elif st == "submitted":
            submitted = _parse_dt(pkt.get("submitted_at"))
            if submitted and (now - submitted).days >= 7:
                items.append({
                    "item_kind": "carrier_packet",
                    "entity_type": "carrier",
                    "entity_id": pkt.get("carrier_id") or "unknown",
                    "entity_label": pkt.get("carrier_label") or pkt.get("carrier_id") or "Carrier",
                    "due_date": submitted.isoformat(),
                })
    return items


async def _scan_overrides(db) -> List[Dict[str, Any]]:
    """Override approved (info) + override expiring within 24h (advisory)."""
    items: List[Dict[str, Any]] = []
    cur = db.transport_dispatch_overrides.find(
        {"tenant": TENANT, "status": "approved"})
    rows = await cur.to_list(2000)
    now = datetime.now(timezone.utc)
    for row in rows:
        expires = _parse_dt(row.get("expires_at"))
        if not expires:
            continue
        if expires < now:
            continue
        # Approved → emit once (deduped via event_key on approved_at).
        items.append({
            "item_kind": "override_approved",
            "entity_type": "dispatch_override", "entity_id": row["id"],
            "entity_label": (row.get("driver_id") or row.get("truck_id") or row["id"])[:24],
            "due_date": row.get("approved_at") or _now_iso(),
        })
        if (expires - now).total_seconds() <= 86400:
            items.append({
                "item_kind": "override_expiring",
                "entity_type": "dispatch_override", "entity_id": row["id"],
                "entity_label": (row.get("driver_id") or row.get("truck_id") or row["id"])[:24],
                "due_date": row["expires_at"],
            })
    return items


# ============================================================================
# Email send adapter — pilot-aware, dry-run aware.
# ============================================================================
async def _send_via_routing_v2(
    db, *, route_key: str, subject: str, body_html: str,
    dry_run: bool, calling_module: str,
) -> Dict[str, Any]:
    """Returns {status, dry_run, recipients_count, audit_id?}.
    Never raises."""
    try:
        from email_routing_v2 import resolve_and_audit
    except Exception as e:  # noqa: BLE001
        return {"status": "errored", "error": str(e)[:160],
                "dry_run": dry_run, "recipients_count": 0}
    # Look up enabled flag.
    route = await db.email_routes.find_one(
        {"tenant_key": TENANT, "route_key": route_key})
    enabled = bool((route or {}).get("enabled"))
    effective_dry_run = dry_run or (not enabled)
    try:
        resolution = await resolve_and_audit(
            db, route_key=route_key, legacy_provider=None,
            subject=subject,
            calling_module=calling_module,
            dry_run=effective_dry_run,
        )
    except Exception as e:  # noqa: BLE001
        return {"status": "errored", "error": str(e)[:160],
                "dry_run": effective_dry_run, "recipients_count": 0}
    recipients = list(resolution.to) if resolution and resolution.to else []
    if not recipients:
        # Audit needs_configuration row.
        try:
            await db.email_routing_audit_v2.insert_one({
                "route_key": route_key, "tenant_key": TENANT,
                "source": "transport_automation",
                "resolved_to_count": 0,
                "subject": (subject or "")[:240],
                "status": "needs_configuration",
                "calling_module": calling_module,
                "dry_run": True, "ts": _now_iso(),
            })
        except Exception:  # noqa: BLE001
            pass
        return {"status": "needs_configuration",
                "dry_run": True, "recipients_count": 0}
    if effective_dry_run:
        return {"status": "dry_run", "dry_run": True,
                "recipients_count": len(recipients)}
    # Real send.
    try:
        from lib.fsi_email_sender import fsi_send_email  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return {"status": "errored", "error": str(e)[:160],
                "dry_run": False, "recipients_count": len(recipients)}
    sent_ids = []
    for to_addr in recipients:
        try:
            provider = await fsi_send_email(
                to_addr, subject or "MASCI Transportation update",
                body_html, db=db)
            sent_ids.append((provider or {}).get("id"))
            await db.email_routing_audit_v2.insert_one({
                "route_key": route_key, "tenant_key": TENANT,
                "source": "transport_automation",
                "resolved_to_count": 1,
                "subject": (subject or "")[:240],
                "status": "sent",
                "resend_message_id": (provider or {}).get("id"),
                "calling_module": calling_module,
                "dry_run": False, "ts": _now_iso(),
            })
        except Exception as e:  # noqa: BLE001
            await db.email_routing_audit_v2.insert_one({
                "route_key": route_key, "tenant_key": TENANT,
                "source": "transport_automation",
                "resolved_to_count": 1,
                "subject": (subject or "")[:240],
                "status": "failed",
                "error": str(e)[:160],
                "calling_module": calling_module,
                "dry_run": False, "ts": _now_iso(),
            })
            return {"status": "errored", "error": str(e)[:160],
                    "dry_run": False, "recipients_count": len(recipients)}
    return {"status": "sent", "dry_run": False,
            "recipients_count": len(recipients),
            "resend_ids": sent_ids}


def _render_email_html(*, kind_label: str, entity_label: str,
                       window: str, due_date: str, body_note: str) -> str:
    """Non-punitive, MASCI-branded HTML template."""
    return (
        "<div style='font-family:Helvetica,Arial,sans-serif;"
        "max-width:560px;margin:0 auto;padding:24px;"
        "border:1px solid #e2e8f0;border-radius:8px'>"
        "<h2 style='color:#92400e;margin:0 0 8px'>MASCI Transportation</h2>"
        f"<div style='font-size:14px;color:#0f172a'>{kind_label} · {entity_label}</div>"
        f"<div style='font-size:13px;color:#334155;margin-top:4px'>Due window: {window} · {due_date[:10]}</div>"
        f"<div style='font-size:13px;color:#0f172a;margin-top:12px'>{body_note}</div>"
        "<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0' />"
        "<div style='font-size:11px;color:#64748b'>"
        "Automated message from the MASCI Operations Platform. "
        "Action required does not imply punitive action — it indicates a "
        "tracked compliance item that needs your attention to maintain "
        "dispatch eligibility.</div></div>"
    )


# ============================================================================
# Eligibility recompute helper.
# ============================================================================
async def _maybe_recompute_eligibility(db, *, entity_type: str,
                                       entity_id: str
                                       ) -> Optional[Dict[str, Any]]:
    """Pure-derive then upsert via the existing transportation router.
    Returns the diff vs the prior state, or None if nothing changed."""
    if entity_type not in ("person", "truck", "carrier"):
        return None
    coll_map = {"person": "transport_persons",
                "truck": "transport_trucks",
                "carrier": "carriers"}
    rec = await db[coll_map[entity_type]].find_one(
        {"id": entity_id, "tenant": TENANT})
    if not rec:
        return None
    prior = await db.transport_eligibility_state.find_one(
        {"target_type": entity_type, "target_id": entity_id,
         "tenant": TENANT})
    prior_state = (prior or {}).get("state")
    # Build context.
    ctx: Dict[str, Any] = {}
    if entity_type == "person":
        try:
            from lib.transport_orientation_status import (
                derive_orientation_status,
            )
            o = await derive_orientation_status(db, entity_id)
            ctx["orientation_status"] = o["orientation_status"]
        except Exception:  # noqa: BLE001
            pass
    try:
        from lib.transport_eligibility import compute_transport_eligibility
        result = compute_transport_eligibility(entity_type, rec, ctx)
    except Exception:  # noqa: BLE001
        return None
    new_state = result.get("state")
    if new_state == prior_state and prior:
        return None
    # Upsert via collection directly (no HTTP).
    now = _now_iso()
    upd = {
        "tenant": TENANT, "target_type": entity_type, "target_id": entity_id,
        "state": new_state, "reasons": result.get("reasons") or [],
        "updated_at": now, "updated_by": "transport_automation",
    }
    if not prior:
        upd["created_at"] = now
        upd["id"] = uuid.uuid4().hex
        await db.transport_eligibility_state.insert_one(upd)
    else:
        await db.transport_eligibility_state.update_one(
            {"_id": prior["_id"]}, {"$set": upd})
    return {"target_type": entity_type, "target_id": entity_id,
            "prior_state": prior_state, "new_state": new_state,
            "reasons": [r.get("code") for r in upd["reasons"]]}


# ============================================================================
# Public runner
# ============================================================================
async def run_transportation_automation(
    db, *, now: Optional[datetime] = None, dry_run: bool = False,
    triggered_by: str = "scheduler",
) -> Dict[str, Any]:
    """Idempotent, dedupe-safe automation pass."""
    now = now or datetime.now(timezone.utc)
    started_at = _now_iso(now)
    counts = {
        "items_scanned": 0, "actions_created": 0,
        "emails_attempted": 0, "emails_sent": 0,
        "emails_needs_configuration": 0, "eligibility_updates": 0,
        "errors": 0,
    }
    actions_emitted: List[Dict[str, Any]] = []
    errors: List[str] = []

    # 1. Scan compliance items.
    scanners = (
        ("truck_inspections", _scan_truck_inspections),
        ("orientation", _scan_orientation),
        ("driver_documents", _scan_driver_documents),
        ("carrier_documents", _scan_carrier_documents),
        ("packets", _scan_packets),
        ("overrides", _scan_overrides),
    )
    all_items: List[Dict[str, Any]] = []
    for name, fn in scanners:
        try:
            chunk = await fn(db)
            all_items.extend(chunk)
        except Exception as e:  # noqa: BLE001
            errors.append(f"scanner={name}: {e}")
            counts["errors"] += 1
    counts["items_scanned"] = len(all_items)

    # Track entities whose eligibility may need recompute.
    affected_entities: set = set()

    # 2. Per-item: compute reminder window, dedupe, materialise action +
    #    fire email.
    for it in all_items:
        try:
            due_dt = _parse_dt(it.get("due_date"))
            if not due_dt:
                continue
            reminder = _reminder_for(due_dt, now)
            if not reminder:
                continue
            window, severity = reminder
            bucket = (
                overdue_bucket(due_dt, now) if window == "overdue" else 0
            )
            event_key = make_event_key(
                item_kind=it["item_kind"], entity_id=it["entity_id"],
                window=window, due_iso=due_dt.date().isoformat(),
                overdue_bucket_idx=bucket,
            )
            route_key = kind_to_route(it["item_kind"], severity, window)
            # Dedupe.
            existing = await db.transport_automation_events.find_one(
                {"tenant": TENANT, "event_key": event_key})
            if existing:
                continue
            # In dry-run mode we PREVIEW only — never write event rows
            # so the same dry-run can be replayed indefinitely. Live
            # runs persist for dedupe.
            if dry_run:
                counts["actions_created"] += 1
                counts["emails_attempted"] += 1
                counts["emails_needs_configuration"] += 1  # treated as preview
                actions_emitted.append({
                    "preview": True,
                    "event_key": event_key,
                    "entity_type": it["entity_type"],
                    "entity_id": it["entity_id"],
                    "item_kind": it["item_kind"],
                    "severity": severity,
                    "window": window,
                    "route_key": route_key,
                    "title": _action_title(it["item_kind"], window,
                                            it.get("entity_label", "")),
                    "due_date": due_dt.isoformat(),
                })
                continue
            # Materialise.
            event_id = uuid.uuid4().hex
            event_doc = {
                "id": event_id, "tenant": TENANT,
                "event_key": event_key,
                "entity_type": it["entity_type"],
                "entity_id": it["entity_id"],
                "route_key": route_key,
                "reminder_window": window,
                "due_date": due_dt.isoformat(),
                "status": "created",
                "dry_run": dry_run,
                "email_audit_id": None,
                "created_at": _now_iso(now),
                "updated_at": _now_iso(now),
                "details": {
                    "item_kind": it["item_kind"],
                    "entity_label": it.get("entity_label", ""),
                    "severity": severity,
                    "overdue_bucket": bucket,
                    "status_note": it.get("status_note"),
                },
            }
            await db.transport_automation_events.insert_one(event_doc.copy())

            # Action queue row — one per OPEN event_key.
            existing_action = await db.transport_action_items.find_one(
                {"tenant": TENANT, "related_event_key": event_key,
                  "status": {"$in": ["open", "in_progress"]}})
            if not existing_action:
                action = {
                    "id": uuid.uuid4().hex, "tenant": TENANT,
                    "source": "automation",
                    "action_type": it["item_kind"],
                    "severity": severity,
                    "entity_type": it["entity_type"],
                    "entity_id": it["entity_id"],
                    "title": _action_title(it["item_kind"], window,
                                            it.get("entity_label", "")),
                    "description": _action_description(it, window),
                    "due_date": due_dt.isoformat(),
                    "status": "open",
                    "assigned_role": _assigned_role(it["item_kind"]),
                    "assigned_user_id": None,
                    "related_route_key": route_key,
                    "related_event_key": event_key,
                    "created_at": _now_iso(now),
                    "updated_at": _now_iso(now),
                    "resolved_at": None, "resolved_by": None,
                }
                await db.transport_action_items.insert_one(action.copy())
                counts["actions_created"] += 1
                action.pop("_id", None)
                actions_emitted.append(action)

            # Email fan-out.
            counts["emails_attempted"] += 1
            send_result = await _send_via_routing_v2(
                db, route_key=route_key,
                subject=_email_subject(it["item_kind"], window, it.get("entity_label", "")),
                body_html=_render_email_html(
                    kind_label=_human_kind(it["item_kind"]),
                    entity_label=it.get("entity_label", ""),
                    window=window, due_date=due_dt.isoformat(),
                    body_note=_action_description(it, window),
                ),
                dry_run=dry_run,
                calling_module="transport_automation",
            )
            if send_result["status"] == "sent":
                counts["emails_sent"] += 1
            elif send_result["status"] == "needs_configuration":
                counts["emails_needs_configuration"] += 1
            elif send_result["status"] == "errored":
                counts["errors"] += 1
                errors.append(f"send {route_key}: {send_result.get('error')}")
            # Update event with final status.
            await db.transport_automation_events.update_one(
                {"_id": event_doc["_id"] if "_id" in event_doc else None,
                 "id": event_id, "tenant": TENANT},
                {"$set": {"status": _final_event_status(send_result),
                          "updated_at": _now_iso(now)}})
            # Track for eligibility recompute.
            if it["entity_type"] in ("person", "truck", "carrier"):
                affected_entities.add((it["entity_type"], it["entity_id"]))
        except Exception as e:  # noqa: BLE001
            errors.append(f"per-item {it.get('item_kind')}/"
                          f"{it.get('entity_id','?')}: {e}")
            counts["errors"] += 1
            continue

    # 3. Recompute eligibility for affected entities.
    for et, eid in affected_entities:
        try:
            diff = await _maybe_recompute_eligibility(
                db, entity_type=et, entity_id=eid)
            if diff:
                counts["eligibility_updates"] += 1
                # Emit a tracked event.
                evk = make_event_key(
                    item_kind="eligibility_changed", entity_id=eid,
                    window=diff["new_state"], due_iso=_now_iso(now)[:10])
                if not await db.transport_automation_events.find_one(
                        {"tenant": TENANT, "event_key": evk}):
                    await db.transport_automation_events.insert_one({
                        "id": uuid.uuid4().hex, "tenant": TENANT,
                        "event_key": evk,
                        "entity_type": et, "entity_id": eid,
                        "route_key": "TRANSPORT_ELIGIBILITY_CHANGED",
                        "reminder_window": "state_change",
                        "due_date": _now_iso(now),
                        "status": "created",
                        "dry_run": dry_run,
                        "created_at": _now_iso(now),
                        "updated_at": _now_iso(now),
                        "details": diff,
                    })
        except Exception as e:  # noqa: BLE001
            errors.append(f"recompute {et}/{eid}: {e}")
            counts["errors"] += 1

    completed_at = _now_iso()
    # 4. Persist the run summary.
    run_doc = {
        "id": uuid.uuid4().hex, "tenant": TENANT,
        "started_at": started_at, "completed_at": completed_at,
        "dry_run": dry_run, "triggered_by": triggered_by,
        "counts": counts, "errors": errors[:50],
        "actions_sample": actions_emitted[:10],
    }
    try:
        await db.transport_automation_runs.insert_one(run_doc.copy())
    except Exception:  # noqa: BLE001
        pass

    return {
        "ok": True,
        "started_at": started_at,
        "completed_at": completed_at,
        "dry_run": dry_run,
        "counts": counts,
        "actions": actions_emitted,
        "errors": errors,
    }


# ============================================================================
# Display helpers — non-punitive labels only
# ============================================================================
HUMAN_KIND = {
    "truck_inspection": "Truck readiness inspection",
    "orientation": "Driver orientation",
    "driver_cdl": "CDL",
    "driver_medical": "Medical card",
    "driver_clearinghouse": "Clearinghouse documentation",
    "driver_doc": "Driver document",
    "carrier_insurance": "Carrier insurance",
    "carrier_w9": "Carrier W-9",
    "carrier_doc": "Carrier document",
    "carrier_packet": "Carrier packet pending review",
    "carrier_packet_correction": "Carrier packet needs correction",
    "override_approved": "Dispatch override approved",
    "override_expiring": "Dispatch override expiring",
    "eligibility_changed": "Eligibility changed",
}

ASSIGN_ROLE = {
    "truck_inspection": "transportation_admin",
    "orientation": "transportation_admin",
    "driver_cdl": "transportation_admin",
    "driver_medical": "safety",
    "driver_clearinghouse": "transportation_admin",
    "carrier_packet": "transportation_admin",
    "carrier_packet_correction": "transportation_admin",
    "override_approved": "operations_leadership",
    "override_expiring": "operations_leadership",
}

WINDOW_PHRASE = {
    "30_days": "Due Soon",
    "14_days": "Due Soon",
    "7_days": "Due Soon",
    "1_day": "Due Today",
    "due_today": "Due Today",
    "overdue": "Overdue",
}


def _human_kind(k: str) -> str:
    return HUMAN_KIND.get(k, k.replace("_", " ").capitalize())


def _assigned_role(k: str) -> str:
    return ASSIGN_ROLE.get(k, "transportation_admin")


def _action_title(item_kind: str, window: str, label: str) -> str:
    return f"{WINDOW_PHRASE.get(window, 'Action Required')} · {_human_kind(item_kind)} · {label}"


def _action_description(it: Dict[str, Any], window: str) -> str:
    base = (f"{_human_kind(it.get('item_kind',''))} for "
            f"{it.get('entity_label','')} is {WINDOW_PHRASE.get(window, window).lower()}.")
    note = it.get("status_note")
    if note == "missing":
        return base + " The required record is missing — please add it via the Transportation portal."
    if note == "expired":
        return base + " This requirement is past its valid window and must be renewed before dispatch."
    return base + " Please confirm and renew before the due date to keep dispatch eligibility current."


def _email_subject(item_kind: str, window: str, label: str) -> str:
    phrase = WINDOW_PHRASE.get(window, "Action Required")
    if window == "overdue":
        return f"Action Required — MASCI Transportation Requirement {phrase} · {label}"
    return f"MASCI Transportation Requirement {phrase} — {_human_kind(item_kind)} · {label}"


def _final_event_status(send_result: Dict[str, Any]) -> str:
    s = send_result.get("status")
    if s == "sent":
        return "emailed"
    if s == "needs_configuration":
        return "needs_configuration"
    if s == "dry_run":
        return "skipped"
    if s == "errored":
        return "errored"
    return "created"
