# Operational Linking Rules

_Phase V-Prelude-A · pre-Wave-1 substrate doctrine · 2026-05-28._

> **2026-05-29 · Phase V.4 supplement.** Two new relationship types
> are reserved for the approval / rejection workflow:
>   - `relationship = "review-event"` · links a DR to each row in
>     `daily_report_review_events` (submit · start_review · approve
>     · reject · return · resubmit · amend).
>   - `relationship = "amends"` · links an amendment record to the
>     original LOCKED_RECORD it amends. Original is NEVER mutated.
> Both follow this doctrine verbatim: links are operational context
> not ownership · auditable forever · `created_by_actor` stamped.
> Implementation gated on operator review.

> **⛔ READ BEFORE TOUCHING.** Every operational link in this
> platform — between photos, reports, incidents, constraints,
> RFIs, schedule activities, inspections, daily reports, safety
> records, field notes, attachments — MUST follow this doctrine.
> Operational spaghetti is forbidden. Evidence chains must survive
> CEI / DOT / FAA / owner / internal review.

## Core doctrine

### 1. Links are operational context, not ownership.
A photo linked to a constraint does NOT become "owned" by the
constraint. The photo remains under its original ownership and
retention. The link only says "these two artifacts are
operationally related."

### 2. Links must be auditable.
Every record in `operational_links` MUST persist:

```jsonc
{
  "id":             "uuid4",
  "created_at":     "tz-aware ISO (TRUST-TIME-1)",
  "created_by":     "actor_id",
  "source_type":    "<artifact kind enum>",
  "source_id":      "fk",
  "target_type":    "<artifact kind enum>",
  "target_id":      "fk",
  "relationship":   "<relationship type enum · see §3>",
  "reason":         "string · ≤ 280 chars · operator-supplied context",
  "visibility":     "<visibility scope enum · see §5>",
  "project_id":     "denormalized for fast project queries",
  "status":         "active | archived | voided | superseded",
  "status_changed_at": "tz-aware ISO · nullable",
  "status_changed_by": "actor_id · nullable",
}
```

No exceptions. A link with missing audit fields is invalid and
must be rejected at write time.

### 3. Links must NEVER mutate source records automatically.
Creating a link must not silently rewrite, recompute, or
re-tag the source or target artifact. Mutations require
explicit, separate operator actions with their own audit trails.

### 4. Links are reversible by status change, never by hard delete.

| Status | Meaning | When set |
|---|---|---|
| `active` | currently relevant | on creation |
| `archived` | superseded by a newer link / period closed | operator action |
| `voided` | created in error · still visible in audit | operator action |
| `superseded` | replaced by a more specific link | automatic when a `supersedes` relationship is created |

Hard deletion of an `operational_links` row is FORBIDDEN. The
evidence chain must survive.

### 5. Links must support chronology.
The platform must be able to reconstruct, from the
`operational_links` table alone:

- What was discovered (events)
- What evidence was captured (photos · attachments)
- What was reported (daily reports · incidents)
- What was blocked (constraints)
- Who was notified (notifications)
- What response occurred (future RFI external responses)
- What resolved it (resolution records)
- What remains open (active links to open artifacts)

This is enforced by the timeline endpoint contract in
`OPERATIONAL_TIMELINE_FOUNDATION.md`.

### 6. Links must preserve legal defensibility.
Every link must survive external review by CEI, DOT, FAA,
owners, internal investigations, dispute panels, and litigation
discovery. This means:

- Audit fields are immutable post-write (except `status_*`)
- Voided links remain visible with their void reason
- Archive does not break chronology
- Visibility is recorded — who could see what, when

---

## §3 · Allowed relationship types

Each relationship type below defines: **meaning**, allowed
**source → target** combinations, and **forbidden** use cases.

