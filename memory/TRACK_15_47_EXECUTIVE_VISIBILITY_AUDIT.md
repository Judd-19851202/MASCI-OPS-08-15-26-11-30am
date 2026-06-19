# TRACK 15.47 · Executive Visibility Audit

**Status:** ✅ AUDIT COMPLETE · gaps documented · no executive tiles built this track (per user directive 2A).

## What executive visibility already exists (post-Track 15.44)
The Executive Overview at `/admin/executive-overview` carries a single tile for incidents:

- **Tile name:** `unresolved_incidents` (count)
- **Threshold:** > 10 = contributes to RED verdict
- **Source:** `db.incidents.count_documents({"resolution_status": {"$in": ["open","investigating"]}})`
- **Display:** integer count only · no breakdown · no time-window filter · no severity filter · no classification filter
- **Verdict line (Track 15.46 FR-02):** "N unresolved incidents (threshold > 10)" appears as a reason bullet when the threshold is crossed

This is sufficient for the question "do we have an incident backlog?" — it is NOT sufficient for the executive-level questions the user enumerated.

## Executive questions audited against current visibility

| Q | Answer today | Gap |
|---|---|---|
| How many incidents this month? | ❌ NO — only "unresolved" snapshot, no time window | Add a 30-day count tile |
| Open investigations (state=investigating)? | ❌ NO — collapsed into `unresolved_incidents` | Split tile by state |
| Open CAPAs (count + overdue count)? | ❌ NO — separate query required | Add a CAPA-status tile |
| Violence-related incidents (any time)? | ❌ NO — `classifications` not aggregated | Add a "Workplace Violence" classification tile |
| Public-interaction incidents (any time)? | ❌ NO — same gap | Same tile |
| Incidents with police involvement? | ❌ NO — `police_called` not aggregated | Optional fourth tile or merge into above |
| Incidents with media exposure (filmed / social)? | ❌ NO — `media_filmed` / `social_media_posted` not aggregated | Optional fifth tile |
| Average days-to-close per incident? | ❌ NO | Out of scope for this track |

## Documented gap list (G6 follow-up · NOT built this track)

| Gap | Source data exists? | Proposed tile name | Threshold suggestion |
|---|:---:|---|---|
| Incidents (30-day window) | ✅ `incidents.created_at` indexed | `incidents_30d` | > 5 → YELLOW · > 15 → RED |
| Open investigations | ✅ `incidents.resolution_status="investigating"` | `incidents_investigating` | > 3 → YELLOW |
| Workplace Violence incidents (90-day) | ✅ `incidents.classifications` array · `physical_assault` / `weapon_*` flags | `wv_incidents_90d` | ≥ 1 → RED |
| Public-Interaction incidents (30-day) | ✅ same source | `public_interaction_30d` | > 2 → YELLOW |
| Overdue CAPAs | ✅ `corrective_actions.due_date < today` AND `status != closed` | `overdue_capas` | > 3 → RED (already in 15.44) |
| Average time-to-close | ✅ derivable from `incidents.created_at` + `incident_state_events` | `avg_close_days` | > 30 → YELLOW |

All six tiles are additive over the existing `executive_overview` route (`backend/routes/executive_overview.py`). None require a new collection. None require a new background job. The existing aggregation pattern (`db.incidents.aggregate([...])`) handles all six.

## Why no tiles were built this track (per user directive 2A)
The user's directive was explicit: **"We've already spent a lot of time on Executive Overview. Let's determine whether there is actually a gap before adding anything."** The audit determined there IS a gap (6 tiles' worth) and documented it. Building the tiles is deferred to a dedicated track that the user can prioritize on its own merits.

## Recommendation for next Executive Overview track
Either:
- Bundle all 6 tiles as Track 15.48 (~3-4 hours work + cert), OR
- Add just `wv_incidents_90d` + `public_interaction_30d` as a 30-minute change to the existing Executive Overview if the trigger event has elevated executive concern.

## Notification path covers the most urgent gap
Importantly: even without exec-overview tiles, the Track 15.47 G6/G10 fan-out delivers **Critical-severity** in-app notifications to the Executive role on every WV incident. The bell + email pipeline gives the executive eyes-on within minutes of submission. The dashboard tiles would be a faster scan; the bell is already there.

## Sign-off
Executive visibility audit complete. 6 specific tiles identified, documented, deferred to a dedicated track. The most urgent visibility gap (real-time exec notification on WV) is closed by Track 15.47 G6 + G10.
