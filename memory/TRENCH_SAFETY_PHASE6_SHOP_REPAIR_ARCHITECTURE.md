# TRENCH SAFETY · PHASE 6 — SHOP REPAIR ARCHITECTURE

**Phase:** 6 — Shop Repair Workflow
**Date:** 2026-02
**Status:** 🟢 Architecture certified · built · tested.

## Mandate (operator-locked)
> Surface and manage trench safety repair work inside the correct authenticated operational surface (Shop Portal) using the **existing** Phase 4B repair stubs + Maintenance Hold engine. **No duplicate repair / hold / status systems.**

## State machine — extended (not replaced)

| Phase | REPAIR_STATUSES |
|-------|-----------------|
| 2 (original) | Open · In Progress · Completed |
| 6 (extended) | Open · In Progress · **Waiting on Parts** · **Vendor Repair** · Completed · **Closed After Verification** |

Phase 4B repair stubs (created automatically by Fail+Major and Fail+Critical inspections) remain unchanged — they ship as `status="Open"`, `kind="repair_recommendation"`. Phase 6 only adds the new statuses that follow Open.

## Hold integration — unchanged invariants
- Maintenance Hold opens on `open_repair`; clears on `complete_repair` only if no other open/in-progress repair exists on the asset.
- If `repair.requires_reinspection=true` then `complete_repair` re-opens Inspection Hold; the Inspection Hold is now ONLY clearable through one of:
  - a passing Monthly Competent Person or Annual Review inspection (Phase 4B path), OR
  - Safety verification on the Completed repair (Phase 6 new path).
- Safety / Certification Holds are NEVER touched by repair endpoints — the hold engine resolver makes them naturally win.

## New endpoints (2)

### `GET /api/trench-safety/shop/repairs` (Shop / Admin)
Shop-facing queue. By default excludes `Closed After Verification`. Joins minimal asset metadata (`asset_type`, `size`, `serial_number`, `operational_status`, `current_project_*`, `current_location`) so the queue UI does not need a second roundtrip per row. Sorted by severity (Critical → Major → Minor → None → unset) then `opened_at`.

Query params: `status`, `severity`, `requires_reinspection`, `include_closed`, `limit`.

Returns `{items, count, counts: {<status>: n}}`.

### `POST /api/trench-safety/repairs/{cert_id}/verify` (Safety / Admin)
The new safety verification path that closes a Completed repair to `Closed After Verification`. Accepts:
```jsonc
{ "verification_notes": "...", "reinspection_passed": true | false }
```
Rules:
- 409 if repair is not in `Completed`.
- If `requires_reinspection && reinspection_passed === true` → clears Inspection Hold via the hold engine, then resolver runs.
- If `reinspection_passed === false` → Inspection Hold stays. Repair still moves to `Closed After Verification`, but the asset stays out of service.
- Higher-priority holds (Safety / Certification) are never touched.

## Existing endpoints extended (no signature changes)
- `PATCH /api/trench-safety/repairs/{id}` now accepts an optional `note: string`. The note is pushed onto `repairs.notes_history[]` (no overwrite); top-level `note` is never persisted.
- `RepairUpdate` accepts the existing fields (status, completion_notes, repair_vendor, repair_cost, photo_refs, requires_reinspection) plus `note`.

## Frontend surface
- **NEW** `pages/shop/ShopTrenchSafetyRepairs.jsx` — calm Shop queue page (filter chips for status, severity dot, hold badge, reinspection badge, source/project/vendor metadata). Reads only from `/shop/repairs`. Single-screen, mobile-first.
- **MOD** `App.js` — `Route path="/shop/trench-safety-repairs" element={S(<ShopTrenchSafetyRepairs />)}` under the Shop auth gate.
- **MOD** `pages/ShopHub.jsx` — added `Trench Safety Repairs` link inside the existing collapsible "More" footer (calm-doctrine compliant; never first-screen).

The repair **detail / management view** continues to live on the existing Safety Portal asset page (`/safety/trench-safety/assets/{id}`) which renders the Phase 4B repairs + Phase 6 status transitions. Shop staff click through from the queue row → asset page.

## i18n
- `lib/i18n.js` extended with Phase 6 strings: Trench Safety Repairs · Waiting on Parts · Vendor Repair · Closed After Verification · Pending Safety Verification · Reinspection Required · Repair Notes · Repair Cost · Repair Vendor · Mark Repair Completed · Do Not Use · Under Repair · Awaiting Verification · Verify Repair · Verification Notes · Start Repair · Add Note.

## Audit events (Phase 6 additions)
- `trench_asset_repair_updated` (PATCH path)
- `trench_asset_repair_verified` (verify endpoint)

Phase 2/4B/5 events (`_opened`, `_completed`) remain unchanged.

## Equipment_master mirror
Unchanged. The mirror's `active_holds[]` and `operational_status` already convey "Maintenance Hold during repair" via the Phase 4B enrichment. Dispatch / Search / Project surfaces inherit Phase 6 state automatically.

## Public field view
Unchanged. `pages/trench_safety/TrenchSafetyQrLanding.jsx::HOLD_STATUSES` already covers `Maintenance Hold` with the "Under Repair / DO NOT USE" banner from Phase 4B.

## Non-negotiables verified
✅ No duplicate repair system.
✅ No duplicate hold system.
✅ No duplicate status system.
✅ No new transport / inspection systems.
✅ No MaintainX / Email / SMS / OCR / QR-PNG / reports / training expansion.
✅ Public Safety Tile untouched beyond Emergency Fix.
✅ Existing Shop / Dispatch / Equipment / Safety / Project workflows untouched (proven by 74/74 prior-phase regression).
