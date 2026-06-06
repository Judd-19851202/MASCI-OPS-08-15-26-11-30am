# TRENCH SAFETY — PHASE 3.5 PUBLIC COMPLETION GO / NO-GO

**Date:** 2026-06-06
**Mode:** Correction sprint — closes 3 verified architecture gaps
**Authorized scope:** GAP-1 (Public Dashboard) · GAP-2 (Public Lookup) · GAP-4 (Public Reporting)
**Verdict:** 🟢 **PHASE 3.5 COMPLETE — SAFE TO START PHASE 4**

---

## 1. What was built

### 1.1 Backend (minimal — extends Phase 2 contract)

| File | Change | Purpose |
|---|---|---|
| `routes/trench_safety/_models.py` | Added `DAMAGE_REPORT_KINDS` enum + `kind: str` field on `DamageReportPublic` | GAP-4 — server validates the 4 allowed report types |
| `routes/trench_safety/public.py` | Added `GET /api/trench-safety/public/overview` (counts only, no PII) · validated `kind` enum on `POST /damage-report` · stamped `kind` into the persisted repair_doc + audit event detail | GAP-1 powers the public dashboard · GAP-4 hardens the intake |

**Endpoints added:**
- `GET /api/trench-safety/public/overview` → `{total_active_assets, counts_by_status, counts_by_type}` — anonymous fleet shape with **zero identities**.

**Endpoints extended:**
- `POST /api/trench-safety/public/damage-report` — now accepts `kind` ∈ {`Damage`, `Unsafe Condition`, `Missing Pins`, `Missing Labels`}; default `Damage` (backwards-compatible); invalid value → 422.

**No collections added. No write surface added. No admin function exposed.**

### 1.2 Frontend (3 new modules + 2 small edits)

| File | Status | Purpose |
|---|---|---|
| `pages/trench_safety/PublicTrenchSafetyDashboard.jsx` | NEW | GAP-1 — public field dashboard at `/trench-safety` |
| `pages/trench_safety/PublicAssetLookup.jsx` | NEW | GAP-2 — reusable lookup card |
| `pages/trench_safety/PublicReportModal.jsx` | NEW | GAP-4 — 4-kind reporting modal |
| `pages/trench_safety/TrenchSafetyQrLanding.jsx` | MODIFIED | Wires the same Report Modal into the QR landing |
| `App.js` | MODIFIED | New public route `/trench-safety` |
| `lib/i18n.js` | MODIFIED | +30 EN/ES key pairs for the new strings |

### 1.3 Live verification

```
GET /api/trench-safety/public/overview
  → {"total_active_assets":7,"counts_by_status":{"Available":6,…,"Inspection Hold":1,"Repair":0},…}

POST /api/trench-safety/public/damage-report  body:{asset_id:"TB-07",kind:"Missing Pins",description:"…"}
  → {"ok":true,"received_at":"2026-06-06T21:05:26.594839+00:00","kind":"Missing Pins"}

POST … body:{asset_id:"TB-07",kind:"Bogus",description:"5char"}
  → 422  {"detail":"kind must be one of ['Damage','Unsafe Condition','Missing Pins','Missing Labels']"}

POST … body:{asset_id:"TB-07",description:"…"}   (no kind)
  → {"ok":true,"received_at":"…","kind":"Damage"}   (backwards-compatible default)
```

SPA route smoke (preview origin):
```
/trench-safety                  → 200  (public dashboard)
/trench-safety/assets/TB-07     → 200  (existing QR landing, now with Report button)
/trench-boxes                   → 200  (legacy preserved)
/safety/trench-safety           → 200  (Safety Portal admin landing — UNCHANGED)
```

Mobile screenshot at viewport 420×900 confirmed:
- Title "Trench Safety" + "FIELD VIEW" kicker
- 4-tile Fleet Overview reading the live counts (7 / 6 / 1 / 0)
- Amber Coaching strip
- Asset Lookup card with input + LOOK UP button
- Three action tiles: Tabulated Data · Safety References · **Report a Problem**
- QR Scan helper
- EN/ES toggle in header
- Caution stripe + MASCI brand bar

Every `data-testid` from the spec was found via Playwright locator: `public-dash-title`, `public-dash-stats`, `public-asset-lookup`, `public-dash-report`, `public-dash-tabdata`, `public-dash-references` (1 each).

---

## 2. NOT-AUTHORIZED rule compliance

| Forbidden item | Status |
|---|---|
| Scan counters | **NOT ADDED** (no scan stat tile, no counter, no "X scans today") |
| Scan statistics | **NOT ADDED** |
| Usage metrics | **NOT ADDED** |
| Engagement widgets | **NOT ADDED** |
| New dashboards (beyond GAP-1) | **NOT ADDED** — only the field-view public dashboard explicitly authorized |
| New analytics | **NOT ADDED** |
| Gamification | **NOT ADDED** |
| New reports | **NOT ADDED** — only the field-reporting MODAL authorized |
| New admin functions | **NOT ADDED** — every admin endpoint still gated, no UI exposed publicly |

