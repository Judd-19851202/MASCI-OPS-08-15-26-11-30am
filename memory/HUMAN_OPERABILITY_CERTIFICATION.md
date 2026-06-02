# HUMAN OPERABILITY CERTIFICATION

**Date**: 2026-06-02
**Authority**: OMEGA — post-deploy human operability check
**Scope**: 6 user-experience questions × 7 affected workflows
**Mode**: Mixed — production probes for governance + preview functional verification for iter453.7 frontend

---

## 1 · The 6 questions, applied per workflow

For each affected workflow:

1. Can a real user **find** the action?
2. Can a real user **complete** the action?
3. Can a real user **tell what happened**?
4. Can a real user **see confirmation**?
5. Can a real user **recover from a mistake**?
6. Can a real user **finish without calling Jaymn**?

---

## 2 · HR Employee Lifecycle (status change · the iter453.7 surface)

| Question | Pre-iter453.7 production | iter453.7 preview build (certified · awaiting deploy) |
|---|:-:|:-:|
| 1 · Find the action | 🔴 Save below fold on 60-70 % of HR device fleet | 🟢 Sticky footer pins "Save Status Change" at the bottom of the drawer on every required viewport |
| 2 · Complete the action | 🟡 Achievable if HR scrolls inside the modal | 🟢 One click — button always visible |
| 3 · Tell what happened | 🟢 Toast banner "Status updated" / "Status updated · N offboarding tasks created" | 🟢 same |
| 4 · See confirmation | 🟢 Drawer header badge re-renders to new status + "Recent status history" appends entry | 🟢 same |
| 5 · Recover from mistake | 🟢 Reactivate / Rehire button (separate `<Dialog>` with its own footer) handles Inactive→Active path; status_history is append-only so prior states are preserved | 🟢 same · plus a clear coach label "COMMITS ON SAVE" reduces accidental-save risk |
| 6 · Finish without calling Jaymn | 🔴 Field reports indicate HR currently calls when the Save button "disappears" | 🟢 Sticky footer eliminates the discoverability friction |

**Verdict (Production current state)**: 🔴 — HR cannot reliably finish.
**Verdict (iter453.7 build · ready to ship)**: 🟢 — all six pass.

---

## 3 · Employee Governance Alpha (anon / Operations / FL flow)

| Question | Result |
|---|:-:|
| 1 · Find the action (Operations: submit a new-hire / termination request) | 🟢 `POST /api/employee-requests` is reachable from FL portal + public forms |
| 2 · Complete the action | 🟢 Submit returns 200/202 with queued request id |
| 3 · Tell what happened | 🟢 Frontend shows "Request submitted to HR" toast |
| 4 · See confirmation | 🟢 Returned request id displayed |
| 5 · Recover from mistake | 🟡 Operations cannot delete/edit a submitted request; must wait for HR review — by design (G-5) |
| 6 · Finish without calling Jaymn | 🟢 Self-service complete |

**Verdict**: 🟢

---

## 4 · Field Leadership Termination Form → HR Queue

| Question | Result |
|---|:-:|
| 1 · Find the action | 🟢 Termination Form lives on FL portal; "Submit termination request" CTA visible |
| 2 · Complete the action | 🟢 Form submits to FL termination intake; HR queue receives item |
| 3 · Tell what happened | 🟢 Toast confirms submission |
| 4 · See confirmation | 🟢 FL sees "Request submitted" + the FL leadership records list updates |
| 5 · Recover from mistake | 🟡 FL cannot withdraw a submitted termination request; must contact HR (by design — Phase Alpha) |
| 6 · Finish without calling Jaymn | 🟢 Self-service complete |

**Verdict**: 🟢 (with one acceptable yellow on recoverability — Phase Alpha governance choice)

---

## 5 · HR Queue (approve / reject)

