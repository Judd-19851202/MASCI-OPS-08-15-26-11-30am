# ITER501 · QUICK WINS

**Date**: 2026-06-02T21:06 UTC
**Mode**: READ-ONLY synthesis
**Authority**: OMEGA ITER501

Top 20 quick-win fixes ranked by ROI = (frequency × frustration × user-count) / effort. All scoped READ-ONLY identification; no code applied here.

---

## Under 1 HOUR (5 items)

| # | Fix | LOC est | Surfaces | ROI rationale |
|--:|---|--:|---|---|
| 1 | **Dispatch drag-drop per-row toast** | ≤ 30 | Dispatch page | Daily dispatcher pain · one `toast.success(\`Reassigned to ${crew}\`)` after the drop event |
| 2 | **JHA poster print-queue toast duration** | ≤ 5 | JHA poster | Bump `duration: 6000` → `12000` so it doesn't auto-dismiss before user can read |
| 3 | **Add tooltip on disabled admin-governance buttons** | ≤ 40 | Admin pages | One reusable `<Tooltip>` wrap on every `disabled` button stating why |
| 4 | **Driver-qualification expiring-soon row badge** | ≤ 60 | Driver-qual list | One conditional `<Badge variant="amber">` per row when `review_due < now+30d` |
| 5 | **Notifications digest "saved" banner** | ≤ 20 | Admin → Notifications | One `toast.success(t("Digest preferences saved"))` on the form's save handler |

**Combined effort**: < 4 hours total · **closes 5 of the Top 25** (#14, #17, #19's tooltip half, #24, plus item #22 from the dead-end register).

---

## Under 4 HOURS (8 items)

| # | Fix | LOC est | Surfaces | ROI rationale |
|--:|---|--:|---|---|
| 6 | **Promote Reopen out of kebab** on Incident detail | ≤ 60 | Incident detail | Top-level button + `LifecyclePanel` already on QA/QC; mirror it |
| 7 | **Promote Reopen out of kebab** on QA/QC detail | ≤ 40 | QA/QC detail | Already has LifecyclePanel; surface Reopen prominently |
| 8 | **Promote Reopen out of kebab** on Site Inspection detail | ≤ 60 | Site Inspection detail | Same pattern |
| 9 | **Reactivate / Rehire merged dialog** | ≤ 50 | HR Employees | Single dialog with explicit "this is a rehire (resets dates)" vs "this is a reactivation (preserves dates)" radio · was Rank #9 in ITER500 |
| 10 | **PM Crew Compliance promoted in PmHub** | ≤ 30 | PmHub | Move tile out of "more" section into the top row |
| 11 | **AdminHub grouping** | ≤ 80 | AdminHub.jsx | Group 35+ tiles by category (Governance · Imports · Notifications · Webhooks · Audit) |
| 12 | **Audit-log "filter active" chip-stack** | ≤ 80 | Admin Audit Log | Render selected filters as removable chips above the table |
| 13 | **Time-off approval verb button** | ≤ 50 | Time-off list | Replace checkbox with explicit Approve / Reject buttons + toast |

**Combined effort**: ~ 1 sprint-day · **closes 8 of the Top 25** (#2 partial, #3, #5, #15, #19, #21, plus discoverability gains).

---

## Under 1 DAY (7 items)

| # | Fix | LOC est | Surfaces | ROI rationale |
|--:|---|--:|---|---|
| 14 | **Approve / Reject promoted on Dispatch list** | ≤ 100 | Dispatch | Top-level buttons replacing dropdown row-action |
| 15 | **Approve / Reject promoted on PO Requests** | ≤ 100 | PO Requests | Same · PO reject also requires reason field (closes #18) |
| 16 | **Asset-transfer receive verb button** | ≤ 60 | Asset Transfer | Replace checkbox with Receive / Reject buttons + toast |
| 17 | **Sub / Vendor archive workflow** | ≤ 150 | Sub/Vendor | One archive button + status filter + `is_archived` field is already in schema |
| 18 | **Hub.jsx grouping** | ≤ 150 | Hub.jsx | Group by role-relevance: Daily / Compliance / People / Equipment / Procurement |
| 19 | **Verb harmonization pass (Save / Submit)** | ~ 300 (string sweep) | Platform-wide | One pass through `t("Save")`, `t("Submit")`, `t("Create")` per page · doctrine: Submit for transactional, Save for ongoing |
| 20 | **Constraint LifecyclePanel substrate** (Rank #2 from ITER500) | ≤ 50 | Constraint detail | Reuse existing LifecyclePanel · Reopen + status history surface |

**Combined effort**: ~ 1 sprint week · **closes 12 of the Top 25** (#2, #6, #10, #16, #18, #20, #22, #23, plus many secondary friction items).

---

## All-quick-wins composite

| Tier | Items | Effort | Top 25 closed |
|---|---:|---|---:|
| < 1 hr | 5 | ~ 4 hr | 5 |
| < 4 hr | 8 | ~ 1 day | 8 |
| < 1 day | 7 | ~ 1 week | 12 |
| **Total** | **20** | **~ 2 weeks** | **~ 20 of Top 25** |

A 2-week focused sprint on this Quick-Wins list resolves roughly **80% of the residual Top 25** without touching backend, schema, or workflow.

---

## What is NOT a quick win (deliberately excluded)

* **OC-005 JHP Acknowledgement Ledger build** — new module, ~ 1 sprint cycle, backend changes
* **Universal undo / status-reversal verb** — touches every lifecycle module, requires schema thinking
* **5-statuses-for-not-working** unification — HR doctrine work, requires Customer #2 / White Label input
* **White Label readiness** — separate multi-week program
* **Accountability Chain Phase 1B** — larger build
* **Dual-field cleanup** (e.g., Incident `lifecycle_state` + `is_closed`) — requires migration

---

End of quick-wins.
