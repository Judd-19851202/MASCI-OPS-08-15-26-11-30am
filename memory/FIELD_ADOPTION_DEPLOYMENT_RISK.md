# Field Adoption Deployment Risk · Phase 9 · Document 2 of 6

**Date:** 2026-05-24
**Frame:** What goes wrong on Day 1 of production deploy that hurts field adoption? Honest answer per role, with named mitigations.

---

## Day-1 risk by role

### Superintendent · LOW risk
- **Concern:** "I've used the paper form for 12 years. This is new."
- **Mitigation:** Phase 5C compressed Daily Report cuts tap count by 30%. CollapseCards mean optional fields don't even render until you ask for them. Field-direct language throughout.
- **Day-1 evidence:** Phase 6 testing agent confirmed 75-tap median; below the 110-tap psychological barrier.

### Foreman · LOW risk
- **Concern:** "What if my report is wrong? Will I get in trouble?"
- **Mitigation:** Near-miss intake is fast (≈ 30 taps, ≈ 3 min). The platform's tone is field-direct ("Tier-1 report is in. No CAPA has been opened yet."). No corporate punishment language anywhere.
- **Day-1 evidence:** Phase 6 banner says "Ready to submit · follow-up optional for this severity" — explicitly tells the foreman they're done.

### Safety Manager · LOW risk
- **Concern:** "Will the platform let me down on a serious incident?"
- **Mitigation:** Phase 6 submit guard on serious-severity Tier-2 (refused until Root Cause + Corrective Actions + Notifications minimally filled). Phase 5D rose follow-up banner on incident detail. Second-reviewer rule on CAPA verification. `INCIDENT_NO_CAPA` governance finding fires automatically.
- **Day-1 evidence:** Live RBAC matrix shows Safety has full author scope on /api/safety/corrective-actions (200) and /api/incidents (200).

### PM · LOW-MEDIUM risk
- **Concern:** "I can see incidents but can't edit them. Is something broken?"
- **Mitigation:** This is intentional design. AccessDenied surface explains the read-only boundary. LifecycleGuide on PM screens reinforces it.
- **Day-1 risk:** A PM under pressure might call IT/admin assuming a bug. Mitigation: AdminGuide PDF + the 5-question Field Shadow validation specifically probes this in Test 5.

