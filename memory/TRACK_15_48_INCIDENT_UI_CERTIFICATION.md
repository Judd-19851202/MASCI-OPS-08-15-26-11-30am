# TRACK 15.48 · Incident UI Certification (Phase 1)

**Status:** ✅ CERTIFIED · live-verified at three viewports.

The Track 15.47 audit identified that the backend accepted every G1-G5 / G7 field via `model_config = ConfigDict(extra="allow")`, but the form UI had been left as a follow-up. 15.48 Phase 1 closed that gap.

## Live render evidence
| Test ID | Desktop 1920x800 | iPad portrait 768x1024 | iPad landscape 1024x768 |
|---|:---:|:---:|:---:|
| `incident-classifications-grid` | ✅ | ✅ | ✅ |
| `incident-classification-workplace-violence` (14 total chips) | ✅ | ✅ | ✅ |
| `incident-flag-threat_made` (G2 · 7 boolean toggles) | ✅ | ✅ | ✅ |
| `incident-flag-police_called` (G3 entry toggle) | ✅ | ✅ | ✅ |
| `incident-police-agency` (G3 · conditional reveal) | ✅ | ✅ | ✅ |
| `incident-police-officer` | ✅ | ✅ | ✅ |
| `incident-police-badge` | ✅ | ✅ | ✅ |
| `incident-police-case` | ✅ | ✅ | ✅ |
| `incident-police-report-number` | ✅ | ✅ | ✅ |
| `incident-damage-value` (G5) | ✅ | ✅ | ✅ |
| `incident-vehicle-plate` (G5) | ✅ | ✅ | ✅ |
| `incident-vehicle-vin` (G5) | ✅ | ✅ | ✅ |
| `incident-insurance-claim` (G5) | ✅ | ✅ | ✅ |
| `witness-phone-N` · `witness-email-N` · `witness-employer-N` · `witness-role-N` · `witness-type-N` (G4) | ✅ | ✅ | ✅ |

Screenshots: `/tmp/15_48_incident_desktop.png`, `/tmp/15_48_incident_ipad_portrait.png`, `/tmp/15_48_incident_ipad_landscape.png`.

## Per-G certification

### G1 · Multi-select Classifications
- ✅ Visible — Section 02B "Defensibility Classifications · Track 15.47" always renders.
- ✅ Editable — 14 chip buttons. Click toggles inclusion. Active chip renders red border + check mark.
- ✅ Saved — array sent in POST body. Verified on live POST: `classifications: ["Workplace Violence"]` round-trips.
- ✅ Retrieved — GET returns the array unchanged.
- ✅ PDF — appears in the details key-value dump on the rendered PDF.

### G2 · Threat & Contact
- ✅ Visible — 7 checkboxes (Threat made / Physical contact / Physical assault / Weapon displayed / Weapon used / Encounter filmed / Posted to social media).
- ✅ Editable — Shadcn Checkbox component, click handler set via `set()`.
- ✅ Saved — boolean payload persisted.
- ✅ Retrieved — same.
- ✅ PDF — each flag renders as a key-value pair.
- ✅ Conditional textarea — when `threat_made` is checked, the verbatim-quote field appears. Same for `weapon_displayed` / `weapon_used` → weapon description.

### G3 · Police Involvement
- ✅ Visible — 4 boolean flags (Police called / arrived / Arrest made / Citation issued).
- ✅ Conditional reveal — when `police_called` is checked, 5 detail fields appear: Agency, Officer, Badge, Case #, Report # + `police_report_obtained` checkbox.
- ✅ Editable, Saved, Retrieved, PDF — all paths verified.

### G4 · Witness sub-doc (extended in 15.47, re-verified in 15.48)
- ✅ Each witness row now captures: Name (EmployeeCombo) + Role (text) + Witness Type (select) + Phone + Email + Employer + Statement + Signature placeholder.
- ✅ Saved as `witnesses[]` array with all keys.
- ✅ PDF renders multi-column witness table with all 5 columns (Name · Role/Phone/Email · Employer · Statement · Signature).

### G5 · Damage & Claim
- ✅ Visible — "Damage / Vehicle / Claim" sub-section.
- ✅ Fields: Damage description (textarea) · Estimated value · Vehicle make/model · VIN · License plate · MASCI asset # · Insurance carrier · Insurance claim #.
- ✅ Editable, Saved, Retrieved, PDF — all paths verified.

## Layout
- Desktop · 3-col chip grid + 2-col field grids
- iPad portrait · 2-col chip grid + 1-col field stacks
- iPad landscape · 3-col chip grid (intermediate breakpoint)

## Operator effort vs. backend acceptance
Pre-15.48: backend accepted everything, form captured 1 (witness fields) of the 4 missing G groups (G1/G2/G3/G5).
Post-15.48: form captures all 4. Operator no longer needs API access or developer help.

## Sign-off
Phase 1 GREEN. Every Track 15.47 field is visible, editable, saved, retrieved, and renders on the PDF. iPad portrait + landscape pass without horizontal scroll.
