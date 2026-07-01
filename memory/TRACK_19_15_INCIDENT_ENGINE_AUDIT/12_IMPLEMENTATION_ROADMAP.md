# Track 19.15 · 12 · Implementation Roadmap

## Phased tracks

### Track 19.16 — Incident Intelligence Engine backend architecture
**Scope:** Additive sub-collections (`incident_case_state`, `incident_investigation_notes`, `incident_corrective_actions`, `incident_evidence`, `incident_regulatory_log`, `incident_case_timeline`). Case lifecycle state machine extension on existing `/incidents/{id}/transition` endpoint. Per-type routing rules in `email_routing_v2` config.
**Risk:** MEDIUM · new collections + state-machine transitions must not break existing incident writes. Regression-lock the existing `incidents` schema before deploying.
**Dependencies:** Track 19.15 audit (this track).
**Tests:** Pytest for every new sub-collection · state-machine transitions · routing rules per type. 100% preservation of existing `incidents` payload.
**Rollback:** Sub-collections are additive; drop them without affecting historical records.
**Deployment plan:** Deploy behind a feature flag `INCIDENT_ENGINE_V2`. Default OFF. Enable in staging, verify, then production.

### Track 19.17 — Field Incident Report branching UI
**Scope:** Rewrite `NewIncident.jsx` to consume FormShell + ProgressRail + PresenceGate + HelpDrawer + SubmitReviewPanel. Implement 8-step field flow with type-specific branching from doc 03. REMOVE regulatory / root-cause / CA fields from field UI (they move to Safety case workspace in 19.18).
**Risk:** MEDIUM · large frontend refactor.
**Dependencies:** Track 19.16 (backend schema extensions), Track 19.11 MAIN (primitives).
**Tests:** Pytest lock on field-UI enforcement (no OSHA / root-cause / CA in field flow). Playwright smoke per incident type. Bilingual parity.
**Rollback:** Feature flag toggle to old `NewIncident.jsx`.
**Deployment plan:** Behind `INCIDENT_ENGINE_V2` + `INCIDENT_UI_V2`. Coexist with legacy for one release.

### Track 19.18 — Safety Case Management workspace
**Scope:** New Safety-facing case workspace at `/safety-portal/incidents/:id/case`. Implements Steps 1–8 of the Safety case flow from doc 10. Wires the sub-collections from Track 19.16.
**Risk:** MEDIUM · new UI surface; existing `SafetyIncidents.jsx` remains.
**Dependencies:** Track 19.16 + 19.17.
**Tests:** Pytest for permissions (only Safety + Management can transition). Playwright for full lifecycle. Bilingual parity.
**Rollback:** Feature-flag off.
**Deployment plan:** Same feature flag family.

### Track 19.19 — Incident PDF / Report redesign
**Scope:** New 14-section PDF from doc 02. Per-audience rendering (Field/PM · Safety · Exec · OSHA-facing).
**Risk:** LOW-MEDIUM · report layer only, no data changes.
**Dependencies:** Tracks 19.16 + 19.17 + 19.18.
**Tests:** Snapshot tests per audience × per incident type (13 types × 4 audiences = 52 snapshots). Bilingual parity.
**Rollback:** Feature-flag to old PDF.
**Deployment plan:** Both PDFs generated in parallel for 2 weeks; ops decides cutover.

### Track 19.20 — Dashboards / analytics / corrective actions
**Scope:** CA dashboard (`/safety-portal/corrective-actions`) with SLA tracking. Analytics view — trends by incident type / project / severity / body part / equipment. Exec digest email.
**Risk:** LOW · analytics-only.
**Dependencies:** 19.16–19.19.
**Tests:** Analytics computed correctly. Bilingual parity. Notification cadence honored.
**Rollback:** Feature-flag off.
**Deployment plan:** Same feature flag family.

## Cross-track guarantees (locked by pytest in every future track)

- Zero schema drift on `incidents` (only additive sub-collections)
- Zero route drift (only new sub-collection endpoints and additive incident lifecycle events)
- Zero drift on any prior modernization track (19.03 → 19.14)
- Bilingual parity: every new EN string has an ES translation
- Session-expired ack-suppression (19.11 Amendment) preserved

## Timeline recommendation

- Track 19.16 · 1 focused session
- Track 19.17 · 1–2 focused sessions (large refactor)
- Track 19.18 · 1–2 focused sessions
- Track 19.19 · 1 focused session
- Track 19.20 · 1 focused session

Total: 5–7 sessions. Each session ships GREEN with regression proof and rollback ready.