The `public/overview` endpoint returns **only counts** — no IDs, no names, no project names, no PII. Not a "scan counter" or "engagement widget"; it's the directive-listed "Trench Safety Overview" capability.

---

## 3. Validation matrix (per directive)

| # | Requirement | Result |
|---|---|---|
| 1 | Public dashboard exists | ✅ `/trench-safety` 200, all 6 sections render, real counts |
| 2 | Public lookup exists | ✅ `PublicAssetLookup` card on dashboard · navigates to `/trench-safety/assets/<id>` |
| 3 | Public reporting exists | ✅ Modal on dashboard + on QR landing · 4-kind enum · creates pending-shop-review repair · audit event written |
| 4 | No admin functions exposed publicly | ✅ All 9 admin capabilities return 401 anonymous (re-verified) |
| 5 | Safety Portal still owns administration | ✅ `/safety/trench-safety/*` routes UNCHANGED · only the read-only Phase 3 surfaces |
| 6 | Operations integration untouched | ✅ `db.equipment_master`, `/api/asset-transfers`, dispatch surfaces unmodified |
| 7 | Mobile works | ✅ Mobile viewport screenshot captured at 420×900; all elements rendered & legible |
| 8 | Spanish works | ✅ 30 EN→ES key pairs added · `LangToggle` operates on the new pages |
| 9 | No deployment performed | ✅ Preview-only |

Additional integrity checks:
- **Pytest regression:** 28/28 backend tests green (`tests/test_trench_safety_phase2.py`)
- **Frontend lint:** 0 issues in `/app/frontend/src/pages/trench_safety/`
- **Backend lint:** 0 issues in `/app/backend/routes/trench_safety/`
- **Backwards compatibility:** Damage-report endpoint accepts payloads WITHOUT `kind` (defaults to `Damage`) — no client breakage.

---

## 4. Architecture lock — final standing

| Lock rule | Status after Phase 3.5 |
|---|---|
| Public Safety Tile owns field reference only | ✅ ALL allowed capabilities now live (GAP-1 / GAP-2 / GAP-4 closed; GAP-3 OSHA + Training deferred to Phase 9 as designed) |
| Safety Portal owns administration | ✅ UNCHANGED — Phase 3 read-only routes, admin endpoints gated |
| Operations Integration owns assignment / location / utilization | ✅ UNCHANGED — equipment_master mirror intact, awaiting Phase 4 wire-up |
| No drift | ✅ — same Mongo collections, same endpoint family, same i18n |
| No admin exposed publicly | ✅ — re-verified 401 across 9 admin capabilities |

---

## 5. State delta

| Surface | Before | After | Δ |
|---|---|---|---|
| Public routes | 2 (`/trench-boxes`, `/trench-safety/assets/:id`) | **3** (+`/trench-safety`) | +1 |
| Public API endpoints | 2 | **3** (+`/api/trench-safety/public/overview`) | +1 |
| Damage-report payload shape | `{asset_id, description, reported_by_name?, contact?}` | `{asset_id, kind?, description, reported_by_name?, contact?}` | +1 field (optional, validated) |
| Frontend modules in `pages/trench_safety/` | 6 | **9** | +3 |
| `i18n.js` Phase-3.5 keys | 0 | **30** EN/ES pairs | +30 |
| Backend writes | 0 schema changes | 0 schema changes | 0 |
| Admin surfaces exposed | 0 publicly | 0 publicly | 0 |
| Test fleet integrity | 7 of 7 MASCI assets | **7 of 7** | 0 |

---

## 6. Sign-off

> Under OMEGA Phase 3.5 Public Trench Safety Completion directive, on 2026-06-06:
>
> 🟢 **PHASE 3.5 COMPLETE — SAFE TO START PHASE 4.**
>
> Three architecture gaps (GAP-1 Public Dashboard · GAP-2 Public Lookup · GAP-4 Public Reporting) closed exactly to the directive scope. Zero forbidden additions (no scan counters, no engagement widgets, no new dashboards beyond the authorized one). All 9 administrative capabilities remain walled off (401 anon). Safety Portal untouched. Operations Integration foundation untouched. 28/28 pytest regression green. Frontend + backend lint clean. EN/ES parity. Mobile verified. No deployment.
>
> 🛑 STOP per directive. Awaiting operator authorization to start Phase 4 — Equipment Inventory + Job Assignment + Project Visibility Integration.

— Phase 3.5, 2026-06-06
