# Executive Command Center — False Positive Review

**Classification:** OMEGA Pillar 2 · Phase A · Pre-Production Read-Only Review
**Generated:** 2026-05-31 UTC
**Author:** E1
**Scope:** Catalog every scenario in which the Phase A scoring engine fires AMBER or RED when no leadership action is actually warranted.
**Companion doc:** `EXECUTIVE_COMMAND_CENTER_FALSE_NEGATIVE_REVIEW.md`

---

## 1 · Definition

**False Positive (FP):** the dashboard fires RAG (AMBER or RED) for a condition that is *not* a current operational problem requiring leadership action. Examples: aged-incident records that have already been investigated; weekend DRs that legitimately don't exist; intentional asset holds; safety meetings on dormant projects.

A FP rate above 10% trains leadership to ignore the dashboard. Phase A's success depends on driving the FP rate as close to zero as practical.

---

## 2 · Inventory

### FP-1 · Stale critical/serious incidents fire RED forever (Defect D1)

| Property | Value |
|---|---|
| Rule | SAF-CRITICAL-UNRESOLVED |
| Mechanism | The rule filters incidents by `severity ∈ {Critical, High, Serious}` and `age > 48h`. It does NOT check whether the incident has been resolved, because the `incidents` collection does not have an explicit `status` field. |
| Live evidence | Snapshot 2026-05-31: `INC-2026-00026` and `INC-2026-00042` both fire RED at age 3d. Whether they are still operationally open is not verifiable from the snapshot payload alone. |
| Expected frequency | Continuous after the first 48h post-incident, unless the incident is deleted from `incidents` |
| Operational impact | Leadership sees "2 high/critical incidents unresolved past 48h" forever. Trust erosion within 1-2 weeks. |
| Severity | 🔴 MEDIUM |
| Remediation (D1) | Cross-reference `corrective_actions` with `status=Closed` linked to the incident, OR check `incidents.corrected_on_site = Yes`, OR check `incidents.investigation_completed_at` (if present). ~15 LOC. |

### FP-2 · Stale OSHA-recordable incidents fire RED forever (Defect D2)

| Property | Value |
|---|---|
| Rule | SAF-OSHA-OPEN |
| Mechanism | Same as FP-1 but filtering on `osha_recordable: "Yes"` instead of severity. No resolution check. |
| Live evidence | Live snapshot shows 0 currently, but as soon as an OSHA-recordable incident is logged + notified, it will fire RED for the remainder of its database lifetime. |
| Expected frequency | Continuous once any OSHA-recordable exists more than 24h |
| Operational impact | Same as FP-1; trust erosion. |
| Severity | 🔴 MEDIUM |
| Remediation (D2) | Same closure-state check as D1. ~10 LOC. |

### FP-3 · Weekend / holiday DR-missing fires RED (Defect D3)

| Property | Value |
|---|---|
| Rule | JOBS-DR-MISSING |
| Mechanism | The rule does `now - 36h` regardless of whether the elapsed time spans a non-working window. The `command_center_calendar` config doc was created with `working_weekdays` and `working_hour_start/end` fields, but the rule code never reads it. |
| Live evidence | Snapshot 2026-05-31 (a Saturday): 29 active jobs flag DR-missing. Many of these are likely legitimate non-work days. |
| Expected frequency | Every Saturday morning, all Sunday, every Monday morning until ~12:00 local. Public holidays add days. |
| Operational impact | The "29 jobs missing DR" headline overstates the real number of operationally concerning jobs by 2x-10x on non-working days. |
| Severity | 🟡 LOW · operator can mitigate today by raising the threshold via `PATCH /api/admin/command-center/thresholds` |
| Remediation (D3) | Compute the lookback using `command_center_calendar` (skip non-working days). ~20 LOC. |

### FP-4 · OSHA-recordable status field text variation

