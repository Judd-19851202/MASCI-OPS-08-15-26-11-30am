# Server Decomposition Status
## iter437 · Phase IV-BETA.5A · cumulative (P4B + P5D + P6)
## Updated 2026-05-27

*Status: 🟢 THREE EXTRACTIONS COMPLETE · catalog updated · stable*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I · server.py size & route distribution

| Metric | Value |
|---|---|
| Line count (post-P6) | **11,303** |
| Cumulative reduction this phase (IV-BETA.5A) | **−31 lines** (from 11334 baseline) |
| `app.include_router(...)` calls | 28+ (3 new this phase) |

> Reduction stays small **by design**. The doctrine prioritizes
> reversibility and zero behavioural change per extraction over
> aggressive line-count cuts.

---

## II · Decomposition roster

### 🟢 EXTRACTED SAFELY in IV-BETA.5A (this phase · 3 routers)

| Router | File | Phase | Tests |
|---|---|---|---|
| Guidance content (5 endpoints) | `routes/guidance_routes.py` | P4B | 9/9 green |
| Health (`/health`, `/healthz`) | `routes/health_routes.py` | P5D | 4/4 green |
| Static helpers (`/qr.svg`) | `routes/static_helpers.py` | **P6 (new)** | **5/5 green** |

### 🟢 EXTRACTED in prior iterations (historical)

| Router | File |
|---|---|
| Training center | `routes/training_center.py` |
| PM | `routes/pm_routes.py` |
| Shop parts | `routes/shop_parts.py` |
| Dispatch lifecycle (iter392) | `routes/dispatch_*.py` |
| Governance (admin-strict) | `routes/governance.py` |
| Governance health | `routes/governance_health.py` |
| Admin digest config / K4 / persistence health / ops / stability | `routes/admin_*.py` |
| Field leadership / portal | `routes/field_leadership*.py` |
| Safety portal (modular) | `routes/safety_portal/*` |
| Operations / operations center | `routes/operations*.py` |
| Integrations | `routes/integrations/*` |
| Deploy readiness | `routes/deploy_readiness.py` |
| Date audit | `routes/date_audit.py` |
| Many others | see `/app/backend/routes/__init__.py` |

### 🟡 NEXT EXTRACTION CANDIDATES — ranked low → medium risk

| Order | Group | server.py lines | Risk | Reason held back |
|---|---|---|---|---|
| 1 | `GET /api/version` | ~807-845 | 🟡 low-medium | Depends on `_STARTUP_TS` + `_SOURCE_HASH` lifecycle globals · needs DI |
| 2 | `GET /api/health/full` | ~672-717 | 🟡 medium | Touches `_BACKUP_SCHEDULER_STATE` + `db.backup_health` |
| 3 | `GET /api/training/videos` (public read) | ~7998-8061 | 🟡 medium | Performs self-heal migration write on read |
| 4 | Dev portal `/api/dev/ops-manual*` | ~857-1180 | 🟢 low (dev-token gated) | Many helpers · needs cluster move |
| 5 | Admin export CSV endpoints | ~1283-1395 | 🟡 medium | Admin-strict · many model imports |

### 🔴 HIGH-RISK / DEFERRED · DO NOT EXTRACT (directive line 8)

| Group | Reason |
|---|---|
| Auth (login / refresh / multi-login / cookie setup) | High-blast-radius · explicit directive ban |
| Notifications | Active websocket coupling · explicit directive ban |
| Uploads / attachments | Storage coupling · explicit directive ban |
| Safety escalation surfaces | Active doctrine work · explicit directive ban |
| Dispatch backend | High volatility · explicit directive ban |
| Compliance/export audit-coupled routes | Audit-trail coupling · explicit directive ban |
| Webhooks | External SLA · explicit directive ban |
| Backup / restore admin routes | Destructive surface |
| Session reset / portal scope enforcement | Cross-cutting · touches every portal |
| Startup `app.include_router(...)` ordering | Boot-fragile |

---

## III · Cumulative extractions (current phase IV-BETA.5A)

| Sub-phase | New extractions | server.py LOC delta |
|---|---|---|
| P3 | 0 (catalog only) | 0 |
| P4B | 5 endpoints (guidance) | −5 |
| P5D | 2 endpoints (health · `/health`, `/healthz`) | −11 |
| **P6 (this pass)** | 1 endpoint (`/qr.svg`) | **−15 cumulative** |

---

## IV · Per-extraction rule (unchanged)

1. Pick **one** group from the LOW-risk band.
2. Confirm it satisfies all four safety criteria: stateless · no auth ·
   bounded input · contract already locked by tests.
3. Mirror an existing extraction pattern (`build_<name>_router(...)`).
4. Run all regressions before and after.
5. Add a small extraction-specific parity test.
6. Declare an operator checkpoint if the post-extraction state is
   meant to be locked.

---

## V · Doctrine reaffirmed

- ✅ Three extractions cumulative in IV-BETA.5A · all cleanly reversible
- ✅ Catalog ranked for future operator authorisation
- ✅ 🔴 HIGH-RISK groups documented as off-limits
- ✅ No startup-order or middleware changes
- ✅ Behavioural parity verified by extraction-specific tests
- ✅ Preview only · NO production deploy
