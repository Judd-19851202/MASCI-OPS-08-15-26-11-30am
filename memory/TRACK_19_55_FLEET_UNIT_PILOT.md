# TRACK 19.55 · Fleet Unit Thread — Pilot Specification

## Route
`/fleet/unit/:unit_number` — behind the existing Shop-portal auth gate
(same guard as Fleet Visibility).

## Entry points
- `Fleet Visibility` unit-card title (`fleet-unit-card-<unit>-open-thread`) — click the unit number to open the thread. Expansion chevron continues to work.
- Any future portal can deep-link to `/fleet/unit/<unit>` directly — Track 19.54 `guidanceMap.js` may be extended later to expose this as the Fleet-Intelligence deep-link.

## Data sources (all pre-existing)
- **`GET /api/assets/{unit_number}/timeline`** — Track 13.26 Asset Service Event Backbone. Certified single source of truth.
- **`GET /api/operational-intelligence/summary`** — filtered client-side to `fleet_intelligence`.

Both endpoints exist today. No new backend was added.

## Backbone event mapping (backbone → OperationalThread event schema)
| Backbone `event_type` | OperationalThread `kind` |
|-----------------------|--------------------------|
| `preop` / `dvir`      | `inspection`             |
| `defect`              | `safety`                 |
| `repair`              | `repair`                 |
| `oos`                 | `safety`                 |
| `assignment` / `transfer` | `assignment`         |
| `photo`               | `photo`                  |
| `document`            | `history`                |
| `po`                  | `po`                     |
| `incident`            | `incident`               |
| anything else         | `other`                  |

## Operational Health derivation (explanatory · deterministic)
Health is derived client-side and always accompanied by a **"Why:"**
statement. Never a bare number.

| Tier               | Trigger                                                              |
|--------------------|----------------------------------------------------------------------|
| Critical           | Any open `oos|*` event with no subsequent `oos|cleared`.             |
| Attention Needed   | Any open `defect|opened` / `defect|acknowledged` OR any recent `preop|failed` / `dvir|failed`. |
| Good               | No holds, no open defects, no recent failures.                       |
| Excellent          | (reserved — not used in the pilot; kept in shell tone map for future use). |

Reasons appended for the "Why: …" line:
- "Currently out of service." (when OOS)
- "Open defect on record." (when open defect)
- "Recent inspection failure." (when failure event)
- "No safety holds on record." (when clean)
- "No active defects." (when clean)
- "No recent inspection failures." (when clean)

## Attention items (Section 2)
Built from live backbone signals only:
- Open OOS → CRITICAL · "Unit N is out of service" · owner Shop Manager · due Today.
- Up to 3 open defects → HIGH · "Open defect · not yet acknowledged / acknowledged, awaiting repair" · owner Shop Manager.
- Recent inspection failures → MEDIUM · "N inspection failures on record" · owner Mechanic.

## Universal Action Queue (max 5)
- "Clear the OOS state (repair + manager review + RTS)." — when OOS.
- "Assign or complete N open defect(s)." — when open defects exist.
- "Review recent inspection failure with mechanic." — when a failure exists.
- Shell caps the list at 5 via `.slice(0, 5)`.

## Relationships (Section 5)
Derived from real timeline payload fields:
- **assigned to project** — from any event with `project_number`.
- **operated by** — from any event where `actor_role === "operator"` (or a `preop` actor).
- **work order** — from any event with `related_work_order_id`.
- **current status** — "Out of service" node when OOS is active.
- **shop history** — always present; deep-links to `/shop/units/:unit/history`.

Every node is clickable when a deep-link exists. No fake graph.

## Operational Intelligence (Section 8)
Consumes the `fleet_intelligence` row from `/api/operational-intelligence/summary`:
- Attention chip (universal 4-value language)
- Trend chip (direction · score · delta)
- Top attention label as the "Top driver" line

## Section 3 · Guidance Card
The Section-3 button opens the Track 19.54 universal Guidance Card for
`fleet_intelligence`. All 10 Guidance Card sections render — zero
duplication.

## Sections that render honest empty states in the pilot
- Section 6 · Documents — "No documents on record."
- Section 7 · Photos — "No photos on record."
- Section 9 · History — "No historical snapshots on record."
- Section 10 · Audit — "No audit entries on record."

Filling these with fake data would violate the mandate ("Everything
must be factual. Never inferred. Never fabricated."). Future tracks may
wire real endpoints without changing the shell.

## Mobile
- Max width `max-w-5xl` (~ 1024px) with padding.
- Every section stacks vertically on mobile / iPad portrait.
- Relationship graph is a compact vertical chain — no horizontal
  overflow at any width.
- Timeline uses the Track 19.54 `OperationalThread` primitive which is
  already mobile-safe.

## Testids exposed on the pilot
Root: `fleet-unit-thread`. All shell testids resolve under this root
(e.g. `fleet-unit-thread-section-2-attention`).

## What the pilot does NOT do
- Does not write to any collection.
- Does not create a new backend route.
- Does not create a duplicate timeline / history / audit system.
- Does not compute a new score.
- Does not send emails.
- Does not upload documents or photos.
