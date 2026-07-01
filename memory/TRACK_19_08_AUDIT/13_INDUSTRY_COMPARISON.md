# TRACK 19.08 · Industry Comparison Report

Benchmark scan (July 2026) against mature operational inspection platforms. **We do not copy.** We benchmark our surface behaviour against the industry-standard patterns operators already know.

Sources: HCSS HeavyJob / Equipment360; Raken; Procore; B2W Track; Fleetio; Samsara; MaintainX; Tenna; Motive.

---

## 1 · Pattern-by-pattern benchmark

| Pattern | Industry standard (2026) | MASCI current state | Delta | Priority for redesign |
| --- | --- | --- | --- | :---: |
| **Progressive disclosure on inspections** | Section-by-section unlock; only failed items expand for photo/comment ("3-Click Inspection" — Fleetio / Samsara / MaintainX). | Daily Report: **done (Track 19.06/19.07)**. Equipment Pre-Op / DVIR / Incident: **flat forms**. | High on Pre-Op/DVIR/Incident | P0 |
| **QR / RFID asset-binding** | HCSS HeavyJob QR-scan loads the exact form for the exact asset; Tenna RFID similar. | Manual asset selection via `EquipmentCombo` on every form. | Moderate — asset-bound form-loading not wired | P2 |
| **Smart Pass defaults (AI-assisted)** | Fleetio Service Advisor / Samsara AI: pre-select "Pass" based on prior inspection + fault codes; user only touches deltas. | Smart Prefill exists on Daily Report (crew + time pattern, Track 19.06 amendment). NOT applied to Equipment/DVIR yet. | Moderate — pattern proven internally on DR | P1 |
| **Photo required for failure** | Samsara / MaintainX: submit disabled until photo attached to failed item; prevents pencil-whip. | Equipment/DVIR: photos are supported but *not required at defect level*; DR: 6-photo global minimum. | Medium — item-level photo requirement absent | P1 |
| **Closed-loop OOS / defect → work-order** | Fleetio+Samsara/Motive: DVIR defect auto-syncs to work-order; resolution auto-syncs back. | Backend HAS this loop (`fleet_defects` → `/shop/fleet/defects/*` → dispatch OOS). UI does NOT confirm the loop to the operator at submit-time. | High — trust drift | P0 |
| **Geo-tag + timestamp verification** | Samsara / Raken: pencil-whip detection via location + duration heuristics. | GPS captured on DR; **not systematically captured on Equipment/DVIR/Meeting**. Timestamp always captured. | Moderate | P1 |
| **Visual defect selection** | Raken: tap-on-diagram of vehicle/machine to mark a defective part. | Text-only checklist grid. | Low priority — nice-to-have for 2027 | P3 |
| **Offline-first** | Universal — all platforms function offline, sync silently. | Autosave present; enqueue-upload present (`enqueueUpload` lib). Draft-store actor-scoped from Track 19.04. | Parity | ✅ |
| **Photo compression + GPS/timestamp/item tagging** | Universal. | Photo pipeline tags GPS/timestamp; **item-level tagging is inconsistent across forms**. | Moderate | P1 |
| **AI-guided coaching from historical patterns** | Fleetio Service Advisor; Samsara AI Guided Coaching. | Not present. | High opportunity — but P3 | P3 |
| **Pencil-whip detection heuristics** | Samsara: flags 100% "pass" streaks; time-to-completion outliers. | No such heuristic on any form. | Moderate | P2 |
| **Contextual "why" text for policy items** | Ideagen / Samsara: inline "why this item exists" text-on-tap. | Present via `<LifecycleGuide>` / `<HelpTipBlock>` but stacked (see duplicate report). | Parity but noisy | Consolidate in P1 |
| **Signature capture with legal-defensibility metadata** | Universal — signer identity + timestamp + IP + device fingerprint. | Signatures collected; not all forms carry the full metadata bundle. Trust-spine covers most. | Moderate | P2 |
| **Live-fired confirmation of downstream commitments** | Fleetio/Samsara: submit screen tells operator which work-orders, notifications, and emails were dispatched. | Zero such feedback. | High operator-trust gap | P0 |

---

## 2 · What we already do BETTER than the industry standard

* **Trust Spine** — every operational event flows through `audit_events` with correlation ids. Fleetio+Samsara relies on the vendor's internal log; MASCI's audit trail is user-inspectable.
* **Actor-scoped drafts** (Track 19.04) — no other platform in this benchmark isolates drafts per device + actor + role at this granularity. This is a genuine MASCI advantage.
* **Six mental checkpoints on the Daily Report** (Track 19.07) — Raken uses "Day Sheet" chronology; nobody frames the DR by *cognitive checkpoint*. This is a differentiator.
* **HR canonical roster propagation** (Track 19.03) — every employee picker reads from a single source of truth. Most competitors have per-portal shadow copies.
* **Heavy-civil-native excavation form** — `trench_excavations` with linked `linked_excavation_ids[]` on DRs. HCSS is the only competitor at parity; B2W nearly so; nobody else.

---

## 3 · What we do WORSE than the industry standard

* **Equipment Pre-Op form density** — competitor forms are section-by-section; ours is flat. See `12_UX_FRICTION_REPORT.md` §3.
* **No live confirmation of the fail cascade** — competitors show "Work order #1234 created · sent to shop foreman Jane" on submit. See `07_FAIL_CASCADE_ANALYSIS.md`.
* **Coaching-panel stacking** — competitors use a single collapsible help drawer; we have three overlapping helper systems (`LifecycleGuide`, `HelpTipBlock`, section-header prose). See `11_DUPLICATE_LOGIC_REPORT.md`.
* **Safety Meeting = attendance-only** — competitors capture attendance AND a knowledge-check ("what will you do differently today?"). We don't. See `11_SAFETY_MEETING_FORENSICS.md`.
* **Photo requirement at defect level** — universal in industry; missing from our Equipment/DVIR forms.

---

## 4 · Redesign guidance (informational — NOT prescriptive)

Applying the industry pattern to MASCI's already-strong data model:

* Reuse **Track 19.06's PresenceGate** primitive across Equipment Pre-Op and DVIR — proven internally.
* Reuse **Track 19.06 Amendment's `_prefilled`** marker on Equipment defects to bring Smart Defaults parity with Fleetio's Service Advisor.
* Wire **submit-time toast** listing: "PDF #1234 rendered · shop ticket #FD-9876 opened · foreman Jane notified · DVIR mirrored to Motive." Ten lines of UI, matches industry standard, closes the trust gap without any schema drift.

None of this is executed in Track 19.08.
