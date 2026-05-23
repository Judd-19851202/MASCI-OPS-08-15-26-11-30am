# REMAINING OPERATIONAL GAPS
**Phase 3B · Iter368**
**Generated:** 2026-05-23

After the Phase 3B convergence audit, the following items remain. **None block redeploy.** They are tracked here for future iteration triage.

---

## Closed this iteration (was a gap)

### iter368-G1 · Incident detail did not surface linked CAPAs
- **Status:** ✅ CLOSED iter368.
- **Fix:** New `source_kind` + `source_id` filters on `GET /api/safety/corrective-actions`; new "Linked CAPAs" section on ViewIncident; 4-test regression lock.

---

## Tracked (low priority polish)

### O1 · Dispatch portal cannot see daily-report crew assignments
- **Severity:** LOW
- **Behavior:** Dispatchers currently work from driver readiness only. If a dispatcher wants to know "who's on the Whitehall project today" they have to ask the PM or look at the daily report directly.
- **Why not closed this iteration:** Dispatch ops directive is "send the qualified driver" — site assignment is a PM responsibility. Adding cross-portal visibility here risks role confusion.
- **Action:** Watch for field requests. If 3+ dispatchers ask for this in a month, add a small "Crew Today" panel that consumes the existing daily-report endpoint scoped to today.

### O2 · Free-text CAPA owner does not auto-create a finding
- **Severity:** LOW
- **Behavior:** When a CAPA is created with a free-text `assigned_to_name` (no `employee_master_id`), the EMP_LINK_UNRESOLVABLE detector does not currently fire on the CAPA itself — only on incidents / daily reports / PPE / training.
- **Why not closed this iteration:** The detector deliberately scopes to high-traffic field surfaces. Adding CAPAs would explode the finding count for subcontractor-assigned actions, which are intentionally free-text by policy.
- **Action:** Keep as-is unless operator wants stricter CAPA accountability.

### O3 · 335 open compliance findings dominated by legacy data
- **Severity:** OPERATIONAL DECISION
- **Behavior:** 230 PPE_MISSING + 73 EMP_ARCHIVED_ACTIVE are historical records pre-dating the linkage program. Convergence score reads 0 ("critical") because of this backlog.
- **Why not closed this iteration:** The findings are accurate — the data IS there. The question is whether to bulk-acknowledge (silences the noise but keeps the records) or actually backfill the underlying records (more work, more visibility).
- **Action:** Operator decides:
  - (a) Bulk-ack legacy PPE_MISSING and accept the score will jump to ~60 ("warning") overnight.
  - (b) Run a one-time backfill on archived/active employees to true up status.
  - (c) Leave as-is; the score will climb naturally as new records pass through the iter359-iter364 prevention loop.

### O4 · Admin pages remain English-only by convention
- **Severity:** LOW (intentional)
- **Behavior:** /admin/* pages do not call useT(); strings are hardcoded English.
- **Why not closed this iteration:** Admin ops are managed by English-speaking super-admin only. Field-facing pages are the priority for bilingual UX. Translating all 24 admin pages would be ~150 strings of work for minimal field-user benefit.
- **Action:** None. Keep convention.

### O5 · status_history field not surfaced in CAPA list view
- **Severity:** LOW
- **Behavior:** `status_history[]` is persisted on every transition and returned by detail GET, but the list endpoint omits it to keep payloads small.
- **Why not closed this iteration:** Working as designed. Frontend list views render status badges, not transitions. Detail views render history correctly.
- **Action:** None.

### O6 · No automated preview→prod parity smoke (manual playbook only)
- **Severity:** LOW
- **Behavior:** Operator must manually fill in POST_REDEPLOY_SMOKE_RESULTS.md after each deploy.
- **Why not closed this iteration:** Building automation requires a `BASE_URL` parametrization in the pytest harness + a one-line bash wrapper. Small but out of Phase 3B scope.
- **Action:** Operator can request "iter369 · automated prod smoke" as a 30-minute follow-up iteration.

---

## Architectural risk watchlist (NOT in Phase 3B scope)

| Risk | Severity | Queued iteration |
|---|---|---|
| 18 RBAC patterns across server.py + routes | MEDIUM | P4 — Auth Gate Consolidation |
| No super-admin MFA | MEDIUM | P5 — needs integration choice |
| No portal-grant audit log | LOW | P5 |
| server.py at 12k+ LOC | LOW (no behavior risk) | P7 — server.py extraction |
| No automated mobile/ES screenshot regression suite | LOW | unscheduled |

---

## Summary

After Phase 3B:
- ✅ 1 real convergence gap found and closed (iter368).
- 📌 6 polish-level items tracked, none blocking.
- ❌ 0 open material gaps preventing redeploy.

The platform is operationally converged. The remaining work is **strategic** (auth, MFA, refactor) not **convergence** (workflow communication).
