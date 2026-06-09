# Motive Day-1 Production Activation Runbook

**Purpose:** Bring a fresh production environment from "Motive is on but nothing is verified" → "Trust Score > 50% and rising" inside one working session.

**Pre-requisites:**
- Operator has admin credentials.
- Motive webhook receiver is mounted (M-1 certification) and at least one day of events has flowed into `motive_events`.

---

## STEP 1 · Run geofence reconciliation

```
POST /api/admin/locations/import-geofences
POST /api/admin/locations/reconcile
```

Or open `/admin/geofence-reconciliation` and click **Import Geofences** → **Run Reconciliation**.

**Expected:** 67-ish proposals across HIGH / MEDIUM / LOW bands.

## STEP 2 · Approve HIGH-confidence project matches

In `/admin/geofence-reconciliation`:
- Filter to **HIGH** band.
- Click **Bulk Approve** (HIGH-only is enforced server-side).
- Spot-check 2–3 rows for sanity, then approve.

**Expected:** ~10–18 JOB geofences move from `Matched` → `Verified`.

## STEP 3 · Verify The Shop

The Shop is auto-categorized as `SHOP` on import. Open `/admin/geofence-reconciliation` → filter `status=Imported` → find The Shop → operator manually verifies via a Reassign action (use The Shop's MASCI shop-record identifier as the "project" placeholder if your schema requires one, or simply Approve when the SHOP reconciliation tool ships).

## STEP 4 · Verify primary Yard

Same as Step 3 for the canonical Yard geofence (category `Terminal / Yard` → `YARD`).

## STEP 5 · Verify Asphalt Plant geofences

Repeat for each plant.

## STEP 6 · Run asset mapping scan

```
POST /api/admin/asset-mapping/scan
```

Or open `/admin/asset-mapping` and click **Run Scan**.

**Expected:** A proposal row per distinct `dispatch.truck_id`, scored against the 190+ Motive `asset_mappings` rows using 7 priority signals (Exact MASCI ID / Unit / Truck / Equipment / VIN / Serial / Fuzzy).

## STEP 7 · Approve HIGH-confidence mappings

In `/admin/asset-mapping`:
- Review the **Top 10 unmapped** table (sorted by active-dispatch volume — highest ROI first).
- For HIGH-band proposals, click **Bulk Approve HIGH**.
- For MEDIUM rows, eyeball one-by-one.

**Expected:** Mapping coverage % rises from 0 → 50%+ in one click.

## STEP 8 · Re-run VER-1 audit

```
GET /api/admin/verification/audit
```

Or open `/admin/verification` (if surfaced) — observe Q1 (verified assignments) rise materially.

## STEP 9 · Capture Trust Score baseline

```
GET /api/admin/executive-summary
```

Record:
- `trust_score_pct` (today)
- `potential_trust_score_pct` (ceiling)
- `coverage_pct`
- `projects_verified` count

## STEP 10 · Document baseline

Paste the executive-summary JSON into the operator's daily ops log. The next-day Trust Score should rise materially as field telemetry catches up with the newly-Verified geofences and newly-Mapped assets.

---

## Rollback

Every step in this runbook is **reversible** by clicking **Reject** in the corresponding queue — no rollback script needed. Approvals do not push to Motive; they only flip a `geocode_status` / `masci_equipment_id` value in MASCI-owned collections.

## Success looks like

After one session, the operator should see:
- `coverage_pct` ≥ 50%
- `trust_score_pct` > 0% (rising)
- `q9_highest_risk_gaps` listing real trucks (not test sentinels)
