# TRACK 19.35 · FIELD FACTS IMMUTABILITY

**Date:** 2026-07-03 · **Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md` · `TRACK_19_34_FIELD_VS_SAFETY_PROTECTION.md`

## Doctrine

> **Field captures facts. Safety investigates.**
>
> The original field report is a **locked record.** It is the ground truth of what the person on the ground said, when they said it. It is never edited from inside the Safety Case Workspace. Any correction, clarification, or additional finding is captured in an investigation-owned tab (Timeline · Evidence · Witnesses · Medical · Police/Agency · Root Cause · Corrective Actions · Communications · Safety Tasks · Linked Records) — never by mutating the field report.

## Why immutability matters

- **Legal / OSHA integrity.** The original narrative from the field is what auditors, insurers, and OSHA investigators trust. If Safety could edit it, the record loses its evidentiary weight.
- **Trust of the reporter.** Foremen, drivers, and laborers write in plain language under pressure. If they knew their words could be rewritten after the fact, they would stop writing them.
- **Trust Spine.** Every downstream artifact (executive PDF · cross-portal reads · CAPA linkage) reads the same immutable field block. Editing it breaks time-machine reads.
- **Root cause discipline.** A shifting field narrative makes root cause analysis meaningless. Immutability forces investigators to reason about the facts as they were reported, and to document their reasoning in the investigation tabs.

## What "immutable in the Safety workspace" means (implementation)

The Track 19.35 **Field Facts** tab is:
- **First tab in the tab strip** — the visible anchor.
- **The default tab on open** (`useState("field_facts")`) — every Safety Manager begins by re-reading what the field said.
- **A `<dl>` display grid** — no `<input>`, `<textarea>`, `<select>`, `<button type="submit">`, or edit-mode toggle inside the panel.
- **Wrapped in a locked-record banner** with the `Lock` icon and the sentence *"Original Field Report — locked record. Facts captured by the field. Cannot be edited from the Safety workspace. Investigation notes, root cause, and OSHA review are recorded in the other tabs."*

## What the Field Facts panel renders

| Field | Source |
|---|---|
| Incident type | `caseDoc.incident_type` → `INCIDENT_FLOWS[type].label` (bilingual via `useT()`) |
| Occurred at | `caseDoc.occurred_at` (formatted via `_fmt`) |
| Reporter | `caseDoc.reporter_name` |
| Location | `caseDoc.location` (falls back to `caseDoc.gps`) |
| Summary | `caseDoc.summary` (falls back to `caseDoc.description`) — `whitespace-pre-line` preserved |
| Immediate actions | `caseDoc.immediate_actions` — `whitespace-pre-line` preserved |

Every value is read-only. Any missing value renders as `—` (existing empty-state convention). No affordance to change any of them.

## Where corrections go instead

If, during investigation, Safety discovers the field report was materially wrong (e.g. wrong reporter name, wrong location, wrong occurred-at), the correction is captured through **existing** audit-tracked surfaces:

- **Timeline tab** — chronological investigator note with actor · timestamp · reason.
- **Case-patch API** (`api.updateSafetyBlock` · `PATCH /api/incident-cases/{id}`) — mutates `safety_block.*`, never `field_block.*`.
- **Audit ledger** (`incident_case_audit`) — every patch is append-only and recoverable.
- **Executive Snapshot** — surfaces the currently-known truth without erasing the original narrative.

The field block itself remains byte-identical to what was submitted.

## Grep invariant (mechanically enforced by the lock test)

The following patterns MUST NOT appear inside the `field_facts` panel of `SafetyCaseWorkspace.jsx`:

- `<input`
- `<textarea`
- `<select`
- Any `onClick` that calls a mutation API (`api.updateFieldBlock`, `api.patchFieldBlock`, `PATCH /api/incident-cases`).
- Any "Edit" · "Save" · "Update" · "Submit" button targeting the field block.

The lock test grabs the panel block (opening `{tab === "field_facts" &&` to closing `)}` before the next tab check) and greps for those tokens.

## Six Pillars implications

- **Powerful** — same immutable field record now powers every downstream investigation surface; no re-entry needed.
- **Simple** — one tab, one banner, one `<dl>` grid. Zero decisions for the user.
- **Beautiful** — calm slate palette · single lock icon · fits the existing workspace chrome.
- **Trusted** — the doctrine is visually and mechanically enforced.
- **Proven** — lock test greps for edit affordances; frontend lint clean.
- **Operational** — same bilingual engine · mobile responsive · zero perf change.

## Rollback

Removing the Field Facts tab returns the workspace to the pre-19.35 shape:
1. Delete the `field_facts` entry in the `TABS` array (1 line).
2. Change the default `useState` from `"field_facts"` back to `"timeline"` (1 char).
3. Delete the `{tab === "field_facts" && ( … )}` render block (~19 lines).
4. Remove the unused `Lock` icon import if no other panel needs it.

Rollback confidence: **HIGH.** No schema · no route · no payload · no state migration.

## Verdict

🟢 **The Field Facts tab is immutable by construction, by grep, and by doctrine.**
