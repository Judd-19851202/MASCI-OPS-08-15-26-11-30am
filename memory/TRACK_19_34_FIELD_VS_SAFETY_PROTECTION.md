# TRACK 19.34 · FIELD VS SAFETY PROTECTION AUDIT

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md`

Proves that the field-facing incident intake **does not ask the field user any question that belongs to Safety, Legal, HR, or Management.**

---

## Doctrine (locked in Track 19.33)

**Field captures facts. Safety investigates. Management decides. Platform routes, records, reports, and protects.**

Field users must **NEVER** be prompted for:
- OSHA recordable (Y/N)
- OSHA reportable (Y/N)
- Insurance liability (Y/N)
- Legal liability
- Final root cause
- Preventability
- Disciplinary conclusion
- Workers-comp determination
- Final case classification

## Audit results

### Frontend audit
Search results against `/app/frontend/src/lib/incidentReportSchema.js` and `/app/frontend/src/pages/IncidentReport.jsx`:

| Forbidden field | Grep result | Status |
|---|---|---|
| `OSHA` / `osha` | 1 hit — only a code comment at `incidentReportSchema.js:287` explicitly declaring the field-vs-safety line: *"Safety-only determinations (OSHA recordability, root cause, …) live in the Case Workspace."* | ✅ Only doctrine reference, never a form field |
| `recordable` | 0 hits | ✅ Clean |
| `reportable` | 0 hits | ✅ Clean |
| `root.cause` / `root_cause` | 0 hits | ✅ Clean |
| `preventab` | 0 hits | ✅ Clean |
| `discipline` | 0 hits | ✅ Clean |
| `workers.comp` / `workers_comp` | 0 hits | ✅ Clean |
| `liability` | 0 hits | ✅ Clean |

**Zero forbidden fields in the field intake.**

### Doctrine banner reinforcement
Track 19.34 additionally introduces the `IncidentFieldDoctrineBanner` component (`components/incident/IncidentFieldDoctrineBanner.jsx`) which renders on the type-picker screen and explicitly says:

> "You're capturing facts. Safety will investigate and decide OSHA · insurance · root cause. Just tell us what happened, where, when, who was involved, and what you did."

This is the primary UX mechanism protecting the field user from investigation-questioning creep in future tracks.

## What field users CAN answer (allowlist)

Per `INCIDENT_FLOWS` step compositions:
- **What happened** — `incident_type` + free-form summary
- **Where** — GPS + project + address
- **When** — date + time
- **Who was involved** — employee picker · public parties · witness list
- **Photos** — mandatory for high-severity types
- **Witnesses** — name + contact
- **Immediate actions** — what you did (mandatory for injury / utility strike)
- **Utility info** (utility_strike only) — locate ticket · utility type · owner · marked · service interrupted · notifications
- **Vehicle info** (vehicle_accident only) — vehicles · drivers · passengers · police · injuries · tow
- **Equipment info** (equipment_accident only) — equipment · operator · spotter · damage · fluid · rollover · OOS
- **Injury info** (employee_injury / public_injury) — body part · injury description · treatment · ambulance · clinic
- **Property damage** — property · owner · damage description · severity
- **Environmental** — substance · quantity · containment · waterway impact · cleanup · agency notification
- **Threat / violence** — threat · physical contact · weapon · police · people separated
- **Theft / vandalism / security** — item · site secured · police · report number
- **Near miss** — what almost happened · potential severity · contributing conditions · prevention

**All questions are observable facts — nothing requires investigation, legal judgment, or Safety expertise.**

## Enforcement mechanism (future-proof)

The Track 19.34 lock test (`test_track_19_34_incident_field_intake_modernization.py`) contains an invariant:
- Greps `incidentReportSchema.js` for forbidden field labels.
- Fails if any future track introduces `osha_recordable`, `root_cause`, `preventability`, `discipline`, `workers_comp`, `liability`, or `recordable` as a field-facing schema entry.
- Non-form comments (like the doctrine declaration at line 287) are permitted.

This makes accidental regression loud and immediate.

## Safety-owned surfaces (the questions that DO get asked · just not to field users)

Per Track 19.16 architecture, the Case Workspace at `/safety/cases/:caseId` (auth-gated to Safety token) is where:
- OSHA recordability is determined
- Root cause is proposed and reviewed
- Preventability is scored
- CAPAs are assigned
- Discipline chain (if any) is captured
- Insurance carrier is notified

None of this is exposed to the field user or to any non-Safety role via the field intake.

## Cross-check with future incident tracks

Future Tracks 19.35 – 19.38 must uphold this doctrine. The Track 19.33 readiness bridge lists the field-owned vs safety-owned matrix that governs those tracks. Any track that proposes adding an OSHA classification field to the field intake fails automatic gate.

## Verdict

🟢 **Field intake is protected.** No investigation questions leak into the field UX. Doctrine is visible to the field user via the banner and enforced by the lock test.