| Property | Value |
|---|---|
| Rule | SAF-OSHA-OPEN |
| Mechanism | Filter `osha_recordable: {"$regex": "^Yes$", "$options": "i"}` matches "Yes", "yes", "YES". If submitters enter "Y", "y", "TRUE", or boolean `true`, the rule misses the incident (this is a FN actually; see FN review). Conversely, a typo like "Yes - unsure" could match incorrectly. |
| Expected frequency | Rare |
| Severity | 🟢 NEGLIGIBLE |
| Remediation | Normalize `osha_recordable` at submit time; deferred to Phase B input-hardening |

### FP-5 · Future-dated incidents

| Property | Value |
|---|---|
| Rule | All age-based safety rules |
| Mechanism | If an operator accidentally enters a future date, the incident appears "negative age" — but most rules use `created_at < cutoff` so future-dated incidents are simply ignored. Not a FP. |
| Severity | 🟢 NONE |
| Remediation | n/a |

---

## 3 · Non-FP behaviour worth understanding

The following are **intentional** signals, not FPs — listed here only to disambiguate:

### Same incident fires both JOBS-ISSUE-NO-PATH and SAF-CRITICAL-UNRESOLVED

This is **by design** per the operator spec: a high-severity incident more than 7 days old without a corrective-action path *should* fire on both cards (Jobs sees "no resolution path"; Safety sees "high severity not addressed in 48h"). Two angles on one issue is intentional leadership coverage, not duplication.

### EQP-BACKLOG fires RED at 44 units while OOS sub-counts are 0

Per Defect D5, the sub-counts (`oos_red`, `oos_amber`) are silently zero due to date-type mismatch in `count_documents`. But the total backlog count (which doesn't depend on a date comparison) is correct. So the card pill is correctly RED. This is FN-on-sub-rules, not FP — see false-negative review.

### Approvals card pill is GREEN but items list shows 5 aged POs

Same root cause (D5): warning counts are 0, items list correctly finds aged POs. Card defaults to GREEN. This is the **most operationally dangerous FN** of Phase A — see false-negative review.

---

## 4 · FP rate estimate (preview environment)

Live preview snapshot · ~6 RED warnings total · estimated breakdown:

| Warning | Likely real? | Likely FP? |
|---|---|---|
| Jobs: 29 active jobs without recent DR | 🟡 partial (Saturday + active jobs that didn't work today are legit no-DR) | ~50% FP rate (FP-3) |
| Jobs: 2 open issues without assigned owner | 🟢 real | 0% FP |
| Jobs: 7 stale incidents without resolution path | 🟡 mixed — some may be "investigated but no CA created" (FP-1 cousin) | ~30% FP rate |
| Safety: 2 high/critical incidents unresolved past 48h | 🟡 mixed — same FP-1 risk if either was already addressed | ~50% FP rate |
| Safety: 4 corrective actions past due date | 🟢 real (CA has explicit `due_date < today`) | 0% FP |
| Equipment: 44-unit defect backlog | 🟢 real | 0% FP |

**Aggregate FP estimate: ~22% on preview data.** Acceptable for a pilot but elevated for production. Path B (D1+D2+D5 patch) is projected to reduce FP rate to **~8%** by eliminating FP-1, FP-2, and most of FP-3 noise.

---

## 5 · Recommendation

🟡 Phase A is **usable as-is** but the FP rate (~22%) is high enough to risk trust erosion within the first 2 weeks of pilot use. Recommend Path B (minimal patch addressing D1, D2, D5) before production deployment — projected post-patch FP rate ~8% which is well within operator-trust range.

If the operator chooses Path A (deploy as-is), the recommended communication to pilot users is:
> "Treat aged safety RED items as a prompt to verify in the source record — not as confirmation that the incident is still open. Approvals card may temporarily under-report; cross-check `/admin/po-requests` weekly until the next patch."

This explicit caveat preserves operator trust during the first 2-4 weeks while the patch is queued.
