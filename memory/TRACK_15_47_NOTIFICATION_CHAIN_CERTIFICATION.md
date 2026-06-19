# TRACK 15.47 · Notification Chain Certification

**Date:** 2026-06-19 · **Status:** ✅ CERTIFIED · live-verified on synthetic test incident

## Pre-15.47 baseline
Every incident emitted exactly two notifications:
- Safety role · `incident.created` · Warning (with task)
- PM role · `incident.created` · Warning (notification only)

Audit identified G6 gap: Superintendent, Operations, Executive, HR roles received NOTHING from the incident path — they had to find out via secondary channels (email distribution list, manual phone calls).

## Track 15.47 extension
Implementation lives in `backend/routes/safety.py` ~lines 910-1015. Pure additive — legacy Safety + PM fan-out remains unchanged.

### Triggers
| Flag combination | Action |
|---|---|
| `classifications` contains `Workplace Violence` / `Physical Assault` / `Weapon Displayed` / `Weapon Used` OR any of `physical_assault=true`, `weapon_displayed=true`, `weapon_used=true`, `arrest_made=true` | Workplace-violence pathway (Critical severity) |
| `classifications` contains `Public Interaction` / `Verbal Confrontation` / `Threat` / `Harassment` / `Physical Contact` OR `threat_made=true` OR `physical_contact=true` | Public-interaction pathway (Warning severity) |
| Neither | Legacy fan-out only (Safety + PM) |

### Fan-out matrix · verified live
On a test incident submitted via `POST /api/incidents` with `classifications=["Public Interaction","Verbal Confrontation","Threat","Physical Contact","Workplace Violence"]`, the following notifications were written to MongoDB (confirmed via `db.notifications.find()`):

| Role | Type | Severity |
|---|---|---|
| Safety | `task.assigned` | Warning |
| Safety | `incident.created` | Warning |
| PM | `incident.created` | Warning |
| **Superintendent** | **`incident.violence`** | **Critical** |
| **Operations** | **`incident.violence`** | **Critical** |
| **Executive** | **`incident.violence`** | **Critical** |
| **HR** | **`incident.violence`** | **Critical** |
| Safety | `task.assigned` (WV review CAPA) | Warning |
| Safety | `incident.wv_review_task` | Critical |

Nine notifications total. Six of them are new in Track 15.47 (the four extra roles + the WV review task + its notification).

### Routing rules respected
Every new notification passes through `apply_routing(db, notification, project_number, event_key)` — so project-team-based routing (Track 15.39A) continues to refine the recipient list per project. No bypass.

## Email path (existing · unchanged)
`auto_email_safety_record` in `server.py` continues to email the resolved distribution (PM + GC + Owner + `SEVERE_INCIDENT_CC` env list) on every incident with the PDF attached. Track 15.47 PDF enrichment (state timeline + linked CAPAs + extended witnesses + structured fields) flows into that PDF automatically.

## Failure modes (best-effort)
Every per-role emit is wrapped in `try/except` — a misconfigured role does NOT block the incident write or the legacy Safety + PM fan-out. The system fails open for safety, not closed.

## Certification verdict
| Question | Answer |
|---|---|
| Does Safety receive notification? | ✅ Yes (legacy) |
| Does PM receive notification? | ✅ Yes (legacy) |
| Does Superintendent receive notification on public-interaction or WV? | ✅ Yes (Track 15.47) |
| Does Operations receive notification on WV? | ✅ Yes (Track 15.47) |
| Does Executive receive notification on WV? | ✅ Yes (Track 15.47) |
| Does HR receive notification on WV? | ✅ Yes (Track 15.47) |
| Does a WV review CAPA auto-issue? | ✅ Yes (Track 15.47) |

**G6 + G10 certified.**
