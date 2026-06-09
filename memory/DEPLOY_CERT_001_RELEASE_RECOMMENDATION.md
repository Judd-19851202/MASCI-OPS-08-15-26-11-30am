# DEPLOY-CERT-001 · Release Recommendation

**Sprint:** DEPLOY-CERT-001 · 2026-06-09  
**Verdict:** 🟡 **CONDITIONAL PASS**

---

## Recommendation

Deployment of the MASCI Operations Platform to production is **APPROVED CONDITIONALLY**.

The live runtime is healthy, integration health is green, the deployment-blocker test suite (PROJECT-IDENTITY-005 compliance gate, 5/5) is GREEN, the canonical-identity doctrine is enforced platform-wide, and the auth gate holds. Production data integrity is sound.

However, one P1 defect was discovered during this very certification (P1-01 · backup-writer orphan `.tmp` files), and three P2 stale pytest fixtures remain unresolved.

The directive explicitly states: *"Deployment is PROHIBITED until all P0 defects are resolved, all P1 defects are resolved, OR Jaymn Judd explicitly accepts the risk in writing."*

There is **one P1 defect** (P1-01). Per the directive, deployment requires **either remediation or written acceptance** of P1-01 from the platform owner.

---

## Two Acceptable Paths Forward

### Path A · Remediation Sprint Before Deploy (recommended)

Authorize one focused maintenance sprint (estimated 1–2 hours) covering:

| Item                                              | Estimate | Sprint Code (suggested) |
|---------------------------------------------------|---------:|-------------------------|
| P1-01 · Backup-writer orphan `.tmp` cleanup       | 30 min   | DEPLOY-FIX-001          |
| P2-01 · HR portal fixture rotation                | 15 min   | DEPLOY-FIX-001          |
| P2-02 · Daily Reports DELETE 410-Gone tests       | 15 min   | DEPLOY-FIX-001          |
| P2-03 · Phase 2 dashboard seed test               | 30 min   | DEPLOY-FIX-001          |
| P2-04 · Fresh backup-verification run + email     |  5 min   | manual (post-fix)       |

Then re-run DEPLOY-CERT-001's deployment-blocker tests (5/5 expected) and deploy.

### Path B · Written Acceptance + Deploy

Owner provides written acceptance covering:

1. P1-01 backup-writer cleanup deferred to first post-deploy maintenance window. **MUST include**: a pre-deploy ops runbook entry "after any manual backup, verify `df -h /app` shows < 90 % full."
2. P2-01, P2-02, P2-03 deferred to a separate maintenance sprint with no production impact (none of these affect live behavior).
3. Owner manually triggers `POST /api/admin/backup-verification/run-now` and visually confirms the resulting email arrives in their inbox **before** announcing the deploy.

---

## What This Recommendation Is NOT

- **Not** a recommendation to fix anything within this sprint. The directive forbids fixes. We surface the conditions only.
- **Not** a verdict on FleetWatcher, Dispatch Automation, or Material Movement Automation — those remain deferred backlog with no testing in this sprint.
- **Not** a fresh mobile-platform certification — that is inherited from HR-TIME-001E and MOTIVE-DATA-003.
- **Not** a fresh restore drill — that is inherited from BACKUP-FIX-001.

---

## Sign-Off

Per OMEGA directive:

> *"No exceptions. Deployment is PROHIBITED until all P0 defects are resolved, all P1 defects are resolved, OR Jaymn Judd explicitly accepts the risk in writing."*

The certification team (E1 / Fork Agent) hereby submits this CONDITIONAL PASS verdict to **Jaymn Judd** for decision.

| Action required from Owner             | Status |
|-----------------------------------------|--------|
| Choose Path A or Path B                 | _pending_ |
| Authorize Path A sprint OR sign Path B acceptance | _pending_ |
| Confirm deploy slot                     | _pending_ |
