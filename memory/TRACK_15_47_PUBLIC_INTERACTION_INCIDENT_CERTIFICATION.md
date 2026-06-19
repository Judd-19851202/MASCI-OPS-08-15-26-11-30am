# TRACK 15.47 · Phase 1A · Public Interaction Incident Certification

**Date:** 2026-06-19
**Audit type:** Forensic · evidence-based · the 10-question test
**Driver:** The actual real-world incident that triggered this track — a verbal confrontation that escalated into physical contact between a member of the public and a MASCI employee.

This document answers the 10 forensic questions that the executive asked, with hard YES / PARTIAL / NO based on the audit findings in `TRACK_15_47_INCIDENT_WORKFLOW_AUDIT.md`.

---

## The 10 questions and the honest answers

### Q1 · Can an employee report it?

**Answer: PARTIAL.**

- **What works:** Public form at `/incident/new` accepts an anonymous report. `POST /api/incidents` writes the record. Rate-limited but functional. Incident shows up on the bell within seconds.
- **What does not work:** There is no `incident_type` value that says "Public Interaction — Verbal" or "Public Interaction — Physical Confrontation". The operator must select `Public / Third Party` or `Security`. The actual encounter classification lives in the free-text `description`.

**Implication:** Six months from now, if a senior analyst asks "How many verbal confrontations did we have in 2026?", the platform cannot answer without a SQL-style scan of the description text.

---

### Q2 · Can witnesses be documented?

**Answer: PARTIAL.**

- **What works:** `witnesses: List[{name, statement}]` is captured and persisted. The PDF renderer dedicates a witnesses table — including a signature column ready to display a signed witness statement.
- **What does not work:** The form captures NAME + STATEMENT only. Missing on each witness row:
  - role (employee / public / law enforcement / vendor)
  - phone
  - address / email
  - employer
  - signature (the field is rendered if present but no UI captures it)
  - witness type for legal evidentiary purposes

**Implication:** When the case is deposed, MASCI cannot reach the witness because the phone number was never captured. The witness's statement is also not signed — it carries less weight in court than a signed statement.

---

### Q3 · Can police involvement be documented?

**Answer: NO.**

- The `IncidentCreate` model has NO field for: `police_called`, `police_arrived`, `responding_officer_name`, `responding_agency`, `report_number`, `case_number`, `report_obtained`, `body_camera_footage_requested`.
- A police report PDF *could* be uploaded inside `photos[]` as base64, but it would render as a photo. There is no way to tag "this attachment is the police report".

**Implication:** When the case goes to the District Attorney or to a civil court, MASCI must produce the police report number from email or memory, not from the incident record.

---

### Q4 · Can vehicle damage be documented?

**Answer: PARTIAL.**

- **What works:** `incident_type="Vehicle / Mobile Equipment"` exists. The `description` is free text.
- **What does not work:** No fields for:
  - estimated damage value ($)
  - VIN
  - license plate (the only one we have for INC-2026-00002 lives inside a photo)
  - insurance claim number
  - third-party adjuster contact
  - tow / impound info
  - third-party vehicle owner contact

**Implication:** Subrogation and recovery — the platform supports neither. Insurance claims are handled outside the platform via email + photo bundles.

---

### Q5 · Can photos be attached?

**Answer: YES.**

- `photos: List[str]` accepts base64-encoded images. PDF renderer dedicates a `PHOTOS` section. INC-2026-00002 carries 1 photo (license plate of the offending vehicle) and it renders cleanly.

**Caveat:** No file-size limit enforced server-side beyond the request size limit. No virus scan. No metadata stripping (GPS in photo EXIF could be sensitive). No max-count enforced.

---

### Q6 · Can statements be attached?

**Answer: PARTIAL.**

- **What works:** Per-witness statement field is captured as free text.
- **What does not work:** A "signed statement PDF from a public witness" can only be added via `photos[]`. There is no dedicated "Statements" sub-array. There is no way to attach a typed-and-signed `.pdf` and have it labeled as a statement.

**Implication:** When opposing counsel asks for "all signed witness statements", they will be mixed in with site photos in the `photos[]` array.

---

