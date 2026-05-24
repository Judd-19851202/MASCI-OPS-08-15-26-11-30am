# Adoption Risk Matrix (Phase 5B)

**Date:** 2026-05-24
**Question:** Which roles are most likely to resist or under-adopt this
platform, and why?
**Method:** Mapped friction findings against the real workday of each
role. Risk = (workflow weight) × (frequency) × (stress level when used).

---

## Per-role adoption risk

### 🔴 Superintendents · HIGH RISK
**Daily touchpoints:** Daily Report (1×/day) · Incident (0–2×/day) · Toolbox talk (1×/day) · Crew/dispatch check (multiple)
**Risk drivers:**
- Daily Report is their **highest-volume submission** and currently the heaviest form (35 inputs, 7 sections).
- Incidents happen under stress; heavy form compounds the stress.
- Field environment: hot, dusty, gloves, sunlight, sometimes spotty service.
**Adoption failure mode:** *Delegation drift* — super hands "filling out the daily" to a junior who lacks the context, data quality drops, platform usage looks healthy but data is shallow.
**Mitigation lever:** Simplify Daily Report progressive disclosure (collapse rarely-used sections). Validate idempotent submit recovery on flaky LTE.

### 🔴 Foremen · HIGH RISK (when promoted to data entry)
**Daily touchpoints:** Toolbox talk · safety meeting · pre-op inspections · QA/QC inspections (varies)
**Risk drivers:**
- Foremen historically own paper/clipboard workflows. Asking them to switch to phone-based entry is a learning curve regardless of UI quality.
- QA/QC forms are field-conducted — same friction class as DR/Incident.
**Adoption failure mode:** *Quiet refusal* — foremen submit only when audited; the platform's reach is artificially narrow.
**Mitigation lever:** Buddy-up rollout (super completes alongside foreman for the first 2 weeks). NOT a UI fix — operational rollout discipline.

### 🟡 PMs · MEDIUM RISK
**Daily touchpoints:** PM crew compliance check · CAPA visibility · Daily Reports list · employee timeline
**Risk drivers:**
- PM workflows are read-oriented (good — low friction).
- Risk is **information overload** if the PM dashboard tries to show everything.
**Adoption failure mode:** *Dashboard ignored* — if too much data shows up at once, PMs stop opening it.
**Mitigation lever:** Verify PM hub keeps the "what needs my attention TODAY" view at the top. The rest can live behind drilldowns.

### 🟢 Safety · LOW RISK
**Daily touchpoints:** CAPA management · incident review · training records · safety meeting digest
**Risk drivers:** Safety teams tend to be **most willing adopters** because the platform explicitly serves their domain (governance, accountability, compliance).
**Adoption failure mode:** *Power-user drift* — Safety asks for more features than crews can absorb. Resist scope expansion.
**Mitigation lever:** Continue feature-freeze discipline.

### 🟢 Dispatch · LOW RISK
**Daily touchpoints:** Driver readiness · fleet status · daily-reports (logistics) · dispatch assignments
**Risk drivers:** Dispatch staff are typically office-based (desktop adoption is easier than field-mobile).
**Adoption failure mode:** *Dual-system holdover* — dispatch keeps using their existing scheduling tool alongside the platform.
**Mitigation lever:** Ensure dispatch can complete a full shift's planning without leaving the platform.

### 🟢 Field Leadership (FL) · LOW RISK (after Phase 5 P1 W5 closeout)
**Daily touchpoints:** dispatch-today · driver-qualification · daily-reports (FL view, new) · training summary (new) · incidents-recent
**Risk drivers:** FL portal was the last addition (iter314+). It's the most modern, mobile-first portal in the system.
**Adoption failure mode:** *Underused because new* — FL leads may not realize how much information is now available.
**Mitigation lever:** Onboarding walkthrough; explicit weekly summary of "what's new in FL portal".

