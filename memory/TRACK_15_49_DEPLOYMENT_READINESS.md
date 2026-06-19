# TRACK 15.49 · Phase 8 · Deployment Readiness

**Status:** 🟢 GREEN · evidence-backed · all nine closure questions answered.

## The final certification question
> "Can MASCI demonstrate not only how an incident occurred, but also how the company responded, investigated, corrected, followed up, and closed the matter?"

## Answer
🟢 **YES.**

## The nine closure questions
| # | Question | Answer | Evidence |
|---|---|:---:|---|
| 1 | What happened? | ✅ | Incident record: description + immediate_cause + contributing_factors + root_cause_notes. PDF Section 2. |
| 2 | Who was involved? | ✅ | person_name / person_role / person_employer + witness sub-doc (4-row example: foreman + operator + public + deputy with phone/email/employer/role). PDF Section 3. |
| 3 | What actions were taken? | ✅ | immediate_actions_taken + state-event transitions (open → investigating → review → closed). PDF Sections 2 + 6. |
| 4 | What corrective actions occurred? | ✅ | Linked CAPAs via `source_kind=incident` with title / owner / due / status / completion. PDF Section 7. |
| 5 | What follow-up occurred? | ✅ | **Aftercare task chain** · 3 auto-issued tasks (24h HR welfare · 72h Safety witness · 7d Safety investigator) with `task_key` labels. PDF Section 8 (NEW in 15.49). |
| 6 | Whether employees were checked on afterward? | ✅ | `incident.aftercare.welfare_24h` task assigned to HR with Critical priority + completion timestamp on PDF. |
| 7 | Whether witnesses were followed up with? | ✅ | `incident.aftercare.witness_72h` task to Safety + witness contact info (phone/email/employer) on every witness row. |
| 8 | Whether CAPAs were completed? | ✅ | Linked CAPA `status` + `completed_at` rendered on PDF Section 7. |
| 9 | Whether the incident was truly closed? | ✅ | Final state-event row "→ closed" with actor + reason + timestamp. PDF Section 6. |

## Risk register at deployment
| Risk | Severity | Mitigation |
|---|---|---|
| Aftercare task not completed (organizational discipline) | LOW | Platform doesn't enforce — operators must own the work. Overdue tasks flag on bell + appear in overdue-CAPA tile if past due_at. |
| Witness status enum not yet structured | LOW | Track 15.50 candidate · B-02. Today the task chain ensures the follow-up happens. |
| Welfare note convenience UI deferred | LOW | Track 15.50 candidate · B-01. Today HR adds notes via lifecycle endpoint. |
| Aftercare task chain depends on `task_key` field — old client versions might not send it | NONE | `task_key` is optional; legacy clients continue to work. |

## Acceptance gates (per directive)
- ✅ Incident lifecycle certified.
- ✅ Employee follow-up certified.
- ✅ Witness follow-up certified.
- ✅ Notification chain certified.
- ✅ PDF defensibility certified.
- ✅ Executive visibility audited.
- ✅ No HIGH-severity gaps remain undisclosed.

**All seven gates met. Track 15.49 closes GREEN. The aftercare chain is live in preview and ready for production.**
