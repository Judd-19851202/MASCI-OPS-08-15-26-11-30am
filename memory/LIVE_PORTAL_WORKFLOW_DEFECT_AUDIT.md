# Live Portal Workflow Defect Audit

_Phase V.5 · P0-2 / P0-3 · 2026-05-29 19:55–20:10 UTC._

> Operator-reported live iPad defects:
> 1. **PM Portal · Pre-Op view routing** — clicking an inspection bounces to /pm/login (was reported as Shop login; root cause identical).
> 2. **PM Portal · Delete button** — visible but always fails on click.
> 3. **Shop Portal · Pre-Op visibility** — "Recent Pre-Op Inspections" link buried in More footer AND non-functional (disabled).
> 4. **PO Receipt / Invoice PDF tap → blank tab** on iPad.

This audit captures the investigation that preceded the fix.

---

## 1 · P0-2A · PM Pre-Op routing bounce

### Reproduction

| Step | Path | Result |
|---|---|---|
| 1 | `POST /api/pm/login` as `chriswright@mascigc.com` | OK · PM token issued |
| 2 | `GET /api/equipment-inspections` with `X-PM-Token` | **HTTP 200 · 82 items** (PM saw every inspection — including ones outside their scope) |
| 3 | `GET /api/equipment-inspections/{id}` with `X-PM-Token` | **HTTP 404** ("Equipment inspection not found" — detail endpoint applies PM scope filter via `compute_pm_scope` at `routes/equipment.py:345`) |
| 4 | Navigate browser to `/pm/equipment/{any-id}` | toast "Inspection not found", URL changes to `/pm/login`. **PM kicked out of portal.** |

### Console-log trace from live preview

```
GET /api/equipment-inspections/50de87a5-...           → 404
GET /api/admin/equipment-inspections/open-items       → 401  ← OpenItemsPanel
GET /api/admin/equipment-inspections/trends?days=90   → 401  ← EquipmentTrendsPanel
```

### Root cause (three-link chain)

1. `EquipmentDashboard.jsx` (used by `/pm/equipment`) renders three child widgets — `EquipmentTrendsPanel`, `OpenItemsPanel`, `ShopActivityFeed` — that hardcode `/api/admin/equipment-inspections/*` endpoints.
2. Backend `/api/admin/*` is locked to admin tokens. PM token gets 401.
3. `lib/api.js` 401 interceptor (pre-fix) blindly cleared **whichever** session tokens the request carried. The 401 from an admin-namespace widget therefore **wiped the PM token**.
4. On next render, `RequireAdminOrPm` no longer admits → bounces to `/pm/login`.

### Compounding factor

The list endpoint `/api/equipment-inspections` returned all 82 inspections regardless of PM scope, while the detail endpoint applied scope. PM saw rows in the list they couldn't actually open — every click produced the 404 → "Inspection not found" toast. Even with the token-clear bug fixed, the inconsistent list/detail scoping made the UX feel broken.

## 2 · P0-2B · PM Delete button

`EquipmentDashboard.jsx:185-193` rendered the Trash button unconditionally on every row. Backend `DELETE /api/equipment-inspections/{id}` requires `require_admin` — PM gets 403. Result: PM sees the button, taps it, sees "Delete failed" toast. Invalid UX per operator's "visible action must match valid permission path" doctrine.

The `ViewEquipmentInspection.jsx:145` detail-page Delete was already gated by `isAdmin()` and was correct.

## 3 · P0-2C · Shop Portal Pre-Op visibility

### Live observation

ShopHub.jsx first-screen sections:
1. Equipment Needing Attention (DispatchLifecycleTile + OpenItemsPanel) — correctly surfaces failed pre-ops.
2. Active Recovery Work · Waiting / Delays · Returned to Service · Operational Continuity History.

But the link to the **full pre-op list** lived only in the "More" footer at line 446:
```jsx
<MoreLink to="?legacy=recent" icon={ClipboardList}
          label="Recent Pre-Op Inspections" disabled />
```

`disabled` → rendered as a `<span>` with the tooltip "Reachable via direct URL · kept out of first-screen cognition". The `to="?legacy=recent"` was a placeholder that never navigated anywhere. **Operator was correct: the link was buried AND non-functional.**

Root cause: there was no `/shop/equipment` route at all in `App.js` (only `/shop/equipment/:id` for the detail view existed). Shop users could not reach the full pre-op list from inside the Shop portal.

## 4 · P0-3 · PO Receipt PDF blank tab

### Reproduction (live preview)

