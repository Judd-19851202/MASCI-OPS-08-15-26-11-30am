# PRODUCTION DRIFT REPORT
**Audit date:** 2026-05-23
**Preview:** `https://backup-forensics.preview.emergentagent.com/api`
**Production:** `https://mascidocs.com/api`
**Both targets confirmed alive:** `/api/health` returns `{"ok":true,"service":"masci-hub"}` from both.

---

## Drift evidence (direct curl probes captured during audit)
Both calls used identical `X-Admin-Token: any` header to defeat anonymous gates; the contrast is endpoint EXISTENCE (404) vs gating (401).

| Endpoint | Prod status | Preview status | Verdict |
|---|---|---|---|
| `/api/hr/driver-qualification/dashboard` | 401 | 401 | ✅ deployed |
| `/api/hr/driver-qualification/import/apply` 🆕 iter352 | **404** | 405 | 🔴 NOT deployed |
| `/api/dispatch/driver-qualification` 🆕 iter353b | **404** | 401 | 🔴 NOT deployed |
| `/api/field-leadership/portal/driver-qualification` (iter314, schema enriched iter353b) | 401 | 401 | ⚠️ deployed but payload SHAPE drift (slim iter314 in prod, rich iter353b shape in preview) |
| `/api/hr/employees/{id}/accountability/timeline` 🆕 iter353c | **404** | 401 | 🔴 NOT deployed |
| `/api/hr/employees/{id}/accountability/brief.pdf` 🆕 iter353c | **404** | 401 | 🔴 NOT deployed |

---

## What this means in operator terms
The platform you USE TODAY does not have:
- ❌ The Unified Employee Accountability Timeline
- ❌ The HR Compliance Brief PDF exporter
- ❌ The Dispatch Driver Readiness page (Approved Drivers / CDL Readiness)
- ❌ The "Drivers Available Right Now" hero tile + click-to-filter
- ❌ The richer FL Driver Readiness view (summary tiles)
- ❌ The self-service CDL Roster Importer
- ❌ The iter353a shared HR+Safety+Admin write authority on accountability records
- ❌ Cumulative regression-locked 123 pytest items

The platform you SEE in preview HAS all of the above.

---

## Iter inventory NOT in production (chronological)
1. **iter350** — HR Safety + CDL + Certificate Visibility Convergence
2. **iter351** — PROD CDL/Approved Driver Bulk Load (data may be missing too)
3. **iter352** — Add 4 Drivers + Self-Service CDL Roster Importer
4. **iter353** Phase 1 — Platform Governance Audit (5 markdown docs)
5. **iter353a** (Backend) — P0 Shared Employee Accountability
6. **iter353a-UI** — HR Safety Records write surfaces
7. **iter353b** — Dispatch + FL Read-Only Driver Qualification Visibility
8. **iter353b-availability** — Drivers Available Right Now tile
9. **iter353c** — Unified Employee Accountability Timeline + HR Compliance Brief PDF
... plus the entire iter330–iter349 batch implied by handoff notes ("24 bounded iters pending redeploy").

---

## Production data drift (presumed, not directly probed for sensitive content)
- **iter351** loaded 82 CDL holders into preview's `employees` collection. Production may still have the pre-iter351 driver roster. **Operator action:** re-run the iter352 importer in production after redeploy.
- iter353a/353a-UI accountability records (training + documents created via HR+Safety shared authority) live only in preview's `safety_training_records` and `safety_documents`. Production has only the legacy Safety-only data.

---

## Production-only failures (none observed this audit)
No endpoint succeeded in prod and failed in preview. Drift is one-directional: preview is ahead.

---

## Remediation
**Single fix:** Trigger production redeploy from the Emergent dashboard. After deploy:
1. Re-run the iter351 CDL bulk-load script against production.
2. Smoke-test the 8 endpoints in the table above against `mascidocs.com` — all should return 401 (not 404).
3. Smoke-test the FL DQ response shape — should include `summary` with `available_now*` keys.
4. Have HR open `/hr/employees/{any-real-id}/accountability` on production — should render the timeline page.

**Why this is THE single highest-impact action available right now:** every piece of operational work in this session sits behind that one deploy click.
