# Track 19.15 · 10 · Future UI Architecture

## Doctrine

The future Incident Intelligence Engine consumes the certified ForgedOps Operational Forms Standard primitives (Tracks 19.10 → 19.14):

- **FormShell** — outer shell (finally adopted here as the first form using the primitive fully)
- **ProgressRail** — 8-step field flow + separate Safety case flow
- **PresenceGate** — every "Yes/No/Not sure" gate in incident-type branching
- **HelpDrawer** — single coaching surface per incident type (bands vary by type)
- **SubmitReviewPanel** — pre-submit review with type-specific downstream commitment matrix
- **Bilingual parity** — every new string EN + ES; translation-on-submit
- **Autosave / draft recovery** — Track 15.60 pattern
- **Session hardening** — Track 19.11 Amendment ack-suppression

## Field flow (Track 19.17)

**Step 1 — What happened?** — Incident-type picker (icon grid). Selecting a type conditions every downstream question via PresenceGate + progressive disclosure.

**Step 2 — Where / when?** — Project + location + date/time + GPS.

**Step 3 — Who was involved?** — Roster picker (existing EmployeeCombo + JobPicker), sub-branches for injured / driver / operator / third-party per incident type.

**Step 4 — Incident-specific facts** — The branching question set from doc 03. This is the biggest step. Uses PresenceGate for every Yes/No/Unsure gate. Skips questions that don't apply.

**Step 5 — Immediate actions** — What the field did in the first 60 minutes. Free-form + suggested chip list (called 911 · called supervisor · moved equipment · isolated area · notified utility · shut off system).

**Step 6 — Photos / evidence** — Camera-first mobile UX (Raken pattern). Evidence-kind picker per upload.

**Step 7 — Witnesses** — Roster + external contact capture.

**Step 8 — Review / submit** — SubmitReviewPanel with per-type downstream commitment matrix (see doc 06 routing). Reporter + supervisor signature.

## Safety case flow (Track 19.18)

**Step 1 — Review field report** — Read-only view of field submission + immediate context.

**Step 2 — Classify incident** — Safety confirms incident type, adds classifications (multi-select from `INCIDENT_CLASSIFICATIONS`), sets severity.

**Step 3 — Investigation** — Free-form narrative + structured findings. Uses `incident_investigation_notes` sub-collection.

**Step 4 — Evidence** — Full evidence catalog. Safety uploads police reports / medical / insurance / OSHA correspondence.

**Step 5 — Regulatory review** — OSHA recordability + reportability determination (Safety-owned). Agency contact log entries in `incident_regulatory_log`.

**Step 6 — Corrective actions** — CA list with owner + due date + status. Written to `incident_corrective_actions`.

**Step 7 — Management review** — Preventability determination + disciplinary decisions. Management sign-off.

**Step 8 — Closeout** — Final sig, PDF locked, case CLOSED.

## Field flow does NOT ask

Track 19.17 UI enforcement (locked by pytest in Track 19.17):
- ❌ OSHA recordability
- ❌ Root cause classification
- ❌ Corrective actions (drafting)
- ❌ Regulatory notification decisions
- ❌ Preventability determination

## Every step is bilingual

Every string routes through `useT()`. Every new EN string has an ES translation.

## PDF rendering per role

- Field / PM see sections 1–9 + 14.
- Safety sees the full 14-section report.
- Executive sees section 1 + case status + CA status only.
- OSHA-facing export renders sections 1–13 (skip audit appendix from external distribution).
