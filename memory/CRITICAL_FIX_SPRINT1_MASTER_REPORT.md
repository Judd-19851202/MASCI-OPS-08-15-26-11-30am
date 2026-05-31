# Critical Fix Sprint 1 · Master Report

**Batch:** OMEGA Critical Fix Sprint 1
**Date:** 2026-05-31
**Verdict:** 🟡 **5 actionable P0/P1 remediation paths identified · 0 modifications made**

> Production-hardening certification consolidating P0-1 through P0-5. Read-only forensic only. No code · no DB writes · no deploys.

---

## 1 · Sprint summary · 5 deliverable bundles

| P0-area | Deliverables produced | Headline finding |
|---|---|---|
| P0-1 · Test-account audit | `TEST_ACCOUNT_AUDIT.md` · `TEST_ACCOUNT_REMEDIATION_PLAN.md` | 1 🔴 test FL user live in prod; 5 🟡 user_directory rows with mcp=False / no login; 7 🟡 user_directory rows with `is_active=null` |
| P0-2 · Incident integrity | `INCIDENT_INTEGRITY_REPORT.md` | 1 🔴 duplicate `doc_id`; 7 🟡 incidents with `status=null`; 3 ID schemas in use |
| P0-3 · Incident delete | `INCIDENT_DELETE_ROOT_CAUSE.md` · `INCIDENT_DELETE_REMEDIATION_PLAN.md` | DELETE route works · permission-gated (Safety token rejected) · no cascade · no audit · frontend swallows error codes |
| P0-4 · Payroll variance | `PAYROLL_VARIANCE_FORENSIC_REPORT.md` | 10 🔴 abandoned test batches by `hrmanager@mascigc.com` 2026-05-12/13 with "John Smith" canary |
| P0-5 · UI hygiene | `UI_HYGIENE_REMEDIATION_REPORT.md` | No empty outlined button found by code inspection; reproduction needs viewport screenshot |

---

## 2 · Severity-ranked master action list (15 items)

### 2.1 · 🔴 P0 (3 items · do first)

| # | Action | File / collection | Effort | Risk if left alone |
|---|---|---|---|---|
| P0-A | Rotate / deactivate `fieldleader@mascigc.com` test FL user | `field_leadership_users` | <30 min | Anyone with repo access can authenticate to production as a Superintendent |
| P0-B | Dedupe `doc_id='INC-2026-00001'` (promote `d9626eeb`; rename `566a38dd` to `INC-2026-00012`) | `incidents` | 1 hr | Audit/report integrity gap |
| P0-C | Delete 10 abandoned payroll-variance test batches + 7 linked decisions | `payroll_variance_batches` · `payroll_variance_decisions` | <1 hr | HR portal operational noise; compliance/audit risk |

### 2.2 · 🟡 P1 (5 items · do next)

| # | Action | File / collection | Effort | Risk if left alone |
|---|---|---|---|---|
| P1-A | Migrate `DELETE /api/incidents/{id}` to **soft-delete** + audit log | `routes/safety.py:810` · `lib/event_fanout.py` · `audit_events` | 2-3 d | Orphans on 6 surfaces · no audit · regulatory exposure |
| P1-B | Frontend: stop swallowing HTTP error codes in `IncidentsDashboard.jsx:50` and `ViewIncident.jsx:209` | 2 frontend files | 1-2 d | Users cannot self-diagnose 401 vs 404 vs 500 |
| P1-C | Audit 5 `user_directory` rows with `mcp=False · never logged in` for default-password state; force rotate if needed | `user_directory` | 1 d | Default-or-known passwords may persist |
| P1-D | Backfill `is_active=True` on 7 `user_directory` rows + schema validator | `user_directory` | <1 d | UI visibility inconsistency |
| P1-E | Update `/app/memory/test_credentials.md` to remove `fieldleader@mascigc.com` after P0-A | docs | <30 min | Documentation drift |

### 2.3 · 🟡 P2 (5 items)

