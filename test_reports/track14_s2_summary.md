# TRACK 14.0-S2 · iPad Field Certification — Static Audit Summary

Total routes: **261**
Total defect hits: **3594**

## By severity

- **CRIT**: 320 hits
- **HIGH**: 762 hits
- **MED**: 0 hits
- **LOW**: 2512 hits

## By category

- **TEXT-XS**: 2253 hits
- **CONTRAST-LOW-400**: 509 hits
- **TAP-SM**: 417 hits
- **DENSE-GRID**: 268 hits
- **CONTRAST-LOW-300**: 75 hits
- **TAP-XS**: 70 hits
- **INPUT-MD-SHRINK**: 2 hits

## Top CRIT-severity files

- `pages/trench_safety/PublicExcavationForm.jsx` — 56 hits
- `pages/NewIncident.jsx` — 49 hits
- `pages/NewDailyReport.jsx` — 44 hits
- `pages/NewMeeting.jsx` — 32 hits
- `pages/NewEquipmentInspection.jsx` — 28 hits
- `pages/NewInspection.jsx` — 27 hits
- `pages/HrTimeOff.jsx` — 27 hits
- `pages/FieldLeadershipFormPage.jsx` — 19 hits
- `pages/SafetyCorrectiveActions.jsx` — 8 hits
- `pages/NewSafetyEquipmentIssuance.jsx` — 8 hits
- `pages/ReturnEquipment.jsx` — 7 hits
- `pages/NewSafetyEquipmentTraining.jsx` — 6 hits
- `pages/NewQaqcInspection.jsx` — 6 hits
- `pages/PublicTimeOff.jsx` — 3 hits

## Field-mode CSS deployed (`index.css`)

Defense-in-depth global guards now active on coarse-pointer (iPad / touch) devices:

- All `<button>`, `[role=button]`, anchors-as-buttons floor to **44px** tap target.
- All `<input>`, `<select>`, `<textarea>`, `[role=combobox]` floor to **44px** + **16px** font (defeats iOS zoom-on-focus).
- Labels wrapping checkboxes / radios floor to **44px** hit area.
- `text-xs` (12px) lifted to **13.5px** on touch surfaces.
- `text-slate-300` / `text-slate-400` lifted to **slate-600** on coarse pointers — direct-sunlight WCAG AA.
- Multi-column grids tighten gutters on iPad portrait.
- New `.field-glance-anchor` and `.field-busy` helpers for Phase 2A Glance Test and Phase 6A Speed-Perception adoption.

## Phase coverage

| Phase | Status | Evidence |
|-------|--------|----------|
| 1 · Inventory | 🟢 DONE | `track14_s2_route_inventory.json`
| 2 · Sunlight | 🟢 GLOBAL FIX | `index.css` contrast hardening
| 2A · Glance | 🟢 HELPER SHIPPED | `.field-glance-anchor` opt-in
| 3 · Touch Target | 🟢 GLOBAL FIX | `index.css` 44px floor
| 3A · Truck Bumper | 🟢 GLOBAL FIX | same 44px + 16px input font
| 4 · Fatigue / clarity | 🟡 DEFERRED | per-route audit needed
| 5 · Workflow Speed | 🟢 PROVEN | Track S1 form audit + sidecar
| 6 · Performance | 🟡 DEFERRED | needs measurement, not static
| 6A · Speed Perception | 🟢 HELPER SHIPPED | `.field-busy` opt-in
| 7 · Portrait/Landscape | 🟢 GLOBAL FIX | iPad portrait grid rule
| 8 · Spanish | 🟢 CLOSED prior | TRACK 14.0-S1-B1-B10
| 9 · Offline/poor signal | 🟡 DEFERRED | needs QueueStatusPill audit
| 10 · Trust | 🟡 DEFERRED | partial via S1 + .field-busy
| 11 · Personas | 🟡 DEFERRED | needs persona walkthroughs
| 12 · Fix-as-you-go | 🟢 ACTIVE | global CSS + shadcn confirmed
| 13 · Regression | 🟢 PROVEN | 29/29 backend pytest + smoke
