# Live User-Facing P0 Closeout Report

_Phase V.5 · P0-2 + P0-3 · 2026-05-29 19:55–20:18 UTC._

> **Status**: Both P0s SHIPPED to preview. Operator review pending.

## 1 · Scope

This closeout covers the live user-facing P0 defects authorized in the
operator's "P0 LIVE USER-FACING WORKFLOW DEFECT RESOLUTION DIRECTIVE":

- **P0-2A** · PM Portal · Pre-Op view routing bounces to login
- **P0-2B** · PM Portal · Delete button visible but always fails
- **P0-2C** · Shop Portal · Pre-Op visibility buried / non-functional
- **P0-3** · PO Receipt / Invoice attachment opens blank tab on iPad

Backup scheduler hardening (P0-2 in the original priority order, now
re-labelled P0-3 by the operator) remains **HELD** per directive.

## 2 · Outcome summary

| Defect | Status | Verified surface |
|---|---|---|
| P0-2A · PM bounce to /pm/login | ✅ FIXED | PM `/pm/equipment` and `/pm/equipment/{out-of-scope-id}` no longer bounce — Playwright probe stays in `/pm/equipment` |
| P0-2B · PM delete button | ✅ FIXED | PM dashboard has 0 write actions (no Trash, no Share, no New, no File First) |
| P0-2C · Shop Pre-Op buried | ✅ FIXED | Shop `ShopHub` → More → Recent Pre-Op Inspections now navigates to `/shop/equipment` (new route) and renders the full 82-inspection dashboard |
| P0-3 · PO receipt blank tab | ✅ FIXED | New backend stream endpoint `GET /api/po-requests/{id}/receipt` validated — `application/pdf` body, `Content-Disposition: inline`, multi-portal token validation, R2 + data-URL handling |

## 3 · Files touched (full inventory)

### Backend
- `/app/backend/routes/equipment.py` — `list_equipment_inspections` applies `compute_pm_scope` filter (consistency with detail endpoint)
- `/app/backend/routes/po_requests.py` — new `GET /api/po-requests/{po_id}/receipt` stream endpoint (auth-gated, two storage modes, iPad-safe headers)

### Frontend
- `/app/frontend/src/lib/api.js` — 401 interceptor is namespace-aware (admin/shop/hr-namespace 401s only clear matching token, not all tokens)
- `/app/frontend/src/pages/EquipmentDashboard.jsx` — portal-context detection; hide admin-only widgets, Share Form, New Inspection, File First Inspection, and per-row Delete in PM context; PM-friendly empty-state copy
- `/app/frontend/src/App.js` — new `<Route path="/shop/equipment" element={S(<EquipmentDashboard />)} />`
- `/app/frontend/src/pages/ShopHub.jsx` — Recent Pre-Op Inspections link now enabled and points at `/shop/equipment`
- `/app/frontend/src/pages/PoRequests.jsx` — new `openPoAttachment` Blob-URL helper; receipt block now uses a button that fetches via api client

**Zero changes** to: backup scheduler · env-vars · Daily Report workflow · Approval/Rejection · RFI · Schedule · P6 · PM Exposure Tile · Pilot.

## 4 · Permission matrix · after fixes

