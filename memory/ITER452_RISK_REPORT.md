# OMEGA · iter452 · Risk Report

**Sprint:** ITER452 · OC-002 + OC-007
**Date:** 2026-06-01
**Overall risk:** 🟢 **LOW**

---

## 1 · Risk register

| # | Risk | Likelihood | Severity | Mitigation | Residual |
|---|---|---|---|---|---|
| R-01 | Audit row write fails silently → transition succeeds without history | Low | Medium | Best-effort writer; document mutation is durable. Outbox pattern scheduled for iter455. | 🟢 |
| R-02 | DR REVIEWED → CLOSED flag "office_review_complete" is checkbox-based, not workflow-verified | Medium | Low | Same standing as the existing supervisor_signature attestation pattern. Audit row preserves actor + timestamp + IP + UA. | 🟡 Operator-accepted |
| R-03 | PV per-row decision safety net (variance_decisions_complete) is server-verified, but flagged-row criteria depend on `flag` field — if upstream tooling stores variants of "flag" the check could over- or under-fire | Low | Medium | Current criteria: `flag ∈ {"flag", "missing_from_payroll"}`. Matches existing payroll_variance writer. Operator may adjust the set in iter455 if customer #2 produces new variants. | 🟢 Tracked |
| R-04 | Notification fan-out on PENDING_REVIEW fires 3 rows × every submit — possible queue pressure if a single DR is repeatedly kicked back and resubmitted | Low | Low | `event_fanout.emit_notification` is rate-friendly. Audit trail of repeated submits is itself a process flag, not a bug. | 🟢 |
| R-05 | PV state machine permits `APPROVED → UNDER_REVIEW` only with Admin/Super-Admin; HR cannot back-step. Could lead to operator confusion. | Medium | Low | UI panel only renders buttons for transitions the actor can perform (`legal_next_states[].allowed_for_actor`). The HR reviewer sees no back-step button when in APPROVED. | 🟢 UX-mitigated |
| R-06 | `_actor_view` returns `actor_role="unknown"` only for shapes that omit both `_actor_kind` and `role`. iter451 incident audit rows for Admin-by-password still show `role="admin"` (correct). iter452 PM/HR rows now show `role="pm"`/`"hr"` (correct). | Very Low | Low | Verified via live audit inspection. | 🟢 |
| R-07 | Cross-portal access guard at `/hr/payroll-variance` rejects Safety-portal sessions — operators may not realize they need to login as HR | Low | Low | Existing platform behaviour (not introduced by iter452). 403 page tells the user which portal to use. | 🟢 By design |
| R-08 | The shared `<LifecyclePanel/>` is now a critical-path component used by iter451 incident (via inline panel) + iter452 DR + iter452 PV. A future bug here affects all 3 workflows. | Low | Medium | Component is pure-render driven by props · linted clean · history drawer rendered identically across workflows · unit tests on backend + manual UI walkthrough. iter455 will add Playwright tests. | 🟢 Acceptable |
| R-09 | OC-007 lifecycle doesn't suppress the existing legacy "approve / dispute / push to payroll" buttons in `HrPayrollVariance.jsx` — operators could in theory call the legacy decision endpoint while the batch is FINALIZED | Medium | Low | Per-row decisions are sub-batch operations that remain valid post-finalize (they're already idempotent in the legacy code). The lifecycle is a **wrapper** over the existing flow, not a replacement. Operator may wish to gate the legacy endpoint on `lifecycle_state != FINALIZED` in iter455. | 🟡 Backlogged |
| R-10 | Phase 1B status canonicalization will need to reconcile DR's `OPEN/PENDING_REVIEW/REVIEWED/CLOSED` and PV's `OPEN/UNDER_REVIEW/APPROVED/FINALIZED` with the 18-vocab consolidation target. | Medium | Low | Already scheduled in Phase 1B. Phase 1A vocabs are domain-specific by design. | 🟡 Backlogged |

---

## 2 · Production-deploy risk assessment

| Vector | Assessment |
|---|---|
| Schema migration required? | **No.** Additive fields are lazy-materialised on first transition. New indexes are idempotent. |
| Zero-downtime deploy? | **Yes.** Backend hot-reload safe; no breaking changes. |
| Rollback path? | **Yes — single revert.** Revert the 6 new files + the 6 additive edits. Audit rows for daily_report + payroll_variance can remain orphaned (harmless) or be dropped. |
| Backwards-compatibility | **100%.** Pre-iter452 DR/PV records read as OPEN via coercion. Clients ignoring the new field continue working. |
| External-system impact | **None.** No 3rd-party API integrations changed. CSV exports unchanged. |
| Customer #2 isolation | **Preserved.** Per-tenant DB; no tenant-bound code. |

---

## 3 · Open items for Phase 1A integration certification (iter455)

These are tracked, not exposures:

1. Wire DR `lifecycle_state` into the Operations Center "DRs pending review" tile.
2. Wire PV `lifecycle_state` into the HR weekly digest (currently shows raw flag counts).
3. Decide whether to gate the legacy PV `decision` endpoint on `lifecycle_state != FINALIZED` (R-09).
4. Add Playwright integration tests against the shared `<LifecyclePanel/>` to lock the UX contract.
5. Phase 1B vocab reconciliation map (R-10).

---

## 4 · Verdict

🟢 **LOW residual risk.** No HIGH or CRITICAL items. The 3 🟡 items (R-02 attestation pattern, R-09 legacy endpoint gate, R-10 vocab reconciliation) are accepted/backlogged respectively. Deployment is safe to proceed on operator authorization.
