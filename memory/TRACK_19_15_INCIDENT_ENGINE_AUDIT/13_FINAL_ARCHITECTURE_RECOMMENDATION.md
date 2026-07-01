# Track 19.15 · 13 · Final Architecture Recommendation

## GO

Proceed to Track 19.16 immediately.

## What we build (in order)

1. **Track 19.16** — Extend `incidents` collection with six additive sub-collections + state-machine lifecycle. Feature-flag `INCIDENT_ENGINE_V2`.
2. **Track 19.17** — Field UI rewrite consuming FormShell + PresenceGate + HelpDrawer + SubmitReviewPanel with 13 incident-type branches from doc 03. Remove regulatory questions from field UI.
3. **Track 19.18** — Safety case workspace at `/safety-portal/incidents/:id/case`.
4. **Track 19.19** — 14-section PDF redesign with per-audience rendering.
5. **Track 19.20** — Dashboards + CA tracking + exec digest.

## What we DO NOT do

- Do not rename the `incidents` collection.
- Do not delete a single existing field.
- Do not break historical records.
- Do not force a single-shot migration.
- Do not touch schemas outside `incidents` scope.
- Do not implement in this track — audit only.

## Doctrine

- **Field captures facts.**
- **Safety investigates.**
- **Management decides.**
- **Platform routes, records, reports, and protects.**

## Verification

- 14 architecture / audit documents (this folder) — 14 required, 14 present.
- Track 19.15 pytest lock suite verifies every doc + every doctrine marker.
- Zero runtime source files touched (enforced by pytest — this track is docs + tests only).
- PRD.md updated.

## Six Pillars — passed

- **Powerful:** captures the right facts, routes to the right people, produces the right reports.
- **Simple:** field operator answers only the questions relevant to their incident type. 5:30 AM Foreman Test passes.
- **Beautiful:** 14-section PDF replaces the raw-boolean-dump defect.
- **Trusted:** field is never asked to make regulatory determinations; Safety owns the record.
- **Proven:** every existing behavior preserved; every future step is pytest-locked.
- **Operational:** the case lifecycle mirrors how a real incident actually plays out from scene to closeout.

## Final call

**GO. Proceed to Track 19.16 with the architecture from documents 01–12 as the source of truth.**
