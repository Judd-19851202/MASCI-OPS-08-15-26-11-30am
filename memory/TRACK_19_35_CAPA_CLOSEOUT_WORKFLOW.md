# TRACK 19.35 · CAPA & CLOSEOUT WORKFLOW

**Date:** 2026-07-03 · **Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md` · `TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md`

## Scope
Document the Corrective Action (CAPA) + Closeout workflow now visibly surfaced by the Track 19.35 Closeout tab in the Safety Case Workspace. Backend behavior is **unchanged** — this doc is a governance ledger.

## Lifecycle stages

```
FIELD SUBMIT  →  TRIAGE  →  INVESTIGATION  →  CAPA ASSIGNMENT  →  CLOSEOUT REVIEW  →  CLOSED
    ↑                                                                    ↑
    Field Facts tab (immutable anchor)              Closeout tab (Track 19.35 · visual gate)
```

## Stage responsibilities

| Stage | Owner | Workspace surface | Track that shipped it |
|---|---|---|---|
| Field submit | Field | `/incidents/report` (public) | Track 19.16 + 19.34 doctrine banner |
| Triage | Safety | Case Header · Case Health widget | Track 19.16 + 19.18 |
| Investigation | Safety | Timeline · Evidence · Witnesses · Medical · Police/Agency tabs | Track 19.16 |
| RCA | Safety | Root Cause tab (RCA panel) | Track 19.16 |
| CAPA assignment | Safety | Corrective Actions tab | Track 19.16 |
| Closeout review | Safety | **Closeout tab (NEW · Track 19.35)** | Track 19.35 |
| Final closure | Safety | Executive header state transition (existing) | Track 19.16 |

## CAPA workflow (unchanged)

- **Create:** `POST /api/incident-cases/{id}/corrective-actions` — Safety Manager assigns a CAPA with `title`, `action_class`, `assigned_to_name`, `due_at`.
- **Verify:** `POST /api/corrective-actions/{action_id}/verify` — Safety Manager marks a completed CAPA verified.
- **States:** OPEN → IN_PROGRESS → COMPLETED → VERIFIED (terminal) · or CANCELED.
- **UI surface:** Corrective Actions tab renders each CAPA card with a Verify button (existing behavior).

Track 19.35 **does not modify** any CAPA state machine, API, or button.

## Closeout tab — what it does (and does not do)

**Does:**
- Renders a 5-item **visual checklist** auto-checking green when the underlying collection has entries.
- Shows current case status (from `caseDoc.status`).
- Provides a short guidance line reminding the Safety Manager that final closure is set from the Executive header.

**Does NOT:**
- Write to backend.
- Change case status.
- Change CAPA state.
- Send emails.
- Trigger notifications.
- Alter the audit ledger.
- Present a "Close case" button.

The Closeout tab is a **read-only integrity mirror** — a visible summary of what other tabs have already captured.

## Checklist logic (line-for-line)

```jsx
<li>Evidence collected                    ← (evidence.length || 0) > 0
<li>Witness statements recorded           ← (witnesses.length || 0) > 0
<li>Root cause / findings documented      ← !!caseDoc?.safety_block?.root_cause
<li>Corrective actions assigned           ← (capa.length || 0) > 0
<li>Regulatory / agency contacts logged   ← (agency.length || 0) > 0
```

Each item renders a `CheckCircle2` icon that is `text-emerald-600` when the condition passes and `text-slate-300` when it does not. A trailing `"✓"` glyph is appended when the condition passes.

## Why every checklist item passes when the underlying collection has entries

The Closeout tab is deliberately permissive: **presence** of an entry is treated as "the Safety Manager captured something in that area." Whether the content is *sufficient* remains a human judgement. This is consistent with the Case Health widget (Track 19.18) which surfaces blockers but never blocks the state transition itself.

**Rationale:** hard-blocking closure on a boolean checklist would over-fit the reality of construction incidents where, for example, no witness is possible (solo operator), no medical is needed (near-miss), or no agency contact is required (property damage on private site). The five checklist items are guides, not gates.

## Final closure remains where it already lives

Track 19.16 shipped case state transitions through the Executive header (existing). Track 19.35 does not touch that surface. A Safety Manager still moves the case to `CLOSED` from the Executive header — the Closeout tab merely shows what is (or is not) already populated to help them make that call.

## Audit trail

Every state transition, CAPA verification, evidence upload, witness update, and safety-block patch continues to append to `incident_case_audit` (existing behavior). Track 19.35 introduces **no new audit reasons.**

## Rollback

Removing the Closeout tab is a 3-step revert:
1. Delete the `closeout` entry from the `TABS` array (1 line).
2. Delete the `{tab === "closeout" && ( … )}` render block (~20 lines).
3. Remove the `CheckCircle2` icon import if no other surface needs it (it is used elsewhere — likely no-op).

Rollback confidence: **HIGH.**

## Verdict

🟢 **CAPA workflow untouched. Closeout tab is a visual mirror of existing state.** Zero drift.
