# Daily Report Compression Map

**Source schema:** `/app/frontend/src/lib/dailyReportSchema.js` · 87 LOC, 35 scalar fields + 7 array fields.
**Current UI:** `/app/frontend/src/pages/NewDailyReport.jsx` · 1,524 LOC.
**Goal:** Reduce simultaneous visible inputs from ~35 → ~12 without removing any field from the data model.

**Classification key:**
- **A · REQUIRED NOW** — must be visible and completed at first submit
- **B · REQUIRED LATER** — must be captured but can be progressively disclosed
- **C · CONDITIONAL** — only shown when operationally relevant
- **D · REDUNDANT** — duplicates existing data (candidates for default/inference)
- **E · LOW VALUE** — optional; can default to empty without breaking lifecycle

---

## Field-by-field matrix

### Report header (7 fields)
| Field | Class | Disposition | Rationale |
|---|---|---|---|
| `project_name` | A | Tier 1 visible · auto-fill from selected project_number | Required for governance/PDF |
| `project_number` | A | Tier 1 visible · default to `lastProject` (already done) | Required, governance-critical |
| `location` | A | Tier 1 visible · 1 line | Required for site context |
| `report_date` | A | Tier 1 visible · default to today (already done) | Required |
| `report_number` | A | Tier 1 visible · auto-fill from `/next-number` (already done) | Auto — operator never types |
| `prepared_by` | A | Tier 1 visible · default to logged-in user | Required, accountability |
| `superintendent` | A | Tier 1 visible · default to `prepared_by` | Required, accountability |

**Net Tier 1:** 4 visible inputs (project_number, location, prepared_by · plus auto-filled date+report_number+superintendent).

### GPS + Weather (4 fields)
| Field | Class | Disposition |
|---|---|---|
| `gps_lat`/`gps_lng`/`gps_accuracy` | A | Auto-captured · invisible to operator |
| `weather_summary` | B | Auto-fetched from GPS · displayed as read-only · operator can edit if needed |
| `weather_snapshots` | E | Tier 3 (rarely-edited intra-day weather array) |

**Net Tier 1:** 0 visible (all auto). Weather summary shown as a chip ("☀ Sunny, 82°F · tap to edit").

### General info / flags (10 fields)
| Field | Class | Disposition |
|---|---|---|
| `schedule_delays` (Yes/No) | A | Tier 1 visible · default "No" |
| `schedule_delays_notes` | C | Auto-expand only if `schedule_delays==Yes` |
| `weather_impact` (Yes/No) | A | Tier 1 visible · default "No" |
| `weather_impact_notes` | C | Auto-expand only if `weather_impact==Yes` |
| `safety_incidents_today` (Yes/No) | A | Tier 1 visible · default "No" — **critical accountability gate** |
| `injuries_reported` (Yes/No) | A | Tier 1 visible · default "No" — **critical accountability gate** |
| `incident_notes` | C | Auto-expand only if either incident flag == "Yes" |
| `safety_notified` (Yes/No) | C | Auto-expand only if either incident flag == "Yes" (already done in current UI) |
| `safety_contact_person` | C | Auto-expand only if `safety_notified==Yes` |
| `safety_contact_time` | C | Auto-expand only if `safety_notified==Yes` |
| `incident_report_filled` (Yes/No) | C | Auto-expand only if incident flag == "Yes" |
| `incident_report_time` | C | Auto-expand only if `incident_report_filled==Yes` |
| `general_notes` | B | Tier 2 — single textarea below Tier 1 |

**Net Tier 1:** 4 always-visible Yes/No toggles (schedule_delays, weather_impact, safety_incidents_today, injuries_reported). All notes auto-expand only when the toggle == Yes. The Safety Escalation block already exists exactly like this — preserve and extend.

### Repeating arrays — DEFER TO TIER 3 "More fields"
| Field | Class | Disposition |
|---|---|---|
| `masci_crews` | A | **Tier 1** — at least one crew row required. Auto-hours already wired. |
| `subcontractors` | E | Tier 3 ("More fields") |
| `visitors` | E | Tier 3 ("More fields") |
| `equipment` | E | Tier 3 ("More fields") |
| `materials` | E | Tier 3 ("More fields") |
| `activities` | E | Tier 3 ("More fields") |
| `distribution_list` | E | Tier 3 ("More fields") |

**Rationale:** MASCI crew is the operationally-critical labor record. Subs/visitors/equipment/materials/activities are filled by some PMs/supers but skipped by most for clean days. The current UI forces every operator to scroll past these empty arrays daily.

