"""TRACK 15.79B · Daily Report Delivery Forensics.

Read-only, admin-gated endpoint that traces — record by record — why
the email auto-dispatch for a given Daily Report did or did not reach
its assigned PM/Co-PM.

Hard contract:
  • No writes. No sends. No mutations. No secrets in the payload.
  • Admin-gated (401/403 anonymous).
  • Re-runs the SAME resolver code path used at submit-time so the
    answer matches reality.
  • Reads from four sources of truth in production Mongo:
      - ``daily_reports``                  (the submitted record)
      - ``jobs_master``                    (legacy PM/email source)
      - ``project_team_assignments``       (live roster · canonical)
      - ``trust_spine_events``             (per-stage lifecycle proof)
      - ``email_routing_audit_v2``         (provider audit row)
  • Classifies the failure point into one of a fixed root_cause_code
    set; the dashboard / operator never has to guess.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query


# ── Failure classification (closed set) ────────────────────────────
ROOT_CAUSE_CODES = {
    "ok_delivered",
    "dead_letter_only",
    "project_number_mismatch",
    "tenant_mismatch",
    "role_name_mismatch",
    "inactive_assignment",
    "primary_flag_mismatch",
    "pm_identity_found_email_missing",
    "copm_identity_found_email_missing",
    "resolver_bypassed_roster",
    "recipients_empty",
    "auto_email_not_scheduled",
    "dispatch_skipped",
    "provider_rejected",
    "audit_missing",
    "trust_spine_missing_notification_stage",
    "dead_letter_unconfigured",
    "unknown",
}

EXPECTED_STAGES_DAILY_REPORT = [
    "record_created", "routing_resolved", "recipients_built",
    "notification_queued", "provider_accepted", "audit_written", "completed",
]


def _normalize_pn(raw: str) -> str:
    """Match the dispatcher's normalization rule (pm_routing._normalize_job_number)."""
    if not raw:
        return ""
    s = str(raw).strip().lower()
    s = s.replace(" - ", "-").replace(" -", "-").replace("- ", "-").replace(" ", "")
    return s


def _public_assignment(row: Dict[str, Any]) -> Dict[str, Any]:
    """Strip PII-heavy fields for the response; keep only what the
    operator needs to see WHY routing did/did not work. We DO surface
    email + display_name because the operator's whole question is
    "what address did the platform actually have for this PM?"."""
    return {
        "assignment_id": row.get("id"),
        "project_number": row.get("project_number"),
        "assignment_role": row.get("assignment_role"),
        "is_primary": bool(row.get("is_primary")),
        "active": bool(row.get("active")),
        "assignment_status": row.get("assignment_status"),
        "display_name": row.get("display_name"),
        "email": (row.get("email") or "").strip().lower() or None,
        "user_id": row.get("user_id"),
        "employee_id": row.get("employee_id"),
        "assigned_at": row.get("assigned_at"),
    }


async def _walk_user_email(db, row: Dict[str, Any]) -> Optional[str]:
    """Mirror pm_routing._resolve_roster_pm fallback walk: email →
    user_directory → employees. Read-only."""
    em = (row.get("email") or "").strip().lower()
    if em:
        return em
    uid = row.get("user_id")
    if uid:
        ud = await db.user_directory.find_one(
            {"id": uid}, {"_id": 0, "email": 1}
        )
        if ud and ud.get("email"):
            return str(ud["email"]).strip().lower()
    eid = row.get("employee_id")
    if eid:
        emp = await db.employees.find_one(
            {"id": eid}, {"_id": 0, "email": 1}
        )
        if emp and emp.get("email"):
            return str(emp["email"]).strip().lower()
    return None


