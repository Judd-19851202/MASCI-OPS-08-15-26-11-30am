# Phase 1A · Rollback Plan

**Program:** OMEGA · PCP · Phase 1A · Final Build Package
**Mode:** Design-only
**Date:** 2026-06-01

---

## 1 · Rollback principles

1. **All Phase 1A changes are additive.** No fields removed. No endpoints removed. No data shapes destroyed.
2. **Rollback = redeploy previous commit.** Backend + frontend rollback is a single Emergent "Deploy previous" action.
3. **New collections survive.** `workflow_state_events` + `jha_acknowledgements` rows persist after rollback; no consumer breaks because the old code doesn't read them.
4. **Migration markers survive.** `lifecycle_state` fields remain on docs after rollback; old code ignores unknown fields.
5. **No data loss.** Soft-deletes preserve every audit row for 7 years.

---

## 2 · Layer-by-layer rollback procedure

| Layer | Action | RTO |
|---|---|---|
| Backend | Operator clicks "Deploy previous backend commit" in Emergent | < 5 min |
| Frontend | Same · "Deploy previous frontend bundle" | < 5 min |
| Both layers | Sequential or parallel (both can happen at once via single button) | < 10 min |
| `workflow_state_events` collection | Leave (audit data preserved) · optional `db.collection.drop()` | < 1 min |
| `jha_acknowledgements` collection | Leave (OSHA evidence preserved) · DO NOT drop | n/a |
| `lifecycle_state` fields on docs | Leave (additive; ignored by old code) | n/a |
| `_lifecycle_migrated_at` markers | Leave | n/a |
| Indexes on existing collections | Leave (no consumer breaks; minor query plan changes only) | n/a |

**Full rollback wall-clock: < 10 minutes.**

---

## 3 · What changes back to pre-Phase-1A behavior

After rollback:

| Behavior | Restored |
|---|---|
| Incidents — no transition buttons; no Mark-* anywhere | yes (pre-Phase 1A state) |
| Daily Reports — no review/approve surface | yes |
| Payroll Variance batches — no finalize button | yes |
| QA/QC — no deficiency state machine | yes (read-shim emits v2 shape but old frontend renders as v1 text array) |
| Site Inspections — no follow-up surface | yes |
| JHA Acknowledgement Ledger — no acknowledgement surface | yes (rows in DB remain · become orphan audit data) |
| Existing PO Request / Asset Transfer / Tasks / etc. | unchanged |

---

## 4 · What does NOT change back

| Item | Why preserved |
|---|---|
| `workflow_state_events` rows accumulated during Phase 1A | OSHA + IRS audit value · cannot be discarded without explicit purge |
| `jha_acknowledgements` rows accumulated | Same · 7-year retention required |
| `lifecycle_state` fields populated on workflow docs | Additive · ignored by old code · re-deployable later |
| Migration markers | Idempotent — re-running migration is safe |
| Indexes created on existing collections | Marginal query plan improvement · safe to leave |

---

## 5 · Rollback decision tree

| Symptom | Cause | Decision |
|---|---|---|
| 5xx errors on transition endpoints | Code bug | **ROLLBACK** if rate >0.1% |
| Frontend crashes on detail pages | Component bug | **ROLLBACK** if any user reports |
| Migration causes startup error | Migration bug | **ROLLBACK** immediately · investigate offline |
| Accountability snapshot returns wrong envelope | Read-shim bug | **ROLLBACK** if exec dashboard breaks |
| Photo viewer regression | Unexpected (no code touches photos) | **ROLLBACK** + RCA |
| Slow query on workflow_state_events | Index missing | NOT a rollback · add index hotfix |
| One incident's state appears wrong | Per-record edge case | NOT a rollback · investigate that record |
| OSHA closure gate too strict | Policy concern | NOT a rollback · operator override + Super-Admin path |

---

## 6 · Partial rollback options

In some scenarios full rollback may be overreach. Per-component rollback paths:

| Component | Partial rollback action |
|---|---|
| OC-005 JHA only (suspect JHA endpoints) | Hotfix: comment out `routes/jha_acknowledgements.py` mount in `server.py` · leave 5 lifecycle workflows live |
| OC-007 Payroll only | Same pattern · disable batch-level transition endpoint · per-row decisions continue |
| Frontend only (Lifecycle panel broken) | Roll back frontend bundle · backend continues serving (admins can use API directly) |
| Backend only (transition endpoints crash) | Roll back backend · frontend gracefully degrades (panel shows "Transition unavailable") |

---

## 7 · Post-rollback action plan

If rollback occurs:

1. Operator declares ROLLBACK at time T
2. Agent runs post-rollback probe battery (verifies pre-Phase 1A behavior)
3. Agent produces `PHASE1A_ROLLBACK_INCIDENT_REPORT.md` documenting:
   * What failed
   * Why we rolled back
   * What rows accumulated during the failed window (in `workflow_state_events` / `jha_acknowledgements`)
   * Plan to re-attempt Phase 1A
4. Operator decides re-attempt window

---

## 8 · Pre-emptive rollback rehearsal

Before production deploy, agent will:
1. Snapshot preview source_hash + frontend bundle hash
2. Verify rollback would restore those exact hashes
3. Document in `PHASE1A_PRE_DEPLOY_ROLLBACK_REHEARSAL.md`

This rehearsal is a 5-minute exercise that confirms the rollback button works.

---

## 9 · Operator-owned rollback runbook (for incident response)

If operator sees a 🔴 incident post-deploy:

```
PHASE 1A ROLLBACK RUNBOOK · v1.0

1. Acknowledge the incident in your monitoring (Sentry/uptime)
2. Open Emergent platform → MASCI Docs project → Deploy tab
3. Click "Deploy previous backend commit"  → wait ~3 min
4. Verify source_hash in /api/version reverted
5. Click "Deploy previous frontend bundle" → wait ~2 min
6. Verify main.<hash>.js reverted
7. Run smoke check: open /admin/incidents (any incident detail) · no errors
8. Notify agent: "ROLLBACK COMPLETE at <ts>"
9. Agent will run post-rollback probe battery and produce incident report
```

---

## 10 · OMEGA discipline

🟢 Rollback wall-clock < 10 min · 0 data loss · all changes additive · per-component partial-rollback options documented · operator runbook documented.

🛑 Continue to `PHASE1A_GO_NO_GO.md`.
