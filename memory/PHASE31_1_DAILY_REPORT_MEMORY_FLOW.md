# PHASE 31.1 · Daily Report Memory Flow

_iter437 · 2026-05-25_

```
┌─────────────────────────────────────────────────────────────────────┐
│  DAY 1 · Monday · Mike on his personal iPhone                       │
│  ─────────────────────────────────────────                          │
│  1. Opens /daily/submit                                             │
│  2. No saved setup → no prompt → blank form                         │
│  3. Fills project, crew, subs, equipment, weather, notes, photos    │
│  4. Submits successfully                                            │
│  5. saveCrewSetup(payload) → strips banned fields →                 │
│     persists ONLY: project_name/_number, prepared_by, superintendent│
│     masci_crews[name,trade], subcontractors[company,trade,foreman], │
│     equipment[description], schemaVersion=1, savedAt=NOW             │
│                                                                     │
│  localStorage key: masci.crew-memory.daily-report.v1                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DAY 2 · Tuesday · Mike on the SAME iPhone                          │
│  ──────────────────────────────────────                             │
│  1. Opens /daily/submit                                             │
│  2. loadCrewSetup() returns Monday's record                         │
│     (schemaVersion=1 · savedAt within 30 days → valid)              │
│  3. <CrewSetupRestorePrompt /> renders ABOVE the form               │
│                                                                     │
│      ┌─────────────────────────────────────────────────────┐        │
│      │ 📜 Use yesterday's crew and equipment setup         │        │
│      │    from this device?                                │        │
│      │    Saved setups stay only on this device.           │        │
│      │    Use this option only if this is your crew        │        │
│      │    device or personal device.                       │        │
│      │                                                     │        │
│      │    [✏ PAVING CREW A]   SAVED YESTERDAY              │        │
│      │    Oxford Resurfacing 2026 · 3 crew members ·       │        │
│      │    1 subcontractor · 2 equipment items              │        │
│      │                                                     │        │
│      │    [↺ Use Setup]   [📄 Start Blank]   [🗑 Clear]    │        │
│      │                                                     │        │
│      │    You can edit crew and equipment after loading.   │        │
│      │    Starting blank will not erase previously         │        │
│      │    submitted reports.                               │        │
│      └─────────────────────────────────────────────────────┘        │
│                                                                     │
│  4. Mike taps [Use Setup]                                           │
│  5. applySetupSnapshotToData(data, snap) → returns merged data:     │
│        ▸ project_name / _number  ← from snapshot                    │
│        ▸ prepared_by / superintendent  ← from snapshot              │
│        ▸ masci_crews  ← 3 rows pre-filled · times/hours BLANK       │
│        ▸ subcontractors  ← 1 row pre-filled · count/hours BLANK     │
│        ▸ equipment  ← 2 rows pre-filled · times/hours BLANK         │
│        ▸ EVERYTHING ELSE  ← preserved from today's blank state      │
│           (today's report_date, weather=empty, notes=empty,         │
│            photos=[], incidents=No, signatures=empty)               │
│  6. Prompt disappears · toast: "Crew setup loaded · edit anything"  │
│  7. Mike updates today's hours, work performed, weather, notes,     │
│     takes photos, signs, submits                                    │
│  8. saveCrewSetup(today's payload) → snapshot refreshed             │
│     (savedAt=NOW · lastUsedAt=NOW)                                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DAY 2 · Tuesday afternoon · Steven grabs Mike's iPad in the trailer│
│  ──────────────────────────────────────────────────────────────     │
│  1. Opens /daily/submit                                             │
│  2. loadCrewSetup() returns Mike's record                           │
│  3. Prompt shows "PAVING CREW A · SAVED YESTERDAY · Oxford..."      │
│  4. Steven recognizes this is Mike's setup → taps [Start Blank]     │
│  5. Prompt disappears · NO fields touched · Mike's setup PRESERVED  │
│     (so Mike sees the same prompt next time he opens the form)      │
│  6. Steven fills a blank report for his own project                 │
│  7. On submit, saveCrewSetup(steven's payload) OVERWRITES Mike's    │
│     setup (one slot per device · Phase 31.1 doctrine: "yesterday's  │
│     setup" implies singular)                                        │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DAY 31 · After 30 days of no opens                                 │
│  ──────────────────────────────────                                 │
│  1. Anyone opens /daily/submit                                      │
│  2. loadCrewSetup() finds the record but savedAt > 30d ago          │
│  3. clearCrewSetup() runs silently                                  │
│  4. Returns null · no prompt rendered · form is blank               │
└─────────────────────────────────────────────────────────────────────┘
```

## State machine summary

| Trigger | Effect |
|---------|--------|
| Form mounts · saved record present + fresh | Render prompt |
| Form mounts · no record OR expired | No prompt · blank form |
| User clicks **Use Setup** | Apply snapshot · clear prompt · bump `lastUsedAt` |
| User clicks **Start Blank** | Clear prompt · record UNTOUCHED |
| User clicks **Clear Saved Setup** | Delete record · clear prompt · toast |
| User clicks pencil on nickname chip | Inline input · Check button persists |
| Successful submission (or queued offline) | `saveCrewSetup(payload)` overwrites with fresh snapshot |
| 30 days elapse without a save | Next load auto-clears the record |
| Schema version mismatch | Auto-clear · operator sees blank form |

## Field-by-field merge contract

| Form field | Source after Use Setup |
|------------|------------------------|
| `report_date` | TODAY (snapshot value ignored — we never persist date) |
| `report_number` | TODAY (auto-fetched · snapshot ignored) |
| `project_name` | snapshot (preserves prior typing if snapshot empty) |
| `project_number` | snapshot (preserves prior typing if snapshot empty) |
| `location` | unchanged (operator captures GPS today) |
| `prepared_by` | snapshot |
| `superintendent` | snapshot |
| `weather_*` | unchanged (today's weather) |
| `gps_*` | unchanged (today's GPS) |
| `safety_*` / incidents | unchanged (today's truth) |
| `general_notes` | unchanged |
| `masci_crews` | snapshot rows · times/hours BLANK |
| `subcontractors` | snapshot rows · count/hours BLANK |
| `equipment` | snapshot rows · hours/times BLANK |
| `materials` | unchanged |
| `activities` | unchanged |
| `visitors` | unchanged |
| `photos` | unchanged |
| `prepared_by_signature` | unchanged |
| `superintendent_signature` | unchanged |
| `distribution_list` | unchanged |
| `schedule_delays*` | unchanged |
