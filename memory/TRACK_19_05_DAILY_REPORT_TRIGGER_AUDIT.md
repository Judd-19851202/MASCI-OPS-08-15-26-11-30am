# Track 19.05 · Daily Report Trigger / Conditional Audit

Every Yes/No gate and its downstream effects. Source: `NewDailyReport.jsx` conditional blocks + backend `create_daily_report` gates.

## Section 02 — Weather

| Trigger | Reveals | Blocks submit? | Routes to |
| --- | --- | --- | --- |
| `weather_impact = "Yes"` | `weather_impact_notes` textarea | No | PDF + PM lifecycle timeline |

## Section 03 — Safety triggers (nested cascade)

| Trigger | Reveals | Blocks submit? | Downstream |
| --- | --- | --- | --- |
| `safety_incidents_today = "Yes"` | `input-incident-notes` + escalation block | No | Advisory RFI flag |
| `injuries_reported = "Yes"` | `safety-escalation-block` → `safety_notified` cascade | No | Advisory RFI + safety routing |
| `safety_notified = "No"` | `safety-not-notified-warning` (calm) | No | UI warning only |
| `safety_notified = "Yes"` | `input-safety-contact-person`, `input-safety-contact-time` | No | Recorded on doc |
| `incident_report_filled = "No"` when injury | `incident-report-required-warning` + `open-incident-form-link` | No | Prompts nav to `/safety/incident/new` |
| `incident_report_filled = "Yes"` | `input-incident-report-time` | No | Recorded |
| `schedule_delays = "Yes"` | `schedule_delays_notes` | No | Advisory schedule-impact flag |

## Row-based sections (implicit trigger via section expansion)

Row-based sections covered: `masci_crews[]`, `subcontractors[]`, `equipment[]`, `materials[]` (inbound deliveries), `outbound_materials[]`, `visitors[]`. CollapseCard state (`iter383 · Phase 5C.1`) determines whether the section is expanded, but does NOT alter the persisted doc — an empty array is valid.

| Section trigger | Effect | Submit gate |
| --- | --- | --- |
| Crew section expanded | Reveals crew rows via `Add Crew Member` | No REQ |
| Subcontractors expanded | Reveals sub rows | No REQ |
| Equipment expanded | Reveals equipment rows | No REQ |
| Materials Delivered expanded | Reveals inbound rows | No REQ |
| Outbound Materials expanded | Reveals outbound rows | No REQ |
| Visitors expanded | Reveals visitor rows | No REQ |

## Section 10 — Production / Delays

| Trigger | Effect |
| --- | --- |
| Add production row | Pushes into `production[]` |
| Add constraint (delay) row | Pushes into `constraints[]`; server derives `may_require_rfi` + `may_affect_schedule` via `_derive_advisory_flags` heuristic |

## Trench excavation gate (backend)

| Trigger | Effect | Blocks submit? |
| --- | --- | --- |
| `excavation_activity_today = "Yes"` with empty `linked_excavation_ids[]` | Server returns HTTP 422 `excavation_record_required` | **YES — HARD BLOCK** |

## Photo minimum gate

`data.photos.length < photo_min (6)` — submit gate footer shows "NEED N MORE PHOTOS TO SUBMIT" and disables the submit button.

## Draft / Prefill triggers

* Actor auth fingerprint match → `pendingDraft` surfaces via `DraftRestorePrompt`.
* Project pick via `applyJob` → `smartPrefillOffer` chip if `/recent-context` returns crew + equipment AND local sections empty.
* No project + no draft AND `hasStalePriorUsage("daily-report-new")` → PriorUsageBanner (soft reassurance only).
* 24 h archive entry present → `DraftRecoveryNotice`.

## Cross-form routing triggers

* Injury reported + incident_report_filled = No → deep link to Incident form.
* Excavation Activity Today → mandatory link to trench excavation record.
* Distribution list → additional email recipients appended at auto-email.

## Redesign risk

* HIGH — safety trigger cascade (Section 03) has legal + insurance implications. Any Yes/No relabelling must preserve semantic mapping.
* HIGH — excavation activity gate (server 422). Redesigning the trench flow must keep the backend contract or update both.
* MEDIUM — photo_min gate. Any change to the minimum must be coordinated with PM/email PDF expectations.
