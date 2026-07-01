# Track 19.06 · Daily Report UI Change Map

## Files touched

| File | Change |
| --- | --- |
| `frontend/src/pages/NewDailyReport.jsx` | Added `_PresenceGate` inline component + `presence` state + 8 Yes/No gates + 10 band labels + Tomorrow/Follow-Up section |

## Additions (UI-only)

### New inline component
```
function _PresenceGate({ label, gateKey, presence, setPresence,
                        testIdBase, hasData, children, t })
```
* Yes-state: renders children (existing CollapseCard/Section).
* No-state: renders a "No — skipped" pill with Change button.
* Unanswered: renders the Yes/No prompt.

### New state
```
const [presence, setPresence] = useState({
  crews: null, subs: null, visitors: null, equipment: null,
  materials_in: null, materials_out: null, delays: null, safety: null,
});
```
* Auto-flips to `"yes"` when the corresponding data array/flag is populated (never flips to `"no"` automatically).

### New Yes/No prompts (operator-facing)

1. `Did MASCI employees work on site today?` → gate `crews`
2. `Were subcontractors on site today?` → gate `subs`
3. `Were visitors or inspectors on site today?` → gate `visitors`
4. `Was MASCI equipment on site or used today?` → gate `equipment`
5. `Were materials delivered or imported today?` → gate `materials_in`
6. `Were materials exported or hauled off today?` → gate `materials_out`
7. `Did anything delay, change, or impact production today?` → gate `delays`
8. `Any safety incidents, injuries, accidents, utility hits, near misses, or inspections today?` → banner over existing safety Yes/No pickers

### New band labels (guiding banners)

1. `Job Setup`
2. `People on Site`
3. `Equipment & Resources`
4. `Materials / Import / Export`
5. `Work Performed & Production`
6. `Delays / Constraints / Extra Work`
7. `Safety / Incidents / Inspections`
8. `Photos & Attachments · Required Evidence`
9. `Tomorrow / Follow-Up`
10. `Sign-Off / Submit`

### New testids

| Prefix | Purpose |
| --- | --- |
| `band-{name}` | Band labels (10 total) |
| `presence-{key}-prompt` | Unanswered Yes/No card |
| `presence-{key}-yes` | Yes button |
| `presence-{key}-no` | No button |
| `presence-{key}-yes-block` | Rendered section when Yes |
| `presence-{key}-no-block` | Skipped pill when No |
| `presence-{key}-change` | Change button on Yes/No states |
| `input-tomorrow-plan` | Tomorrow / Follow-Up textarea |

### New section

**Tomorrow / Follow-Up** — writes to `data.narrative_sections.tomorrow_plan` (existing Track 15.62 additive schema field, already documented in the Track 19.05 data model map).

## Removals

**Zero removals.** Every field, every button, every testid documented in Track 19.05 remains in place.

## Preserved doctrine

| Doctrine | Verification |
| --- | --- |
| Track 19.03 HR roster canonical source | `EmployeeCombo.jsx` unchanged; `fetchHrRoster` + `subscribeHrRoster` still consumed |
| Track 19.04 actor-scoped autosave | `useFormDraft` unchanged; `savedByActor` still stamped |
| Track 19.04 explicit Smart Prefill offer | `smartPrefillOffer` state + offer chip unchanged |
| Track 19.04 unified attachments | `AttachmentUpload` unchanged; `attachments[]` still submitted |
| Track 19.05 schema protection | Every persisted schema key present (verified by test_no_schema_keys_removed_or_renamed) |
| Excavation hard gate | Backend 422 `excavation_record_required` unchanged |
| 6-photo minimum | `photo_min: 6` in `dailyReportSchema.js` unchanged |
| Historical immutability | DELETE endpoint 410 unchanged |
| Trust-spine correlation | `workflow="daily-report"` unchanged |

## Line-count Δ

* `NewDailyReport.jsx`: +~300 lines net (band labels + PresenceGate wrappers + Tomorrow section + inline component).
* No files deleted.

## Redesign is UI-only

The Track 19.06 redesign is a UI reorganization. The persisted Daily Report document produced by the redesigned flow is byte-identical to a document produced by the pre-19.06 flow (with the same operator answers). Any submitted DR remains valid, viewable, exportable, emailable, and PDF-renderable.
