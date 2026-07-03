# TRACK 19.61 · Human Walkthrough — Asset Thread

Concrete moment-by-moment walkthroughs of nine personas opening the
Asset Thread. Each answers: **what did I gain that I did not have
before?**

---

## 1 · Shop Manager — a broken excavator

**Before:** Opens `/shop/hub_v2`, scrolls the asset queue, clicks the
unit, lands on `/shop/units/<unit>/history`, and pieces together
defects, PM schedule, and inspection failures across three pages.

**After:** Deep-links from Shop Hub → `/admin/assets/EXC-217/thread`.
One page. Section 1 shows the unit is a Cat 336F in the Denver yard,
retired: false. Section 2 lists two attention items — an open OOS from
today and the pending "Calibration certificate · asset lane" upload.
Section 4 is the full 13.26 backbone timeline. Section 5 lets him hop
to the Historical Records queue and to the fleet lens with one click.

**Gain:** All questions answered without switching pages.

---

## 2 · Fleet Manager — DVIR failure this morning

**Before:** Opens `FleetVisibility.jsx`, spots the red chip, clicks the
unit, sees a stub page.

**After:** Same deep-link — but now `/fleet/unit/…` is aliased to the
same shell. Health = "Critical" with explanation "Currently out of
service. Recent inspection failure." Action queue lists **exactly**
"Clear the OOS state (repair + manager review + RTS)."

**Gain:** Same shell used by the Shop Manager — one conversation.

---

## 3 · Dispatcher — is the roll-off truck available for the 6am job?

**Before:** Bounces between `dispatch-portal/fleet`,
`EquipmentDashboard`, and the driver directory.

**After:** Types the unit number into the Asset Thread route (resolver
accepts unit_number, VIN, or serial). Section 1 shows status =
"active", no OOS event on the timeline in the last 30 days. Section 2
attention is empty.

**Gain:** Yes/no in under three seconds.

---

## 4 · Superintendent — where did my pipe laser go?

**Before:** No easy answer. Pipe lasers are not on `FleetVisibility`
because they don't have a `unit_number` in the fleet sense.

**After:** Opens `/admin/assets/PL-004/thread` (serial). Resolver maps
PL-004 → canonical asset_id. Mission shows "Pipe Laser · Survey
Equipment · assigned to Superintendent Chris · at Site 12". Section 5
(Relationships) links to the "asset acknowledgement" record from the
issuance flow. Timeline shows the transfer event.

**Gain:** The full asset universe — not just trucks — has a thread.

---

## 5 · Safety Officer — is this laser calibrated?

**Before:** Guesses. There is no place for a calibration certificate to
live because Historical Records did not have an asset lane.

**After:** Section 6 (Documents) shows every linked historical
document. The `calibration_certificate` slug is present in the Track
19.61 catalog. If the record is `pending_approval`, it appears in
Section 2 (Attention) as "1 asset document awaiting HR/Admin
approval".

**Gain:** A place for legacy paper to live and be surfaced.

---

## 6 · PM (project manager) — what equipment is on my project?

**Before:** Reads yesterday's daily report.

**After:** From `/pm/command-center`, clicks the asset in the project
thread's Relationship section → deep-links to Asset Thread. Sees
mission, timeline, and open defects for that asset. Understands
whether tomorrow's schedule is at risk.

**Gain:** One-click hop from Project Thread → Asset Thread.

---

## 7 · HR / Admin — I have a pile of purchase agreements to file

**Before:** No lane for asset-native paper. Warranty cards ended up in
random shared drives.

**After:** Historical Records intake now accepts
`entity_kind=asset&asset_id=<id>` and creates records in the same
`employee_records` collection under the `asset` lane with the new
record_type slugs (`warranty`, `purchase_agreement`,
`title_registration`, `insurance_policy`, `calibration_certificate`,
`operator_manual`, `spec_sheet`, `bill_of_sale`, `historical_
inspection_report`, `historical_maintenance_record`, `asset_photo`,
`other_asset_document`). Approval flow reuses the existing queue.

**Gain:** Legacy paper has a home. Zero new tables.

---

## 8 · Executive — how is my equipment portfolio doing?

**Before:** Reads the weekly digest email.

**After:** Opens any asset thread. Section 8 (OI) shows the class-
routed OI product (`fleet_intelligence` for trucks/heavy;
`shop_intelligence` for survey/tech). No thread page ever sends email,
so opening threads produces zero inbox activity — even under
audit.

**Gain:** Deeper drill-down without touching digest workflows.

---

## 9 · Field Mechanic (Shop) — did I already start on this?

**Before:** Checks Shop Manager Queue and hopes.

**After:** Opens the thread → Section 4 timeline shows every event
he's touched (mechanic assignments, repair start/complete) in order,
newest first. Section 5 links to the WO.

**Gain:** No lost context between shifts.

---

## What every persona has in common

- The **same 10 sections in the same order**.
- The **same attention language** (max 5, CRITICAL / HIGH / MEDIUM).
- The **same relationship graph primitive**.
- The **same guidance card** (or an honest empty state when no OI
  product applies).
- **No emails triggered by opening a thread. Ever.**