### Dispatcher · LOW risk
- **Concern:** "I need to dispatch a driver who's marked unqualified. Can I override?"
- **Mitigation:** By design impossible. The unqualified gate is a safety violation prevention. Dispatch must resolve the underlying issue (medical, CDL, approval).
- **Day-1 evidence:** /api/incidents 401 for dispatch (correct — they don't author safety records).

### HR · LOW-MEDIUM risk
- **Concern:** "DQ file completion is taking forever."
- **Mitigation:** Accepted reality. FMCSA requires every field. The platform makes it as fast as the regulation allows, not faster. LifecycleGuide per section helps orient new HR staff.
- **Day-1 risk:** First-time HR user may attempt to skip required FMCSA fields and be blocked. Mitigation: validation messages are field-direct, not legalese.

### Field Leadership (FL) · LOW risk
- **Concern:** "I want notifications on my phone like the other portals get."
- **Mitigation:** Phase 5D closed exactly this — FL per-user accounts now hit /api/notifications. Live-verified in `FINAL_PRE_DEPLOYMENT_SYSTEM_AUDIT.md`.
- **Day-1 evidence:** GET /api/notifications with X-FL-Token → 200.

### Admin · LOW risk
- **Concern:** "Will I be flooded with governance noise?"
- **Mitigation:** Phase 7 signal discipline review documented every finding's tier + aggregation rule. 60-day post-deploy re-review pinned.
- **Day-1 evidence:** /api/admin/governance/summary 200; only admin can read it.

---

## Day-1 cross-cutting risks

### Risk 1 · Bell badge overwhelm (MEDIUM)
- **Mechanism:** A backlog of governance findings + open CAPAs + driver-qualification alerts could pile up on the Safety + Admin bells the moment people log in.
- **Symptom:** "60+ unread" badge → user gives up on the bell.
- **Mitigation:** P2 item in `REMAINING_HIGH_VALUE_FIXES.md` — "50+ · review and acknowledge" cap (1 hour of work). Recommended PRE-deploy if backlog volume is known to be high.
- **Acceptance:** If the 50+ cap is deferred, monitor bell counts during first week and ship the cap if needed.

### Risk 2 · Spanish-speaking crews encounter EN-only edge strings (LOW)
- **Mechanism:** Phase 6 added 11 EN→ES keys for the new completion banners. Older strings spot-checked, but a small number of legacy strings may still lack ES translations.
- **Symptom:** Mixed-language banner ("Status · Ready to submit" partly EN, partly ES).
- **Mitigation:** Fall-back behavior of `t()` returns the EN key when ES is missing — degrades gracefully, no broken UI.
- **Acceptance:** Track via field-shadow Test 1 (Superintendent at 390 px); add missing keys reactively.

### Risk 3 · Foreman submits a near-miss that should have been medical (HIGH severity, accepted)
- **Mechanism:** Phase 8 `FIELD_ADOPTION_RISK_REVIEW.md` named this as the accepted residual risk.
- **Symptom:** Under-classification at intake; Safety reviewer catches it on second pass.
- **Mitigation:** `INCIDENT_NO_CAPA` finding flags serious incidents without follow-up CAPAs. Human review is the final gate.
- **Acceptance:** No software can fully prevent under-classification at intake. The platform does the most a platform can do.

### Risk 4 · Memorial Day modal intercepts first click (LOW, time-bounded)
- **Mechanism:** Public-facing remembrance modal renders on first page load. The testing agent's Phase 5D and Phase 6 reports both surfaced this as a quirk.
- **Symptom:** First click on a severity button doesn't register because the dismiss icon catches it.
- **Mitigation:** Modal has an explicit close button (×) and is dismissible with Escape. Date-gated — will disappear naturally after Memorial Day weekend.
- **Acceptance:** Operationally invisible after 2026-05-27.

### Risk 5 · A user under pressure tries to bypass the Tier-2 lock on a serious incident (HIGH, prevented)
- **Mechanism:** User wants to submit Tier-1 only and complete Tier-2 "later."
- **Symptom:** Hits submit, gets refusal toast, frustration.
- **Mitigation:** This is the desired behavior. Phase 6 submit guard exists precisely to prevent under-completion of serious-incident reports. Toast wording: "Complete the highlighted section or mark it not used today."
- **Acceptance:** This friction is operationally protective, not a bug.

---

## Field-shadow validation queue

Per `FIELD_SHADOW_VALIDATION_KIT.md`, the following five role-tests should run during the first 14 days of production deploy:

| Day | Test | Critical pass criteria |
|---|---|---|
| 1-3 | Superintendent · Daily Report | ≤ 8 min submission; no accidental schedule-delay-without-detail |
| 2-4 | Foreman · Near-miss intake | ≤ 4 min; no unnecessary Tier-2 attempted |
| 5-7 | Safety Manager · Serious incident | First submit blocked; user understood reason without help |
| 7-10 | Dispatcher · Driver readiness | ≤ 3 min unqualified-driver resolution |
| 10-14 | PM · Crew compliance | Correctly identifies read-only boundary; no edit attempts |

A failure in any test escalates to PRODUCTION_RISK_REGISTER.md.

---

## Confidence level

| Axis | Confidence |
|---|---|
| Field user comprehension | HIGH |
| Operational completion rate | HIGH |
| Severity under-classification protection | MEDIUM (accepted risk) |
| Cross-portal navigation discoverability | HIGH |
| Mobile usability | HIGH (Phase 6 mobile verified) |
| EN+ES bilingual coverage | HIGH (Phase 5D/6 keys added; spot-check passed) |
| Bell volume manageability | MEDIUM (50+ cap recommended but not yet shipped) |

**Net field adoption deployment risk: LOW with one MEDIUM item (bell volume).**

---

## Recommended pre-deploy actions

1. **Ship the 50+ bell cap** before deploy IF current production-bound dataset has any role with > 50 unread notifications projected on Day 1. Otherwise defer to first-week observation.
2. **Pin the 5 field-shadow tests** in the operator's calendar for the appropriate days.
3. **Communicate the Tier-2 lock behavior** to Safety + Admin before deploy so first-day surprise is converted to first-day confidence.

Everything else: deploy as-is.
