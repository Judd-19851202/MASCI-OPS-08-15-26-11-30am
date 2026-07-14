# TRACK DR-02 · Canonical Daily Report Architecture Lock

Date: 2026-07-14
Mode: Planning and architecture only
Relationship to DR-01: **This document supersedes DR-01 wherever conclusions conflict.**

## Final verdict

**VERIFIED**

The repository is sufficient to lock one permanent Daily Report architecture. The codebase does not merely contain bugs; it contains architectural duplication across shells, draft identity, Smart Prefill, AI-summary paths, legacy APIs, and downstream source models. Those duplicates are now classified and locked.

## Permanent canonical statement

From DR-02 forward, the platform has exactly one Daily Report system:
- one shell contract
- one draft identity contract
- one autosave contract
- one restore contract
- one Smart Prefill contract
- one AI/accepted-summary contract
- one submission contract
- one lifecycle
- one notification/event chain
- one search identity model
- one PDF/export contract
- one ODS semantic contract

Legacy V2 may remain temporarily as a **compatibility boundary only**, not as a second Daily Report architecture.

## Pillar violations identified in current repo

### Powerful
- Violated because Smart Prefill is absent in one active shell.

### Simple
- Violated because one route can resolve to two different field contracts and there are two summary systems.

### Beautiful
- Violated because recovery semantics are presented through overlapping prompts with mixed trust boundaries.

### Trusted
- Violated because the same report can occupy different draft identities and the same feature behaves differently by shell.

### Proven
- Violated because shell parity is not locked and duplicate systems force operator-discovered regressions.

### Deployable
- Violated because duplicate APIs and summary paths make behavior hard to certify safely.

### Durable
- Violated because version drift keeps reappearing at continuity boundaries.

### Relentless Ownership
- Violated because downstream consumers read from multiple historical contracts instead of one clearly-owned Daily Report model.

## Architecture lock decisions

### 1. Daily Report shell
- Current: V1 and V3 are both live via router fork.
- Canonical: one permanent shell only.
- Classification: **Replace** shell competition; **Remove** router fork.

### 2. Draft architecture
- Current: one shared primitive but multiple keys/scopes.
- Canonical: one `useFormDraft` + `draftStore` contract with actor ownership and project+date scope.
- Classification: **Merge** key families; **Replace** unstable scope formula.

### 3. Autosave architecture
- Current: shared engine, shell drift in identity.
- Canonical: one autosave engine and one telemetry contract.
- Classification: **Deprecate** alternate DR autosave hooks.

### 4. Restore architecture
- Current: live draft restore, archived-draft recovery, local setup restore, and Smart Prefill are mixed.
- Canonical: one layered recovery model with explicit semantics.
- Classification: **Merge** restore capabilities, **Remove** semantic overlap.

### 5. Smart Prefill architecture
- Current: backend source exists; V1 has two UI paths; V3 has none.
- Canonical: one server-backed source, one UI, one apply path.
- Classification: **Replace** duplicate apply paths; **Merge** capability into permanent shell.

### 6. AI architecture
- Current: `ai_accepted_summary` path and `daily_operational_summary*` path both exist.
- Canonical: one accepted-summary contract feeding submit + PDF + ODS + intelligence.
- Classification: **Replace** competing summary architecture.

### 7. Submission architecture
- Current: canonical `/daily-reports` plus legacy `/dr-v2/drafts` stack.
- Canonical: one field submission API = `/api/daily-reports`.
- Classification: **Redirect/Deprecate** legacy field-entry paths.

### 8. Attachment architecture
- Canonical: one evidence architecture spanning photos + attachments + manifest.

### 9. Notification architecture
- Canonical: lifecycle/event-driven notifications, not shell-driven behavior.

### 10. Search architecture
- Canonical: one Daily Report identity across detail, global search, doc-id lookup, approved exports, and PDF.

### 11. ODS architecture
- Canonical: one Daily Report semantic fact model; legacy source labels retained only for lineage.

### 12. Executive Brief integration
- Canonical: Daily Report reaches executive/PM brief surfaces through ODS facts only.

### 13. Scheduling integration
- Canonical: Daily Report is signal-only; it must not directly mutate schedules.

### 14. Weekly Reconciliation integration
- **UNKNOWN as a named dedicated subsystem.** Repo proves indirect payroll/evidence reconciliation links but not one dedicated Daily Report-owned weekly reconciliation module.

### 15. Trust Spine integration
- Canonical: one `daily-report` workflow stage chain.

### 16. Audit integration
- Canonical: content hash + lifecycle events + accepted-summary provenance + Trust Spine stages.

### 17. PDF integration
- Canonical: one PDF contract and one canonical summary field family.

### 18. Export integration
- Canonical: one export source family from canonical Daily Report records.

### 19. Mobile architecture
- Canonical: progressive disclosure, responsive, field-first controls.

### 20. Offline architecture
- Canonical: one foreground retry queue + one draft store + one idempotency contract.

### 21. Synchronization architecture
- Canonical: one queue settlement model and one commit-after-delivery rule.

## Evidence-backed duplicate register summary

| Area | Final class |
|---|---|
| shell competition | Replace |
| route fork | Remove |
| draft key split | Merge |
| draft scope split | Replace |
| restore semantics overlap | Merge |
| duplicate Smart Prefill paths | Replace |
| duplicate summary/AI systems | Replace |
| legacy V2 field-entry APIs | Deprecate |
| legacy V2 approved/PDF aliases | Redirect |
| V2 dormant shell | Deprecate |

## What a new engineer must not invent
- no new second draft engine
- no alternate restore UX for the same concept
- no second accepted-summary field family
- no alternate field submit API
- no schedule-mutating side path from Daily Report
- no new raw-doc intelligence path bypassing ODS for executive/PM brief surfaces

## Unknowns that remain honest but non-blocking
- production shell distribution
- exact browser/device incidence rates
- whether Weekly Reconciliation is a named business module beyond payroll/evidence reconciliation links

These are runtime/governance unknowns, not architecture ambiguities.

## Final lock

The Daily Report architecture is hereby locked as **one permanent system**. Any future implementation that reintroduces competing shells, competing summary fields, competing draft identities, or competing downstream source models would violate DR-02.
