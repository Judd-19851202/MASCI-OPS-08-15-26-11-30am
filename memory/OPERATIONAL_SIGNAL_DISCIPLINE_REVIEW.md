# Operational Signal Discipline Review · Phase 7 · WS3

**Date:** 2026-05-24
**Purpose:** Catalog every signal the platform raises (banner, badge, finding, notification, modal, toast) and assign each one to keep / suppress / aggregate / downgrade / elevate. Anchored to the existing `NOTIFICATION_DISCIPLINE_MATRIX.md` and the operational glossary.

**Goal:** Keep critical signals critical. Quiet everything else. Defeat signal fatigue before it starts.

---

## Categorization rules

| Category | Rule |
|---|---|
| **KEEP** | Already correctly placed; no action. |
| **SUPPRESS** | Currently fires but adds no operational value; remove or hide. |
| **AGGREGATE** | Multiple firings should roll into one digest item. |
| **DOWNGRADE** | Currently CRITICAL or modal; should be quiet badge / digest only. |
| **ELEVATE** | Currently quiet; needs more visibility for the right audience. |

---

## Banner / inline signals

| Signal | Where | Status | Action |
|---|---|---|---|
| Phase 5D Follow-Up Required rose banner | `ViewIncident.jsx` | Severity-gated; CTA + glossary link | KEEP |
| Phase 5D Investigation Open amber banner | `ViewIncident.jsx` | Live-derived from linked CAPAs | KEEP |
| Phase 5D Operationally Complete emerald | `ViewIncident.jsx` | Live-derived | KEEP |
| Phase 6 incident completion summary | `NewIncident.jsx` (above submit) | 4-state rose/emerald/slate; field-direct prompt | KEEP |
| Phase 6 daily completion summary | `NewDailyReport.jsx` (above submit) | Signal-driven gaps + filled-section count | KEEP |
| LifecycleGuide (8 variants) | various detail pages | Concise; bilingual; print:hidden | KEEP |
| Payload-heavy attachment warning | Daily report | Amber soft warning at ≥ 30 attachments | KEEP |
| Memorial Day remembrance modal | Public hub | Dismissable; date-gated | KEEP (cultural, intentional) |
| "X more photo(s) before you can submit" | Incident + Daily | Red bold uppercase | KEEP — but consider rose tone in future polish cycle |
| Severity-escalation auto-incident proposal | Daily report Section 03 | Triggers an incident draft | KEEP |
| Per-section "Optional / N entered" pill | CollapseCard | 4 tone variants (slate/amber/emerald/rose) | KEEP |
| Idempotency duplicate-submit toast | All public forms | Quiet info toast | KEEP |
| Draft-recovery toast | NewDailyReport + NewIncident | Surfaces only when a draft exists | KEEP |
| Autosave indicator | useDraftSync | Quiet text "Draft saved · X ago" | KEEP — verify visible at 390 px |
| Sign-in attempt rate-limited toast | Login pages | Captcha-grade messaging | KEEP |
| Portal Access Restricted card | RequireSafety/RequirePm/etc | Clear; offers other-portals links | KEEP |

**No banner suppression or aggregation needed.** The banner discipline is already tight.

---

## Bell / notification signals (per `NOTIFICATION_DISCIPLINE_MATRIX.md`)

| Signal | Tier | Current routing | Action |
|---|---|---|---|
| Incident · severity ≥ medical | CRITICAL | Safety + PM + HR + email (if AUTO_EMAIL_REPORTS) | KEEP |
| Incident · near-miss / first-aid | IMPORTANT | Safety + PM bell + digest | KEEP |
| CAPA assigned | IMPORTANT | Assignee + Safety bell | KEEP |
| CAPA overdue | IMPORTANT | Assignee + Safety + Admin bell; re-fire 7d | KEEP |
| CAPA awaiting verification > 7 days | IMPORTANT | Safety + Admin | KEEP |
| Driver disqualified | CRITICAL | Dispatch + FL + HR + Safety bell | KEEP |
| Training expired | IMPORTANT | PM + HR + Safety weekly digest (aggregated) | KEEP |
| Training expiring 30 days | IMPORTANT | HR + Safety weekly digest | KEEP |
| PPE missing employee linkage | IMPORTANT | Safety governance digest (NOT bell) | KEEP |
| Daily report submitted | INFO | PM bell low-prominence | KEEP — verify low-prominence styling at 390 px |
| Safety escalation on daily report | CRITICAL | Safety + PM + Admin bell + email | KEEP |
| Governance · convergence score drop ≥ 10 | IMPORTANT | Admin digest | KEEP |
| Governance · new CRITICAL finding | CRITICAL | Admin + Safety bell + digest | KEEP |
| Backup verification failed | CRITICAL | Admin bell + dev hook; 24 h re-fire | KEEP |
| Auto-email failure (Resend bounce) | IMPORTANT | Admin bell | KEEP |
| PM portal: incident on assigned project | IMPORTANT | PM bell only | KEEP |
| FL portal: severe incident on watched project | IMPORTANT | FL bell via unified `/api/notifications` | KEEP (Phase 5D closure) |
| Record acknowledged | INFO | Original notifier bell | KEEP |
| Record archived | INFO | None (portal-only) | KEEP |

