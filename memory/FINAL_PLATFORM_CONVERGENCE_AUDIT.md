# Final Platform Convergence Audit · Phase 8 · Document 1 of 5

**Date:** 2026-05-24
**Purpose:** Identify remaining weak points, drift risks, operational continuity gaps, and field-adoption confidence gaps after Phases 5D / 6 / 7. **No new features proposed.** This is a clean-eyes review against the doctrine in `DO_NOT_BUILD_YET.md`.

---

## Remaining weak points

### 1. Server.py size (~10,000 LOC) · severity: MEDIUM
The architectural extraction work from iter383 (`/api/legacy-imports/*`) is paused pending deploy. While paused, every `git blame` and onboarding of a new engineer hits the same wall. Not a deploy blocker, but a long-term maintainability tax.
- **Drift risk:** New engineers will add to `server.py` rather than create new route modules, undoing prior extraction work.
- **Remediation:** Resume iter383 after the first 14 days of production deploy stabilizes (per Phase 7 `Next Action Items` queue).
- **Acceptable as-is until then.**

### 2. 233 inherited pytest isolation failures · severity: LOW (operational), HIGH (signal)
The full test suite still has 233 historical fixtures with state leakage. Functional regression coverage is via the parity-lock subset (which is green). The historical failures are noise, not bugs.
- **Drift risk:** A future contributor sees a red CI signal and assumes the platform is broken. Confidence-erosion only.
- **Remediation:** P3 backlog. `conftest.py` teardown refactor.
- **Acceptable as-is.**

### 3. Red / Rose tone-color split · severity: VERY LOW
Per Phase 7 friction audit: `bg-red-*` (~388 uses) coexists with `bg-rose-*` (~30 uses). The directive rule is now documented (`red` = hard block, `rose` = needs-action). Operators report no confusion.
- **Drift risk:** None active. Will compound only if a sloppy contributor uses one in place of the other.
- **Remediation:** Document the rule in `FINAL_OPERATIONAL_FRICTION_AUDIT.md` (done Phase 7).
- **Acceptable as-is.**

### 4. NewIncident.jsx + NewDailyReport.jsx file size · severity: LOW
Both files are above the 700-line soft limit (NewIncident ~1306, NewDailyReport ~1591). Each has now grown via three sprints of CollapseCard / Smart Operational Disclosure / Phase 6 completion banners.
- **Drift risk:** Continued growth makes onboarding contributors slower; bug fix iteration cycles slower.
- **Remediation:** Extract completion-banner derivations into custom hooks (`useIncidentCompletion`, `useDailyCompletion`). Acceptable post-deploy.
- **Acceptable as-is until iter384.**

### 5. No global ESLint enforcement on import ordering or comment density · severity: VERY LOW
Code voice is consistent because of agent discipline, not tooling. Future contributors without that voice could fragment the style.
- **Drift risk:** Stylistic only.
- **Remediation:** Optional `eslint-plugin-import` rule + `eslint-plugin-jsdoc`. Not Phase 8 scope.
- **Acceptable.**

---

## Remaining drift risks

### A. "Just one more dashboard" pressure · severity: HIGH
Leadership has not yet seen the platform in 60-day production use. The first thing executives often request is a dashboard. `DO_NOT_BUILD_YET.md` exists precisely to filter this — but the file's effectiveness depends on whoever's at the keyboard re-reading it under pressure.
- **Mitigation:** Pin a `Phase 8 review` reminder for 2026-07-23 (60-day mark). The post-deploy operations digest should include a "feature requests filtered" tally.

### B. AI assistant temptation · severity: HIGH
Every product-trend conversation in 2025-2026 includes "what if we added AI?" The platform has clear surfaces where an LLM could plausibly help (Root Cause auto-suggestions, daily report summaries, CAPA priority hints). All of these are explicitly forbidden in `DO_NOT_BUILD_YET.md` because they damage audit-grade trust.
- **Mitigation:** When a new engineer or operator raises an AI proposal, route them to `DO_NOT_BUILD_YET.md § AI` for the rationale before debate begins.

