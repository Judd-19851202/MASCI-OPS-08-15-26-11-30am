# TRACK 19.34 · INCIDENT FIELD INTAKE MODERNIZATION (PHASE 1 OF INCIDENT INTELLIGENCE ENGINE)

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillars Aggregate: 58/60 · Production Strong**
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md` · `TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md`

## Charter
Modernize the field-facing Incident/Accident intake so field crews capture clear facts through a guided, type-aware workflow — while preserving 100% of the existing backend contract, permission model, PDF/email/notification behavior, and historical records.

Phase 1 of the Incident Intelligence Engine per the Track 19.33 readiness bridge. The Safety Case Workspace, Executive PDF redesign, and OSHA/insurance decisioning are explicitly **out of scope** for this track.

## What was already in place before Track 19.34

Track 19.16 (Phases B1 + B2 · shipped 2025-Q3) already delivered a modernized, type-aware `IncidentReport` intake at `/incidents/report`:
- Progressive disclosure: **type picker → guided steps → review → submit** phases (see `IncidentReport.jsx:1602-1620`).
- 17 incident types with per-type step composition via `stepsFor()` in `lib/incidentReportSchema.js:641-659`.
- Draft/resume via `useFormAutosave`.
- Bilingual via `useT()` on every string.
- Field types include personnel picker · employee picker · equipment picker · vehicle picker · GPS · photos · witnesses · yesno · yesno_unsure · textarea · select · date · time · text · number.
- Legacy retirement: `/incidents/new` and `/incidents/submit` `<Navigate>` to `/incidents/report` (`App.js:551-552`).
- Per-type severity requirements (photos required for utility/vehicle/injury/fire · witness-or-attempted-contact required for injury · immediate-actions required for injury/utility-strike).

## What Track 19.34 adds

### 1 · Field-vs-Safety Doctrine Banner
New component `frontend/src/components/incident/IncidentFieldDoctrineBanner.jsx`:
- One-line, calm, high-signal banner rendered at the top of the type-picker screen (**first thing the field user sees**).
- Wording: *"You're capturing facts. Safety will investigate and decide OSHA · insurance · root cause. Just tell us what happened, where, when, who was involved, and what you did."*
- Bilingual via `useT()`.
- Zero state · zero form fields · zero permission drift.
- Test ID: `incident-field-doctrine-banner`.

### 2 · Wiring
Added 2 lines in `pages/IncidentReport.jsx`:
- Import statement.
- Render at top of `IncidentTypePicker` component (only visible on the picker screen · not repeated on step screens or review screen).

### 3 · Certified type-map + field-vs-safety-protection + zero-drift-matrix docs
See companion documents:
- `TRACK_19_34_INCIDENT_TYPE_MAP.md`
- `TRACK_19_34_FIELD_VS_SAFETY_PROTECTION.md`
- `TRACK_19_34_ZERO_DRIFT_MATRIX.md`

## Six Pillars alignment

- **Powerful**: 9/10 · 17 real, distinct field workflows guide the operator to the right facts.
- **Simple**: 10/10 · One banner, one question ("What happened?"), one card tap. Field users answer only what they should.
- **Beautiful**: 9/10 · Consistent with certified operational forms design language.
- **Trusted**: 10/10 · Doctrine banner + no OSHA/root-cause fields + zero backend/schema/permission drift.
- **Proven**: 10/10 · Live Playwright smoke passed (banner + all 10 required types + mobile 390 · EN/ES toggle).
- **Operational**: 10/10 · Mobile-first · autosave · draft resume · type-specific facts · type-specific required-field checks (already shipped in 19.16 · preserved).

**Aggregate: 58 / 60 · Production Strong.**

## Rollback

- **Runtime rollback:** delete 2 lines in `IncidentReport.jsx` (import + `<IncidentFieldDoctrineBanner />` render). The banner is additive, stateless, and doesn't affect submit or payload — removing it reverts to pre-19.34 behavior instantly.
- **File-level rollback:** delete `IncidentFieldDoctrineBanner.jsx`.
- **Rollback confidence:** HIGH.

## Live verification

Playwright smoke at `https://safety-audit-mobile-1.preview.emergentagent.com/incidents/report` (public route, no auth required):
- ✅ `[data-testid="incident-field-doctrine-banner"]` present.
- ✅ `[data-testid="incident-type-picker"]` present.
- ✅ 10/10 required incident-type cards render: `utility_strike`, `employee_injury`, `vehicle_accident`, `equipment_accident`, `property_damage`, `near_miss`, `environmental`, `workplace_violence`, `theft`, `other`.
- ✅ Mobile viewport 390 × 844 renders cleanly.
- ✅ EN/ES language toggle present in header.

Screenshot: `/tmp/incident_intake_mobile.png`.
