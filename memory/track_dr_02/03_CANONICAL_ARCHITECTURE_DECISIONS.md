# Canonical Architecture Decisions

Date: 2026-07-14
Track: DR-02

## Decision 1 · Daily Report shell

### Current state
- `DailyReportRouter` serves `NewDailyReport` or `NewDailyReportV3` on the same live route.

### Problems found
- Violates **Simple**, **Trusted**, and **Durable**.
- Same URL can produce different continuity, Smart Prefill, queue, and recovery behavior.

### Canonical future state
- **One permanent Daily Report shell**.
- Canonical behavior baseline: V3 sectioned UX may be retained **only if** it absorbs the full continuity and Smart Prefill contract; otherwise the current V1 contract is the safer functional baseline.
- Architecture lock decision: **the permanent shell is a single unified Daily Report shell derived from the richer continuity contract, not from version identity.**

### Files affected
- `frontend/src/pages/DailyReportRouter.jsx`
- `frontend/src/pages/NewDailyReport.jsx`
- `frontend/src/pages/NewDailyReportV3.jsx`
- `frontend/src/components/daily-report-v3/sections.jsx`

### Legacy retained
- V3 section components may be retained as implementation building blocks.

### Legacy removed
- V1/V3 route competition.

### Migration plan
- Freeze one shell contract → port missing behavior into the chosen permanent shell → remove router fork.

---

## Decision 2 · Draft architecture

### Current state
- Shared `useFormDraft()` primitive exists, but Daily Report uses multiple base keys and multiple scope formulas.

### Problems found
- Breaks **Trusted** and **Durable**.
- Same report instance can exist under different identities.

### Canonical future state
- **One draft engine: `useFormDraft` + `draftStore` + `draftTelemetry`.**
- **One Daily Report base key family shared by every active Daily Report surface.**
- **One scope contract based on stable operator work context only: project_number + report_date.**

### Files affected
- `frontend/src/lib/resiliency/useFormDraft.js`
- `frontend/src/lib/resiliency/dailyReportScope.js`
- `frontend/src/pages/NewDailyReport.jsx`
- `frontend/src/pages/NewDailyReportV3.jsx`
- `frontend/src/lib/resiliency/draftStore.js`

### Legacy retained
- archived draft support from `draftStore`

### Legacy removed
- `report_number`-based scope identity
- Daily Report use of non-canonical keys

### Migration plan
- Move all Daily Report draft writes/reads to one key contract first before any UI migration.

---

## Decision 3 · Autosave architecture

### Current state
- Debounced IndexedDB autosave via `useFormDraft`, plus lifecycle flush attempts.

### Problems found
- Contract drift between shell identities produces silent loss.
- lifecycle flush is described as synchronous but implemented on async storage.

### Canonical future state
- **One autosave engine: `useFormDraft`**.
- Explicit guarantees:
  - debounced change-save
  - lifecycle-triggered best-effort flush
  - telemetry on write/restore/failure
  - no shell-specific autosave logic

### Files affected
- `frontend/src/lib/resiliency/useFormDraft.js`
- `frontend/src/lib/resiliency/draftTelemetry.js`
- active Daily Report shell

### Legacy retained
- telemetry batching and health observability

### Legacy removed
- Daily Report dependence on alternate autosave hooks (`useDraft`, `useDraftSync`)

### Migration plan
- Daily Report becomes exclusive consumer of one autosave contract; older hooks remain only for non-DR forms until separately retired.

---

## Decision 4 · Restore architecture

### Current state
- Live draft restore, archived-draft recovery, crewMemory local restore, and server Smart Prefill are mixed across shells.

### Problems found
- Violates **Simple**, **Beautiful**, **Trusted**.

### Canonical future state
- One layered restore model, in this order:
  1. live same-report draft restore
  2. archived same-report recovery
  3. local setup-memory restore (`crewMemory`)
  4. server Smart Prefill (`recent-context`)
- Each layer must have separate copy, separate actions, separate trust boundary.

### Files affected
- `DraftRestorePrompt.jsx`
- `DraftRecoveryNotice.jsx`
- `crewMemory.js`
- active Daily Report shell

### Legacy retained
- archive recovery and local setup memory as distinct capabilities

### Legacy removed
- reusing one UI component to stand in for multiple recovery semantics

### Migration plan
- sequence the prompts and copy explicitly so operators always know what source they are restoring from.

---

## Decision 5 · Smart Prefill architecture