### Q7 · Can corrective actions be tracked?

**Answer: YES (but with a caveat about defensibility).**

- **What works:** `safety/corrective-actions` CAPA records exist. They can be linked to an incident via `source_kind="incident"` + `source_id=<incident_id>`. They have owner, due date, priority, status, completion notes, closed-by. 6 incident-sourced CAPAs already exist in preview.
- **The caveat:** The incident PDF renders the FREE-TEXT `corrective_actions` field from the incident itself, NOT the linked CAPA records. A reader of the PDF cannot tell whether the corrective action was actually completed, who completed it, when, and what the verification was.

**Implication:** Defensible "we fixed it" evidence requires running TWO queries (incident + linked CAPA), not one.

---

### Q8 · Can management see it?

**Answer: PARTIAL.**

- **What works:** PM gets an in-app notification automatically. Safety gets one + a task. The Executive Overview tile `unresolved_incidents` counts all incidents (collapsed into one count).
- **What does not work:** No breakdown by incident type, severity, or violence-related categorization. No "public-interaction incidents this month" tile. No automatic escalation to Operations or Executive when the incident type is violence-related.

**Implication:** Executive must ask "are we seeing more public-interaction incidents?" and the platform cannot answer at-a-glance.

---

### Q9 · Can safety see it?

**Answer: YES.**

- Safety receives in-app notification + dedicated task immediately. The SafetyIncidents portal lists every incident with filter. CSV export works. PDF export works. Cross-link to linked CAPAs works.

**This is the strongest part of the workflow.**

---

### Q10 · Can it be proven six months later in court?

**Answer: PARTIAL — and this is the one that matters.**

What CAN be proven from the platform six months later:
- ✅ The incident was reported on a specific date.
- ✅ Who reported it.
- ✅ What the reporter said happened (description text).
- ✅ Photos that were uploaded.
- ✅ Supervisor signature.
- ✅ Incident status changes via the `state_events` query (NOT on the PDF).
- ✅ Linked CAPA records via a separate query (NOT on the PDF).

What CANNOT be proven from the platform six months later:
- ❌ The police report number / agency / case number — not captured.
- ❌ The responding officer's name — not captured.
- ❌ The witness's phone number — not captured.
- ❌ Whether the witness's statement was signed — signature field exists on the renderer but no capture path.
- ❌ Whether a weapon was involved — no structured field.
- ❌ Whether the public member touched the employee — no structured field.
- ❌ Whether the encounter was filmed / posted — no structured field.
- ❌ The damage value for civil recovery — no monetary field.
- ❌ The state-event audit history on the printable artifact — query only, not on PDF.
- ❌ The completion status of corrective actions on the printable artifact — query only, not on PDF.

**Implication:** Today the PDF is a self-report, not a chain-of-custody artifact. In court, opposing counsel can ask "where is the witness's contact info?" and MASCI must answer "we did not capture it." This is the chain-of-custody gap that the user's directive flagged as critical.

---

## Summary scorecard

| # | Question | Status |
|---|---|:---:|
| Q1 | Can an employee report it? | 🟡 PARTIAL |
| Q2 | Can witnesses be documented? | 🟡 PARTIAL |
| Q3 | Can police involvement be documented? | 🔴 NO |
| Q4 | Can vehicle damage be documented? | 🟡 PARTIAL |
| Q5 | Can photos be attached? | 🟢 YES |
| Q6 | Can statements be attached? | 🟡 PARTIAL |
| Q7 | Can corrective actions be tracked? | 🟢 YES (with PDF caveat) |
| Q8 | Can management see it? | 🟡 PARTIAL |
| Q9 | Can safety see it? | 🟢 YES |
| Q10 | Can it be proven six months later in court? | 🔴 PARTIAL — gap is large |

**Overall verdict on the certification target ("if the same incident happened tomorrow morning would MASCI know exactly what to do?"):**

🟡 **YELLOW — the reporting works, the workflow works, but the structured capture and the courtroom-defensibility do not.**

The exact remediation list is in `TRACK_15_47_IMPLEMENTATION_RECOMMENDATIONS.md`. Per the 4C directive, no fixes are implemented in this track without user authorization.
