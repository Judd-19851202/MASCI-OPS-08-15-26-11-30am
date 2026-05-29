# ODR VISIBILITY ALIGNMENT REPORT

_Phase ODR-Governance Extension · ODR Compliance Check · 2026-05-29_

This report audits the **13 ODR architecture artifacts** against
the master visibility doctrine
(`FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md`) and confirms the ODR
spec remains compliant with FLL doctrine.

**Read-only. No implementation. No spec mutations made by this
report — only conflicts identified and proposed clarifications
recorded.**

---

## 1 · Audit scope

Checked artifacts:

- `ODR_DATA_MODEL.md`
- `ODR_UI_WIREFRAMES.md`
- `ODR_ECOSYSTEM_INTEGRATION_MAP.md`
- `ODR_PDF_LAYOUT_DESIGN.md`
- `ODR_MIGRATION_PLAN.md`
- `ODR_GAP_AUDIT.md`
- `ODR_DELTA_INTEGRATION_SUMMARY.md`
- `ODR_PUBLIC_LINK_DEVICE_CONTINUITY_ADDENDUM.md`
- `ODR_FINAL_GOVERNANCE_ADDENDUM.md`
- `ODR_SPEC_LOCK_READINESS_REVIEW.md`
- `ODR_SPEC_LOCK_CERTIFICATION.md`
- `ODR_COACHING_GUIDANCE_ADDENDUM.md`
- `ODR_COACHING_AND_GUIDANCE_CERTIFICATION.md`

Audit lens: do the surfaces, projectors, and consumer contracts
already in the ODR spec match the per-FLL visibility verbs in
`ROLE_AWARE_OPERATIONAL_VISIBILITY_MATRIX.md`?

---

## 2 · Compliance scorecard

| Topic | Existing ODR spec | FLL doctrine target | Verdict |
|---|---|---|---|
| Foreman own-ODR view | FULL on own; `Mine` view scopes to author | FULL (own) | ✅ aligned |
| GF coordination view (FLL-2) | Implicit (Inbox project-scope) — no explicit GF layer | LIMITED (own crews) | 🟡 clarify-needed |
| Superintendent ODR Center | FULL on assigned projects · Inbox + amend + return + approve | FULL (project) | ✅ aligned |
| Senior Super regional view | FULL regional in governance addendum | FULL (region) | ✅ aligned |
| PM consumption | read-only · aggregate trends · no edit/amend/return/approve | LIMITED (read-only consumption) | ✅ aligned |
| Ops Leadership (FLL-6) | Not explicitly addressed in current ODR spec | SUMMARY (org-wide) | 🟡 clarify-needed |
| Public-link surface scope | 5 endpoints · own-day only · device continuity | (outside FLL · public surface) | ✅ aligned |
| Coaching consumption (PM) | aggregate-only · no per-foreman | LIMITED · per V11 | ✅ aligned |
| FL Training Center metrics | aggregate-only | FULL aggregate at FLL-3+ | ✅ aligned |
| Readiness coaching exposure | foreman own + Super+ visible · aggregated to PM | LIMITED / FULL / SUMMARY ladder | ✅ aligned |
| Photos by tag | governed by photo_governance + role | LIMITED (by FLL) | ✅ aligned |
| Operational Timeline sidecar (Wave 1.1) | PM-token visible on project detail | needs FLL refinement | 🟡 clarify-needed (see TIMELINE_ROLE_VISIBILITY_STANDARD.md) |
| Operational Search consumer | declared planned consumer · no per-FLL contract yet | LIMITED→FULL→SUMMARY ladder | 🟡 clarify-needed |
| Field Memory consumer | declared planned · no per-FLL contract yet | mirror-record visibility (V12) | 🟡 clarify-needed |

**Final tally**: 9 fully aligned · 5 clarification-needed · 0
conflicts. No part of the ODR spec **contradicts** the visibility
doctrine; five areas need a small clarification at spec lock.

---

## 3 · Detailed findings

### F1 · GF (FLL-2) coordination layer (CLARIFY)

The ODR spec treats Foreman and Superintendent as the two field
tiers. The visibility doctrine introduces General Foreman (FLL-2)
as a coordination tier between them.

**Proposed clarification at lock**:

- The FL ODR Inbox (Superintendent surface) gains a documented
  "scope" filter (own crews vs all-project crews). The same
  endpoints serve both FLL-2 (own crews) and FLL-3 (all).
- No new auth role. The `X-FL-Token` already carries scope
  information; doctrinal labels FLL-1/2/3 differ in scope, not in
  token type.
