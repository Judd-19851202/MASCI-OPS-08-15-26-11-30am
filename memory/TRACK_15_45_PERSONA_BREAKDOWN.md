# TRACK 15.45 · Persona Breakdown

**Date:** 2026-06-19
**Mode:** AUDIT ONLY

Per-persona friction inventory. Each entry references its row in the Top-25 register.

---

## 1 · Superintendent

| Workflow | Friction observed | Top-25 ref |
|---|---|---|
| Daily Report submission | Delay-cause taxonomy maintenance UI is admin-only and not discoverable | FR-09 |
| Safety Meeting attendee entry | One-by-one row entry · no bulk multi-select from employees collection | FR-07 |
| JHA crew acknowledgement (mobile) | Signature pad smaller than desktop · field workers complain | FR-08 |
| Team Assignment after-hours | History drawer admin-only · superintendents can't self-check team changes mid-day | FR-13 |
| Photo upload from iPad | Multi-photo selection works but no batch caption/tag UI | FR-14 |
| Time entry → DR pre-fill | Crew hours typed manually each day; equipment hours similarly | FR-15 |

---

## 2 · PM

| Workflow | Friction observed | Top-25 ref |
|---|---|---|
| Notification action label | Source-module chip helps (Track 15.40) but action verb often "Updated" — too generic | FR-03 |
| Multi-notification triage | Mark-all-read clears everything but PMs often want to keep one or two pinned | FR-16 |
| Project crew compliance drill | Compliance page exists but PM has to filter by project manually each visit | FR-17 |
| Field Leadership review queue | Drill from notification works · the review form has multiple "Save & Next" patterns | FR-18 |
| Crew acknowledgement override | Override path exists but requires two confirmations and a reason | FR-19 |

---

## 3 · Safety

| Workflow | Friction observed | Top-25 ref |
|---|---|---|
| Safety meeting topic selection | Search-then-pick · no recent-topics shortcut · topics list grows over time | FR-20 |
| Multi-project meeting | One meeting per project · can't link a single meeting record to two project numbers | FR-21 |
| Incident → CAPA linkage | CAPA must be created separately and linked by ID · no inline "Create CAPA from this incident" shortcut | FR-22 |
| Equipment training expiry alert | Notification fires correctly · UI for "expires in 14 days" surfaces only on the document expirations page | FR-06 |
| Safety meeting attendee bulk-add | Documented HIGH friction · see Superintendent FR-07 | FR-07 |

---

## 4 · Shop

| Workflow | Friction observed | Top-25 ref |
|---|---|---|
| Shop-to-PM handoff timing | When a PM Work Order is scheduled, the PM sees a notification but no dedicated "incoming maintenance" surface on their project home | FR-04 |
| Unit history retrieval | Master History page works · clicking a unit from Equipment Dashboard requires 2 hops | FR-23 |
| Fuel/Lube visit recording | Form has many fields · field mechanics on iPads complain about scroll | FR-24 |
| Service truck reconciliation | Reconciliation UI is desktop-friendly but cramped on iPad portrait | FR-25 |

---

## 5 · Dispatch

| Workflow | Friction observed | Top-25 ref |
|---|---|---|
| Driver qualification expiration cadence | Configurable via env vars only · dispatchers can't see "expires in N days" inline on the driver profile | FR-06 |
| Haul ledger review | Works well · minor: row filtering UI doesn't persist across navigation | FR-11 |
| Day-1 debrief form | Multi-step · no auto-save between steps | FR-12 |

---

## 6 · HR

| Workflow | Friction observed | Top-25 ref |
|---|---|---|
| HR-incident attachment naming | Original filename retained · no template/prefix UI | FR-05 |
| HR safety records gating | Non-HR scope 403 message is generic | FR-10 |
| Compliance brief PDF retrieval | Works · PDF foundation v15.41.1 audit block (Track 15.42) | n/a (resolved) |
| Driver-qualification import | Existing import path; UX could surface validation errors per-row | FR-26 (LOW, not in Top-25) |

---

## 7 · Executive

| Workflow | Friction observed | Top-25 ref |
|---|---|---|
| Jobs at risk single-screen | ✅ Closed in Track 15.44 (Executive Overview tiles) | resolved |
| Overdue items rollup | ✅ Closed in Track 15.44 | resolved |
| Staffing-issues callout | ✅ Closed in Track 15.44 | resolved |
| Unresolved actions composite | ✅ Closed in Track 15.44 | resolved |
| Executive Overview discoverability | Page lives at `/admin/executive-overview` · no nav entry from `LeadershipHubV2` yet | FR-01 |
| Verdict ribbon drill-back | Verdict RED/YELLOW/GREEN derives from deterministic rule · operators can't yet see "why RED" without scanning all 6 tiles | FR-02 |

---

🟢 **Per-persona breakdown complete. 25 active items ranked in the next deliverable.**
