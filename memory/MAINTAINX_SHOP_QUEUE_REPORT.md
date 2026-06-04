# MAINTAINX · SHOP QUEUE REPORT

**Date:** 2026-06-04 19:30 UTC
**Sprint:** OMEGA — Defect Source Coverage Command Center
**Mode:** READ-ONLY (no writes)

This report covers the Shop Portal addition: a calm, read-only **MaintainX Readiness Queue** tile placed on the Shop Hub. The directive explicitly required: *Show Ready / Blocked / Duplicate Risk / Awaiting RTS. Read-only. No work-order buttons. No MaintainX actions. No edit capability.*

---

## 1 · What was built

- NEW `frontend/src/components/shop/ShopMaintainxReadinessTile.jsx` (78 LOC)
- MOD `frontend/src/pages/ShopHub.jsx` — one new import, one new `<ShopMaintainxReadinessTile />` placement.

The tile consumes the existing portal-gated endpoint `GET /api/integrations/maintainx/defect-coverage` (admin-strict + any-portal-token gate built in P0-A/P0-B + this sprint). No new endpoint, no new collection, no Shop-portal-specific endpoint.

---

## 2 · Tile content

| Cell | Value displayed | Source |
| --- | --- | --- |
| Ready | `totals.ready_for_maintainx` | classifier |
| Blocked | `totals.blocked` | classifier |
| Duplicate Risk | `totals.duplicate_risk` | classifier |
| Awaiting RTS | `totals.out_of_service` (open OOS defects = need RTS once repaired) | derived |

Footer text (rendered):

> Counts reflect every active equipment defect across DVIR, Pre-Op, Manual OOS, and Maintenance Holds. **No work orders are created from this view.**

No action buttons. No `onClick` handlers attached to cells. No deep-links into MaintainX. No drill-down view from the Shop portal (drill-down is admin-only by design — Shop sees the readiness queue but not the underlying defects, to keep the portal operations-focused).

---

## 3 · Placement on Shop Hub

```jsx
// frontend/src/pages/ShopHub.jsx
<LastActivityLine portal="shop" />

{/* iter511 · MaintainX Readiness Queue · read-only intelligence */}
<ShopMaintainxReadinessTile />

{/* … existing Shop Console kicker, Equipment Needing Attention, … */}
```

Renders immediately below the existing "Last Activity" trace and above the Equipment Needing Attention section — so a shop manager opening the portal sees a 4-cell snapshot of MaintainX readiness without scrolling.

The tile self-mounts AFTER the data resolves (loading state collapses the section to render nothing) so a slow API does not interfere with shop operations.

---

## 4 · Live preview verification

| Cell | Value (preview baseline) |
| --- | --- |
| Ready | `2` |
| Blocked | `134` |
| Duplicate Risk | `2` |
| Awaiting RTS | `110` |

Confirmed via Playwright smoke (`shop-mx-readiness-tile` + `shop-mx-ready` + `shop-mx-blocked` + `shop-mx-dup` + `shop-mx-awaiting-rts` test-ids all resolved with non-empty inner text).

---

## 5 · Compliance with directive

| Requirement | Verdict |
| --- | --- |
| Show Ready / Blocked / Duplicate Risk / Awaiting RTS | YES (4 cells, in order) |
| Read-only | YES (no `<Button>` with action handler; no `api.post/put/patch/delete`) |
| No work-order buttons | YES |
| No MaintainX actions | YES |
| No edit capability | YES (no inputs anywhere) |

---

## 6 · Safety guarantees

- Tile imports `api` from `@/lib/api` and issues exactly one `GET` request (`/integrations/maintainx/defect-coverage`).
- No `setItem` calls — no tokens written by this component.
- No write to MaintainX, `fleet_defects`, `equipment_inspections`, `asset_holds`, `asset_mappings`, or `equipment_master`.
- Shop-portal token is the bearer; admin / safety / dispatch / PM / HR / field-leadership tokens are also accepted for the same read.

---

## 7 · Verdict — Shop Queue

```
SHOP MAINTAINX READINESS QUEUE  :  COMPLETE

  4-cell read-only tile                    : DONE
  Placement on Shop Hub                    : DONE (above Equipment Attention)
  Live data in preview                     : YES (2 / 134 / 2 / 110)
  No action buttons                        : VERIFIED
  No write paths                           : VERIFIED
```
