# STATUS CANONICAL DICTIONARY

**Authority**: FOCP MASTER PROGRAM · Phase 8
**Mode**: READ-ONLY inventory + proposed canonical vocabulary
**Date verified**: 2026-06-02

---

## Observed status vocabulary (source-direct inventory)

From `grep` of `STATUSES` constants and string literals across `/app/backend/` and `/app/frontend/src`:

### Backend status enums (deduplicated)

| Source | Vocabulary |
|---|---|
| `operational_constraints.py` | `open`, `monitoring`, `resolved`, `void` |
| `document_expirations.py` | `Current`, `Expiring Soon`, `Expired` |
| FleetDVIR | `Pass`, `Fail`, `Needs Service`, `Out of Service`, `(empty)` |
| Employee lifecycle | `active`, `on_leave`, `suspended`, `terminated`, `resigned`, `inactive` (6 states) |
| Time-Off | `pending`, `approved`, `denied`, `need_info` |
| Asset Transfer | `Requested`, `Approved`, `In Transit`, `Received`, `Closed`, `Rejected`, `Cancelled` |
| PO Request | `Submitted`, `Approved`, `Clarify`, `Rejected`, `Closed`, `Cancelled` |
| Incident lifecycle | `open`, `in_review`, `corrective_pending`, `closed`, `reopened` (state-machine) |
| QA/QC lifecycle | `IN_PROGRESS`, `DEFICIENCY_RAISED`, `PENDING_RE_INSPECTION`, `CLOSED` |
| Site Inspection lifecycle | `IN_PROGRESS`, `FINDINGS_RAISED`, `PENDING_RE_INSPECTION`, `CLOSED` |
| Daily Report lifecycle | similar but distinct state names |
| Payroll Variance | similar set |
| HR Queue | `pending`, `needs_review` (FRICTION #17 — ambiguous dual-state) |

### Distinct status words observed

`active`, `approved`, `Cancelled`, `closed`, `CLOSED`, `Clarify`, `corrective_pending`, `Current`, `DEFICIENCY_RAISED`, `denied`, `Expired`, `Expiring Soon`, `Fail`, `FINDINGS_RAISED`, `inactive`, `in_review`, `IN_PROGRESS`, `In Transit`, `monitoring`, `needs_review`, `need_info`, `Needs Service`, `on_leave`, `open`, `Out of Service`, `Pass`, `pending`, `PENDING_RE_INSPECTION`, `received`, `rejected`, `Rejected`, `Reopened`, `Requested`, `resigned`, `resolved`, `Submitted`, `suspended`, `terminated`, `void`

**~ 38 distinct status words** across the platform. Casing inconsistent (snake_case + Title Case + UPPER_SNAKE).

## Operator-mandated target vocabulary

Per directive Phase 8: *Needs Revision · Needs Correction · Action Required · Pending Verification · Pending Closure · Closed · Reopened*

This is **a user-facing display vocabulary**, NOT a backend storage replacement. The backend's per-workflow state names are correct for state-machine logic; the operator's request is for the **UI surface label** to converge across workflows.

## Canonical mapping (proposed)

| Operator-target label | Maps from (backend) |
|---|---|
| **Action Required** | `open`, `Submitted`, `Requested`, `pending` (pre-approval) |
| **Pending Verification** | `in_review`, `IN_PROGRESS`, `need_info`, `Clarify`, `monitoring` |
| **Needs Revision** | `DEFICIENCY_RAISED`, `FINDINGS_RAISED`, `corrective_pending` |
| **Needs Correction** | `PENDING_RE_INSPECTION` |
| **Pending Closure** | `Approved` (post-approval, pre-close), `In Transit`, `received` |
| **Closed** | `Closed`, `CLOSED`, `closed`, `resolved`, `Received` (final), `Cancelled`, `void`, `terminated`, `resigned`, `denied`, `rejected` |
| **Reopened** | `reopened`, `Reopened` |
| (Compliance display) | `Current`, `Expiring Soon`, `Expired` — keep as-is; they're not lifecycle states |
| (Asset condition display) | `Pass`, `Fail`, `Needs Service`, `Out of Service` — keep as-is |

## Doctrine recommendations

1. **Backend state names remain workflow-specific** — they encode state-machine logic. Renaming them is a high-risk refactor with low product value.
2. **Frontend display labels converge to the canonical 7** — implemented via a `statusDisplay(workflow, backendStatus)` helper that returns the operator-target label + a color + an icon. ~ 200 LOC of pure mapping code.
3. **Status badges replace status strings** — adopt the design-tokens already used by Rank #1 (color + uppercase + monospace) consistently across all list pages and detail pages.
4. **HR Queue dual-state (`pending` vs `needs_review`)** → merge in display: both display as "Action Required" with a sub-tag differentiating reason.
5. **Employee 5-statuses problem (FRICTION #2)** → keep all 5 in backend; in HR-facing UI display them via the canonical mapping; in non-HR UI collapse to `Active` / `Not Active` with a tooltip explaining "see HR for details."

## Effort estimate

* `statusDisplay()` helper + per-workflow mapping table: **2 days**
* Frontend rollout (badges + list-page + detail-page surfaces): **3 days**
* QA + i18n + storybook update: **2 days**
* **Total**: **~ 1 sprint week** — confirmed-still-valid quick-win (TR-0005)

## Closes

* TR-0005 (canonical dictionary missing)
* TR-0004 (verb harmonization — partial; the display-side)
* Multi-workflow "what does 'Closed' mean?" friction items from prior registers

---

End of canonical dictionary.
