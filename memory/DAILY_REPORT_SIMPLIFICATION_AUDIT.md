# DAILY REPORT SIMPLIFICATION AUDIT

**OMEGA Stop Order Acknowledged · 2026-02-07**

This audit is in response to the OMEGA Stop Order. No code has been implemented since the stop. Two files were created earlier in the Phase 10D.2 sprint and are NOT yet wired:
- `/app/frontend/src/components/dailyreport/DayActivityTriggers.jsx` (created, not imported)
- `/app/frontend/src/lib/dailyReportCompliance.js` (extended with `photoCategories` + `sections` — the *exact* over-engineering this directive is correcting)

Both can be removed or rewritten depending on how you want this sprint to resolve. Recommendation: rewrite both per the simplified blueprint in Section 7 below.

---

## OWN-DRIFT ADMISSION

I drifted into developer thinking. Phase 10D added two new components (`DailyReportStatusCard` + `PreviousReportSuggestions`) and a pure engine. The status card was useful as a one-line health indicator but I subsequently extended it with paragraph-level explanations ("Owners and the GC look at location for context."), severity tags ("4 ACTION · 2 REVIEW"), and counts. That is duplication. A 5:30 AM foreman doesn't read paragraphs. He reads a single line: **"3 things left."**

The Phase 10D.2 in-flight work was about to make this worse — per-photo-category requirement chips would have added 6–11 more cards to the status panel.

This audit reverses that direction.

---

## 1 · Everything currently creating complexity

| Source                                                           | Why it adds complexity                                                                                   |
|------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| `DailyReportStatusCard.jsx` — current "paragraph-per-requirement" body | Reads like a second form. Each chip has Title + Why + Action. The foreman re-reads what he already sees in the form. |
| `DailyReportExcavationActivity.jsx` — verbose "Coaching, not punishment" sub-banner | Permanent wall of coaching text where a YES/NO + 2 buttons would do.                                       |
| Existing Section 03 (General Information)                        | 6+ paragraphs of "yes/no" toggles with helper text. Most foremen swipe past them. The triggers should drive section visibility instead. |
| Pre-existing CollapseCard "status badge" wording                 | "Optional" · "No subs today" · "3 entered" — useful but lives next to the Status Card and the form headers. Triple-display. |
| 14 photo coaching paragraphs in Section "Photos"                 | A single chip "Need N photos of …" beats six paragraphs of OSHA-style explanation.                       |
| `OshaCoachingBlock` × 8 on the Excavation form                   | Collapsed by default — but a permanent visual presence on the page. Most blocks could disappear entirely unless a risky selection triggers them. |
| Stop-Work + Coaching banners at the top of every public form     | One-line message is enough. Two giant strips above every form is two strips too many. |

---

## 2 · Everything duplicated

| Concept                       | Duplicated locations                                                                            |
|-------------------------------|-------------------------------------------------------------------------------------------------|
| "Project Selected" indicator  | (a) JobPicker chip · (b) Status Card "PROJECT NOT SELECTED" requirement · (c) Section 01 header. |
| "Crew on report" indicator    | (a) Section 04 row count · (b) CollapseCard status badge · (c) Status Card requirement chip.    |
| "Photos missing" indicator    | (a) Section 09 "X/6 photos" badge · (b) Status Card requirement · (c) submit button label "NEED 4 MORE PHOTO(S)". |
| "Signature missing" indicator | (a) Section 11 empty-signature placeholder · (b) Status Card · (c) submit button label.         |
| "Excavation activity"         | (a) Section 03 YES/NO · (b) Status Card requirement · (c) `LinkedExcavationCompliance` cards.   |
| "Weather impact"              | (a) Section 03 YES/NO · (b) Section 02 weather widget · (c) Status Card "weather row" requirement. |
| "Save status"                 | (a) Header chip "SAVED JUST NOW" · (b) Restore card "You have unsaved work from earlier" · (c) Discard/Restore buttons. |

The fix: each concept should appear **once** on the screen — at the point of action.

---

## 3 · Decisions the platform could make, not the foreman