| # | Action | File / collection | Effort | Risk if left alone |
|---|---|---|---|---|
| P2-A | Backfill `status="open" · resolution_status="open"` on the 7 production incidents | `incidents` | <1 d | Reporting accuracy gap |
| P2-B | Decide fate of 4 legacy `users.role=owner` accounts (last login 2026-04-28) | `users` | 1 d (incl. owner consult) | Stale credential surface |
| P2-C | Add `db.incidents.createIndex({doc_id: 1}, {unique: true, sparse: true})` after P0-B | DB | <1 d | Prevent future doc_id duplicates |
| P2-D | Investigate `doc_id_counters` atomic-increment logic | `lib/doc_id_counters.py` or similar | 1 d | Root cause of P0-B; recurrence prevention |
| P2-E | Operator captures HR portal "empty outlined button" viewport screenshot for repro | UX evidence | <30 min (operator) | UI defect cannot be fixed without repro |

### 2.4 · 🟢 P3 (2 items · do later)

| # | Action | Effort | Risk if left alone |
|---|---|---|---|
| P3-A | Standardize portal header chrome (CompanyInfoDialog + Password button on all hubs or none) | 1-2 d | Cosmetic UX inconsistency |
| P3-B | Sweep 63 `// TODO` / `// FIXME` markers in non-critical code | 2-3 d (sweep) | Development debt |

---

## 3 · Recommended execution order

🟢 **Critical Fix Sprint 1 batch (proposed)** — if operator authorizes:

1. **DB-only sweep** (no code change · ~2 hr total):
   - P0-A (deactivate test FL user)
   - P0-B (dedupe doc_id)
   - P0-C (delete 10 payroll test batches + 7 decisions)
   - P1-D (backfill 7 `user_directory.is_active=True`)
   - P2-A (backfill 7 incidents to `status="open"`)
   - P2-C (unique index on `doc_id`)
   - **Verify:** count, list, snapshot probes all consistent · no regression in Pillar 1/2 endpoints
2. **Code-side patch** (one tight PR · ~3-5 d):
   - P1-A (soft-delete migration)
   - P1-B (frontend error code surfacing)
   - Pytest coverage on both
3. **Operator-side audits** (no agent action needed):
   - P1-C (default-password audit · operator runs DB checks)
   - P1-E (update test_credentials.md)
   - P2-B (owner consult)
   - P2-D (investigate counters · code review)
   - P2-E (screenshot HR header)
4. **Deferred to later batch:**
   - P3-A · P3-B

---

## 4 · Combined Sprint 1 effort estimate

| Phase | Effort |
|---|---|
| DB sweep (7 actions) | ~2 hr |
| Code patch (2 actions, full PR + tests + recert) | 3-5 dev-days |
| Operator audits (P1-C/E, P2-B/D/E) | 1-2 calendar days incl. consults |
| **Total** | **3-5 dev-days + operator-coordination time** |

---

## 5 · OMEGA discipline scorecard (this batch)

| Discipline rule | Verdict |
|---|---|
| Zero code changes | 🟢 |
| Zero DB writes | 🟢 |
| Zero deployments | 🟢 |
| Zero feature work | 🟢 |
| Zero white-label work | 🟢 |
| Zero ForgedOps portal work | 🟢 |
| Zero Escalation engine work | 🟢 |
| Zero Pillar 3/4 work | 🟢 |
| Read-only forensic certification only | 🟢 |
| Reports produced + agent stops | 🟢 |

---

## 6 · Deliverables index

| File | Purpose |
|---|---|
| `CRITICAL_FIX_SPRINT1_MASTER_REPORT.md` (this file) | Master severity-ranked action list |
| `TEST_ACCOUNT_AUDIT.md` | P0-1 inventory |
| `TEST_ACCOUNT_REMEDIATION_PLAN.md` | P0-1 remediation |
| `INCIDENT_INTEGRITY_REPORT.md` | P0-2 |
| `INCIDENT_DELETE_ROOT_CAUSE.md` | P0-3 root cause |
| `INCIDENT_DELETE_REMEDIATION_PLAN.md` | P0-3 remediation |
| `PAYROLL_VARIANCE_FORENSIC_REPORT.md` | P0-4 |
| `UI_HYGIENE_REMEDIATION_REPORT.md` | P0-5 |

---

## 7 · Closeout

🟡 **Critical Fix Sprint 1 forensic batch complete.** 15 remediation actions documented across 5 P0 areas. 3 🔴 P0 actions remediable in ~2 hours of DB-only work; 5 🟡 P1 actions in 3-5 dev-days; 5 🟡 P2 + 2 🟢 P3 for later. **No modifications made.**

🛑 STOP. Awaiting explicit operator authorization for the remediation batch.
