# ODR · FINAL GOVERNANCE ADDENDUM

_Phase V.1 · Operational Daily Record · Pre-Lock Final Governance · 2026-05-29_

This addendum is the **last architecture revision** before
specification lock. It establishes:

- Field Leadership as the governance owner of ODR quality.
- PM as a pure consumer of ODR data.
- Public ODR as field-data collection only — no management surface.
- A new Field Leadership **ODR Center** with role-based visibility.
- The **ODR Inbox** model (Missing · Draft · Submitted · Returned · Approved).
- The **completion / readiness coaching** visibility contract.
- The **amendment / edit doctrine** (24h foreman · unlimited Super+).
- The **official record doctrine** (submission = official record · approval = quality validation).
- The **signature doctrine** (foreman acknowledgement at submit).
- The **attachment doctrine** (architecturally supported · selectively exposed).
- Re-affirmation of the **public-link device continuity** doctrine.

**No implementation. No routes. No collections. No UI build.**

---

## 1 · Doctrine statements (O21–O35 · new)

These extend the locked operator doctrine (O1–O20) and are anchored
in every relevant artifact.

| # | Statement |
|---|---|
| O21 | ODR governance resides in the **Field Leadership Portal**, not in PM. |
| O22 | The **PM Portal consumes** ODR data; it does not own quality or governance. |
| O23 | **Public ODR** is field-data collection only: create / save draft / upload photos / submit. Nothing else. |
| O24 | Public ODR users shall **not** see prior reports, approval queues, analytics, dashboards, project-wide visibility, other crews, other foremen, or report history. |
| O25 | The **Field Leadership ODR Center** is the operational reporting command center, with role-based views (Foreman · Superintendent · Senior Superintendent · PM read-only). |
| O26 | The **ODR Inbox** has five categories: Missing · Draft · Submitted · Returned · Approved. Project-scoped. |
| O27 | **Completion visibility** is coaching, not punishment. Visible to Foreman + Superintendent + PM. Never used for employee scoring. |
| O28 | **Foreman edits** are allowed within a **24-hour edit window** after submission. After 24 h, only Superintendent / Senior Superintendent / Admin may amend. |
| O29 | **Amendments preserve** the original record · the amendment record · timestamp · user · reason. **No deletion. Ever.** |
| O30 | **Submission** of an ODR creates the **official company record.** Approval validates quality but does not change the record's status as official. |
| O31 | **Foreman certification signature** (a simple acknowledgement) is required at submit, stored with the ODR, embedded in the PDF. PM approval signatures are deferred to a future wave. |
| O32 | The ODR shall **architecturally support** attachments: photos · delivery / haul tickets · density / asphalt / concrete tickets · CEI directives · FAA notices · arbitrary PDF attachments. Exposure of each attachment type is operator-staged. |
| O33 | The **public-link device continuity doctrine** (O11–O20) is **retained in full**: no preload, no duplicate-yesterday, no carry-forward, no auto-populate from prior reports — unless device continuity passes. |
| O34 | The Field Leadership ODR Center surfaces and the PM consumption surfaces share a single backend (`odr` collection · projector layer) — there is **never** a parallel "PM-side" data model. |
| O35 | Every state transition (draft → submitted → returned → approved · or any amendment) appends to the existing append-only audit substrate (`odr_section_events` + new `odr_amendments`). |

---

## 2 · Roles & visibility (Field Leadership ODR Center)

| Role | Authenticated portal | Token | Can view | Can edit | Can return / approve | Can amend post-24h | Can search across projects |
|---|---|---|---|---|---|---|---|
| **Foreman** | Field Leadership | `X-FL-Token` (per-user) | only own ODRs (drafts · submitted · returned · approved) | own ODRs within 24-hour window | ❌ | ❌ | ❌ (only own) |
| **Superintendent** | Field Leadership | `X-FL-Token` (per-user · scoped to assigned projects) | **all** ODRs across all crews on assigned projects | ✅ (any time · amendment trail required) | ✅ | ✅ | ✅ (within assigned scope) |
| **Senior Superintendent** | Field Leadership | `X-FL-Token` (per-user · regional scope) | all ODRs across assigned regional projects | ✅ | ✅ | ✅ | ✅ (regional scope) |
| **PM** | PM Portal | `X-PM-Token` (per-user) | all ODRs on own projects (read-only consumer) | ❌ | ❌ (read-only) | ❌ | ✅ search · ✅ export · ✅ quality metrics · ✅ completion metrics |
| **Admin** | Admin Portal | `X-Admin-Token` | all ODRs platform-wide | ✅ | ✅ | ✅ | ✅ |

**Public link surface** (anonymous foreman entry · device-continuity
gated) is **not a role** — it is an unauthenticated data-collection
surface that can only create / save-draft / submit one specific
ODR at a time.

---

## 3 · ODR Inbox (Field Leadership Portal)