### Current state
- backend `/jobs/{project_number}/recent-context` exists; V1 consumes it via two UI paths; V3 does not consume it.

### Problems found
- Breaks **Powerful**, **Simple**, **Trusted**.

### Canonical future state
- **One Smart Prefill source:** `/jobs/{project_number}/recent-context`
- **One Smart Prefill UI**
- **One apply transform**
- Local `crewMemory` is not Smart Prefill; it is local setup recovery.

### Files affected
- `backend/server.py`
- active Daily Report shell
- `CrewSetupRestorePrompt.jsx`

### Legacy retained
- backend recent-context contract

### Legacy removed
- duplicate apply path in V1
- absence of Smart Prefill parity in active shell

### Migration plan
- preserve backend contract; collapse UI to one explicit server-prefill flow.

---

## Decision 6 · AI architecture

### Current state
- Two summary/assist architectures exist:
  1. active `DailySummaryAssist` using `/dr-v2/ai/synthesize`
  2. additive `daily_summary.py` deterministic draft/accept endpoints using `daily_operational_summary*`

### Problems found
- Duplicate AI/summary systems violate **Simple**, **Trusted**, and **Relentless Ownership**.
- Downstreams consume `ai_accepted_summary`, while the alternate summary path writes a different field family.

### Canonical future state
- **One Daily Report summary/AI contract feeding the canonical submit payload only.**
- The accepted summary stored on Daily Report must be the same field family consumed by submit validation, ODS, PDF, and intelligence surfaces.
- AI remains assistive only: supervisor is source of truth, no factual overwrite, provenance retained, provider details masked.

### Files affected
- `frontend/src/components/daily-report/DailySummaryAssist.jsx`
- `backend/routes/dr_v2.py`
- `backend/routes/daily_summary.py`
- `backend/routes/daily_reports.py`
- `backend/services/ods_spine/ingest.py`
- `backend/pdf_render.py`

### Legacy retained
- deterministic/fallback composition principles
- evidence/provenance and acceptance metadata

### Legacy removed
- competing `daily_operational_summary*` field family for Daily Report canonical flow

### Migration plan
- standardize on one accepted-summary field family and one generation/acceptance path before any UI polish.

---

## Decision 7 · Submission architecture

### Current state
- V1/V3 submit to `/api/daily-reports`; V2 draft stack submits to `/api/dr-v2/drafts`.

### Canonical future state
- **One canonical field submission API: `POST /api/daily-reports`**.
- Any legacy V2 draft stack becomes compatibility-only and not part of the permanent field architecture.

### Files affected
- `backend/routes/daily_reports.py`
- `backend/routes/dr_v2.py`
- active Daily Report shell

### Classification
- `/api/dr-v2/drafts` = **Deprecate** for field entry

---

## Decision 8 · Attachment architecture

### Current state
- photos in `photos[]`; non-photo docs upload via `/daily-reports/attachments/upload`; evidence manifest and extraction endpoints exist.

### Canonical future state
- **One attachment model:**
  - photos remain photo evidence entries
  - non-photo documents remain `attachments[]`
  - both converge through one evidence-manifest architecture for downstream proof

### Evidence
- `backend/server.py:3365-3404`
- `backend/routes/daily_reports.py:1196-1262`
- `backend/pdf_render.py:215-280`

---

## Decision 9 · Notification architecture

### Current state
- submit-time auto email dispatch + lifecycle pending-review notifications + field submitter kickback path.

### Canonical future state
- **One event-driven notification architecture keyed to Daily Report lifecycle stages**.
- Notifications must be emitted by lifecycle/event transitions, not shell-specific behavior.

### Evidence
- `backend/lib/email_dispatch.py:56-161`
- `backend/routes/daily_reports.py:497-499,855-856`
- `backend/routes/daily_report_lifecycle.py:131-186`

---

## Decision 10 · Search architecture

### Current state
- global search, doc-id search, approved-list export, and detail read surfaces all touch Daily Reports.

### Canonical future state
- **One canonical Daily Report identity** drives:
  - detail route lookup
  - global search row generation
  - approved report listing
  - PDF/export lookup

### Evidence
- `backend/doc_ids.py:220-243`
- `backend/routes/global_search.py:711-742`
- `backend/routes/dr_v2_pdf.py:292-570`

---

## Decision 11 · ODS architecture

### Current state
- ODS ingest supports `daily_report_v1` and `daily_report_v2` separately.