def _classify(
    *,
    assignments: List[Dict[str, Any]],
    pm_assignment: Optional[Dict[str, Any]],
    copm_assignments: List[Dict[str, Any]],
    pm_email: Optional[str],
    copm_emails: List[str],
    recipients: List[str],
    expected: List[str],
    spine_stage_index: Dict[str, Dict[str, Any]],
    audit_rows: List[Dict[str, Any]],
    dead_letter_configured: bool,
    routed_via_dead_letter: bool = False,
) -> str:
    """Closed-set failure classifier. Returns one of ROOT_CAUSE_CODES.

    Order matters: more specific causes win over generic ones."""
    # Delivered cleanly.
    completed = spine_stage_index.get("completed") or {}
    provider = spine_stage_index.get("provider_accepted") or {}
    audit_sent = any((r.get("status") or "").lower() == "sent" for r in audit_rows)
    if (
        completed.get("status") == "ok"
        and provider.get("status") == "ok"
        and audit_sent
        and recipients
        and not routed_via_dead_letter
    ):
        return "ok_delivered"

    # Provider rejected: spine recorded a queued/provider-failed event.
    if provider.get("status") == "failed":
        return "provider_rejected"

    # Notification stage skipped entirely (auto-email disabled).
    nq = spine_stage_index.get("notification_queued") or {}
    if nq.get("status") == "skipped":
        return "auto_email_not_scheduled"

    # Resolver fell back to dead-letter — PM never resolved, but the
    # tenant has ADMIN_DEAD_LETTER_TO configured so SOMEONE got the
    # email (not the assigned PM). This is the most common live
    # "PM didn't receive it" pattern when the roster lookup misses.
    if routed_via_dead_letter:
        # Refine further if we can name the underlying miss.
        if pm_assignment and not pm_email:
            return "pm_identity_found_email_missing"
        if assignments and not pm_assignment:
            return "primary_flag_mismatch"
        return "dead_letter_only"

    # Recipients_built event exists but failed: dispatcher fell through.
    rb = spine_stage_index.get("recipients_built") or {}
    if rb.get("status") == "failed":
        if not dead_letter_configured and not recipients:
            return "dead_letter_unconfigured"
        return "recipients_empty"

    # Routing resolved but failed (no PM resolved at all).
    rr = spine_stage_index.get("routing_resolved") or {}
    if rr.get("status") == "failed":
        if assignments and pm_assignment and not pm_email:
            return "pm_identity_found_email_missing"
        if not pm_assignment and not copm_assignments:
            # No assignment row matches the project_number at all.
            # Could be project_number_mismatch, role_name_mismatch,
            # inactive_assignment, or simply no assignment exists.
            return "recipients_empty"
        return "recipients_empty"

    # Resolver returned PM email but kind=daily-report bypassed roster?
    # Detect: PM resolved via jobs_master.pm_email but the live roster
    # has a DIFFERENT primary PM. Surfaces stale jobs_master rows.
    if pm_email and pm_assignment:
        roster_email = (pm_assignment.get("email") or "").strip().lower()
        if roster_email and roster_email != pm_email:
            return "resolver_bypassed_roster"

    # Trust spine missing the notification stage entirely → dispatch
    # never started (e.g. exception in schedule_auto_email path).
    if "recipients_built" not in spine_stage_index and (
        "record_created" in spine_stage_index
        or "routing_resolved" in spine_stage_index
    ):
        return "trust_spine_missing_notification_stage"

    # PM identity row exists but every walk failed.
    if pm_assignment and not pm_email:
        return "pm_identity_found_email_missing"
    if (
        not pm_assignment
        and copm_assignments
        and not copm_emails
    ):
        return "copm_identity_found_email_missing"

    # No assignments at all but a Daily Report exists.
    if not assignments and not recipients:
        if not dead_letter_configured:
            return "dead_letter_unconfigured"
        return "recipients_empty"

    # Audit row missing for a Daily Report whose spine completed.
    if completed.get("status") == "ok" and not audit_rows:
        return "audit_missing"

    return "unknown"