| Decision the foreman makes today                                | Source the platform already owns                                                                |
|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| "Was depth ≥ 4 ft?"                                             | Numeric `depth_ft`. (Already auto-derived in Phase 10C — apply same pattern to DR.)             |
| "Did I add 6 photos?"                                            | `photos.length`. Show the counter. Don't ask.                                                   |
| "Was Safety notified?"                                           | If `safety_incidents_today === "Yes"` AND there is an incident report linked, infer Yes.        |
| "Project Number / Customer / PM / Superintendent"                | `jobs_master` (already pulled by JobPicker — should populate ALL these fields, not just project).|
| "Crew / Equipment for this job"                                  | Previous Daily Report for same project_number. (Phase 10D suggestion exists — make it auto-apply silently on first job-select, with one-tap "Yesterday" already covered.) |
| "Weather"                                                        | GPS + weather API (already wired in `Section 02 weather widget`).                                |
| "Date of work"                                                   | `Date.now()` — already defaulted.                                                                |
| "Report number"                                                  | Backend auto-increment (already auto-fetched).                                                   |
| "Prepared by"                                                    | Last foreman who submitted on this project — should be the default.                              |
| "Superintendent"                                                 | `jobs_master.superintendent` for the chosen job.                                                 |
| "Foreman / Leadman / CP roles on a sub list"                     | `employees.role` — already in roster, currently filtered by role in EmployeePicker.              |

Total foreman decisions that disappear if the platform thinks first: **roughly 11 out of 14 default-visible decisions on a happy-path Daily Report.**

---

## 4 · Things foremen type today that the platform already knows

| Currently typed                                  | Should be auto-filled from                                          |
|--------------------------------------------------|---------------------------------------------------------------------|
| Project Name                                     | JobPicker → `jobs_master.project_name`                              |
| Project Number                                   | `jobs_master.project_number`                                        |
| Customer                                         | `jobs_master.client`                                                |
| PM Name                                          | `jobs_master.project_manager`                                       |
| Superintendent                                   | `jobs_master.superintendent` (currently NOT pulled — gap)           |
| Location                                         | `jobs_master.location` + GPS reverse-geocode                        |
| Crew roster                                      | Previous Daily Report (same project_number)                          |
| Equipment list                                   | Previous Daily Report (same project_number)                          |
| Foreman / Prepared By                            | Last submitter on this project (`daily_reports.prepared_by` MAX by date) |
| Phone / contact                                  | `employees.phone` for the selected foreman                          |
| Activity / work-performed                        | Previous Daily Report (offer "Copy + edit" — already in Phase 10D)   |
| Subs (recurring) — Sun Belt Rentals, etc.        | Previous Daily Report                                               |
| Weather                                          | weather API + GPS                                                   |

Phase 10D wired one of these (`Previous Daily Report Suggestions` for crew/equipment/activity) but it requires a tap. The directive says: **auto-apply silently, then let the foreman override**.

---

## 5 · Sections that should be hidden until triggered

Current default-visible section count on a fresh Daily Report: **11 sections** (`01 Report Info`, `02 Weather`, `03 General Information`, `04 MASCI Crews`, `05 Subs`, `06 Visitors`, `07 Equipment`, `08 Deliveries`, `09 Activity/Production`, `10 Delays/Extra Work`, `11 Sign-Off`).

After "platform thinks first" simplification:

