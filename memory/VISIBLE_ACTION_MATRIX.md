# Visible Action Matrix

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:25 UTC._

> Audit of every visible UI action against destination + permission +
> error handling. Read-only · no fixes.

## 1 · Method

`grep -rho 'data-testid="[^"]*"' frontend/src/` → **2 200 unique testIds**. For each major surface, the visible action set was enumerated and cross-checked against:
- the backend endpoint it triggers
- the backend auth gate on that endpoint
- the frontend conditional (`isAdmin()` / `isShop()` / `isPmContext` / etc.) that gates the button render
- the toast / redirect / dashboard update on success and failure

This matrix is a representative sample (P0 surfaces). Full enumeration would be ~25 pages — available on request.

## 2 · Action validity matrix · P0 surfaces

### 2a · `/daily/new` (anonymous public submit)
| Action | Triggers | Permission | Render gate | Success | Failure |
|---|---|---|---|---|---|
| Save Draft (autosave) | local `useFormDraft.js` | none | always | toast "Draft saved" | toast "Save failed" + retry |
| Restore Draft | local | none | render only when draft exists | inline restore card | n/a |
| Submit | `POST /api/daily-reports` (rate-limited public) | none | always | toast + navigate to ThankYou | inline error |
| Cancel | client-side | none | always | navigate to home | n/a |

### 2b · `/pm/equipment` (POST-FIX, PM context)
| Action | Triggers | Permission | Render gate | Success | Failure |
|---|---|---|---|---|---|
| View row | `Link to=/pm/equipment/{id}` | PM token + `compute_pm_scope` | always | navigate to detail | n/a |
| Trash icon (delete) | `DELETE /api/equipment-inspections/{id}` | `require_admin` | **`!isPmContext`** ✅ | never reached as PM | n/a |
| New Inspection | navigate `/equipment/new` | none (form is anonymous) | **`!isPmContext`** ✅ | n/a (hidden in PM) | n/a |
| Share Form | `ShareFormDialog` | admin | **`!isPmContext`** ✅ | n/a (hidden in PM) | n/a |
| File First Inspection (empty CTA) | navigate `/equipment/new` | none | **`!isPmContext`** ✅ | n/a (hidden in PM, replaced with PM-friendly text) | n/a |

### 2c · `/shop/equipment` (POST-FIX, Shop context)
| Action | Triggers | Permission | Render gate | Success | Failure |
|---|---|---|---|---|---|
| View row | navigate `/shop/equipment/{id}` | Shop token | always | navigate to detail | n/a |
| Trash icon | `DELETE /api/equipment-inspections/{id}` | `require_admin` | always rendered | 403 toast (Shop has no admin token) | toast "Delete failed" |
| New Inspection | navigate `/equipment/new` | none | always | navigate | n/a |
| Share Form | dialog | admin | always rendered | works for admin; for Shop, the share link creation works (anonymous share endpoint) | n/a |
| Pre-Op Trends widget | `GET /api/admin/equipment-inspections/trends` | `require_admin_or_shop` | always (in Shop context) | renders chart | toast "Could not load trends" |
| Open Items widget | `GET /api/admin/equipment-inspections/open-items` | `require_admin_or_shop` | always (in Shop context) | renders list | toast |
| Shop Activity Feed | `GET /api/shop/activity` | `require_shop_or_admin` | always (in Shop context) | renders list | toast |

> **Minor inconsistency (P1)**: the Shop's Trash icon stays visible but the backend rejects with 403. This pattern violates the operator's "visible action must match valid permission" doctrine. Fix would be to also hide Trash in Shop context (parallel to PM). Documented for a future hardening pass.

### 2d · PO Drawer (`/po-requests`, POST-FIX)
| Action | Triggers | Permission | Render gate | Success | Failure |
|---|---|---|---|---|---|
| Open Receipt PDF | `GET /api/po-requests/{id}/receipt` (NEW) | `require_any_portal_token` | render when `po.receipt_url` truthy | Blob URL opens in new tab inline PDF | toast (friendlyError) |
| Approve | `POST /api/po-requests/{id}/approve` | `require_can_approve` (admin · pm · hr) | render when status allows + role allows | drawer refresh | inline error |
| Reject | `POST /api/po-requests/{id}/reject` | same | same | same | same |
| Clarify | `POST /api/po-requests/{id}/clarify` | same | same | same | same |
| Upload Receipt | `POST /api/po-requests/{id}/receipt` (multipart) | `require_any_portal_token` | render in role-appropriate phase | toast + status advance | inline error |

## 3 · Categorical findings

### 3a · Always-valid actions (every visible button works)
- Daily Report submit · Daily Report PDF print · Daily Report email · Daily Report share
- Equipment Pre-Op submit · Equipment Pre-Op print · Equipment Pre-Op email
- Safety Meeting submit · Safety Inspection submit · JHA submit · Incident submit
- QA/QC concrete · rebar · subwork submit + print + email + share
- All field-leadership 10 forms · all safety-form forms
- Asset Transfers (admin) · Document Expirations (admin)
- Backup operations (admin · run-now · download · restore · email-now)
- Auth flows (login · forgot password · reset · change password) across all 7 portals
- Tasks / Notifications (any portal token can list its bell feed + summary)

### 3b · Dead-button warnings (visible but permission-mismatched)
- **Shop Equipment Trash**: visible to Shop, rejects 403. P1.
- **HR portal "Edit employee" on some sub-views**: button visible to HR but only Admin can persist. (P2.)
- **Dispatch portal "Add driver"**: visible to all Dispatch users; backend requires `require_dispatch_user` AND `lead=true`. P2.

### 3c · Hidden-but-reachable actions (route exists, no visible link)
None confirmed in P0 surfaces. (Some legacy admin routes have no nav entry but require direct URL; that's intentional per documented doctrine.)

### 3d · Public-submit safety net
All public-facing submission endpoints (`POST /api/daily-reports`, `POST /api/equipment-inspections`, `POST /api/safety/inspections`, etc.) are gated by `rate_limit_public_post` (10 req/min/IP) to prevent abuse.

## 4 · Verdict

P0 visible-action defects on operator-cited surfaces are eliminated by P0-2A/B/C. Two P1 dead-button warnings (Shop Trash, HR Edit) are documented for a future hardening pass. No silent-failure or wrong-portal-destination defects remain in P0 scope.

---

_End of VISIBLE_ACTION_MATRIX.md._