Visible to Superintendent · Senior Superintendent · Admin (and a
scoped own-only variant for Foreman; an analytics-only variant for
PM).

```
┌──────────────────────────────────────────────────────┐
│  Field Leadership · ODR Inbox · Project #43-217      │
├──────────────────────────────────────────────────────┤
│                                                       │
│   MISSING    DRAFT    SUBMITTED    RETURNED   APPROVED│
│     [2]       [1]       [4]         [1]        [187]  │
│                                                       │
├──── Missing ────────────────────────────────────────┤
│  · Crew "Reyes Pipe"     · 2026-05-28 · expected     │
│  · Crew "Davis Paving"   · 2026-05-28 · expected     │
├──── Draft ──────────────────────────────────────────┤
│  · Reyes Pipe  · 2026-05-29 · last saved 11:24 ET    │
├──── Submitted ──────────────────────────────────────┤
│  · Davis Paving · 2026-05-28 · submitted 18:11 ET    │
│  · 3 more …                                          │
├──── Returned ───────────────────────────────────────┤
│  · Reyes Pipe  · 2026-05-26 · "fix compaction value" │
├──── Approved ───────────────────────────────────────┤
│  · 187 records (most recent: 2026-05-28 paving crew) │
└──────────────────────────────────────────────────────┘
```

The Inbox is **project-scoped** by default; scope expands by role
(Superintendent = assigned projects · Senior Super = region · Admin
= platform). Each category is a saved server-side query backed by
existing `odr.status` + `odr.project.report_date` indices — no
new collection.

### Inbox category semantics

| Category | Definition |
|---|---|
| Missing | An expected (project, crew, report_date) tuple has no ODR row · derived from `project · crew · dispatch board calendar` |
| Draft | `odr.status = "draft"` |
| Submitted | `odr.status = "submitted"` (= official record · not yet quality-validated) |
| Returned | `odr.status = "returned"` (Superintendent or above returned for revision) |
| Approved | `odr.status = "approved"` (quality validated · official record unchanged) |

---

## 4 · Completion / readiness visibility (coaching · not punishment)

The existing `ReadinessSnapshot` (DATA_MODEL § 3.15 + § A6
CompletionTelemetry) gains an explicit **visibility audience** map:

| Audience | Sees readiness coaching prompts? | Sees raw completion telemetry? |
|---|---|---|
| Foreman (own ODR) | ✅ (in Section 15) | ❌ — never (per O9 + O27) |
| Superintendent | ✅ (Inbox row badge: "5 coaching items") | ❌ aggregated only |
| Senior Super | ✅ aggregated | ❌ aggregated only |
| PM | ✅ aggregated · per-project trends | ❌ aggregated only |
| Admin | ✅ | ✅ — only operator with raw telemetry visibility |

**Hard rule (O27):** completion telemetry is never surfaced as a
per-foreman score. The Inbox may show "5 reports with missing
photos" but never "Carlos Reyes ranks 4th in completion."

---

## 5 · Amendment doctrine

### 5.1 Foreman 24-hour edit window

- A foreman may freely edit fields on a `status="submitted"` ODR
  they authored, for **24 hours** after `submitted_at_utc`.
- Edits within the window do **not** appear in the amendment log;
  they are treated as final-pass corrections.
- At 24 h + 1, the ODR locks for the foreman; only Super / Senior
  Super / Admin may amend.

### 5.2 Superintendent (and above) amendment

- May amend any field on any ODR within their scope, at any time.
- Each amendment appends one row to the new `odr_amendments`
  collection (defined in DATA_MODEL addendum below).
- The amendment row carries: actor_uid · actor_role · field_path ·
  old_value_hash · new_value_hash · reason · at_utc.
- The original value is preserved inside the amendment row, **and**
  the ODR's field carries the new value. **Nothing is deleted.**

### 5.3 No deletion, ever

- A `status="returned"` ODR is not deleted — it is annotated and
  re-submitted.
- A foreman cannot delete a draft once submitted.
- Admin cannot delete an ODR. The strongest action available is
  `status="returned"` with an amendment row explaining why.

---

## 6 · Official record doctrine

```
   Draft
     ↓
   Submitted   ← THIS IS THE OFFICIAL COMPANY RECORD
     ↓
   Returned    (optional · for quality revision)
     ↓
   Re-Submitted (still the official record · amendment chain attached)
     ↓
   Approved    (quality validated · record unchanged)
```

- The moment `submitted_at_utc` is stamped, the ODR is the
  **official company record** for that (project · crew · date)
  tuple.
- Approval does **not** create the official record; it validates
  the record's quality.
- This matters legally: an unapproved-but-submitted ODR is **still
  the company's authoritative account of that field day** for
  claims / FDOT / FAA / attorney purposes. The approval workflow
  is internal quality assurance, not a legal gate.

---

## 7 · Signature doctrine

### 7.1 Foreman acknowledgement at submit

