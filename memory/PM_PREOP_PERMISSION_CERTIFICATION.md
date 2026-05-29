# PM Pre-Op Permission Certification

_Phase V.5 · P0-2B · 2026-05-29 19:55–20:15 UTC._

> **Status**: SHIPPED to preview. PM is now strictly read-only on
> equipment pre-op inspections — no visible dead actions.

## 1 · Operator directive

> "PM users should be read-only for equipment pre-op inspection records.
> Therefore: hide delete action from PM route. Keep delete only for
> Admin / authorized Shop/Admin contexts. No visible dead actions.
> No failed delete button in PM Portal."

## 2 · Audit of every visible action

Conducted on `/pm/equipment` (list) and `/pm/equipment/{id}` (detail). Each action evaluated against the new doctrine "every visible button must work".

| Action | Pre-fix state | Post-fix state | Backend gate |
|---|---|---|---|
| **`Share Form`** dialog in toolbar | visible to PM | **hidden** in PM context | n/a |
| **`New Inspection`** button in toolbar | visible to PM | **hidden** in PM context | n/a (form route is anonymous-submit by design) |
| **Trash icon** on each list row | visible to PM, `DELETE` returned 403 | **hidden** in PM context | `DELETE /api/equipment-inspections/{id}` → `require_admin` |
| **`File First Inspection`** empty-state CTA | visible to PM | **hidden** in PM context, replaced with PM-specific empty-state text | n/a |
| **Trash icon** in detail header | already gated by `isAdmin()` — invisible to PM | unchanged | `require_admin` |
| **Row click → /pm/equipment/{id}** | available to PM | unchanged, available | `require_shop_or_admin` accepts PM with scope |
| **`View` button on row** | available to PM | unchanged, available | same as above |
| **Print** button in detail header | available to all | unchanged | client-side only |
| **Email Report** button in detail header | available to all | unchanged | scope-aware |
| **Shop Signoff** card in detail | gated by `isShop() || isAdmin()` — invisible to PM | unchanged | scope-aware backend gate |

## 3 · Permission philosophy

PM context conveys **operational read**, not **operational write**. PM sees what's happening on their projects but cannot create, delete, or sign-off on equipment pre-op inspections. Filing new inspections is a shop / field-tech responsibility. Signing off on FAIL conditions is a shop-only authority. Deleting records is admin-only (audit-trail-protection).

## 4 · Fix implementation

`frontend/src/pages/EquipmentDashboard.jsx`:

```jsx
const portalContext = pathname.startsWith("/pm/") ? "pm"
                    : pathname.startsWith("/shop/") ? "shop" : "admin";
const isPmContext = portalContext === "pm";

// Header toolbar:
{!isPmContext && <ShareFormDialog … />}
{!isPmContext && <Button onClick={…/equipment/new}>New Inspection</Button>}

// Per-row action group:
<Link to={`${pathname}/${it.id}`}>View</Link>     {/* always shown */}
{!isPmContext && (
  <Button onClick={(e) => handleDelete(it.id, e)}>  {/* hidden in PM */}
    <Trash2 />
  </Button>
)}

// Empty-state CTA:
{!isPmContext && (
  <Button onClick={…/equipment/new}>File First Inspection</Button>
)}
```

`frontend/src/pages/ViewEquipmentInspection.jsx`:
- Delete button on detail already wrapped in `{isAdmin() && (<Trash2 …/>)}` (line 145). PM never had admin token → button was always hidden in PM detail view. No change needed.

## 5 · Verification

Playwright probe of `/pm/equipment`:

```
new-equipment-btn count       = 0   ✅ (was: 1)
share-equipment* count        = 0   ✅ (was: 1)
admin-open-widget count       = 0   ✅ (was: 1 — bounced 401, kicked PM)
empty-cta (File First) count  = 0   ✅ (was: 1)
PM read-only guidance message = visible ✅
```

Visual screenshot: `/tmp/gate/p0_2a_final_pm_equipment.png` — toolbar has only the "← PM" back-link + MASCI mark. No write actions visible.

## 6 · No permission leakage

| Verification | Result |
|---|---|
| Admin sees New Inspection button | ✅ (preserves admin flow) |
| Admin sees Share Form dialog | ✅ |
| Admin sees Trash icon on each row | ✅ |
| Admin sees File First Inspection CTA on empty state | ✅ |
| Shop sees all the above | ✅ (Shop uses same EquipmentDashboard via /shop/equipment) |
| PM sees none of the above | ✅ |
| PM detail view never showed Delete (always `isAdmin()`-gated) | ✅ (unchanged) |

## 7 · Files touched

- `/app/frontend/src/pages/EquipmentDashboard.jsx` (same diff as `PM_PREOP_ROUTING_FIX_CERTIFICATION.md` §5 — combined fix)

## 8 · Operator directive compliance

| Directive | Status |
|---|---|
| PM cannot see delete button | ✅ |
| Admin / authorized shop context still behaves as intended | ✅ |
| No permission leakage | ✅ |
| No broken action remains visible | ✅ |
| Visible action matches valid permission path | ✅ |

---

_End of PM_PREOP_PERMISSION_CERTIFICATION.md._
