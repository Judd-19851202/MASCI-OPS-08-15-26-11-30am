# OMEGA · iter451 · Risk Report

**Sprint:** ITER451 · OC-001 Incident Lifecycle
**Date:** 2026-06-01
**Overall risk:** 🟢 **LOW**

---

## 1 · Risk register

| # | Risk | Likelihood | Severity | Owner | Mitigation | Residual |
|---|---|---|---|---|---|---|
| R-01 | Audit row write fails silently due to Mongo blip → transition succeeds without history | Low | Medium | Backend | Best-effort writer with retry not yet wired. Document mutation is the durable source of truth (`lifecycle_state` persists even if audit row is lost). iter452 will add an outbox pattern. | 🟢 Accepted |
| R-02 | Operator confuses iter450 design vocab (`IN_PROGRESS`, `PENDING_REVIEW`) with iter451 operator-mandated vocab (`UNDER_INVESTIGATION`, `CORRECTIVE_ACTION_REQUIRED`) | Medium | Low | Documentation | This report + `_INDEX.md` explicitly call out the divergence and confirm the iter451 directive supersedes the iter448 design package for OC-001. | 🟢 Mitigated |
| R-03 | Frontend panel renders for unauthorized actors but transitions 403 server-side | Low | Low | Frontend | `GET /api/incidents/{id}/lifecycle` returns `legal_next_states[].allowed_for_actor`; UI only renders buttons where `allowed_for_actor` is true. Server still enforces independently. | 🟢 Defence-in-depth |
| R-04 | OSHA closure attestation client-side checkbox is not legally sufficient signature | High | Medium | Compliance | Same standing as the existing `reporter_signature` / `supervisor_signature` fields — checkbox-based attestations are platform-wide pattern. Auditor traceability is preserved via `actor_role`, `actor_id`, `actor_name`, IP, UA, timestamp in the audit row. Operator may upgrade to typed-name or canvas signature in a follow-up sprint. | 🟡 Operator-accepted |
| R-05 | Reopen permits the same actor who closed the incident to reopen → potential workflow gaming | Medium | Low | Process | Audit trail captures both events with timestamps + reasons. Operator may add a 4-eyes rule (different actor required to reopen) in iter455 integration cert if desired. | 🟢 Audit-mitigated |
| R-06 | `coerce_incident_state` defaults missing/unknown values to `OPEN` — silent normalization could mask data corruption | Low | Low | Backend | The coercion is logged via state-event row on first transition. Operator audit query: `db.incidents.aggregate([{$match:{lifecycle_state:{$exists:false}}}, {$count:'pre_iter451'}])` returns count of pre-iter451 incidents. | 🟢 Acceptable |
| R-07 | New `workflow_state_events` collection grows unbounded | Low | Low | DBA | Append-only by design. 7-year retention TTL aligned with OSHA + IRS retention is scheduled for iter455 deployment migration. Today the volume is small (~5 rows per closed incident). | 🟢 Tracked |
| R-08 | PM (project manager) role currently has no transitions allowed | Medium | Low | Product | Per operator directive — only Safety / Admin / Super-Admin may transition incidents. PM stays read-only on lifecycle. If business wants PM-driven incident progression, raise as Phase 1B request. | 🟢 By design |
| R-09 | The iter450 design package referenced `IN_PROGRESS`/`PENDING_REVIEW` — Phase 1B status-canonicalization will need to reconcile incidents' new vocabulary with the wider 18-vocab consolidation | Medium | Medium | Phase 1B | Already on the Phase 1B backlog (`PHASE1A_STATE_MACHINE.md §3` notes the canonical 5-vocab; incidents now use a domain-specific 5-vocab that aligns conceptually but not lexically). Phase 1B will produce the alias map. | 🟡 Backlogged |
| R-10 | Frontend panel re-renders on every successful transition (refetches `/lifecycle` + history). Could rate-limit excessive clicks | Very Low | Negligible | Frontend | `busy` state guard already disables buttons during request. Toast suppression handled by `sonner`. | 🟢 Mitigated |

---

## 2 · Production-deploy risk assessment

| Vector | Assessment |
|---|---|
| Schema migration required? | **No.** Additive fields are lazy-materialised on transition. New collection auto-created on first write. |
| Zero-downtime deploy? | **Yes.** Backend hot-reload safe; no breaking changes to existing endpoints. |
| Rollback path? | **Yes — single revert.** Revert the 5 new files + the 2 edits to `server.py` / `ViewIncident.jsx`. New collection can stay (orphaned but harmless) or be dropped manually. |
| Backwards-compatibility | **100%.** Pre-iter451 incidents read as `OPEN` via coercion. Clients that ignore the new field continue working. |
| External-system impact | **None.** No 3rd-party API integrations changed. No email/webhook signatures changed. |
| Customer #2 isolation | **Preserved.** New collection is per-tenant database; PM-scope filter unchanged. |

---

## 3 · Open items for Phase 1A integration certification (iter455)

These are tracked, not exposures:

1. Wire the `lifecycle_state` field into `accountability_projection.py` so the Operations Center "open incidents" tile reflects canonical state instead of `incident_date`-based heuristic.
2. Wire into `command_center.py` "Incidents Open" KPI.
3. Add notification fan-out on `to_state ∈ {PENDING_CLOSURE, CLOSED}` per Phase 1A integration design.
4. Decide on 4-eyes reopen rule (R-05).
5. Cross-link with CAPA `corrective_actions` — when a CAPA verified → flip linked incident from CORRECTIVE_ACTION_REQUIRED → PENDING_CLOSURE automatically (currently manual).

---

## 4 · Verdict

🟢 **LOW residual risk.** No HIGH or CRITICAL items. The 2 🟡 items (R-04 attestation, R-09 vocab reconciliation) are accepted by-design and backlogged respectively. Deployment is safe to proceed on operator authorization.