**No bell suppression or aggregation needed.** The 19-row matrix is correctly tiered.

---

## Governance findings (cross-portal contradictions)

| Finding | Severity | Aggregation | Action |
|---|---|---|---|
| `EMP_LINK_UNRESOLVABLE` (PPE issuance without master employee link) | warning | One per issuance | KEEP |
| `CAPA_AWAITING_VERIFICATION` (> 7 days in Pending Review) | warning | One per CAPA | KEEP |
| `INCIDENT_NO_CAPA` (serious incident with no linked CAPA) | critical | One per incident | KEEP |
| `DRIVER_QUAL_EXPIRED` (active driver, expired card) | critical | One per driver | KEEP |
| `IDENTITY_DRIFT` (employee name on records doesn't match master) | warning | Aggregated per employee | KEEP |
| `SAFETY_DR_INC_MISMATCH` (Daily Report safety incident with no /api/incidents record) | critical | One per pair | KEEP |
| `TRAINING_OVERDUE_ASSIGNED` (employee on active assignment with expired training) | warning | One per employee-training pair | KEEP |
| Convergence score drop ≥ 10 points | aggregated finding | Digest only | KEEP |

**Recommendation — DO NOT add new finding types until a 60-day live operations review of the existing 8.** Adding governance signals before validating the current set creates noise.

---

## Toast / modal signals

| Signal | Style | Action |
|---|---|---|
| Validation failure (missing required field) | Red toast | KEEP — already field-direct |
| Submit refused (Phase 6 Tier-2 guard) | Red 6 s toast | KEEP |
| Save success | Green toast | KEEP |
| Save failure (network) | Red toast w/ retry hint | KEEP |
| Draft recovered | Quiet toast with Discard action | KEEP |
| Confirm delete | Modal | KEEP — destructive actions need explicit confirm |
| Confirm severity downgrade on incident | Modal | KEEP |
| Logout | Sheet-style confirm | KEEP |

**No toast/modal change needed.**

---

## Aggregate behavior to keep watching post-deploy

1. **Daily Report submitted bell** — INFO tier. If PMs report bell fatigue from many DRs per project per week, consider aggregating by project per day. Watch first 60 days.
2. **CAPA overdue 7-day re-fire** — IMPORTANT tier. If overdue items pile up and re-fires become wallpaper, consider re-firing only when the CAPA crosses a new severity threshold (e.g., +14 days, +30 days).
3. **Governance digest weekly cadence** — IMPORTANT tier. Monday 14:00 UTC. If Safety reports they've stopped reading it, switch to "fire when convergence score drops" only. Watch first 90 days.

These are observation items, NOT change items. **No code change in Phase 7.**

---

## Signals NOT in the platform that should stay NOT in the platform

| Signal | Why we don't have it |
|---|---|
| "Crew member tagged in a photo" | Privacy, no operational value. |
| "PM didn't read daily report" | Surveillance optics; PMs read what they need to read. |
| "Foreman has filled 5 reports this week" | Gamification; the directive forbids it. |
| "Safety review took N days" | Performance theater; the data exists for audit but doesn't need a banner. |
| "Equipment used X% of time" | Analytics bloat; equipment master + DR rows answer the real questions. |
| Push notifications to phones | No SMS/push infrastructure; bell + digest is sufficient. |
| AI-suggested corrective actions | Encourages perfunctory CAPAs; Safety must think through each one. |

---

## Phase 7 verdict

The platform's signal discipline is mature. **No signal needs to be added, suppressed, aggregated, downgraded, or elevated in this sprint.**

Action: ship this document as the canonical reference. Re-read it at the 60-day and 90-day post-deploy marks before making any signal-level changes.