| Question | Result |
|---|:-:|
| 1 · Find the action | 🟢 HR hub tile + dedicated queue page |
| 2 · Complete the action | 🟢 Approve button + Reject button visible per request row |
| 3 · Tell what happened | 🟢 Toast + queue row updates |
| 4 · See confirmation | 🟢 Approved request becomes an employee record / status change; rejected stays as audit row |
| 5 · Recover from mistake | 🟢 HR can re-queue rejected items; approved hires can be lifecycle-mutated via the drawer |
| 6 · Finish without calling Jaymn | 🟢 |

**Verdict**: 🟢

---

## 6 · QA/QC Lifecycle Panel (ITER453 OC-003 · ViewQaqcInspection)

| Question | Result |
|---|:-:|
| 1 · Find the action | 🟢 Lifecycle panel rendered prominently on the inspection view (per ITER453_UI_POLISH_IMPLEMENTATION_REPORT.md) |
| 2 · Complete the action | 🟢 Close / Reopen / Rework buttons present with clear labels |
| 3 · Tell what happened | 🟢 Toast banner + lifecycle panel state chip changes |
| 4 · See confirmation | 🟢 Closure modal returns updated state + audit drawer reflects |
| 5 · Recover from mistake | 🟢 Reason-required Reopen path is the recovery mechanism |
| 6 · Finish without calling Jaymn | 🟢 |

**Verdict**: 🟢

---

## 7 · Site Inspection Lifecycle Panel (ITER453 OC-004 · ViewInspection)

| Question | Result |
|---|:-:|
| 1 · Find the action | 🟢 Same lifecycle panel pattern |
| 2 · Complete the action | 🟢 Same Close / Reopen / Rework with closure-action contract enforced server-side |
| 3 · Tell what happened | 🟢 Toast + state chip |
| 4 · See confirmation | 🟢 Same audit drawer |
| 5 · Recover from mistake | 🟢 Reason-required Reopen |
| 6 · Finish without calling Jaymn | 🟢 |

**Verdict**: 🟢

---

## 8 · Resend Webhook (operator-facing operability)

This is not a human-facing UI; it's an operator-set env var + a webhook URL given to the Resend dashboard. The "user" here is the operator setting up the env.

| Question | Result |
|---|:-:|
| 1 · Find the action | 🟡 Documented in `WEBHOOK_SECRET_DEPLOYMENT_REPORT.md`; operator missed twice |
| 2 · Complete the action | 🟢 Single env var + restart |
| 3 · Tell what happened | 🟡 No proactive notification — operator must probe `POST /api/webhooks/resend` to verify enforcement |
| 4 · See confirmation | 🟢 Re-probe returns 401 once secret is set |
| 5 · Recover from mistake | 🟢 Reset env + restart |
| 6 · Finish without calling Jaymn | 🟡 — Jaymn IS the operator; the recurrence pattern shows the deployment checklist is not visually loud enough |

**Verdict**: 🟡 — operationally completable, but procedurally fragile. **Recommendation**: add a startup probe that logs `WARNING: RESEND_WEBHOOK_SECRET is unset in production` to backend boot so it's surfaced loudly in deploy logs.

---

## 9 · Cross-cutting human-operability findings

| Surface | Finding | Severity |
|---|---|:-:|
| HR drawer Save action (pre-iter453.7) | Below-fold reachability defect — 🔴 BLOCKER per operator field evidence | 🔴 → 🟢 post-deploy of iter453.7 |
| Webhook secret enforcement (production) | Recurrence #2 — procedural gap, not code gap | 🟡 |
| Phase Alpha governance UX | All 6 questions PASS for every Operations / FL / HR flow | 🟢 |
| iter453 lifecycle panels (QA/QC + Site Inspection) | 6 questions PASS · operator-approved closure-action contract | 🟢 |

---

## 10 · STOP

Human operability assessment complete. The single 🔴 blocker (HR Save reachability) is resolved by iter453.7 once deployed. The 🟡 webhook gate is procedural and requires the operator's manual env-var action.

# **HUMAN OPERABILITY VERDICT: 🟡 STRONG-PASS WITH ONE PRODUCTION-GATING DEPLOY ACTION (iter453.7) AND ONE PRODUCTION-GATING ENV ACTION (RESEND_WEBHOOK_SECRET)**