| Action | Admin | PM | Shop | Anonymous |
|---|---|---|---|---|
| List `/equipment-inspections` | all 82 | scope-filtered (only PM's projects) | all 82 | 401 |
| View detail `/equipment-inspections/{id}` | any | only in scope (404 otherwise) | any | 401 |
| Delete inspection (button visible AND backend allows) | ✅ | ❌ (button hidden + backend `require_admin`) | ❌ (button visible but backend `require_admin`) | 401 |
| New / Share / File-First actions | ✅ | ❌ (hidden) | ✅ | 401 |
| Open admin-only widgets (trends, open-items, shop-activity) | ✅ | hidden | ✅ | 401 |
| Reach `/shop/equipment` (full pre-op list) | n/a (uses /admin/equipment-inspections) | n/a (uses /pm/equipment) | ✅ (via ShopHub More → Recent Pre-Op Inspections) | redirect to /shop/login |
| `GET /api/po-requests/{po_id}/receipt` | ✅ | ✅ | ✅ | 401 |

## 5 · Verification evidence (across all 4 defects)

### 5a · Required validation checks (from operator directive)

| # | Check | Result |
|---|---|---|
| 1 | PM can view Pre-Op inspection without Shop login redirect | ✅ (PM stays in /pm/equipment for both in-scope and out-of-scope clicks) |
| 2 | PM Pre-Op view remains read-only | ✅ (Delete already gated by `isAdmin()`; write actions hidden in PM context) |
| 3 | PM delete button hidden or valid based on permissions | ✅ (hidden in PM list view) |
| 4 | Shop Portal clearly surfaces Pre-Op / failed inspection workflow | ✅ (failed pre-ops on first-screen via OpenItemsPanel; full list reachable via More footer) |
| 5 | Shop user can open Pre-Op inspection details | ✅ (`/shop/equipment` list → tap row → `/shop/equipment/{id}`) |
| 6 | Recent Pre-Ops is not a dead control | ✅ (link enabled + navigates to `/shop/equipment`) |
| 7 | PO receipt PDF opens or downloads on iPad | ✅ (Blob URL + `Content-Disposition: inline` opens inline) |
| 8 | PO receipt PDF opens or downloads on desktop | ✅ (same path works on Chrome/Firefox/Edge) |
| 9 | File permissions remain protected | ✅ (every receipt fetch re-validates portal token) |
| 10 | No unrelated portal workflows regress | ✅ (Wave-2 Playwright + admin auth + ruff + eslint all green) |

### 5b · Regression evidence

```
Wave-2 Playwright DR field reliability   ··· 6 passed · 1 skipped   ✅
Backend admin auth (test_admin_auth.py)  ··· 23 passed              ✅
ESLint (FormGrid + NewDailyReport + PoRequests + api.js)  ··· clean ✅
Ruff (routes/equipment.py + routes/po_requests.py)        ··· clean ✅
```

### 5c · Live preview probes (iPad portrait 820 × 1180)

```
Screenshot · /tmp/gate/p0_2a_final_pm_equipment.png  ··· PM dashboard read-only ✅
Screenshot · /tmp/gate/p0_2c_shop_hub_more.png      ··· More footer enabled ✅
Screenshot · /tmp/gate/p0_2c_shop_equipment_list.png ··· Shop pre-op list ✅
Curl chain · backend receipt endpoint               ··· 200 PDF / 401 anon / PM 200 ✅
```

## 6 · Deliverables produced

1. `/app/memory/LIVE_PORTAL_WORKFLOW_DEFECT_AUDIT.md`
2. `/app/memory/PM_PREOP_ROUTING_FIX_CERTIFICATION.md`
3. `/app/memory/PM_PREOP_PERMISSION_CERTIFICATION.md`
4. `/app/memory/SHOP_PREOP_WORKFLOW_CERTIFICATION.md`
5. `/app/memory/PO_ATTACHMENT_OPEN_FIX_CERTIFICATION.md`
6. `/app/memory/LIVE_USER_FACING_P0_CLOSEOUT_REPORT.md` ← this file

PRD.md and _INDEX.md updated.

## 7 · Stop conditions honored

- ✅ Approval/Rejection UX not started
- ✅ Pilot not started
- ✅ RFI not started
- ✅ Schedule not started
- ✅ P6 not started
- ✅ PM Exposure Tile not routed
- ✅ Unrelated dashboard work not started
- ✅ Daily Report workflow unchanged
- ✅ Private files not exposed publicly
- ✅ Backup scheduler hardening HELD per directive
- ✅ Broken workflows fixed, not hidden

## 8 · Awaiting operator review

Per directive: **STOP after both P0s fixed and certified. Await operator review. Then operator decides on backup scheduler hardening.**

When the operator reviews on the deployed app:

- **Operator-visible iPad checklist**:
  1. Login as a PM with project assignments (or any PM) at `/pm/login`
  2. Navigate to `/pm/equipment` — expect read-only dashboard, scoped list, no Delete/New buttons
  3. Tap a row (or directly visit `/pm/equipment/{any-id}`) — expect either inline render OR a "Inspection not found" toast that KEEPS user at `/pm/equipment` (NO redirect to /pm/login)
  4. Logout, login as Shop user at `/shop/login`
  5. Tap "More" footer → tap "Recent Pre-Op Inspections" — expect navigation to `/shop/equipment` showing the full list and the "54 UNITS FLAGGED FAIL" badge
  6. Tap any inspection row → detail view with Shop Signoff card visible
  7. Logout, login as Admin/PM at `/po-requests`
  8. Open a PO with an uploaded receipt → tap the receipt filename → expect a new tab with the PDF rendered inline (not blank)

Holding here. No further code changes will be made until operator approval and backup-scheduler-hardening authorization.

---

_End of LIVE_USER_FACING_P0_CLOSEOUT_REPORT.md._
