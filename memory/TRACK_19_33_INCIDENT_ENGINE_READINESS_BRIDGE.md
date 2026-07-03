# TRACK 19.33 · INCIDENT INTELLIGENCE IMPLEMENTATION READINESS BRIDGE

**Date:** 2026-07-03 · **Status:** DOCUMENTATION ONLY (no code changes)
**Anchor:** Track 19.15 architecture · `TRACK_19_27_INCIDENT_INTELLIGENCE_ENGINE_DEEP_DIVE.md` (if present) · `PRODUCTION_READINESS_QUALITY_GATE.md`

## Charter
Prepare the next major Incident Intelligence Engine implementation track. **This track does not implement the engine.** It locks the scope, doctrine, protections, and gate checklist so the next track starts from certified ground.

## Doctrine (must not deviate)

### Field vs Safety ownership model
| Actor | Owns | Does NOT own |
|---|---|---|
| Field (crew · foreman · superintendent) | **Facts** — who, where, when, what happened, immediate photos, first-aid state, witnesses | OSHA recordability, insurance liability, root cause, disciplinary conclusion |
| Safety (Safety Manager · investigator) | **Investigation** — evidence, findings, CAPAs, executive-facing narrative, OSHA classification | Final management decisions on discipline / claims |
| Management (Executive · Ops leadership) | **Decisions** — insurance, discipline, claims, corrective directives | Investigation methodology |
| Platform | **Routes · records · reports · protects** — audit trail, PDF generation, email routing, permission gating | Judgment calls |

**Field users must NEVER be prompted to answer:**
- OSHA recordable (Y/N)
- OSHA reportable (Y/N)
- Insurance liability (Y/N)
- Final root cause
- Preventability (Y/N)
- Disciplinary conclusion

Those questions live in the Safety Case Workspace, gated by Safety-token authentication.

## Track split recommendation

### Track 19.34 · Phase 1 · Incident intake modernization (RECOMMENDED FIRST TRACK)
Scope:
- Modernize the field-facing `/incidents/report` and `/near-miss` entry forms.
- Add explicit "You're capturing facts — Safety will investigate" doctrine banner.
- Reorganize the fact-capture form using operational form primitives (`ProgressRail` + `SubmitReviewPanel` + `HelpDrawer` + `useFormAutosave`).
- Introduce **incident-type routing** (10 types below) — the field user picks the type, the form adapts.
- **Keep existing case workspace unchanged** in this phase — the field intake is the only surface touched.
- Preserve OSHA-classification fields in the case workspace (Safety-only).

### Track 19.35 · Phase 2 · Case workspace investigation upgrades
### Track 19.36 · Phase 3 · Executive PDF redesign
### Track 19.37 · Phase 4 · Passive incident-presence scoring
### Track 19.38 · Phase 5 · Cross-portal read fanout (Employee 360 · PM job dashboards · Executive Intelligence)

## Incident types to prepare for Phase 1

At minimum, all 10 types below must be supported by the modernized field intake. Each type has a distinct fact-capture emphasis (indicated in parentheses); each still writes to the same `incident_cases` collection with a `type` discriminator.

1. **Utility Strike** — depth · locate ticket · marked-out state · shutoff response.
2. **Employee Injury** — body part · injury nature · first-aid rendered · medical transport.
3. **Vehicle Accident** — DOT recordable · units involved · other-party details.
4. **Equipment Accident** — equipment unit · asset condition · downtime.
5. **Property Damage** — damage extent · cost estimate · owner notified.
6. **Near Miss** — kiosk-friendly · anonymous-safe · learn-from-close-call framing.
7. **Environmental Spill** — substance · volume · containment status · regulatory reportability handled by Safety.
8. **Workplace Violence / Threat** — parties · law enforcement notified · safety of others.
9. **Theft / Vandalism / Security** — items · access point · law enforcement notified.
10. **Other** — free-form facts · Safety triages type on review.

## Required existing routes to preserve

Track 19.16 shipped and certified the following. **No breaking changes permitted in future incident tracks.**

- `/incidents/report` · `/incidents/report?type=…` — field intake (Phase B1)
- `/near-miss` · `/near-miss?type=…` — kiosk intake (Phase B2)
- `/incidents/new` · `/incidents/submit` — legacy redirects (must stay as `<Navigate>` targets)
- `/safety/cases` · `/safety/cases/:caseId` — Case Workspace (Phase C)
- `/safety/cases/:caseId/reports/:reportType` — Executive PDF endpoint (Phase E)
- `/safety/executive-intelligence` — Executive Intelligence Center (Phase D)
- `POST /api/incident-cases` · `GET /api/incident-cases/{id}` · `PATCH /api/incident-cases/{id}` — case CRUD
- `POST /api/incident-cases/{id}/evidence` — evidence upload (SHA-256 + R2 + base64 fallback)
- `POST /api/incident-cases/{id}/audit` — investigator note (append-only)
- `GET /api/safety/cases/{id}/reports/executive.pdf` — ReportLab-generated executive PDF

## Required data model protections