### 🟡 HR · MEDIUM RISK
**Daily touchpoints:** Employee CRUD · driver qualification dashboard · accountability timeline · training records
**Risk drivers:**
- HR workflows are forms-heavy (employee lifecycle, status changes, terminations).
- Same risk as super: heavy forms = adoption resistance.
**Adoption failure mode:** *Excel side-channel* — HR reverts to spreadsheet for bulk updates, platform falls out of sync.
**Mitigation lever:** Verify bulk-import paths work cleanly (the existing `/api/admin/employees/upload` and driver-qualification import endpoints). HR shouldn't need to enter 50 employees one-by-one.

### 🟡 Shop · MEDIUM RISK
**Daily touchpoints:** Shop part orders · shop console · activity · time-card review
**Risk drivers:**
- Shop staff often have **older devices** and slower data plans.
- Mobile experience untested at scale for shop console.
**Adoption failure mode:** *Slow page load → workaround* — shop staff call instead of using the platform.
**Mitigation lever:** Profile shop-console page load time; ensure under 2s on LTE.

### 🟢 QA/QC · LOW–MEDIUM RISK
**Daily touchpoints:** QA/QC inspection submission · inspection lists
**Risk drivers:** QA/QC forms are mandatory and heavy (concrete forms, rebar, sub work). Field-conducted.
**Adoption failure mode:** Same as Daily Report — delegated or skipped.
**Mitigation lever:** Apply the same DR-style progressive disclosure pattern if/when measured weight justifies.

---

## Cross-role risk patterns

### Pattern A · "Heavy form fatigue"
**Affects:** Superintendents, Foremen, QA/QC.
**Symptom:** Quality erodes faster than usage drops. Users keep submitting, but each submission has fewer fields filled.
**Detection:** Monitor `description`-field length vs structured-field completion rates. If `description` grows while structured fields go empty, the form is too heavy.

### Pattern B · "Notification fatigue"
**Affects:** PMs, Safety, FL.
**Symptom:** Inbox count rises, click-through rate falls.
**Detection:** Track per-role notification read-rates over rolling 7 days. <30% read-rate = notifications too noisy.

### Pattern C · "Dual-system holdover"
**Affects:** Dispatch, HR.
**Symptom:** Platform usage is consistent but reconciliation conversations keep happening ("but Excel said X").
**Detection:** Ask each role at week 2 and week 6 if they still maintain a parallel system.

### Pattern D · "Mobile blindspot"
**Affects:** Anyone using a phone in the field.
**Symptom:** No complaints, but submission timestamps show entries done after returning to the truck/office (not in real-time).
**Detection:** Compare submission timestamp vs event timestamp (incident_date+incident_time, report_date).

---

## Rollout-discipline recommendations (not UI changes)

These are **operational rollout** levers, not software:

1. **Sequence rollout by role.** Start with Safety + Dispatch (lowest risk, highest enthusiasm). Add PMs. Then Supers + Foremen with side-by-side support.
2. **Field shadow before any UI change.** Watch one super do one daily report on their actual phone in actual conditions before authorizing any of the simplification recommendations.
3. **30-day check-in per role.** A standing meeting with each role to surface friction points the audit may have missed.
4. **One "champion" per role.** Identify the most enthusiastic adopter in each role and rely on them for peer training. Don't push management-led mandates.

---

## Summary

| Risk level | Roles |
|---|---|
| 🔴 HIGH | Superintendents · Foremen |
| 🟡 MEDIUM | PMs · HR · Shop · QA/QC |
| 🟢 LOW | Safety · Dispatch · FL |

**Worst-case scenario:** Supers and Foremen quietly under-adopt because
the DR and Incident forms feel like office software. Data quality drops
gradually. Symptoms appear at week 4–6 of full rollout.

**Mitigation strategy:** Watch C1/C2 simplifications in
`WORKFLOW_SIMPLIFICATION_RECOMMENDATIONS.md` carefully. Do not authorize
new feature work that adds form weight to any role currently rated HIGH.