- The Foreman "Mine" view (UI § G4) is unchanged.

### F2 · Ops Leadership (FLL-6) ODR surface (CLARIFY)

ODR spec has no FLL-6 surface today. Visibility doctrine assigns
SUMMARY-only.

**Proposed clarification at lock**:

- A future Admin-Portal "ODR Health" panel renders aggregated
  org-wide trends (completion %, readiness %, constraint frequency,
  safety event rate · per project · per region). Aggregates only.
- Deep-drill from FLL-6 is gated to per-record reads via Admin
  audit logging.
- This surface is **not in V.1 scope** but the contract is
  reserved.

### F3 · Operational Timeline sidecar role visibility (CLARIFY)

The Wave 1.1 Timeline Sidecar currently shows up on PM Project
Detail (PM token). The visibility doctrine asks per-FLL
filtering.

**Proposed clarification at lock**:

- See dedicated artifact `TIMELINE_ROLE_VISIBILITY_STANDARD.md`
  for the full per-FLL contract.
- Sidecar visibility on PM is **LIMITED** (events PM cares about);
  Super sees FULL on FL Portal project page.
- No code change in V.1 — the Wave 1.1 sidecar already shows
  text-first / calmness-locked events; the per-FLL filter applies
  at projector layer when implemented.

### F4 · Operational Search per-FLL contract (CLARIFY)

ODR ecosystem map names Search as a consumer but does not yet
define per-FLL scope.

**Proposed clarification at lock**:

- FLL-1 search → own-project, own-crew, own-author records only.
- FLL-2 → adds own-crews.
- FLL-3 → project scope.
- FLL-4 → region scope.
- FLL-5 → all PM-owned projects.
- FLL-6 → SUMMARY only (aggregated hit counts; per-record drill
  requires Admin escalation).

### F5 · Field Memory per-FLL contract (CLARIFY · V12 anchor)

Field Memory must inherit visibility from the records it stores.

**Proposed clarification at lock**:

- Memory queries default to the caller's FLL scope.
- A Memory pattern that includes data the caller cannot see in
  raw form is either (a) excluded, or (b) returned as SUMMARY
  with no row-level traceback.
- Memory never escalates visibility.

---

## 4 · ODR spec sections requiring small wording adds at lock

These additions are **not required before lock** (no conflict), but
operator may opt to incorporate them at the moment of issuing the
lock command:

1. `ODR_FINAL_GOVERNANCE_ADDENDUM.md § 2` — add an explicit FLL-2
   GF row to the role table, scoped to "own crews on assigned
   project".
2. `ODR_FINAL_GOVERNANCE_ADDENDUM.md § 5` — add FLL-6 (Ops
   Leadership) as a future SUMMARY-only consumer; not in V.1.
3. `ODR_ECOSYSTEM_INTEGRATION_MAP.md` — add a "Per-FLL visibility"
   row to each of the 12 consumer descriptions, referencing this
   matrix.
4. `ODR_PDF_LAYOUT_DESIGN.md § 10` — confirm the existing variant
   list (executive / claims_only / cei_packet / fdot_owner /
   attorney_full) maps to FLL-3+ + FLL-5; FLL-6 sees no PDFs by
   default (SUMMARY only).
5. `ODR_COACHING_GUIDANCE_ADDENDUM.md § 7-§ 8` — re-affirm FL
   Training Center is FLL-3+ and PM coaching consumption is FLL-5;
   no FLL-1 / FLL-2 access to either dashboard.

---

## 5 · No new ODR conflicts found

Specifically, the audit found **no** conflicts in:

- Coaching exposure (O50 + V11 align perfectly)
- Public-link surface scope (no FLL visibility issue · separate
  trust boundary)
- Amendment doctrine (FLL-3+ amend post-24h · doctrine consistent)
- Official record doctrine (independent of visibility · no conflict)
- Foreman signature (per-record, foreman-only · doctrine consistent)
- Attachment doctrine (visibility tracks ODR row · doctrine consistent)

---

## 6 · Verdict

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ✅  ODR ARCHITECTURE COMPLIANT WITH FLL DOCTRINE            ║
║                                                              ║
║   9 / 14 topics fully aligned                                 ║
║   5 / 14 topics need small clarifications at lock time        ║
║   0 conflicts                                                 ║
║                                                              ║
║   Clarifications are additive · do not change the ODR        ║
║   spec's existing contracts.                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

_End of ODR Visibility Alignment Report._