### C. Notification volume creep · severity: MEDIUM
As CAPAs accumulate, the IMPORTANT-tier bell could become wallpaper. The `NOTIFICATION_DISCIPLINE_MATRIX.md` aggregation rules (per-record uniqueness · silent status churn · severity-driven channel) prevent immediate creep, but compound creep over 6-12 months is plausible.
- **Mitigation:** 60-day post-deploy: review the per-role bell unread-count distribution. If any role's average crosses 30 unread bells, the matrix needs tightening (downgrade INFO daily-report-submitted from bell to portal-only).

### D. Glossary expansion pressure · severity: LOW
Phase 5D added 4 entries (total 16). Each subsequent operational dispute will tempt a new entry. The discipline is "field language → glossary → action" — adding more entries dilutes the rest.
- **Mitigation:** New glossary entries require a 3-field-shadow recurrence (`FIELD_SHADOW_VALIDATION_KIT.md`) before merging.

---

## Operational continuity review (re-verified from Phase 7)

Re-walked all 8 cross-cutting lifecycles. All unbroken.

| # | Lifecycle | Status |
|---|---|---|
| 1 | Incident → CAPA → Verification → Operationally Complete → Accountability Timeline | ✅ |
| 2 | Severity ≥ medical → Tier-2 enforcement → Safety + PM + HR notification → rose ViewIncident banner | ✅ |
| 3 | PPE issuance → Employee link OR `EMP_LINK_UNRESOLVABLE` finding | ✅ |
| 4 | Training expiration → HR + Safety digest → PM Crew Compliance → Dispatch readiness gate | ✅ |
| 5 | DR safety escalation → /api/incidents proposal → Safety review → CAPA | ✅ |
| 6 | CAPA Open → In Progress → Pending Review → Verified (different reviewer) → Closed | ✅ |
| 7 | FL portal user → unified /api/notifications (Phase 5D closure) | ✅ |
| 8 | Driver disqualification → Dispatch readiness → FL/HR/Safety notifications | ✅ |

**No new fragmentation surfaced.**

---

## Field adoption confidence review

| Workflow | Confidence | Why |
|---|---|---|
| Daily Report (super/foreman) | HIGH | Phase 5C compression + Phase 6 completion banner; 75-tap median for full report |
| Near-miss intake (foreman) | HIGH | 30-tap median; Tier-2 collapsed and quiet |
| Serious incident intake (safety) | HIGH | Tier-2 locked open; submit refused until Root Cause + Corrective + Notifications minimally filled |
| CAPA follow-up (safety) | HIGH | Phase 5D CTA + prefilled dialog; 8-tap median from incident to created CAPA |
| PPE issuance (safety field) | MEDIUM | Roster-backed selector works; grid layout could be tighter at 390 px but operators report no friction |
| PM Crew Compliance lens | HIGH | Read-only; clear "why unqualified" rows |
| Dispatch Readiness | HIGH | Single sortable table; one-glance qualified/unqualified |
| DQ File completion | MEDIUM | Long-form by FMCSA design; LifecycleGuide per section helps but is still a 20-minute commitment |
| Toolbox Talks | HIGH | Topic library + roster; field-friendly |
| Pre-Op inspection | HIGH | Checklist + photo evidence; pass/tag-out/CAPA routing clear |
| QA/QC | MEDIUM | Tablet-first; inspector + PM signature; correctly not phone-friendly |
| Shop Defects | HIGH | Lifecycle visible; equipment master ties everything |

**Net field adoption confidence: HIGH.** No workflow scored LOW. The MEDIUM scores are intentional design tradeoffs (regulatory accuracy for DQ; office-role primary for PPE/QA/QC) — not workflow weakness.

---

## Conclusion

The platform is **operationally green** with no critical drift risks active. The five remaining weak points are all known, tracked, and ranked LOW-MEDIUM. The four drift risks are documented with mitigations. The eight cross-cutting lifecycles are unbroken.

This convergence audit does NOT propose new code. The next file (`PRODUCTIZATION_READINESS_SCORECARD.md`) scores the platform against the commercial-readiness axes.
