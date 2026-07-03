# TRACK 19.35 · REGULATORY REVIEW ARCHITECTURE

**Date:** 2026-07-03 · **Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md` · `TRACK_19_34_FIELD_VS_SAFETY_PROTECTION.md`

## Purpose
Document how OSHA · Workers' Comp · Police / Agency · Insurance regulatory review is captured inside the Safety Case Workspace **without ever asking a field user for that determination.**

## Doctrine
> The field never answers **"Is this OSHA recordable?"** The field describes what happened. Safety — with training, records, and the medical + investigation trail — makes the recordable determination.

Track 19.34 enforced this on the *intake* side (grep-based forbidden-field lock). Track 19.35 completes the loop by defining the *investigation-side* surfaces where those determinations live.

## Where each regulatory determination is captured

| Determination | Owner | Workspace surface | API |
|---|---|---|---|
| OSHA recordable (Y/N) | Safety | Executive Snapshot (`snap.osha_recordable`) — driven by `safety_block` | `PATCH /api/incident-cases/{id}` → `safety_block.osha_recordable` |
| OSHA reportable (Y/N) | Safety | Same surface — `safety_block.osha_reportable` | Same route |
| Lost-time days | Safety | Executive Snapshot (`snap.lost_time_days`) · Medical tab | `PATCH /api/incident-cases/{id}` → `safety_block.lost_time_days` (or medical entry) |
| Root cause | Safety | Root Cause tab (existing RCA panel) | `POST /api/incident-cases/{id}/safety_block` → `root_cause_summary` + `contributing_factors[]` |
| Contributing factors | Safety | Root Cause tab | Same route |
| Corrective actions (CAPA) | Safety | Corrective Actions tab | `POST /api/incident-cases/{id}/corrective-actions` |
| Preventability | Safety | Executive Snapshot (readonly view) · `safety_block.preventability` | `PATCH /api/incident-cases/{id}` |
| Workers' comp claim | Safety / HR | Medical tab (existing surface) · `medical.workers_comp_claim` | Existing medical API |
| Insurance / liability | Safety / Admin | Communications tab (agency + carrier log) · Executive Snapshot readonly | `POST /api/incident-cases/{id}/communications` |
| Police / agency report | Safety | Police / Agency tab (existing surface) | `POST /api/incident-cases/{id}/agency-contacts` |
| Discipline | HR / Management | HR portal (not the Safety Case Workspace) | HR routes (out of scope for the workspace) |

## Zero-drift preservation

Track 19.35 **adds no new backend surface** for any of these determinations. Every route in the table already exists and shipped in earlier tracks. The Track 19.35 UI merely:

1. **Anchors** the investigation in the immutable Field Facts tab (so the Safety Manager reads the raw field narrative before making a determination).
2. **Closes** the investigation via the Closeout checklist tab (so the Safety Manager visually verifies the required surfaces have been populated before final closure).

Neither tab writes to backend. Neither tab reads any new endpoint. Both tabs render existing case-document fields.

## The Closeout checklist and its evidence sources

The Closeout tab renders a five-item checklist that auto-checks (✓) when the underlying collection has entries:

| Checklist item | Evidence source | Passes when |
|---|---|---|
| Evidence collected | `evidence[]` (from `api.listEvidence`) | `evidence.length > 0` |
| Witness statements recorded | `witnesses[]` (from `api.listWitnesses`) | `witnesses.length > 0` |
| Root cause / findings documented | `caseDoc.safety_block.root_cause` (existing field) | truthy |
| Corrective actions assigned | `capa[]` (from `api.listCorrectiveActions`) | `capa.length > 0` |
| Regulatory / agency contacts logged | `agency[]` (from `api.listAgency`) | `agency.length > 0` |

The checklist is **display-only**: nothing writes back. Final closure remains a Safety-signoff action from the Executive header (unchanged Track 19.16 surface).

## Field-vs-Safety protection preserved

The Track 19.34 grep invariant (no `osha_recordable`, `root_cause`, `preventability`, `workers_comp`, `liability`, `discipline` labels in the field-facing schema or intake page) is **not weakened** by Track 19.35. Track 19.35 touches only `SafetyCaseWorkspace.jsx`, which is a Safety-gated page — the exact place where those labels are allowed to appear.

## OSHA compliance intelligence — future track

Track 19.35 does **not** introduce automated OSHA recordable/reportable logic. That work is scoped for a later track (see PRD backlog: *"OSHA compliance intelligence"*). Today's determination remains a Safety-Manager decision recorded through the existing `PATCH /api/incident-cases/{id}` route.

## Rollback impact on regulatory review

Rollback of Track 19.35 (removal of the Field Facts + Closeout tabs) has **zero effect** on any regulatory review surface. All OSHA / WC / agency / RCA / CAPA capture continues through the tabs shipped in prior tracks.

## Verdict

🟢 **Regulatory review architecture is preserved and clarified.** Field users continue to be shielded from regulatory questions. Safety Managers continue to make determinations through existing certified routes.