| Step | Result |
|---|---|
| Open PO drawer in `/po-requests` | OK |
| `po.receipt_url` is stored as a 2-MB `data:application/pdf;base64,...` string (preview has `r2_upload_callable=None`, so all receipts use the base64 fallback per `routes/po_requests.py:680-689`) | this is a working data URL on the backend |
| Frontend rendered `<a href={po.receipt_url} target="_blank" rel="noopener noreferrer">` | clicking tries to navigate the new tab to a 2-MB data URL |
| iPad Safari: refuses to navigate to multi-megabyte data URLs in a new tab | **blank tab** |
| Desktop Chrome / Firefox / production R2 signed URLs: works UNTIL signed URL expires (R2 signed URLs default to a finite TTL — operator-managed) → blank tab |

### Root cause

Two storage modes (data URL · signed R2 URL) shared a single fragile rendering path (`<a href={raw_url} target="_blank">`). Both modes fail:
- Data URL: too large for Safari to navigate to.
- Signed R2 URL: expires.
- Either way: blank tab on tap.

The correct architecture per the operator's "Preferred fix direction" is a **stable backend stream endpoint** that:
- Validates the user's portal token.
- Reads the stored `receipt_url` (data URL or signed URL).
- Streams the bytes inline with `Content-Disposition: inline; filename="..."`.
- Frontend fetches via the api client (with auth headers), wraps as a Blob, opens via `URL.createObjectURL`.

This:
- Eliminates raw data URLs from the frontend payload.
- Eliminates dependence on URL expiry.
- Works on iPad Safari (Blob URLs with `application/pdf` open inline reliably).
- Validates permission on every open (no public exposure).

## 5 · What is fixed (high-level)

| Defect | Fix | File(s) |
|---|---|---|
| P0-2A · PM bounce to login | (1) `api.js` 401 interceptor is now namespace-aware — `/api/admin/*` 401 ONLY clears admin token. PM/Shop/HR sessions survive admin-side widget failures. (2) `EquipmentDashboard.jsx` hides admin-only widgets in PM context. (3) Backend `list_equipment_inspections` now applies the same `compute_pm_scope` filter the detail endpoint uses — PM only sees inspections they can actually open. | `frontend/src/lib/api.js`, `frontend/src/pages/EquipmentDashboard.jsx`, `backend/routes/equipment.py` |
| P0-2B · PM Delete button | `EquipmentDashboard.jsx` and the form share dashboard hide the Trash button + New Inspection button + Share Form dialog + File First Inspection button when `pathname.startsWith("/pm/")`. PM is now strictly read-only. | `frontend/src/pages/EquipmentDashboard.jsx` |
| P0-2C · Shop pre-op visibility | (1) `App.js` adds `<Route path="/shop/equipment" element={S(<EquipmentDashboard />)} />`. (2) `ShopHub.jsx` "Recent Pre-Op Inspections" link is no longer `disabled` and now navigates to `/shop/equipment`. Failed pre-ops continue to live on first-screen via the existing `OpenItemsPanel`. | `frontend/src/App.js`, `frontend/src/pages/ShopHub.jsx` |
| P0-3 · PO Receipt PDF blank tab | (1) New backend endpoint `GET /api/po-requests/{po_id}/receipt` streams the bytes with correct content-type + `Content-Disposition: inline`. Validates `require_any_portal_token`. Handles both data-URL and http(s) URL storage. (2) Frontend `PoRequests.jsx` uses a new `openPoAttachment` helper that fetches via the api client (auth headers attached), wraps as Blob, opens in new tab with fallback to download anchor. | `backend/routes/po_requests.py`, `frontend/src/pages/PoRequests.jsx` |

## 6 · Permission matrix (after fixes)

| Action | Admin | PM | Shop | Anonymous |
|---|---|---|---|---|
| List `/equipment-inspections` | all 82 | scope-filtered (only PM's projects) | all 82 | 401 |
| View detail `/equipment-inspections/{id}` | any | only in scope (404 otherwise) | any | 401 |
| Delete inspection | ✅ | ❌ (button hidden) | ❌ | 401 |
| Open admin-only widgets (trends, open-items, shop-activity feed) on /equipment dashboard | visible | **hidden** | visible | 401 |
| New Inspection button on /equipment dashboard | visible | **hidden** (read-only) | visible | 401 |
| Open `/shop/equipment` (full pre-op list) | n/a (uses /admin/equipment-inspections) | n/a (uses /pm/equipment) | visible from ShopHub "More" footer | redirected to /shop/login |
| GET `/api/po-requests/{po_id}/receipt` | ✅ | ✅ | ✅ | 401 |

---

_End of LIVE_PORTAL_WORKFLOW_DEFECT_AUDIT.md._