- A single check + tap on submit:
  - "I certify the information on this report is true and complete
    to the best of my knowledge."
  - Stored as `signature.foreman_acknowledgement` on the ODR.
  - Field carries: `acknowledged: bool` · `acknowledged_at_utc` ·
    `acknowledged_by_uid` · `acknowledged_from_fingerprint` (when
    public link · ties to continuity gate).
- Rendered on the PDF cover next to the foreman name + date.

### 7.2 PM approval signatures · deferred

- Not in V.1 scope.
- The `review.status_history[]` events on the ODR already capture
  PM approve / return actions with timestamps and UIDs.
- A dedicated cryptographic signature is **planned for V.1.1+**.

---

## 8 · Attachment doctrine

The ODR is architected to carry **any** of the attachment categories
below. Exposure (UI surface · capture flow · PDF placement) is
staged separately.

| Category | Architectural support | Exposed in V.1? |
|---|---|---|
| Photos (tagged + voice caption) | ✅ existing `photos: List[PhotoRef]` | ✅ |
| Delivery tickets | ✅ via `materials[].ticket_numbers` + new `Attachment` doc | 🟡 ticket numbers ✅ · PDF image scan 🟡 (M1+) |
| Haul tickets | ✅ same | 🟡 |
| Density reports | ✅ via attached PDF | 🟡 M1+ |
| Asphalt tickets | ✅ via attached PDF / image | 🟡 |
| Concrete tickets | ✅ via attached PDF / image | 🟡 |
| CEI directives | ✅ via attached PDF / image | 🟡 (capture in PM portal · linked to ExtraWork) |
| FAA notices | ✅ via attached PDF / image | 🟡 M1+ |
| Arbitrary PDF attachments | ✅ generic `Attachment` doc | 🟡 M1+ |

A new lightweight document type `Attachment` is added to the data
model (see DATA_MODEL addendum); `attachments: List[AttachmentRef]`
joins `photos: List[PhotoRef]` at the top level.

---

## 9 · Doctrine anchors (O21–O35 → spec)

| Doctrine | Anchor |
|---|---|
| O21 governance in FL | DATA_MODEL roles · UI ODR Center · ECOSYSTEM FL surface |
| O22 PM = consumer | ECOSYSTEM PM read-only · MIGRATION migrates PM reads |
| O23 public ODR simple | ECOSYSTEM public surface scope · UI flows |
| O24 public sees nothing else | ECOSYSTEM trust boundary § (extended) |
| O25 FL ODR Center | UI new ODR Center wireframe |
| O26 Inbox 5-category | DATA_MODEL `status` enum + Inbox query layer · UI |
| O27 coaching not punish | § 4 above + DATA_MODEL audience map |
| O28 24h edit window | DATA_MODEL `amend_allowed_until_utc` · § 5 above |
| O29 amendment preserves | new `odr_amendments` collection · trendline-protected |
| O30 official record | DATA_MODEL `status` semantics + this doc § 6 |
| O31 foreman signature | DATA_MODEL `signature` block |
| O32 attachments supported | DATA_MODEL `Attachment` type · UI selective surfaces |
| O33 continuity retained | already locked in O11–O20 |
| O34 single backend | ECOSYSTEM § (one `odr` collection · projectors only) |
| O35 audit append-only | `odr_section_events` + new `odr_amendments` |

---

## 10 · How this addendum lands in each artifact

| Artifact | Update |
|---|---|
| `ODR_DATA_MODEL.md` | New `Signature` block · `Attachment` type + `attachments: List` · `odr_amendments` collection + `Amendment` model · `amend_allowed_until_utc` field · audience map for telemetry |
| `ODR_UI_WIREFRAMES.md` | Field Leadership ODR Center · Inbox 5-tab · Foreman own-records view · Superintendent review queue · PM read-only consumption surface · attachment add affordance |
| `ODR_ECOSYSTEM_INTEGRATION_MAP.md` | Governance vs consumption split · FL Portal as governance owner · PM Portal as read-only consumer · no parallel backend |
| `ODR_MIGRATION_PLAN.md` | M2 includes FL ODR Center build-out · M3 amendment policy hardening · legacy daily_reports approvals re-routed to FL Inbox semantics · attachment migration plan |
| `ODR_SPEC_LOCK_READINESS_REVIEW.md` | Add 6 new certification points (governance · public simplicity · Inbox · PM consumption · amendment · signature/attachment) |
| `_INDEX.md` | Adds row for this addendum + Spec Lock Certification |

Each artifact carries a short "Final Governance Addendum" section
at the end of its file — added in this revision pass. Original
content + earlier addenda remain authoritative for their scope;
this addendum is read **alongside** the others.

---

## 11 · Stop condition honoured

- ✅ No implementation
- ✅ No code · no routes · no collections · no UI · no probe code
- ✅ Wave M0 NOT begun
- ✅ Architecture-only revision
- ✅ V-Prelude Observation Freeze on broader platform still intact

Awaiting operator spec-lock authorization.

_End of Final Governance Addendum._
