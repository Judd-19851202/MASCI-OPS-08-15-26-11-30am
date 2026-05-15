# MASCI Operations Platform — Phase 1 QA Report (Iter A)

**Iter135 · 2026-05-15**

This is the output of the static route/endpoint crawl + targeted live verification across the entire platform. It's the input for Iters B–D (UX standardization, mobile sweep, exports/training/data, integrations/perf/health/deploy).

---

## 📊 Inventory

| Surface | Count |
|---|---|
| Frontend `<Route>` declarations | **175** (174 unique after dedupe fix) |
| Backend `@router.X` endpoints (prefix-resolved) | **356** unique paths |
| Frontend axios/api calls | **362** |
| FE → BE matched | **353** |
| FE → BE unmatched (real) | **0** after fixes (was 9; 6 false-positive, 3 fixed) |
| Duplicate FE routes | **0** after fix (was 1) |

---

## 🔴 Real Bugs Found & FIXED (Iter A)

### 1. Duplicate `/admin/equipment` route (dead code) — FIXED
- **Symptom**: `App.js` declared the route twice (lines 284 + 325). React-Router used the first match; `EquipmentDashboard` mounted at line 325 was unreachable from `/admin/equipment`.
- **Fix**: Removed the second declaration. `EquipmentDashboard` is still reachable via `/admin/equipment-inspections` (line 325→322).
- **Verified**: route table no longer has duplicates.

### 2. `POST /api/admin/logout` → 404 — FIXED
- **Symptom**: `AdminShell.jsx:92` calls `api.post("/admin/logout")` on sign-out. Endpoint didn't exist → 404 in network tab on every admin sign-out. FE swallows the error so users never saw it, but the platform should not be emitting 404s under normal operation.
- **Fix**: Added `@api_router.post("/admin/logout")` — admin-token-gated, records an `admin_logout` event to `db.audit_events`, returns `{ok:True}`. Token revocation remains client-side.
- **Verified**: live curl returns 200 with admin token, 401 anonymous.

### 3. `POST /api/pm/logout` → 404 — FIXED
- **Symptom**: `PmShell.jsx:80` calls `api.post("/pm/logout")` on sign-out. Same pattern.
- **Fix**: Added `@api_router.post("/pm/logout")` — gated by `require_admin_async` (accepts PM + Admin tokens), records `pm_logout` audit event.
- **Verified**: live curl 200.

### 4. Dead `GET /api/equipment-units` fetch in NewEquipmentInspection.jsx — FIXED
- **Symptom**: `NewEquipmentInspection.jsx:234` called `/equipment-units?equipment_type=…` to populate a saved-units autocomplete. Endpoint was retired in iter22; the 404 was being silently swallowed in a try/catch.
- **Fix**: Removed the dead axios call. The autocomplete is now always empty (operators type the unit number) — same UX as before, just no 404 in dev tools.

---

## 🟢 Crawler False Positives (verified working via curl)

The static crawler flagged 6 endpoints that looked unmatched because they used `@router.get("")` with the path on `APIRouter(prefix=...)`. Each verified 200 via live curl:

| Endpoint | Live Status | Source |
|---|---|---|
| `GET /api/admin/date-audit` | 200 | `routes/admin_ops.py` (or similar) |
| `GET /api/admin/digest-settings` | 200 | `routes/admin_digest_config.py` |
| `PATCH /api/admin/digest-settings` | 200 | same |
| `GET /api/field-leadership` | 200 | `routes/field_leadership.py` |
| `POST /api/field-leadership` | 200 | same |
| `GET /api/job-photos` | 200 | `routes/job_photos.py` |

These are not bugs. The crawler's prefix-resolution regex needs improvement; tracked as a tooling note, not an action item.

---

## 🟡 Backend Orphans (104 endpoints with no frontend caller)

The crawler identified 104 backend endpoints with no obvious frontend axios caller. **Most are intentional** — admin-only routes, dev portal endpoints, CSV/PDF exports, server-to-server hooks. The filtered list:

- ~25 are `/api/admin/*` operational endpoints called via admin dashboards (curl/test scripts only)
- ~30 are `/api/dev/*` developer portal endpoints (intentional)
- ~20 are PDF/CSV streaming endpoints (`*.pdf`, `*.csv`)
- ~15 are dispatch/operations routes called via dynamic `${listUrl}` patterns the regex doesn't follow
- ~14 are utility/internal (auth, health-check, seed routes)

**Recommendation**: leave for Iter B/C — many will be touched anyway during the UX consolidation. Full list cached at `/app/QA_REPORT_PHASE1_orphans.txt`.

---

## 🧹 Carryover findings for Iter B (UX/UI Standardization)

These items are out-of-scope for the static crawl but flagged during file inspection for Iter B:

- **AdminShell sidebar** added 1 new section (`Operator Training`) in iter134 — Iter B should verify sidebar item ordering & active-state styling matches across all portal sidebars.
- **Hub tile patterns vary**: SafetyHub uses `SectionTile`, HrHub uses inline tile components, PmHub uses `PmTile`, ShopHub uses tabs. Iter B should normalize on a shared component.
- **Filter pill styling** is inconsistent across SafetyFireExtinguishers vs SafetyCorrectiveActions vs OpsTrainingCenter (similar but not identical class names + responsive behavior).
- **Header signature** ("Home / Back / Change Password / Sign Out") is mostly uniform — Dispatch, Shop, FieldLeadership now have a "Guides" button added in iter134; AdminShell has it in the sidebar. Iter B should formally validate every portal has the four required header items.

---

## 📋 Iter A Deliverables Summary

✅ Static crawl complete — 175 FE routes, 356 BE endpoints, 362 axios calls cross-referenced.  
✅ All 9 unmatched calls investigated; 3 real bugs fixed, 6 false-positives validated.  
✅ 1 duplicate FE route removed.  
✅ Backend services healthy after all fixes.  
✅ This report serves as the input to Iter B/C/D.

---

## 🗺️ Phase 1 Roadmap (next iterations)

- **Iter B — UX/UI + Mobile**: design system unification, mobile responsiveness sweep, consistent hub component, normalized filter/empty/loading states.
- **Iter C — Exports/PDF + Training + Data Relationships**: PDF/CSV print stabilization, finish/update training guides, enforce master-collection single-source-of-truth.
- **Iter D — Integrations + Performance + Health + Deploy**: integration failure-mode validation, query performance audit, System Health/TTL/error coverage, staging-deploy discipline.