| Type | Meaning | Allowed examples | Forbidden |
|---|---|---|---|
| `references` | informational reference · weakest link | report → constraint · meeting → incident | NOT for evidence chains (use `evidence_for`) |
| `caused_by` | causal relationship · A happened because of B | incident → constraint · constraint → constraint | NOT for vague "related" — must be operator-attested |
| `blocks` | A is blocking B's forward progress | constraint → schedule_activity · constraint → constraint | NOT for slow-down — only hard blocks |
| `blocked_by` | inverse of `blocks` | schedule_activity → constraint | Never the canonical direction — only display reciprocal |
| `supports` | A provides supporting context for B | photo → report · attachment → constraint | NOT for evidence (use `evidence_for`) |
| `evidence_for` | A is documentary evidence of B's claim | photo → constraint · photo → incident · attachment → rfi | NOT for incidental references |
| `resulted_in` | A produced B as an outcome | constraint → rfi · incident → capa | NOT for parallel co-occurrences |
| `related_to` | weakest catch-all · use sparingly | any → any | NOT when a stronger relationship applies — grep this often |
| `supersedes` | A replaces B · B is retired by A | inspection → inspection · rfi → rfi | Cascades `B.status = superseded` |
| `resolved_by` | A is closed because of B | constraint → rfi-response · incident → capa | NOT for resolution attempts that failed |
| `escalated_from` | A is an escalation of B | rfi → constraint · incident → constraint | NOT for unrelated escalations |
| `escalated_to` | inverse of `escalated_from` | constraint → rfi | Never canonical — display reciprocal only |
| `impacts` | A operationally impacts B | constraint → schedule_activity · constraint → project | NOT for trivial effects |
| `impacted_by` | inverse of `impacts` | schedule_activity → constraint | Never canonical — display reciprocal only |
| `documents` | A is a documentary record of B | meeting → constraint · daily_report → incident | NOT for evidence (use `evidence_for`) |
| `response_to` | A is a response to B | external_response → rfi | NOT for internal commentary |
| `generated_from` | A was created from B (workflow) | rfi → constraint · capa → incident | NOT for manual transcription |

### Inverse relationships (display only)

`blocked_by`, `impacted_by`, `escalated_to` are NEVER stored
canonically. The system displays them as derived/reciprocal
context, but the canonical row uses `blocks` / `impacts` /
`escalated_from`.

---

## §4 · Allowed artifact types

For each artifact type, the linkage matrix below defines what it
**MAY** link to, what it **SHOULD NOT** link to, and any
visibility / retention considerations.

| Artifact | May link to | Should NOT link to | Visibility | Retention |
|---|---|---|---|---|
| `daily_report` | constraint · incident · photo · field_note · meeting | employee_record (PII) · payroll | crew + PM + Admin | 7 years |
| `incident` | constraint · photo · capa · safety_record · daily_report | rfi (external scope) | Safety + PM + Admin | indefinite |
| `inspection` | constraint · capa · photo · qa_qc_record | daily_report (separate domain) | Safety / QC + PM + Admin | 7 years |
| `photo` | any operational artifact | employee_record · payroll | inherits parent surface | inherits parent |
| `attachment` | any operational artifact | direct external_response | inherits parent | inherits parent |
| `field_note` | constraint · daily_report · photo · inspection | rfi (external scope) | author + PM + Admin | 2 years |
| `operational_constraint` | any operational artifact · future_rfi · future_schedule_activity | employee_record (only if jha-attested) | per role visibility matrix | indefinite |
| `future_rfi` | constraint · photo · attachment · daily_report · future_schedule_activity · external_response | dispatch_event | PM + GC + (external for shared) | indefinite + extra |
| `future_schedule_activity` | constraint · future_rfi · daily_report (progress) | photo (use intermediary report) | PM + Super + Admin | per project archive |
| `future_schedule_import` | future_schedule_activity (bulk) | constraint (linkage via activity) | Admin + PM | indefinite |
| `future_external_response` | future_rfi (canonical) | constraint (link via rfi) | GC + Admin · audit | indefinite |
| `safety_record` | incident · meeting · constraint · capa | payroll · time_off | Safety + PM + Admin | indefinite |
| `dispatch_event` | constraint (haul-impact) · daily_report (progress) | rfi (out of scope) | Dispatch + PM | 2 years |
| `equipment_record` | dispatch_event · daily_report · incident | rfi (external scope) | Dispatch + Shop + PM | indefinite |
| `employee_record` | safety_record (jha) · meeting (attendance) | constraint · photo (PII risk) | HR + PM (project-scoped) | per HR retention |
| `project` | any (project_id denormalized on every link) | n/a | per role visibility | indefinite |
| `job` | project (subset) | n/a | per role visibility | indefinite |
| `meeting` | daily_report · constraint · incident · attendance | payroll | attendees + PM + Admin | 7 years |
| `qa_qc_record` | inspection · constraint · photo | rfi (use intermediary inspection) | QC + PM + Admin | 7 years |
| `trench_record` | safety_record · incident · daily_report · photo | rfi (use intermediary incident) | Safety + Super + PM | indefinite |
| `jha_record` | safety_record · meeting · employee_record (attestation) | dispatch_event | Safety + Super + PM | per project archive |

