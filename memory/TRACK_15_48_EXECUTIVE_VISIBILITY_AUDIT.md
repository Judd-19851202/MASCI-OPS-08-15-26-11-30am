# TRACK 15.48 · Executive Visibility Audit (Phase 6)

**Status:** ✅ AUDIT COMPLETE + SMALLEST-ADDITIVE FIX DELIVERED. Foundation bumped to v15.48.1.

## Pre-15.48 gap (carried from 15.47 audit)
Executive Overview tile `safety` returned a single `unresolved_incidents` count. No way to answer at a glance:
- "Have we had a Workplace Violence incident recently?"
- "Have we had a spike in public-interaction encounters?"

Track 15.47 audit documented this gap and deferred a build per user directive 2A. Track 15.48 closed it with the smallest possible additive change.

## What changed (smallest additive solution · no V2)
Single file: `backend/routes/executive_overview.py` (the existing Track 15.44 aggregator).

### Two new counts on the existing `safety` tile
- `wv_incidents_90d` · COUNT incidents in last 90 days where `classifications` includes any of `["Workplace Violence","Physical Assault","Weapon Displayed","Weapon Used"]` OR the boolean flags `physical_assault=true / weapon_displayed=true / weapon_used=true` are true.
- `public_interaction_30d` · COUNT incidents in last 30 days where `classifications` includes any of `["Public Interaction","Verbal Confrontation","Threat","Harassment","Physical Contact"]` OR `threat_made=true / physical_contact=true`.

### Verdict integration
- Any WV incident in last 90 days → forces verdict to RED + adds a `verdict_reasons` line.
- More than 2 public-interaction incidents in last 30 days → forces verdict to YELLOW + adds a `verdict_reasons` line.

### Frontend tile (existing Track 15.46 FR-02 surface)
- `ExecutiveOverview.jsx` safety tile now shows two new lines:
  - "**N** workplace-violence incidents (90d)" with red emphasis when N > 0
  - "**N** public-interaction incidents (30d)" with amber emphasis when N > 0
- testids: `tile-safety-wv` and `tile-safety-public-interaction`

## Live evidence
- `GET /api/admin/executive/overview` returns `foundation_version: "15.48.1"`.
- `wv_incidents_90d: 1` (the synthetic INC-2026-00488).
- `public_interaction_30d: 1`.
- `verdict: "RED"` (driven by units OOS, open CAPAs, AND the WV incident).
- `verdict_reasons` includes "1 workplace-violence incident(s) in last 90 days".

## What the audit deferred (per user directive 2A · NOT built)
The 15.47 audit identified six potential tiles. 15.48 added the two most urgent (WV + Public-Interaction) to the existing safety tile. The remaining four are documented for a dedicated track:
| Deferred tile | When to build |
|---|---|
| `incidents_30d` rolling | If exec wants throughput vs snapshot |
| `incidents_investigating` | If lifecycle bottleneck visibility becomes a concern |
| `avg_close_days` | If KPIs track close-out velocity |
| `overdue_capas` split tile | Currently bundled into safety; split if needed |

## Sign-off
GREEN. The two most-urgent executive visibility gaps from 15.47 are closed with the smallest possible additive change. No V2 system, no new endpoint, no new collection. The remaining 4 tiles are documented and deferred for explicit user prioritization.

## Six forensic questions
| Question | Answer | Evidence |
|---|---|---|
| Can leadership see workplace violence? | ✅ YES | `wv_incidents_90d` tile + verdict reason + Critical-severity notification (Track 15.47 G6) |
| Can leadership see public interaction incidents? | ✅ YES | `public_interaction_30d` tile + verdict reason |
| Can leadership see open investigations? | 🟡 PARTIAL | `unresolved_incidents` count exists; investigating-state split deferred |
| Can leadership see overdue CAPAs? | ✅ YES | Existing tile + verdict reason (Track 15.46 FR-02) |
| Can leadership see unresolved incidents? | ✅ YES | `unresolved_incidents` count |
| Can leadership see police-involved incidents? | 🟡 PARTIAL | Police fields per-incident exist but no aggregate tile · low priority because notification path covers urgency |

Three GREEN, two PARTIAL (deferred to dedicated track), zero RED.