- `db.incident_cases` schema **must not gain destructive migrations**.
- `db.incident_case_audit` remains append-only.
- Any new fact-capture fields must be **nullable** and added with `contract_version` bump.
- SHA-256 original evidence preservation must remain intact.
- Trust Spine linkage (`incident_case.employee_ids`, `incident_case.equipment_ids`, `incident_case.project_id`) must not be renamed.
- Employee 360 read consumer must not break — additive fields only.

## Required PDF redesign principles

For Track 19.36 (Phase 3):
- Executive PDF header: MASCI logo · case number · type · date · status.
- Investigation summary in first page (findings · CAPAs · not raw evidence dump).
- OSHA classification block on page 2 (Safety-only fields — never exposed to field user).
- Evidence appendix at the back — captions, timestamps, no thumbnails on same page as narrative.
- Signature block at the end — Safety Manager · Executive Sponsor.
- No blank filler pages · no raw DB dumps · no PII beyond what the case requires.

## Required Quality Gate checklist (per Track 19.30)

Every incident-engine implementation track (19.34 – 19.38) must produce:
- Six Pillar score with per-track evidence.
- Zero-Drift Matrix — schemas · routes · payloads · PDFs · emails · notifications · permissions · Trust Spine · audit events.
- Rollback path (with feature flag + full source revert).
- Playwright smoke — field intake · case workspace · PDF generation · role visibility.
- Backend lock test — endpoint contract + audit event write + read-only endpoint invariance.
- Bilingual coverage — every field-facing string uses `useT()`.
- Mobile / iPad / desktop smoke — field intake is mobile-critical.
- Pilot observation cadence entry — foreman fact-capture + safety investigation walkthroughs.

## Rollback strategy (for future tracks)

Every incident-engine phase must ship with:
1. Feature flag defaulting to OFF for existing users, ON for new pilots (or vice versa per track scope).
2. Additive backend fields (nullable) so rolling back the frontend leaves the DB compatible.
3. Preserved `_legacy` routes for one full track cycle before retirement.
4. Documented rollback URL + localStorage flag key per track.

## Migration safety strategy

- **No destructive migrations.** All new fields are additive · nullable.
- **Contract versioning** on `incident_cases` — bump `contract_version` per phase.
- **Read fanout consumers** (Employee 360 · Case Workspace · PM job dashboards) must degrade gracefully if a new field is absent.
- **Case Workspace state machine** must remain forward-compatible — new states appended, never renumbered.
- **Executive PDF** — Track 19.36 must render acceptably against both new and legacy case documents.

## Risk matrix (for future tracks)

| Risk | Severity | Mitigation |
|---|---|---|
| Field user answers OSHA classification | HIGH | Doctrine banner + form gating — OSHA fields Safety-only. |
| Legacy case docs render incorrectly under new UI | MEDIUM | Contract-version-aware rendering · fallback to legacy view. |
| Audit trail regression | HIGH | Append-only enforcement · lock tests on `incident_case_audit` write invariants. |
| Permission leakage (PM sees Safety internals) | HIGH | Backend gate on every case endpoint · sidebar visibility filter. |
| Executive PDF has PII leakage | MEDIUM | PII field allowlist · redaction pass · legal review of pilot output. |
| Mobile field intake broken by new type routing | MEDIUM | Playwright mobile smoke on every incident type. |

## Testing matrix (for future tracks)

| Category | Track 19.34 | Track 19.35 | Track 19.36 | Track 19.37 | Track 19.38 |
|---|---|---|---|---|---|
| Backend unit | ✅ | ✅ | ✅ | ✅ | ✅ |
| Backend route contract | ✅ | ✅ | ✅ | ✅ | ✅ |
| Frontend lint / build | ✅ | ✅ | ✅ | ✅ | ✅ |
| Playwright field intake smoke | ✅ (each type) | — | — | — | — |
| Playwright case workspace smoke | — | ✅ | — | — | — |
| Playwright PDF smoke | — | — | ✅ | — | — |
| Role permission smoke | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bilingual smoke | ✅ | ✅ | ✅ | — | ✅ |
| Mobile / iPad / desktop | ✅ | ✅ | ✅ | — | ✅ |
| Audit event smoke | ✅ | ✅ | ✅ | ✅ | ✅ |
| Trust Spine smoke | — | — | — | ✅ | ✅ |
| Rollback sanity | ✅ | ✅ | ✅ | ✅ | ✅ |

## First implementation recommendation

**Start with Track 19.34 (Phase 1 · Field intake modernization).** Rationale:
1. Highest-visibility for field users (they use this every day).
2. Lowest-risk change — additive fact-capture with doctrine banner.
3. Establishes the "field ≠ safety" line clearly before deeper investigation upgrades.
4. Preserves the entire existing case workspace (Track 19.16 · Phases C-E) untouched.
5. Provides the fact-capture quality that Phase 2/3 investigations depend on.

## Next steps

- User approval to proceed with Track 19.34 (Phase 1 · Field intake modernization).
- Confirm the 10 incident types listed above match MASCI operational reality.
- Confirm the field-vs-safety ownership model against internal Safety leadership.
- Pilot observation session with a foreman filing a real incident (fact-capture UX quality baseline).

## Final call

This bridge document is a **planning artifact**, not code. It locks the doctrine, protections, and gate checklist so the next incident-engine implementation track can start clean without re-litigating scope or safety.

🟢 **READY TO EXECUTE Track 19.34 whenever authorized.**