### Photos + Sign-off (3 fields)
| Field | Class | Disposition |
|---|---|---|
| `photos` (min 6) | A | Tier 1 visible · prominent uploader at top of "Photos" section |
| `prepared_by_signature` | A | Tier 1 visible · single signature pad |
| `superintendent_signature` | A | Tier 1 visible · single signature pad (can be skipped if `superintendent==prepared_by`) |

---

## Compressed initial submission path

```
┌─ Daily Report — DR-20260224-001 ──────────────────────────────────┐
│  Project: [project_number ▼]  Location: [_____________________]   │
│  Prepared by: [prepared_by ▼]                                     │
│                                                                    │
│  ☀ Sunny, 82°F  ·  GPS captured  ·  Draft saved 4s ago            │
│                                                                    │
│  Today flags                                                      │
│    Schedule delays? [No ▼]                                        │
│    Weather impact?  [No ▼]                                        │
│    Safety incident? [No ▼]                                        │
│    Injuries?        [No ▼]                                        │
│                                                                    │
│  Crew on site (tap + Add)                                         │
│    ┌─────────────────────────────────────────────┐                │
│    │ + Add crew member                            │                │
│    └─────────────────────────────────────────────┘                │
│                                                                    │
│  Photos (6 minimum)                                                │
│    [Upload]  [Take photo]  Progress: 0 / 6                        │
│                                                                    │
│  Sign                                                              │
│    [✍ Signature pad]                                              │
│                                                                    │
│  [ ▽ More fields (Subs · Visitors · Equipment · Materials · Activities) ]
│                                                                    │
│  [           SUBMIT — 12 fields complete           ]              │
└────────────────────────────────────────────────────────────────────┘
```

**Visible inputs at default state:** 12 (down from 35).
**Visible inputs if all toggles "No":** 12.
**Visible inputs if `safety_incidents_today==Yes`:** 16 (escalation block auto-opens).
**Visible inputs if user taps "More fields":** all 35.

---

## Conditional logic map (preserve and extend existing)

```
schedule_delays == "Yes"          → show schedule_delays_notes
weather_impact == "Yes"           → show weather_impact_notes
safety_incidents_today == "Yes"
  OR injuries_reported == "Yes"   → require + show incident_notes,
                                    safety_notified, incident_report_filled
safety_notified == "Yes"          → require safety_contact_person, safety_contact_time
incident_report_filled == "Yes"   → require incident_report_time
masci_crews.length == 0           → block submit ("at least 1 crew member required")
photos.length < photo_min (6)     → block submit ("6 photos required")
```

**Note:** The Safety Escalation conditional is **already implemented** in the current UI (lines 884–1020 of `NewDailyReport.jsx`). Compression only requires applying the same conditional pattern to schedule_delays + weather_impact.

---

## Mobile-first field ordering

Order matters on a phone. Top = highest information density per cm of screen.

1. Project + report_number chip (always)
2. Location
3. Prepared by + superintendent (auto-defaulted, expand on tap)
4. Weather chip + GPS indicator (read-only, no scroll cost)
5. **4 Yes/No flags** (single thumb taps)
6. Crew quick-add
7. Photos progress + Upload
8. Signature
9. Submit button
10. (Tier 3 disclosure at bottom — most users never scroll this far)

---

## Estimated click + time reduction

| Metric | Current | Compressed | Δ |
|---|---|---|---|
| Visible inputs at first render | 35 | 12 | −66% |
| Taps to complete clean-day report | ~25 | ~9 | −64% |
| Estimated completion time | 4–6 min | 60–90s | −70% |
| Scroll depth (phone) | ~5 screen-heights | ~1.5 screen-heights | −70% |

**Caveat:** these are estimates based on the static schema. Actual field-shadow data should validate before any code lands.

---

## Implementation footprint

**Files touched:** 1 (`NewDailyReport.jsx`)
**Backend touched:** 0
**LOC added/changed:** ~80 (mostly CSS state + a `useState` for `showMore`)
**Risk:** LOW. All schema preserved. All conditional logic already exists in pattern. All submission paths unchanged.
**Rollback:** Single CSS flag (`showMore=true` default) restores current behavior.

---

## What this map explicitly preserves

- ✅ All 35 fields + 7 arrays in `buildDailyReportDefaults()` remain in the model
- ✅ Autosave / draft recovery (`useDraftSync`) untouched
- ✅ Auto-hours per crew member untouched
- ✅ Auto report-number sequencing untouched
- ✅ GPS + weather auto-fetch untouched
- ✅ Idempotency key untouched
- ✅ Backend validation untouched
- ✅ Distribution list / PDF generation untouched
- ✅ Photo minimum (6) gate untouched
- ✅ Signature requirements untouched
- ✅ Lifecycle/fan-out triggers untouched

**Compression = visual & sequencing only. Data fidelity = 100%.**