def make_router(db, require_admin_dep) -> APIRouter:
    router = APIRouter(prefix="/api/admin")

    @router.get("/daily-report-delivery/forensics")
    async def dr_delivery_forensics(
        since_hours: int = Query(36, ge=1, le=168),
        project_number: Optional[str] = Query(None, max_length=64),
        limit: int = Query(50, ge=1, le=200),
        include_environment_probe: bool = Query(
            False,
            description=(
                "When true, the response includes a NON-SECRET "
                "environment fingerprint: presence-flags for "
                "AUTO_EMAIL_REPORTS / RESEND_API_KEY and recent doc "
                "counts in trust_spine_events / email_routing_audit_v2 "
                "/ daily_reports. Boolean flags only — no secret "
                "values, no URLs, no keys."
            ),
        ),
        _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        # Lazy imports keep startup cost low and avoid circular refs.
        # NOTE: we intentionally do NOT call ``recipients_for_record_async``
        # — that helper triggers ``_audit_dead_letter`` which WRITES to
        # ``email_routing_audit_v2`` + ``platform_audit``. This endpoint
        # is read-only by contract. We re-implement the same resolution
        # rules locally, calling only the pure-read helpers.
        from pm_routing import (  # noqa: PLC0415
            resolve_pm_for_record_async,
            _dead_letter_recipients,
            _resolve_roster_co_pms,
            PM_ONLY_KINDS,
            ALWAYS_CC,
        )

        since_dt = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        since_iso = since_dt.isoformat()
        q: Dict[str, Any] = {"created_at": {"$gte": since_iso}}
        if project_number:
            q["project_number"] = {
                "$regex": f"^{re.escape(project_number)}$", "$options": "i",
            }

        cursor = (
            db.daily_reports.find(
                q,
                {
                    "_id": 0, "id": 1, "doc_id": 1, "report_number": 1,
                    "project_number": 1, "project_name": 1, "report_date": 1,
                    "prepared_by": 1, "created_at": 1, "submitted_by": 1,
                    "submitted_at": 1,
                },
            )
            .sort("created_at", -1)
            .limit(int(limit))
        )
        drs = [row async for row in cursor]

        dead_letter_to = await _dead_letter_recipients(db)
        dead_letter_configured = bool(dead_letter_to)

        rows: List[Dict[str, Any]] = []
        counters = {
            "reports_found": len(drs),
            "reports_with_pm_assignment": 0,
            "reports_with_copm_assignment": 0,
            "reports_with_pm_email_resolved": 0,
            "reports_with_copm_email_resolved": 0,
            "reports_with_recipients_built": 0,
            "reports_with_send_attempt": 0,
            "reports_with_provider_accept": 0,
            "reports_dead_lettered": 0,
            "reports_unconfigured": 0,
            "reports_silent_failure": 0,
        }

        for dr in drs:
            dr_id = dr.get("id") or ""
            dr_doc_id = dr.get("doc_id") or dr.get("report_number") or ""
            pn_raw = (dr.get("project_number") or "").strip()
            pn_norm = _normalize_pn(pn_raw)

            # 1 · jobs_master match (case-insensitive exact + normalized
            #     fallback). This is what resolve_pm_for_record_async
            #     does internally — replicate so we can SURFACE the
            #     match (or absence) to the operator.
            job_master_match: Optional[Dict[str, Any]] = None
            if pn_raw:
                job_master_match = await db.jobs_master.find_one(
                    {"project_number": {
                        "$regex": f"^{re.escape(pn_raw)}$", "$options": "i",
                    }},
                    {"_id": 0, "project_number": 1, "pm_email": 1,
                     "project_manager": 1, "co_pm_emails": 1},
                )
                if not job_master_match:
                    async for j in db.jobs_master.find(
                        {}, {"_id": 0, "project_number": 1, "pm_email": 1,
                             "project_manager": 1, "co_pm_emails": 1},
                    ):
                        if _normalize_pn(j.get("project_number") or "") == pn_norm:
                            job_master_match = j
                            break

            canonical_pn = (
                (job_master_match or {}).get("project_number") or pn_raw
            )

            # 2 · project_team_assignments — both with the canonical pn
            #     and (for diagnostic value) every active row whose
            #     normalized pn matches.
            roster_query_used = {
                "project_number": canonical_pn,
                "assignment_role": {"$in": ["pm", "co_pm"]},
                "active": True,
            }
            assignments_raw: List[Dict[str, Any]] = []
            async for row in db.project_team_assignments.find(
                roster_query_used, {"_id": 0},
            ):
                assignments_raw.append(row)

            # Diagnostic fallback: scan every active PM/co_PM row in the
            # tenant; flag any that match `pn_norm` but were NOT picked
            # up by the canonical query. This surfaces
            # project_number_mismatch + role_name_mismatch + inactive.
            extra_diagnostic: List[Dict[str, Any]] = []
            async for row in db.project_team_assignments.find(
                {}, {"_id": 0},
            ):
                if _normalize_pn(row.get("project_number") or "") != pn_norm:
                    continue
                # Skip rows already picked up.
                if any(
                    r.get("id") == row.get("id") for r in assignments_raw
                ):
                    continue
                role = (row.get("assignment_role") or "").strip().lower()
                if role not in {"pm", "co_pm"}:
                    extra_diagnostic.append({
                        "diagnostic": "role_name_mismatch",
                        "expected_role_keys": ["pm", "co_pm"],
                        **_public_assignment(row),
                    })
                    continue
                if not bool(row.get("active")):
                    extra_diagnostic.append({
                        "diagnostic": "inactive_assignment",
                        **_public_assignment(row),
                    })
                    continue
                if (row.get("project_number") or "") != canonical_pn:
                    extra_diagnostic.append({
                        "diagnostic": "project_number_mismatch",
                        **_public_assignment(row),
                    })
                    continue
                extra_diagnostic.append(_public_assignment(row))

            pm_assignment: Optional[Dict[str, Any]] = next(
                (a for a in assignments_raw
                 if (a.get("assignment_role") or "").lower() == "pm"
                 and a.get("is_primary")),
                None,
            )
            copm_assignments_raw = [
                a for a in assignments_raw
                if (a.get("assignment_role") or "").lower() == "co_pm"
            ]

            # 3 · email walk per assignment row.
            pm_email_resolved: Optional[str] = None
            if pm_assignment:
                pm_email_resolved = await _walk_user_email(db, pm_assignment)
            copm_emails_resolved: List[str] = []
            for c in copm_assignments_raw:
                em = await _walk_user_email(db, c)
                if em and em not in copm_emails_resolved:
                    copm_emails_resolved.append(em)

            # 4 · re-run the resolver ONLY for PM identity (pure read).
            #     Build the dist locally so this endpoint stays
            #     side-effect-free (no _audit_dead_letter writes).
            resolver_record = {
                "id": dr_id,
                "doc_id": dr_doc_id,
                "project_number": pn_raw,
                "project_name": dr.get("project_name") or "",
            }
            try:
                resolver = await resolve_pm_for_record_async(
                    db, resolver_record,
                )
                pm_name_resolver, pm_email_resolver = (
                    resolver if resolver else (None, None)
                )
                # Build co-PM list the same way recipients_for_record_async
                # does — union legacy jobs_master.co_pm_emails + roster.
                legacy_co = []
                if job_master_match:
                    raw_co = job_master_match.get("co_pm_emails") or []
                    if isinstance(raw_co, list):
                        primary_lower = (pm_email_resolver or "").lower()
                        seen = {primary_lower} if primary_lower else set()
                        for e in raw_co:
                            if not isinstance(e, str):
                                continue
                            em = e.strip().lower()
                            if em and em not in seen:
                                seen.add(em)
                                legacy_co.append(em)
                roster_co = await _resolve_roster_co_pms(db, canonical_pn)
                resolver_co_pm_emails: List[str] = []
                already = {(pm_email_resolver or "").lower()}
                for em in (legacy_co + roster_co):
                    if em and em not in already:
                        already.add(em)
                        resolver_co_pm_emails.append(em)

                # Daily-report is PM_ONLY (no compliance CC fan-out).
                is_pm_only = "daily-report" in PM_ONLY_KINDS  # always True
                resolver_to: List[str] = []
                if pm_email_resolver:
                    resolver_to.append(pm_email_resolver)
                resolver_cc: List[str] = list(resolver_co_pm_emails)
                # If no primary PM resolved, the dispatcher would fall
                # back to ADMIN_DEAD_LETTER_TO. We surface that the
                # dispatch *would* have routed to dead-letter — without
                # writing the audit row.
                routed_via_dead_letter = False
                if not resolver_to:
                    resolver_to = list(dead_letter_to)
                    if resolver_to:
                        routed_via_dead_letter = True
                # is_pm_only is True for daily-report; we never add
                # ALWAYS_CC for this kind. _ = is_pm_only is intentional.
                _unused_is_pm_only = is_pm_only  # noqa: F841
                # De-dupe to + cc into all.
                seen_all = set()
                recipients: List[str] = []
                for e in resolver_to + resolver_cc:
                    k = (e or "").lower()
                    if k and k not in seen_all:
                        seen_all.add(k)
                        recipients.append(e)
                resolver_error = None
            except Exception as exc:  # noqa: BLE001 — read-only forensic
                pm_name_resolver, pm_email_resolver = (None, None)
                recipients, resolver_to, resolver_cc = ([], [], [])
                resolver_co_pm_emails = []
                routed_via_dead_letter = False
                resolver_error = str(exc)[:200]

            # 5 · trust_spine_events: every stage emitted for this
            #     record's lifecycle.
            spine_events: List[Dict[str, Any]] = []
            spine_query = {
                "workflow": "daily-report",
                "record_id": {
                    "$in": [str(dr_id), str(dr_doc_id)],
                },
            }
            async for ev in db.trust_spine_events.find(
                spine_query,
                {"_id": 0, "ts": 1, "stage": 1, "status": 1,
                 "failure_reason": 1, "remediation": 1, "module": 1,
                 "correlation_id": 1},
            ).sort("ts", 1):
                spine_events.append(ev)
            # Index latest event per stage for classification.
            spine_stage_index: Dict[str, Dict[str, Any]] = {}
            for ev in spine_events:
                spine_stage_index[ev["stage"]] = ev
            missing_stages = [
                s for s in EXPECTED_STAGES_DAILY_REPORT
                if s not in spine_stage_index
            ]

            # 6 · email_routing_audit_v2 — find audit rows from the
            #     dispatcher for this DR. The dispatcher writes
            #     calling_module="auto_email_dispatch:daily-report" so
            #     scope the query tightly to avoid noise; cross-check
            #     against the time window of this DR's lifecycle.
            audit_rows: List[Dict[str, Any]] = []
            audit_q: Dict[str, Any] = {
                "calling_module": "auto_email_dispatch:daily-report",
                "ts": {"$gte": dr.get("created_at") or since_iso},
            }
            async for ar in db.email_routing_audit_v2.find(
                audit_q,
                {"_id": 0, "ts": 1, "subject": 1, "status": 1,
                 "resolved_to_count": 1, "resolved_cc_count": 1,
                 "resend_message_id": 1, "error": 1, "route_key": 1,
                 "dry_run": 1, "tenant_key": 1, "calling_module": 1},
            ).sort("ts", 1).limit(20):
                # Match by DR doc_id appearing in the audit subject —
                # the dispatcher's build_email_subject embeds the
                # report number for daily-report kind.
                subj = (ar.get("subject") or "")
                if dr_doc_id and dr_doc_id in subj:
                    audit_rows.append(ar)
                elif dr_id and dr_id in subj:
                    audit_rows.append(ar)
                elif (
                    pn_raw and pn_raw in subj
                    and (dr.get("created_at") or "") <= (ar.get("ts") or "")
                ):
                    # Conservative: only the first such row, to avoid
                    # cross-pollination between same-project DRs.
                    if not audit_rows:
                        audit_rows.append(ar)

            # 7 · classify the failure point.
            root_cause = _classify(
                assignments=assignments_raw,
                pm_assignment=pm_assignment,
                copm_assignments=copm_assignments_raw,
                pm_email=pm_email_resolved or pm_email_resolver,
                copm_emails=copm_emails_resolved,
                recipients=recipients,
                expected=EXPECTED_STAGES_DAILY_REPORT,
                spine_stage_index=spine_stage_index,
                audit_rows=audit_rows,
                dead_letter_configured=dead_letter_configured,
                routed_via_dead_letter=routed_via_dead_letter,
            )

            # Pick a single failure_point string for the dashboard.
            failure_point = (
                "delivered" if root_cause == "ok_delivered"
                else (missing_stages[0] if missing_stages else "resolver")
            )

            operator_remediation = {
                "ok_delivered": "No action — delivery proven.",
                "dead_letter_only":
                    "No primary PM was resolved by the platform but "
                    "ADMIN_DEAD_LETTER_TO IS configured — so the email "
                    "went to the office admin address, NOT the assigned "
                    "PM. Assign a PM in the Team Roster panel for this "
                    "project AND clear/refresh the jobs_master row.",
                "project_number_mismatch":
                    f"Roster row's project_number does not equal the Daily Report's "
                    f"project_number after normalization (DR='{pn_raw}', "
                    f"norm='{pn_norm}'). Re-save the project_team_assignments "
                    f"row with the canonical project_number.",
                "role_name_mismatch":
                    "Roster row exists but assignment_role is not 'pm' or 'co_pm'. "
                    "Re-assign via Admin → People & Access → Multi-Portal Directory.",
                "inactive_assignment":
                    "Roster row exists but active=false. Re-activate the assignment.",
                "primary_flag_mismatch":
                    "PM roster row exists but is_primary=false. Mark the PM "
                    "as primary in the Team Roster panel.",
                "pm_identity_found_email_missing":
                    "PM assignment row exists but no email could be resolved "
                    "from the row, user_directory, or employees. Add an email "
                    "to the user_directory record for this PM.",
                "copm_identity_found_email_missing":
                    "Co-PM assignment row(s) exist but no email could be resolved. "
                    "Add emails to the user_directory records for the Co-PMs.",
                "resolver_bypassed_roster":
                    "jobs_master.pm_email holds a different email than the live "
                    "Team Roster primary PM. Clear jobs_master.pm_email OR "
                    "update the roster, then re-send.",
                "recipients_empty":
                    "Resolver returned zero recipients. Confirm a PM is "
                    "assigned in the Team Roster panel for this project.",
                "auto_email_not_scheduled":
                    "AUTO_EMAIL_REPORTS env var is false OR RESEND_API_KEY missing. "
                    "Verify production env vars on this deploy.",
                "dispatch_skipped":
                    "schedule_auto_email() did not invoke _dispatch_auto_email. "
                    "Inspect backend logs for the exception swallowed in the "
                    "schedule_auto_email wrapper.",
                "provider_rejected":
                    "Resend returned no message_id. Inspect Resend status page "
                    "and RESEND_API_KEY validity.",
                "audit_missing":
                    "Trust Spine recorded provider_accepted=ok but no audit row "
                    "was written. Inspect email_routing_v2.write_audit logs.",
                "trust_spine_missing_notification_stage":
                    "Daily Report saved + record_created event fired, but the "
                    "dispatcher never reached recipients_built. Inspect logs for "
                    "an exception in _dispatch_auto_email or pm_routing.",
                "dead_letter_unconfigured":
                    "No PM resolved AND ADMIN_DEAD_LETTER_TO unconfigured for "
                    "the tenant. Set the dead-letter recipients via Admin → "
                    "Email Routing.",
                "unknown":
                    "Cause not classifiable from available evidence. Inspect "
                    "backend logs around the Daily Report's submission ts.",
            }[root_cause]

            platform_fix_required = root_cause in {
                "resolver_bypassed_roster",
                "dispatch_skipped",
                "trust_spine_missing_notification_stage",
                "audit_missing",
                "auto_email_not_scheduled",
            }

            # Bump counters
            if pm_assignment:
                counters["reports_with_pm_assignment"] += 1
            if copm_assignments_raw:
                counters["reports_with_copm_assignment"] += 1
            if pm_email_resolved or pm_email_resolver:
                counters["reports_with_pm_email_resolved"] += 1
            if copm_emails_resolved:
                counters["reports_with_copm_email_resolved"] += 1
            if (spine_stage_index.get("recipients_built") or {}).get("status") == "ok":
                counters["reports_with_recipients_built"] += 1
            if (spine_stage_index.get("notification_queued") or {}).get("status") == "ok":
                counters["reports_with_send_attempt"] += 1
            if (spine_stage_index.get("provider_accepted") or {}).get("status") == "ok":
                counters["reports_with_provider_accept"] += 1
            if root_cause == "dead_letter_unconfigured":
                counters["reports_unconfigured"] += 1
            elif (
                root_cause == "dead_letter_only"
                or any(
                    "dead_letter" in (r.get("route_key") or "").lower()
                    for r in audit_rows
                )
            ):
                counters["reports_dead_lettered"] += 1
            if root_cause == "trust_spine_missing_notification_stage":
                counters["reports_silent_failure"] += 1

            rows.append({
                "report_id": dr_id,
                "doc_id": dr_doc_id,
                "submitted_at": dr.get("created_at"),
                "report_date": dr.get("report_date"),
                "project_number": pn_raw,
                "project_number_normalized": pn_norm,
                "project_name": dr.get("project_name"),
                "submitted_by": dr.get("prepared_by") or dr.get("submitted_by"),
                "job_master_match": {
                    "found": bool(job_master_match),
                    "project_number": (job_master_match or {}).get("project_number"),
                    "pm_email": (job_master_match or {}).get("pm_email") or None,
                    "project_manager": (job_master_match or {}).get("project_manager") or None,
                    "co_pm_emails": (job_master_match or {}).get("co_pm_emails") or [],
                },
                "team_roster_match": {
                    "count_canonical": len(assignments_raw),
                    "rows": [_public_assignment(a) for a in assignments_raw],
                    "diagnostic_misses": extra_diagnostic,
                },
                "roster_query_used": roster_query_used,
                "pm_assignment": (
                    _public_assignment(pm_assignment) if pm_assignment else None
                ),
                "copm_assignments": [
                    _public_assignment(c) for c in copm_assignments_raw
                ],
                "pm_email_resolved": pm_email_resolved or pm_email_resolver,
                "copm_emails_resolved": copm_emails_resolved,
                "resolver_result": {
                    "pm_name": pm_name_resolver,
                    "pm_email": pm_email_resolver,
                    "co_pm_emails": resolver_co_pm_emails,
                    "to": resolver_to,
                    "cc": resolver_cc,
                    "error": resolver_error,
                },
                "recipients_built": bool(recipients),
                "expected_recipients": (
                    list(dict.fromkeys(
                        [pm_email_resolved or pm_email_resolver]
                        + copm_emails_resolved
                    ))
                    if (pm_email_resolved or pm_email_resolver) or copm_emails_resolved
                    else []
                ),
                "actual_recipients_count": len(recipients),
                "email_attempted": bool(
                    (spine_stage_index.get("notification_queued") or {}).get("status")
                    in {"ok", "failed"}
                ),
                "provider_accepted": (
                    (spine_stage_index.get("provider_accepted") or {}).get("status")
                    == "ok"
                ),
                "resend_message_id_present": any(
                    ar.get("resend_message_id") for ar in audit_rows
                ),
                "email_routing_audit": [
                    {
                        "ts": a.get("ts"),
                        "status": a.get("status"),
                        "route_key": a.get("route_key"),
                        "resolved_to_count": a.get("resolved_to_count"),
                        "resolved_cc_count": a.get("resolved_cc_count"),
                        "subject": (a.get("subject") or "")[:120],
                        "resend_message_id_present": bool(a.get("resend_message_id")),
                        "error_present": bool(a.get("error")),
                    }
                    for a in audit_rows
                ],
                "trust_spine_stages": [
                    {
                        "ts": ev.get("ts"),
                        "stage": ev.get("stage"),
                        "status": ev.get("status"),
                        "module": ev.get("module"),
                        "failure_reason": ev.get("failure_reason"),
                    }
                    for ev in spine_events
                ],
                "missing_stages": missing_stages,
                "failure_point": failure_point,
                "root_cause_code": root_cause,
                "operator_remediation": operator_remediation,
                "platform_fix_required": platform_fix_required,
            })

        return {
            "ok": True,
            "track": "15.79B",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "since_hours": since_hours,
            "project_number_filter": project_number,
            "tenant_dead_letter_configured": dead_letter_configured,
            "expected_stage_contract": EXPECTED_STAGES_DAILY_REPORT,
            "environment_probe": (
                await _environment_probe(db, since_dt)
                if include_environment_probe else None
            ),
            **counters,
            "reports": rows,
        }

    return router


async def _environment_probe(db, since_dt: datetime) -> Dict[str, Any]:
    """Return a NON-SECRET environment fingerprint for diagnostics.

    Surfaces presence-flags (booleans only) and recent doc counts so
    the operator can verify the dispatcher is actually reaching Mongo
    in production. NEVER returns API keys, URLs, or secret values."""
    import os  # noqa: PLC0415
    since_iso = since_dt.isoformat()
    counts: Dict[str, Any] = {}
    for coll in (
        "trust_spine_events", "email_routing_audit_v2",
        "platform_audit", "daily_reports",
        "project_team_assignments", "jobs_master",
    ):
        try:
            total = await db[coll].count_documents({})
            recent = await db[coll].count_documents(
                {"$or": [
                    {"ts": {"$gte": since_iso}},
                    {"created_at": {"$gte": since_iso}},
                ]}
            )
            counts[coll] = {"total": total, "recent_in_window": recent}
        except Exception as exc:  # noqa: BLE001
            counts[coll] = {
                "total": None, "recent_in_window": None,
                "error": str(exc)[:200],
            }
    # Sample the most-recent trust_spine_event so we can see if ANY
    # write has ever landed.
    try:
        last_spine = await db.trust_spine_events.find_one(
            {}, sort=[("ts", -1)],
            projection={"_id": 0, "ts": 1, "workflow": 1, "stage": 1,
                        "status": 1, "module": 1},
        )
    except Exception as exc:  # noqa: BLE001
        last_spine = {"error": str(exc)[:200]}
    # Sample the most-recent email_routing_audit_v2 row likewise.
    try:
        last_audit = await db.email_routing_audit_v2.find_one(
            {}, sort=[("ts", -1)],
            projection={"_id": 0, "ts": 1, "status": 1,
                        "calling_module": 1, "resolved_to_count": 1},
        )
    except Exception as exc:  # noqa: BLE001
        last_audit = {"error": str(exc)[:200]}
    # Sample the 5 most recent FAILED audit rows so the operator can
    # see Resend's exact error strings without DB access. We strip
    # potentially-secret fields (sender_email, recipients) and only
    # surface the calling_module + ts + truncated error string.
    try:
        recent_failures: List[Dict[str, Any]] = []
        async for row in db.email_routing_audit_v2.find(
            {"status": {"$in": ["failed", "error", "rejected"]}},
            projection={"_id": 0, "ts": 1, "status": 1,
                        "calling_module": 1, "route_key": 1,
                        "error": 1, "subject": 1, "dry_run": 1},
        ).sort("ts", -1).limit(5):
            # Truncate any error string to 240 chars (already done at
            # write-site, but be defensive).
            err = row.get("error")
            if isinstance(err, str):
                row["error"] = err[:240]
            # Truncate subject (no PII expected, but cap length).
            subj = row.get("subject")
            if isinstance(subj, str):
                row["subject"] = subj[:160]
            recent_failures.append(row)
    except Exception as exc:  # noqa: BLE001
        recent_failures = [{"error_querying_failures": str(exc)[:200]}]
    return {
        "auto_email_reports_env_truthy": (
            (os.environ.get("AUTO_EMAIL_REPORTS") or "")
            .strip().lower() in ("true", "1", "yes")
        ),
        "resend_api_key_configured": bool(
            (os.environ.get("RESEND_API_KEY") or "").strip()
        ),
        "admin_dead_letter_to_configured": bool(
            (os.environ.get("ADMIN_DEAD_LETTER_TO") or "").strip()
        ),
        "app_env": (os.environ.get("APP_ENV") or "").strip() or None,
        "collection_counts": counts,
        "last_trust_spine_event": last_spine,
        "last_email_routing_audit_v2": last_audit,
        "recent_audit_failures": recent_failures,
    }


__all__ = ["make_router", "ROOT_CAUSE_CODES"]