### Canonical future state
- **One Daily Report ODS contract** with one semantic fact model, regardless of legacy source.
- Legacy source labels may remain for migration lineage, but downstream intelligence must treat Daily Report as one domain.

### Evidence
- `backend/services/ods_spine/ingest.py:64-260,322-816`

---

## Decision 12 · Executive Brief integration

### Current state
- ODS PM/executive brief surfaces exist and consume ODS facts, not raw Daily Report docs.

### Canonical future state
- Daily Report contributes to executive/PM brief surfaces **only through ODS facts**.

### Evidence
- `backend/routes/ods_intelligence.py:250-336,485-560`

---

## Decision 13 · Scheduling integration

### Current state
- Daily Report captures schedule-impact signals but explicitly says it must not directly create schedule entries.

### Canonical future state
- Daily Report remains a **signal source**, not a schedule mutator.

### Evidence
- `backend/routes/daily_reports.py:1119-1176`
- `frontend/src/pages/NewDailyReport.jsx:1024-1041,2845`

---

## Decision 14 · Weekly Reconciliation integration

### Current state
- Direct dedicated “Weekly Reconciliation” Daily Report module is not proven in repo.
- Indirect reconciliation links exist via HR time verification and evidence/material reconciliation.

### Canonical future state
- **UNKNOWN as a distinct named subsystem.**
- Repository proves Daily Report feeds payroll/time verification and evidence/material reconciliation; it does not prove one dedicated weekly reconciliation owner module.

---

## Decision 15 · Trust Spine integration

### Current state
- Trust Spine defines a `daily-report` workflow lifecycle.

### Canonical future state
- Daily Report must emit one authoritative lifecycle through Trust Spine stages.

### Evidence
- `backend/lib/trust_spine.py:75-84`

---

## Decision 16 · Audit integration

### Current state
- audit envelope hash, lifecycle state events, and read-only footer endpoint exist.

### Canonical future state
- One immutable audit model combining:
  - record content hash
  - lifecycle transition history
  - accepted summary provenance
  - Trust Spine stages

### Evidence
- `backend/routes/daily_reports.py:1264-1294`
- `backend/routes/daily_report_lifecycle.py:118-129,198-254`

---

## Decision 17 · PDF integration

### Current state
- one canonical alias exists, but renderer can still source from legacy or modern V2-approved records.

### Canonical future state
- One canonical PDF contract for Daily Report, backed by one report identity and one summary field contract.

### Evidence
- `backend/routes/dr_v2_pdf.py:452-570`
- `backend/pdf_render.py:190-280,334-335,832-833,1608-1640`

---

## Decision 18 · Export integration

### Current state
- canonical CSV export reads `daily_reports` only.

### Canonical future state
- Daily Report export surfaces must read the canonical Daily Report record family only.

### Evidence
- `backend/routes/daily_reports.py:1296-1353`

---

## Decision 19 · Mobile architecture

### Current state
- V3 is more step-based/mobile-conscious; V1 is broader and denser.

### Canonical future state
- The permanent shell must preserve:
  - explicit steps/progressive disclosure
  - large tap targets
  - offline status clarity
  - field-first data-testid/accessibility discipline

### Evidence
- `frontend/src/components/daily-report-v3/sections.jsx`
- `frontend/src/pages/NewDailyReportV3.jsx:630-759`
- `frontend/src/pages/NewDailyReport.jsx:1389-3168`

---

## Decision 20 · Offline architecture

### Current state
- foreground-only retry queue + IndexedDB draft storage.

### Canonical future state
- One offline architecture:
  - local draft persistence via IndexedDB
  - foreground retry queue with shared idempotency
  - no shell-specific queue semantics

### Evidence
- `frontend/src/lib/resiliency/resiliencyQueue.js:1-240`

---

## Decision 21 · Synchronization architecture

### Current state
- idempotency + queue replay exist, but V3 parity drifts.

### Canonical future state
- One synchronization contract:
  - one idempotency key scope per report instance
  - one queue payload repair path
  - one success/failure settlement contract

### Evidence
- `NewDailyReport.jsx:1150-1197`
- `NewDailyReportV3.jsx:563-593`
- `resiliencyQueue.js:147-180`

## Decision conclusion

The canonical Daily Report architecture is a **single field-entry system** with one shell contract, one draft/restore contract, one Smart Prefill contract, one accepted-summary contract, one submit path, one lifecycle, one identity, and one downstream evidence chain.