| Section                            | Should default to                                                              |
|------------------------------------|--------------------------------------------------------------------------------|
| 01 Report Info (Job, Date, #)     | **Visible** — but auto-filled. Foreman only confirms.                          |
| 02 Weather                         | **Visible** — but auto-filled from GPS+API. Foreman only confirms.             |
| 03 General Information (triggers)  | **Replaced** by the single "What happened today?" checkbox row.                |
| 04 MASCI Crews                     | **Visible** — pre-populated with yesterday's crew.                             |
| 05 Subs                            | Hidden unless "Subs today?" = Yes.                                             |
| 06 Visitors                        | Hidden unless "Visitors today?" = Yes.                                         |
| 07 Equipment                       | **Visible** — pre-populated with yesterday's equipment. Single tap to remove.  |
| 08 Material Deliveries             | Hidden unless "Deliveries today?" = Yes.                                       |
| 09 Activity / Production           | **Visible** — activity narrative is the day's actual story.                    |
| 09b Production quantities          | Hidden unless "Production to report?" = Yes.                                   |
| 10 Delays / Extra Work             | Hidden unless "Delays today?" = Yes.                                           |
| 10b Weather impact rows            | Hidden unless "Weather impact?" = Yes.                                         |
| 10c Incidents                      | Hidden unless "Incident today?" = Yes.                                         |
| 10d Injuries                       | Hidden unless "Injury today?" = Yes.                                           |
| 10e Excavation Activity            | Hidden unless "Excavation today?" = Yes.                                       |
| 11 Sign-Off                        | **Visible** — single signature pad + Submit.                                   |

**Target default-visible section count: 6** (Report Info · Weather · What Happened Today · Crew · Activity · Sign-Off). Down from 11. **−45 %**.

---

## 6 · Coaching blocks that should be removed (or moved to "only when risky")

### Daily Report

| Block                                                                  | Recommendation |
|------------------------------------------------------------------------|----------------|
| "One report per crew, per day. Capture labor, subs, materials, weather, and photos so payroll and PM coordination run clean tomorrow." (sub-header) | **Remove.** The form title is enough. |
| Status Card paragraphs ("Owners and the GC look at location for context.") | **Remove.** Replace with "3 things left" + one-tap jump. |
| DailyReportExcavationActivity "Coaching, not punishment" amber strip   | **Remove.** Keep only the YES/NO and Create/Link buttons. |
| Section 03 paragraph helper text                                       | **Remove.** Each YES/NO question is self-explanatory. |
| Photo section: "Required Photo Kinds — capture each before crew descent." + 7 line items | **Replace** with a single horizontal scroller of 6 chips with a green check or empty placeholder. |
| PreviousReportSuggestions "X crew members · Y equipment items · work-performed text available" | **Trim** to "Yesterday: 8 crew · 6 equip · 3 lines."  |

### Excavation Form

| Block                                          | Recommendation |
|------------------------------------------------|----------------|
| 8 × `OshaCoachingBlock` (Soil/Protective/Access/Utility/Water/Atmos/CP) | **Move out of the form**. They should only render in two cases: (a) the foreman is currently focused in that field, OR (b) the live compliance engine has fired a requirement related to that field. Otherwise, hide. |
| Compliance Card "Live OSHA Status" eyebrow + verbose status reason | **Compress** to one line: "Ready ✓" or "3 things to fix" with a chevron. |
| Top stop-work + amber coaching strip on every public form | **Consolidate** to a single one-line banner at the very top: "Stop the job if anything looks wrong — that's the rule." |

---

## 7 · REDESIGNED DAILY REPORT WORKFLOW

A foreman opens `/daily/submit` at 5:30 AM. What they should see:

```
┌────────────────────────────────────────────────────────────┐
│  SUBMIT  ←  [SAVE]  EN | ES   ●                            │
└────────────────────────────────────────────────────────────┘

DAILY JOB REPORT                                  Ready ✓
─────────────────────────────────────────────────────────────

TODAY'S JOB
                          [#20-07 T5686 SR 15/SR600 SANFORD]
                          Customer: FDOT  ·  PM: Brent Hutt
                          Super: Manny Garcia
                          Weather: 71°F, partly cloudy
                          Date: Feb 07, 2026  ·  Report #2057
                                                      [Edit]

WHAT HAPPENED TODAY?     (tap what applies — defaults to No)

 □ Normal production   □ Subs on site    □ Visitors
 □ Deliveries          □ Production qty  □ Delays / extra
 □ Weather impact      □ Incident        □ Injury
 □ Excavation today

CREW                                          [Use Yesterday]
                          8 from yesterday, prefilled below
                          • Tony Reyes  (Leadman)
                          • Carlos Diaz (Crew)
                          • [4 more]
                                                  [Add Crew]

EQUIPMENT                                     [Use Yesterday]
                          6 from yesterday, prefilled
                          • CAT 320 EXC #C12
                          • Bobcat E50 #M07
                          • [4 more]
                                              [Add Equipment]

ACTIVITY
                          ┌──────────────────────────────────┐
                          │ What did the crew do today?      │
                          │ (Copy from yesterday available)  │
                          └──────────────────────────────────┘
                                          [Copy yesterday's]

PHOTOS                                              0 / 6
                          [+] Overall   [+] Work
                          [+] Crew      [+] Material
                          [+] Safety    [+] Closeout

──────────────────────────────────────────────────────────────

                          [SIGN AND SUBMIT]
```

That's the entire normal-day form. Nine "What happened today?" checkboxes silently expand a focused panel ONLY when checked.

### Sticky status — replacement for the verbose Status Card

```
3 things left → Crew · Photos · Sign
```

One line. Tappable. Each word jumps to the section. When everything is in: `Ready ✓ → tap to submit`.

### Auto-apply on job select (silent — no confirmation tap)

1. Foreman picks job → all jobs_master fields filled.
2. Backend silently loads the most recent Daily Report for that project_number.
3. Crew + Equipment + Activity-narrative prefilled into the form.
4. A small toast at the bottom: "Yesterday's setup applied · undo" (5 sec auto-dismiss).

If the foreman doesn't undo it, the work disappears.

### Coaching policy

- No permanent coaching blocks visible by default.
- Coaching shows ONLY when the foreman picks something risky:
  - "Trench Box selected but no asset linked" → fire ONE coaching tooltip on the protective system field.
  - "Incident = Yes" → fire ONE coaching tooltip on the Incident panel.
- All other coaching lives in the OSHA Library / help system (deferred backlog), accessible from the header `?` icon.

### Submit button

- Bottom-sticky.
- Says `SIGN AND SUBMIT` when ready.
- Says `3 LEFT — TAP TO FIX` when not ready, and tapping it scrolls to and focuses the first incomplete section.

### Mobile

- One column always.
- 56-pt minimum tap targets on all action items.
- Each section is `min-h-screen / 4` so a single section fits comfortably on a phone with no scrolling within the section.

---

## 8 · Files that need a rewrite (NOT a delete)

Conservative cleanup plan to land the redesign without breaking integrations:

| File                                                                  | Action                                                                      |
|-----------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `components/dailyreport/DailyReportStatusCard.jsx`                    | **Rewrite** to single-line "N things left → A · B · C" with no paragraphs.  |
| `components/dailyreport/PreviousReportSuggestions.jsx`                | **Rewrite** to auto-apply silently + one-tap "undo" toast.                  |
| `components/dailyreport/LinkedExcavationCompliance.jsx`               | **Trim** to single-line summary: `EX-2026-001 · 6 ft · Type C · Action Required` + chevron. |
| `components/dailyreport/DayActivityTriggers.jsx` (in-flight)          | **Rewrite** to single-row checkbox grid (no per-row coaching, no helper text). |
| `lib/dailyReportCompliance.js`                                        | **Trim** — drop paragraph `why` and `action` text. Keep `status` + `requirements[].label` (3-word labels). |
| `pages/NewDailyReport.jsx`                                            | **Rewrite Section 03** to remove the YES/NO grid and replace with `DayActivityTriggers`. **Wrap Sections 05/06/08/10/11(weather/incident/injury/excavation rows)** in `triggered=Yes` conditional render. Remove the Section sub-header paragraph. |
| `components/trench/DailyReportExcavationActivity.jsx`                 | **Trim** — remove the amber coaching strip. Keep YES/NO + Create/Link buttons. |
| `lib/excavationCompliance.js` + `components/trench/ExcavationComplianceCard.jsx` | **Trim** — drop verbose status reason, drop paragraph `why`, keep one-line per requirement. |
| `components/trench/OshaCoachingBlock.jsx`                             | **Make conditional** — render ONLY when the section's compliance engine has fired a related requirement. |

---

## 9 · Metrics targets (post-rewrite)

| Metric                                                            | Phase 10D today | After this rewrite | Target Δ |
|-------------------------------------------------------------------|-----------------|--------------------|----------|
| Default-visible sections on a fresh Daily Report                  | 11              | 6                  | **−45 %** |
| Foreman taps to reach "Ready ✓" on a normal day with prior report | ~32             | ~10                | **−69 %** |
| Foreman typed characters on a normal day                          | ~200            | ~25 (work narrative only) | **−87 %** |
| Status card lines of text                                         | ~30 across 6 cards | 1 line          | **−97 %** |
| Permanent coaching blocks on the screen                           | 8 (Excavation) + 2 (DR) = 10 | 0                 | **−100 %** |

---

## 10 · What I will NOT do

- I will **not** add another panel.
- I will **not** add another chip.
- I will **not** add a new coaching tone.
- I will **not** add a new "intelligence" feature.
- I will **not** add a new section.

This sprint is about subtraction.

---

## 11 · Recommendation

Hold for OMEGA review. Two paths forward:

**Path A — full simplification rewrite (recommended).**
Execute Section 7 redesign. Touches ~9 files. Net effect: deletes more than it adds. Expected to land in one focused sprint.

**Path B — incremental trim (lower risk, slower).**
Trim the existing Status Card to one line, remove Section 03 paragraph helper text, hide CollapseCards behind the "What happened today?" checkbox row. Leave the rest as-is. Lower delta but unblocks foremen immediately.

I recommend **Path A**. The system has accumulated enough developer-style decoration that incremental trimming will leave half-finished simplification in production. A focused rewrite sprint, scoped exactly to the Section 7 blueprint, fixes it in one pass.

Awaiting OMEGA decision before any further code changes.

---

*Audit prepared under the OMEGA Stop Order · Daily Report Simplification Correction Directive · MASCI Operations Platform.*
