# TRACK 19.54 · Guidance Card Specification

## Doctrine
The **Guidance Card** is the universal operational primitive. Every
attention item, every trend, every recommendation, every alert
surfaces through this ONE card. If a portal creates a different card,
the platform has drifted.

## The Seven Questions
Every card must answer, without exception:

1. **What happened?** — Section 2 "Operational Summary"
2. **Why does it matter?** — Section 3 "Why It Matters"
3. **What caused it?** — Section 4 "Primary Drivers"
4. **Who owns it?** — Section 6 "Responsible Roles"
5. **What should happen next?** — Section 5 "Recommended Actions"
6. **What supports this?** — Section 7 "Supporting Evidence"
7. **Where do I go?** — Section 8 "Deep Links"

## The Ten Sections (in order)

| # | Section              | testid                                    | Data source                                                                     |
|---|----------------------|-------------------------------------------|---------------------------------------------------------------------------------|
| 1 | Title                | `guidance-card-title`                     | product.display_name + `AttentionChip` + `TrendChip`                            |
| 2 | Operational Summary  | `guidance-card-summary`                   | `product.top_attention_label` or first `needs_immediate_attention` item        |
| 3 | Why It Matters       | `guidance-card-why`                       | Deterministic mapping from `attention_level` → operational consequence         |
| 4 | Primary Drivers      | `guidance-card-drivers`                   | `sections[section_key='key_drivers' \| 'primary_drivers']`                     |
| 5 | Recommended Actions  | `guidance-card-actions`                   | `sections[section_key='recommendations' \| 'recommended_actions']` — MAX 5      |
| 6 | Responsible Roles    | `guidance-card-roles`                     | `guidanceMap.rolesFor(product_id)`                                             |
| 7 | Supporting Evidence  | `guidance-card-evidence`                  | `sections[section_key='supporting_evidence' \| 'operational_facts']` — max 6    |
| 8 | Deep Links           | `guidance-card-deep-links`                | `guidanceMap.deepLinksFor(product_id)` — always includes OI Cockpit             |
| 9 | Relevant Guidance    | `guidance-card-guidance`                  | Static link to `/guidance` (Operational Guidance Center)                        |
|10 | Decision Boundary    | `guidance-card-decision-boundary`         | Immutable copy: "This information supports operational decision-making..."      |

## Action Quality Standard (max 5)
Recommended Actions are extracted 1:1 from the certified OI digest's
`recommendations` section (or `plan_this_week` fallback). The Guidance
Card does **not** rewrite, paraphrase, or invent actions. It also caps
the list at 5 via `.slice(0, 5)` — enforced by the lock test.

Empty state is honest: "The latest digest lists no operational
actions. Consult the Cockpit drill-down." — no filler, no
motivational copy, no "monitor" / "keep an eye on" wording.

## Universal Attention Vocabulary
Every card renders `AttentionChip` with a hint:

- `CRITICAL` — Immediate action required.
- `HIGH` — Address today.
- `MEDIUM` — Plan this week.
- `LOW` — Healthy.

## Universal Trend Vocabulary
Every card renders `TrendChip` in direction-first order:

- `▲ Improving`
- `→ Stable`
- `▼ Declining`

Followed by the score and delta percent. Direction leads the number.

## Data flow
```
[click tile on OiAttentionStrip]
    ↓
GuidanceCard(product = summary row)
    ↓
GET /api/operational-intelligence/history?product_id=X&limit=1
    ↓ (history_id)
GET /api/operational-intelligence/history/{history_id}
    ↓ (sections)
render sections 4 / 5 / 7 from `sections[]`
```

No POST. No PUT. No DELETE. No domain endpoint. Verified by the lock
tests `test_guidance_card_no_writes` and
`test_guidance_card_consumes_only_existing_endpoints`.

## Not-doing list
- Does **not** create a recommendation engine (extracts from the
  digest).
- Does **not** create a new AI (no LLM calls, no scoring, no
  classification).
- Does **not** create a duplicate score model (reuses the certified
  score payload).
- Does **not** create a new notification path (no email, no push).
- Does **not** create a new command center or dashboard.
- Does **not** own or write to any collection.

## Deep-link map (static)
See `guidanceMap.js`. Each product_id maps to (a) the portal home most
relevant for that intelligence and (b) the OI Cockpit as the universal
fallback. Only routes that already exist in `App.js` are used — the
lock test suite covers this indirectly via the "no new routes" prior
tests.
