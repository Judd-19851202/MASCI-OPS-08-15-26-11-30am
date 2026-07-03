# TRACK 19.35 · SAFETY CASE WORKSPACE INVESTIGATION UPGRADES (PHASE 2 OF INCIDENT INTELLIGENCE ENGINE)

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillars Aggregate: 58/60 · Production Strong**
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md` · `TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md` · `TRACK_19_34_INCIDENT_FIELD_INTAKE_MODERNIZATION.md`

## Charter
Turn the Safety Case Workspace from a functional record view into a **guided investigation workspace** anchored by an immutable Field Facts view and closed by a Closeout checklist. Track 19.16 (Phase C) shipped the workspace foundation with 10 tabs; Track 19.35 adds the missing "anchor" and "closer" tabs so the case lifecycle is visibly complete.

## What was already in place before Track 19.35
Per `SafetyCaseWorkspace.jsx` (Track 19.16 Phase C · Track 19.18 Operational Readiness polish):
- 10 tabs: Timeline · Evidence · Witnesses · Medical · Police/Agency · Root Cause · Corrective Actions · Communications · Safety Tasks · Linked Records.
- Blocker jump-to-tab from Case Health widget (`BLOCKER_TAB`).
- Executive Snapshot side panel.
- Case story · next action.
- Bilingual via `useT()`.
- API surface via `caseWorkspaceApi.js` — evidence · witnesses · medical · agency · communications · tasks · corrective actions · safety-block update.

## What Track 19.35 adds

### 1 · Field Facts tab (immutable anchor · first tab · default landing)
- New tab key `field_facts`, icon `Lock`, first in the tab strip.
- **Default `useState` tab is now `field_facts`** — every Safety Manager opening a case starts by reviewing the immutable field report before jumping into investigation.
- Renders a locked-record banner: *"Original Field Report — locked record. Facts captured by the field. Cannot be edited from the Safety workspace. Investigation notes, root cause, and OSHA review are recorded in the other tabs."*
- Displays incident type · occurred-at · reporter · location · summary · immediate actions.
- **No edit affordances.** Any correction goes through the audit-tracked case-patch API, not directly into the field record.

### 2 · Closeout tab (final tab · lifecycle closer)
- New tab key `closeout`, icon `CheckCircle2`, last in the tab strip.
- Renders a checklist confirming: evidence collected · witness statements recorded · root cause documented · corrective actions assigned · regulatory/agency contacts logged.
- Each checklist item auto-checks (✓) when the underlying collection has entries.
- Shows current case status; notes that final closure is set from the Executive header (existing surface).

### 3 · Preserved 10 investigation tabs
All existing tabs (Timeline · Evidence · Witnesses · Medical · Police/Agency · Root Cause · Corrective Actions · Communications · Safety Tasks · Linked Records) are unchanged. Zero behavior drift.

## Conceptual mapping (spec's 7 areas → shipped 12 tabs)

Track 19.35 spec asks for 7 conceptual areas; the shipped implementation delivers **12 tabs** that cover the same 7 areas more granularly. See `TRACK_19_35_CASE_WORKSPACE_INVESTIGATION_UPGRADES.md` § "Conceptual mapping" companion table.

| Spec area | Shipped tab(s) |
|---|---|
| Field Facts | **Field Facts** (new · immutable) |
| Investigation Notes | Timeline (chronological events + investigator notes) |
| Evidence | Evidence · Witnesses · Medical |
| Regulatory Review | Police/Agency · Communications |
| Findings | Root Cause · Safety Tasks |
| CAPAs | Corrective Actions |
| Closeout | **Closeout** (new · checklist) |

## Files touched
| File | Type | Δ |
|---|---|---|
| `frontend/src/pages/SafetyCaseWorkspace.jsx` | edit | +1 icon import (`Lock`) · +2 TAB entries · +1 default-tab change · +2 render blocks (Field Facts + Closeout) |

**Backend files touched: 0.**

## Rollback
- Revert 4 sections in `SafetyCaseWorkspace.jsx`: `TABS` array (remove field_facts + closeout entries) · default-tab literal (`"field_facts"` → `"timeline"`) · Field Facts render block · Closeout render block.
- No file-level deletion required.
- No state migration.
- **Rollback confidence: HIGH.**

## Six Pillars
See `TRACK_19_35_QUALITY_GATE_CLOSEOUT.md`. Aggregate **58/60 · Production Strong**.
