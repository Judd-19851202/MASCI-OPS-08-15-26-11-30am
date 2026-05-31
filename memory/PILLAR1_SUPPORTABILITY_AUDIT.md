# Pillar 1 · Supportability Audit (Phase 4)

**Batch:** Pillar 1 · Pre-Deployment Operational Certification · Phase 4
**Date:** 2026-05-31
**Scope:** Evaluate whether a future ForgedOps support engineer (not on the original build team) can answer the five fundamental support questions using **platform surfaces alone** — admin UI, API endpoints, and governance docs. No code change in scope.

---

## 1 · The five support questions

For an aged RED Pillar 1 item, ForgedOps support must be able to answer:

1. Why is this red?
2. Who owns it?
3. Why is it overdue?
4. What changed?
5. When did it change?

---

## 2 · Surfaces available to ForgedOps support

| Surface | Auth | Returns | Pillar 1 relevant? |
|---|---|---|---|
| `GET /api/admin/command-center/snapshot` | admin token | 5 cards · warnings · items · rule_id per item | 🟢 entry point |
| `GET /api/admin/command-center/drilldown/{card_id}/{item_id}` | admin token | source_doc + `accountability` sub-doc (4 owner fields) + `timeline` (last 25 events) | 🟢 primary support tool |
| `GET /api/admin/command-center/thresholds` | admin token | full rule table with predicate · operational_risk · leadership_action · owner_role · expected_resolution | 🟢 rule justification |
| `GET /api/admin/command-center/calendar` | admin token | timezone + working hours | 🟢 calendar context |
| `GET /api/admin/accountability/sources` | admin token | 6 sources catalog | 🟢 routing context |
| `GET /api/admin/accountability/item?source_module=X&source_record_id=Y` | admin token | full 23-field canonical projection + `timeline_events` | 🟢 deep-dive surface |
| `GET /api/admin/accountability/snapshot?per_source=N` | admin token | aged-item lists per source | 🟢 cross-source view |
| Source-collection admin pages (existing) | admin token | full source-doc UI (`/admin/incidents/...`, `/admin/jobs?...`, `/po-requests/...`) | 🟢 last-mile drill |
| Memory docs (`/app/memory/*.md`) | repo access only | architecture · audit · certification · roadmap | 🟢 _but not_ a runtime surface |

---

## 3 · Per-question support evaluation

### 3.1 · Q1: Why is this red?

**Answerable: 🟢 YES.**

Walk-through on a real item (live snapshot 2026-05-31):

```json
{
  "what_wrong": "High incident INC-2026-00026 open 4d",
  "why_red": "Rule SAF-CRITICAL-UNRESOLVED · age ≥ 48h",
  "rule_id": "SAF-CRITICAL-UNRESOLVED"
}
```

Support engineer follows `rule_id` to `/api/admin/command-center/thresholds`:

```json
"SAF-CRITICAL-UNRESOLVED": {
  "amber_hours": 24,
  "red_hours": 48,
  "severities_critical": ["critical", "high", "serious"],
  "predicate": "High/Critical/Serious incident unresolved beyond age threshold",
  "operational_risk": "Personnel safety exposure · regulatory exposure",
  "leadership_action": "Safety lead briefs Operations Director · site visit if warranted",
  "owner_role": "safety",
  "expected_resolution": "Critical: 24h · High: 48h"
}
```

🟢 Complete answer available without leaving admin surfaces.

### 3.2 · Q2: Who owns it?

**Answerable: 🟢 YES.**

Drilldown `accountability` sub-doc (Phase 1A-4):

```json
{
  "owner_role": "safety",
  "owner_user_id": "fb15...",
  "owner_employee_id": "EMP-0123",
  "owner_display_name": "Alec Perkins"
}
```

When upstream routing data is sparse, the placeholder is the truth ("Safety", "Shop", "Pending Approver", "Unassigned PM"). The `PILLAR1_OWNER_FIDELITY_REPORT` documents the resolution mechanism. The placeholder semantics are documented in `ACCOUNTABILITY_OWNER_RESOLUTION_AUDIT.md` (Resolvable-vs-preserved matrix).

🟢 Complete · with explicit semantics for placeholder cases.

### 3.3 · Q3: Why is it overdue?

**Answerable: 🟡 PARTIAL.**

Accountability projection provides:
- `due_at` — the deadline (CA due_date · PO 3-day SLA · incident 48h cap)
- `last_activity_at` — most recent timestamped event
- `overdue` — boolean derived from `due_at` and the calendar

But: there is **no surface that explains _why_** something slipped past its due date. Possible causes (workload · approver vacation · vendor delay · waiting on parts) live in source-document detail (CA comments · PO audit · incident notes) that the support engineer must open individually.

Mitigation today:
- `drilldown.source_doc` returns the raw row, so source-detail is one click away.
- `timeline_events` includes status-history transitions and (where present) audit comments.

