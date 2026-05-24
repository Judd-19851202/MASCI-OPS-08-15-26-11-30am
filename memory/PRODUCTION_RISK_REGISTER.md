# Production Risk Register

**Date:** 2026-05-24
**Source:** Live deployment readiness audit findings.

---

## R1 · `PATCH /api/incidents/{id}` not implemented

**Severity:** 🟡 MEDIUM (planning-doc gap, not a current behavior bug)
**Surface:** Backend `routes/safety.py`
**Finding:** `PATCH /api/incidents/{id}` returns 405. Only POST is wired.
**Phase 5C planning doc impact:** `INCIDENT_FAST_ENTRY_STRATEGY.md` and `PHASE5C_WORKFLOW_COMPRESSION_PLAN.md` Iter 4 described a "Tier-2 PATCH follow-up enrichment" pattern. That backend capability does not exist today.
**Actual current behavior:** The Phase 5C.1 `CollapseCard` implementation submits **all Tier-1 + Tier-2 fields in a single initial POST**. The cards are visual disclosure only. Data fidelity is 100% on first submit. Therefore the missing PATCH does NOT affect any user-visible workflow.
**Production impact:** ZERO today.
**Future impact:** If a workflow ever needs "save now, enrich later" for incidents (e.g., a super submits Tier-1 from the field then Safety adds Tier-2 from the office), backend PATCH will need to be added.
**Recommended action:** Update planning docs to reflect "all fields in one POST" reality; defer backend PATCH until a real workflow need surfaces.
**Mitigation today:** None required.

---

## R2 · Operational Glossary asset not found at expected path

**Severity:** 🟢 LOW
**Surface:** Frontend
**Finding:** Audit search for `/app/frontend/src/lib/glossary*` and `/app/frontend/src/components/Glossary*` returned no matches.
**Interpretation:** Operational terminology is likely inlined per-component (in LifecycleGuide content, label strings, etc.) rather than centralized in a single glossary asset.
**Production impact:** Functional — users see consistent terminology through existing component code.
**Future impact:** Without a single source of truth, terminology drift may accumulate (Phase 5 directive: "operational language convergence" was flagged earlier).
**Recommended action:** Post-deploy: consider creating `/app/frontend/src/lib/operationalGlossary.js` as a single keyed export, then refactor existing copy to reference it. Low priority; do not block deploy.
**Mitigation today:** None required.

---

## R3 · FL token cannot access `/api/notifications`

**Severity:** 🟢 LOW
**Surface:** Backend `routes/tasks_notifications.py`
**Finding:** The portal-isolation matrix showed `GET /api/notifications` returns 200 for admin/pm/safety/hr/dispatch but **401 for FL**.
**Interpretation:** FL portal uses its own dedicated surface (`/api/field-leadership/portal/notifications-recent`) instead of the shared `/api/notifications` route.
**Production impact:** No user-visible regression — FL users see notifications via their portal-specific surface (verified live: 200).
**Inconsistency cost:** Documentation friction. The "any portal token works on /api/notifications" expectation set by other roles doesn't apply to FL.
**Recommended action:** Either add FL to the `make_require_any_portal_token` factory used by `/api/notifications`, OR document the FL-specific path as the canonical FL notification source in the `OPERATIONAL_ADOPTION_HARDENING.md` notes.
**Mitigation today:** None required.

---

## R4 · Inherited full-suite isolation debt (existing, documented)

**Severity:** 🟢 LOW (informational only — not new)
**Source:** 233 failures + ~54 errors in `pytest tests/` full run.
**Finding:** Predates Phase 4D iter382. Test isolation / DB teardown / order dependencies in legacy tests. Documented in `PHASE4D_EXTRACTION_TRACKER.md` "Testing Reality Reset" section.
**Production impact:** ZERO — these are test-suite hygiene issues, not application behavior.
**Recommended action:** Separate quality-debt project. Not in deploy scope.
**Mitigation today:** None required.

---

## R5 · No real-device mobile validation performed

**Severity:** 🟡 MEDIUM (uncertainty, not a known defect)
**Source:** Audit time-box + environment limitations.
**Finding:** Playwright viewport-flag did not take effect for screenshot capture; body-text rendered correctly but actual phone-device sunlight/glove/intermittent-LTE testing was not performed in this audit.
**Production impact:** UNKNOWN — Phase 5B audit noted Daily Report and Incident forms as "🔴 HIGH adoption risk" pending field shadow. Phase 5C/5C.1 compression should have lowered that risk, but no live confirmation exists yet.
**Recommended action:** Within first 48 hours post-deploy, shadow one supervisor through one Daily Report and one Near Miss submission on their actual phone. Capture tap count and completion time. Compare against the estimates in `FIELD_FRICTION_MEASUREMENT.md`.
**Mitigation today:** Document this gap in deploy-readiness so post-deploy monitoring can fill it.

---

## R6 · Memorial Day landing-page content is the current public root

**Severity:** 🟢 LOW (intentional)
**Surface:** Frontend public root.
**Finding:** Live curl shows the public landing renders the Memorial Day remembrance content (bilingual). Body title is "MASCI Operations Platform · Run every job. Control every detail. Protect everything."
**Interpretation:** Intentional Phase 5 addition (operational language convergence). Not a defect.
**Recommended action:** Verify with operator that this remembrance content is appropriate to be visible on the public root during the production launch (e.g., not season-bound).
**Mitigation today:** Operator decision.

---

## Risk summary

| ID | Severity | Type | Blocking? |
|---|---|---|---|
| R1 | 🟡 MEDIUM | Planning-doc drift (no current impact) | NO |
| R2 | 🟢 LOW | Asset organization | NO |
| R3 | 🟢 LOW | API consistency | NO |
| R4 | 🟢 LOW | Inherited test debt | NO |
| R5 | 🟡 MEDIUM | Untested condition | NO |
| R6 | 🟢 LOW | Content review | NO |

**Total risks:** 6 · **Blocking:** 0.