---

## §5 · Link visibility doctrine

Visibility is **role-aware** and **explicit**. A link does NOT
grant visibility to its target unless the role's capability
already permits it.

| Visibility scope | Who sees |
|---|---|
| `internal` | all platform roles per their existing capabilities |
| `pm-scope` | PM + Admin only |
| `safety-scope` | Safety + Admin only |
| `dispatch-scope` | Dispatch + Admin only |
| `hr-scope` | HR + Admin only |
| `cross-portal-read` | source-portal capability + Admin |
| `external-shared` | the explicit external envelope (RFI sharing) |
| `audit-only` | only admin audit surfaces · never operator UI |

**Critical rule:** creating a link with `external-shared`
visibility requires the target artifact to ALREADY be in an
explicit sharing envelope. The link cannot leak data by being a
back-door visibility grant.

---

## §6 · Link direction doctrine (canonical)

Canonical direction is enforced at the storage layer. The system
may DISPLAY reciprocal context, but the stored row must follow
the table below.

| Canonical | Display reciprocal as |
|---|---|
| `photo evidence_for constraint` | "constraint backed by 3 photos" |
| `daily_report references constraint` | "constraint referenced in 2 reports" |
| `constraint blocks future_schedule_activity` | "activity blocked by 1 constraint" |
| `future_rfi generated_from constraint` | "constraint generated 1 RFI" |
| `external_response response_to future_rfi` | "RFI has 3 responses" |
| `incident related_to constraint` (only if safety-attested) | "constraint linked to 1 safety incident" |
| `inspection supersedes inspection` | "this inspection supersedes 1 prior" |

Bidirectional storage is FORBIDDEN. One canonical row per
relationship. Display logic synthesizes the inverse.

---

## §7 · Operational timeline doctrine

The timeline endpoint (`/api/timeline`) is a pure aggregation
over `operational_links`. The timeline must:

- Filter to a single `project_id` per call (no cross-project
  bleed)
- Sort by `at` (operator-local-tz aware per TRUST-TIME-1)
- Honor `visibility` — never surface `audit-only` links to
  operators
- Group into discoverable rhythm (day → discipline → artifact)
- Render as calm slate text · never a chart · never a gantt

The timeline must answer the 8 chronology questions in §5 of
the core doctrine above. Each answer must be traceable to its
source row in `operational_links`.

**Forbidden:**
- ⛔ Noisy activity feeds
- ⛔ "X minutes ago" copy on rows older than 24 h
- ⛔ Engagement-style decorations (likes · reactions · counts of
  views)
- ⛔ Color-coded swimlanes

---

## §8 · Link creation rules

Links may be created by:

1. **Explicit operator action** — operator selects a target,
   names a relationship, supplies a reason.
2. **Controlled workflow action** — e.g., an inspection
   close-out automatically creates `inspection supersedes
   inspection` when the operator marks a prior inspection
   replaced.
