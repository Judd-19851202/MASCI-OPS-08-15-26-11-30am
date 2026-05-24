# Notification Discipline Matrix · Phase 6 · WS5

**Purpose:** Single source of truth for how the platform classifies and routes notifications. Used to keep noise down, prevent duplicate alerts, and make sure the right audience sees the right urgency on the right channel.

**Non-goals (this iteration):**
- No new email / SMS / push delivery.
- No new notification engine.
- No widening of any existing recipient_role.

---

## Tier definitions

| Tier | Latency | Channel | Color cue | Meaning |
|---|---|---|---|---|
| **CRITICAL** | Immediate | Bell badge + portal banner | rose | Operational risk now. Must be acknowledged. |
| **IMPORTANT** | Same-day | Bell badge + weekly digest | amber | Action needed soon but not life-safety. |
| **INFO** | None | Visible only inside platform | slate | Status change, audit trail, no action expected. |

---

## Event matrix (current routing)

| Event type | Audience(s) | Tier | Channel(s) | Suppress / aggregate rule | Owner | Expected action |
|---|---|---|---|---|---|---|
| **Incident · severity ≥ medical** | safety, pm, hr | CRITICAL | bell + digest + (Resend email if AUTO_EMAIL_REPORTS=true) | Idempotency key per incident; second submit on same key suppressed | Safety | Open follow-up CAPA same day |
| **Incident · near-miss / first-aid** | safety, pm | IMPORTANT | bell + digest | Aggregated into Safety weekly digest if no CAPA opened in 24 h | Safety | Review within 48 h |
| **CAPA assigned** | assignee + safety | IMPORTANT | bell | One per assignment; status_history additions do not re-notify | CAPA owner | Move to In Progress |
| **CAPA overdue** | assignee + safety + admin | IMPORTANT | bell + admin digest | Re-fires once per 7 days while still overdue | Safety | Update status or extend due date |
| **CAPA awaiting verification > 7 days** | safety + admin | IMPORTANT | bell | Once per 7-day window | Safety reviewer (different person than owner) | Verify or reject |
| **Driver disqualified** (medical/CDL expired or approved=false) | dispatch, fl, hr, safety | CRITICAL | bell + dispatch digest | Suppressed if a re-qualification CAPA is already Open | HR (master record) | Resolve before next dispatch slot |
| **Training expired** | employee's PM + HR + safety | IMPORTANT | weekly digest | Aggregated by employee; one row per person per training type | HR + Safety | Re-train or remove from assignments |
| **Training expiring within 30 days** | HR + safety | IMPORTANT | weekly digest | Aggregated; never sent more than once per training cycle | HR | Schedule renewal |
| **PPE issuance missing employee linkage** | safety | IMPORTANT | governance digest | Surfaces only as `EMP_LINK_UNRESOLVABLE` governance finding; not a separate bell ping | Safety | Re-link or accept as subcontractor |
| **Daily report submitted** | pm | INFO | bell (low-prominence) | One per submission; multi-day burst from same project aggregated | PM | Skim for issues |
| **Safety escalation on daily report** | safety + pm + admin | CRITICAL | bell + Resend email (if enabled) | Idempotency key per DR; cannot be suppressed | Safety | Verify escalation captured in incident |
| **Governance · convergence_score drop ≥ 10 points** | admin | IMPORTANT | admin digest | Once per drop; re-fires only if score keeps falling | Admin | Investigate the new findings driving the drop |
| **Governance · new CRITICAL finding** | admin + safety | CRITICAL | bell + admin digest | Idempotent on finding_id (sha1 of rule+entity) | Admin | Acknowledge or resolve |
| **Backup verification failed** | admin | CRITICAL | bell + dev hook | Re-fires every 24 h while still failing | Admin | Manual backup or fix scheduler |
| **Auto-email failure (Resend bounce)** | admin | IMPORTANT | bell | Re-fires per recipient per cycle | Admin | Verify recipient address |
| **PM portal: incident on assigned project** | the PM | IMPORTANT | bell | Once per incident, scoped to PM project list | PM | Coordinate with safety |
| **FL portal: severe incident on a watched project** | fl | IMPORTANT | bell (via /api/notifications fan-out) | New as of Phase 5D · uses unified `/api/notifications` surface | FL | Field follow-up + accountability |
| **Record acknowledged / resolved** | original notifier | INFO | bell | One acknowledgement per finding | Admin | None — audit trail |
| **Record archived (employee, equipment, doc)** | safety + hr | INFO | none (only visible in portal lists) | n/a | HR / Admin | None |

---

## Aggregation rules (do not duplicate)

1. **Per-record uniqueness.** Every notification carries a `linked_source_module` + `linked_source_record_id`. The bell list never shows two rows for the same source record + recipient_role.
2. **Status churn is silent.** Moving a CAPA from `Open → In Progress` does NOT spawn a new notification. Only assignments, overdue triggers, and awaiting-verification-too-long do.
3. **Severity drives channel.** CRITICAL bells must also surface in the Admin digest. IMPORTANT bells only appear in digest if not acknowledged within the digest cycle.
4. **Auto-resolve > manual resolve.** Governance findings that auto-resolve (`system_auto`) do not re-notify — the lack of a finding IS the all-clear signal.

---

## Channels — current state

| Channel | Implementation | Enabled in preview? | Enabled in production? |
|---|---|---|---|
| Bell badge + `/api/notifications` list | `routes/tasks_notifications.py` | ✅ all 7 portals (FL added Phase 5D) | ✅ |
| Weekly Safety digest | `safety_digest` cron, Mondays 14:00 UTC | ✅ | ✅ (if `AUTO_EMAIL_REPORTS=true`) |
| Weekly PO/Admin digest | `po_digest` cron | ✅ | ✅ (if `AUTO_EMAIL_REPORTS=true`) |
| Resend transactional email | `lib/event_fanout.py` + Resend API key | dry-run only | Only on AUTO_EMAIL_REPORTS=true |
| SMS / push | none | n/a | n/a |

---

## Discipline checklist for new notifications

Before adding any new notification, the author must answer:

1. **Is it actionable?** If the user can't DO anything with it, it should be a status pill on a record, not a notification.
2. **Is it already represented?** Most "new" notification ideas duplicate a governance finding or a CAPA reminder. Re-use, don't re-build.
3. **What's the suppress rule?** Every notification needs an aggregation rule. Without one, it becomes noise.
4. **Who owns it?** If no role is clearly the owner, the notification has no destination.
5. **Tier?** Default to IMPORTANT. CRITICAL is reserved for "this is happening NOW and someone must respond."

If any of the 5 answers is unclear, the notification doesn't ship.

---

## Where to read this file from

- **Backend authors** — Reference when wiring `emit_notification` / `emit_task_and_notification` calls; the `severity` + `recipient_role` must match this matrix.
- **Frontend authors** — Reference when building any new badge or status surface; use the same color cues (rose / amber / slate).
- **Audit / compliance** — This file is the canonical artifact for "who got told what, by what rule" reviews.
- **Operators** — Use during NotificationsDigest review to confirm received items map to a row above.

---

## Next steps (post-Phase 6)

- Audit the live Safety digest output for any 24 h period to confirm zero rows that would also appear in the bell list (no double-delivery).
- Consider a per-user "Mute INFO" preference if INFO volume ever becomes operationally relevant (not yet).
- Reassess CRITICAL latency once mobile signal handling work in Phase 6 WS4 lands in field shadow.
