# PHASE 31.1 · Daily Report Crew Memory Continuity

_iter437 · 2026-05-25 · Pass A_

## Mission
Reduce repetitive field entry on Daily Reports by remembering
yesterday's crew + equipment setup ON THIS DEVICE ONLY. Save 60-90
seconds of typing every morning. Never become an account system,
never sync to a server, never let one crew see another's data.

## Doctrine (verbatim from Phase 31.1 spec)
- **Device-local memory only** · `localStorage` · `masci.crew-memory.daily-report.v1`
- **Daily Report ONLY** · no fan-out to incidents / inspections / HR /
  safety / PM / dispatch / shop without an explicit Phase update
- **Never silent auto-fill** · always show the calm restore prompt
- **3 buttons exactly**: Use Setup · Start Blank · Clear Saved Setup
- **30-day TTL** · rolling on every "Use Setup" (lastUsedAt refresh)
- **Optional setup nickname** · local-only · editable inline
- **NO server sync · NO admin visibility · NO surveillance · NO
  cross-device · NO dashboards · NO analytics · NO AI suggestions**

## Allowed fields (saved)
| Field | Source | Notes |
|-------|--------|-------|
| `prepared_by` | foreman / reporter name | text |
| `superintendent` | supervisor name | text |
| `project_name` | job name | text |
| `project_number` | job number | text |
| `masci_crews[]` | crew roster | name + trade ONLY · hours/work_performed STRIPPED |
| `subcontractors[]` | subs on site | company + trade + foreman ONLY · count/hours/work_performed STRIPPED |
| `equipment[]` | equipment list | description ONLY · hours/times/notes STRIPPED |
| `nickname` | optional setup label | local-only · 60-char cap |

## Banned fields (NEVER saved · stripped defensively in `extractSetupSnapshot`)
- Production quantities (materials, activities, % complete, station ranges)
- Notes / general_notes / schedule_delays_notes / weather_impact_notes
- Incident fields (incident_notes, safety_*, injuries_reported)
- Signatures (prepared_by_signature, superintendent_signature)
- Operational comments
- Weather (weather_summary, weather_snapshots, weather_impact flags)
- Attachment references (photos)
- GPS coordinates (gps_lat, gps_lng, gps_accuracy)
- Distribution list (PM/GC/DOT/insurance emails)
- Visitors (site visitor log)
- Idempotency keys / report numbers / report dates

## What ships in iter437
- **`lib/crewMemory.js`** — extract / save / load / clear / rename /
  apply. Defensive re-extraction on save so callers cannot accidentally
  persist banned fields. 30-day TTL · rolling on `applySetupSnapshotToData`.
- **`components/daily-report/CrewSetupRestorePrompt.jsx`** — calm amber
  3-button card. Nickname chip with inline rename. Summary line:
  `<project> · <N> crew members · <N> subcontractor · <N> equipment items`.
- **`pages/NewDailyReport.jsx`** wiring:
  - Loads saved setup on mount → renders prompt above the draft prompt
  - On submit success (or queued-offline path) → `saveCrewSetup(payload)`
  - On Use Setup → `applySetupSnapshotToData` → toast confirmation
  - On Clear Saved Setup → `clearCrewSetup()` → toast confirmation
- **25 new EN→ES strings** in `lib/i18n.js`
- **Pre-existing dead-code cleanup**: removed 24 lines of orphaned JSX
  after the component close (from an older iteration · ESLint flagged
  it once new code increased the parse surface)

## Live verification (iter437 smoke)
- Seeded a representative snapshot (Mike Smith / Steven J / Oxford
  Resurfacing 2026 · 3 crew · 1 sub · 2 equipment)
- Prompt rendered: ✅
- Summary computed correctly: ✅
- Nickname chip displayed "PAVING CREW A": ✅
- Use Setup populated project_name field + cleared prompt: ✅
- ESLint clean: ✅

## What this iteration explicitly did NOT do
- ❌ NO fan-out to other forms (incident / inspection / HR / safety /
  PM / dispatch / shop) — strict scope lock per Part 2
- ❌ NO server-side storage of crew setups
- ❌ NO admin draft/setup browser
- ❌ NO cross-device sync
- ❌ NO surveillance · ranking · scoring · "AI suggestions"
- ❌ NO new admin endpoint · NO new Mongo collection · NO new env var
- ❌ NO new BANNED word in any user-facing string: profile / template
  / cache / autofill / synced / account / browser memory all absent

## Backlog
- 🟡 P2 · Operator-owned mobile real-device certification on iPhone
  Safari + Android Chrome + iPad Safari + rugged tablet
- 🟡 P3 · After operational proof: consider Phase 31.2 fan-out to a
  second high-friction form (Incident reports? Inspections?) — only
  with explicit user approval per doctrine

## Verdict
🟢 The platform now offers Mike (and every operator) the calm
"yesterday's setup is right there, edit anything, never silent" pattern
on Daily Reports. Doctrine of restraint held end-to-end · zero new
admin surfaces · zero new server endpoints · zero new collections.