Gap: there is no canonical "blocker reason" field. The Lifecycle Spec (`ACCOUNTABILITY_LIFECYCLE_SPEC.md`) deliberately did NOT introduce one to avoid schema mutation.

🟡 Partial · operator must inspect source-doc detail to confirm cause.

### 3.4 · Q4: What changed?

**Answerable: 🔴 NO (today).**

Pillar 1's timeline projection is **append-only event history** translated from source `audit[]` / `status_history[]`. It tells the engineer _that_ something changed and _when_, but **not what the field-level before-and-after diff was**.

Mitigation today:
- `timeline_events[*].event_kind` + `.detail` + `.actor_display_name` provide narrative.
- Source-level admin pages may show field diffs where the source schema captures them (CA `status_history[]` is the richest; PO `audit[]` is medium; incidents are sparse).

The `ACCOUNTABILITY_TIMELINE_SPEC.md` calls this out explicitly as Pillar 1B territory (Escalation framework) — adding a field-diff stream is OUT of Pillar 1 scope today.

🔴 No canonical "what changed" surface · would require future spec work.

### 3.5 · Q5: When did it change?

**Answerable: 🟢 YES.**

Every projection carries:
- `created_at`
- `assigned_at`
- `due_at`
- `first_viewed_at` (when populated by source)
- `last_activity_at`
- `resolved_at`
- `timeline_events[*].at` (per-event ISO timestamps)

Timestamps follow the platform's UTC-store-and-tz-aware-transmit doctrine (see `TIMESTAMP_UTILITY_STANDARD.md`).

🟢 Complete.

---

## 4 · Aggregate support readiness

| Question | Verdict | Surfaces sufficient? |
|---|---|---|
| Q1 · Why red? | 🟢 YES | snapshot + thresholds |
| Q2 · Who owns? | 🟢 YES | drilldown.accountability |
| Q3 · Why overdue? | 🟡 PARTIAL | drilldown.source_doc · operator must read detail |
| Q4 · What changed? | 🔴 NO | no field-level diff surface |
| Q5 · When changed? | 🟢 YES | timeline_events |

**3 GREEN · 1 PARTIAL · 1 RED.**

---

## 5 · Supportability gaps (documented for future scoping · NO REMEDIATION in this batch)

| Gap | Severity | Where addressed |
|---|---|---|
| No canonical "blocker reason" field on aged items | LOW-MED | Would require source-schema additions on tasks/CAs/POs · OUT of Pillar 1 scope |
| No field-level "what changed" diff stream | MED | Pillar 1B Escalation Framework spec · OUT of Pillar 1 scope today |
| Drilldown timeline capped at last 25 events | LOW | Documented in Phase 1A-4 cert · adjustable threshold |
| `/api/admin/accountability/item` uses BASE projection (not resolved variant) | LOW | Support sees "Pending Approver" / "Safety" placeholder here even when Command Center shows the resolved name. Could be misread as a discrepancy. Documented in `ACCOUNTABILITY_PROJECTION_REPORT.md` §3.2. |
| No support-facing "search by employee" surface | LOW | Phase 1A-6 Dashboard candidate · NOT in scope |
| Placeholder semantics ("Safety" = no individual yet accountable) not visible in UI; only documented in markdown | LOW-MED | Could be addressed by inline tooltip or empty-state hint — a Pillar 1A-6 candidate |
| No tenant-aware support filtering (single tenant today) | n/a | Customer #2 work · see `PILLAR1_WHITE_LABEL_READINESS_REPORT.md` |

---

## 6 · Recommended ForgedOps runbook (documentation only)

If a future ForgedOps engineer is paged on an aged RED Pillar 1 item:

```
1. GET /api/admin/command-center/snapshot
   → identify card_id + item_id
2. GET /api/admin/command-center/drilldown/{card_id}/{item_id}
   → read .why_red · .accountability.owner_display_name · .accountability.due_at
3. GET /api/admin/command-center/thresholds
   → read rules[rule_id].predicate · .operational_risk · .leadership_action
4. If "why overdue" unclear: open drilldown.source_doc and read comments/audit[]/status_history[]
5. If owner is a placeholder (Safety · Shop · Pending Approver · Unassigned PM):
   → reference ACCOUNTABILITY_OWNER_RESOLUTION_AUDIT.md §3 (resolvable-vs-preserved matrix)
   → the placeholder IS the truth · no individual is yet accountable on this item
6. Route to owner_role's department lead per the leadership_action text
```

This runbook can be productized into a `/admin/forgedops/runbook` page in a future authorized batch (NOT in scope).

---

## 7 · Closeout

🟡 **SUPPORTABILITY GOOD WITH ONE STRUCTURAL LIMIT.** A ForgedOps engineer can answer 4 of the 5 fundamental support questions from platform surfaces today; the fifth ("what changed") requires Pillar 1B-era spec work that is explicitly out of Pillar 1 scope.

**STOP. No code. No new endpoints. Awaiting operator review.**