3. **Approved system suggestion** — a quiet, reviewable,
   dismissible suggestion in the UI ("This photo was taken at
   the same time as Constraint #137. Link as evidence?") · the
   operator must confirm.
4. **Future automated inference** — only after operator
   confirmation. NO auto-link based on vague text matching. NO
   LLM-suggested links without confirmation. NO inferred links
   from EXIF.

**Forbidden:**
- ⛔ Silent auto-linking on save
- ⛔ Hallucinated links from any source
- ⛔ Bulk auto-link migrations without explicit operator review

---

## §9 · Link retention rules

A link inherits retention from the **highest-retention artifact**
involved. Examples:

- `photo evidence_for constraint` → if constraint is indefinite,
  the link is indefinite, even if the photo's standalone
  retention would have expired earlier.
- `daily_report references constraint` later upgraded to
  `daily_report references rfi` (via supersession): retain the
  full chain.
- Archived parent → link remains visible in audit context with
  the parent's `archived` status surfaced.
- Voided parent → link remains, status flagged `voided`, visible
  in audit only.

The evidence chain MUST NOT break under archive, void, or
supersession.

---

## §10 · Governance testing requirements

Phase V-Prelude Wave 1 implementation MUST ship with regression
tests covering:

| Probe | What it asserts |
|---|---|
| **No orphan links** | every link has a valid `source` and `target` row in their respective collections |
| **No invalid artifact types** | `source_type` and `target_type` ∈ §4 enum |
| **No visibility leaks** | a `pm-scope` link is never reachable from an FL operator's API call |
| **No hard-delete cascades** | deleting a source/target leaves the link intact (status flips) |
| **No circular critical ownership** | A `resulted_in` B AND B `resulted_in` A is FORBIDDEN |
| **No link mutation side effects** | creating a link does not alter source/target documents |
| **Timeline ordering correctness** | `/api/timeline` results sorted by `created_at` with stable tie-break on `source_id` |
| **Audit metadata completeness** | every link row has all 11 audit fields populated |
| **Status transition safety** | `active → voided` is allowed; `voided → active` requires admin attestation |
| **Cross-portal visibility honored** | RBAC integration tests cover every visibility scope |

These probes wire into `scripts/pre_deploy_check.sh` as
`stage_operational_links_doctrine`. The probe is sub-second.

---

## §11 · API surface (V-Prelude Wave 1)

```
POST   /api/operational-links                     create
GET    /api/operational-links?project_id=...      project-scoped list
GET    /api/operational-links/:id                 detail
PATCH  /api/operational-links/:id/status          archive | void | unvoid
GET    /api/timeline?project_id=...&from=...&to=...   chronology aggregation
```

All endpoints:
- Admin-authenticated or capability-gated per the visibility
  matrix in §5
- Return tz-aware ISO timestamps (TRUST-TIME-1)
- Exclude Mongo `_id` from every response
- Rate-limited per portal token

---

## §12 · Failure modes prevented by this doctrine

| Failure mode | Prevented by |
|---|---|
| Evidence chain broken on archive | §9 retention rules |
| Operator surprised by silent re-link | §3 no auto-mutation |
| Cross-project context bleed | §7 single `project_id` filter |
| External sharing leak via back-door link | §5 critical rule |
| Hallucinated AI links | §8 confirmation requirement |
| Circular `resulted_in` causing infinite loops | §10 circular-ownership probe |
| Bidirectional storage drift | §6 canonical direction |
| Hard delete losing audit trail | §4 status enum, no DELETE |
| Visibility leak via link inheritance | §5 explicit role enforcement |

---

## §13 · Phase-V handoff

When V.1 RFI MVP lands, `future_rfi` becomes `rfi`. When V.3
Schedule lands, `future_schedule_activity` becomes
`schedule_activity`. No schema migration required — the
artifact-type enum is forward-extended.

The `operational_links` collection is the SHARED SUBSTRATE for
every cross-system relationship from V-Prelude through V.6+.
Get the doctrine right NOW · every future phase inherits it.

---

_End of doctrine. No code changes accompany this document._
