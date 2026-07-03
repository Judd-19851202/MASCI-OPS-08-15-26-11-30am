# TRACK 19.41 · Universal Operational Intelligence Product Standard

**Status:** 🟢 LOCKED (contract enforced by pytest).

Every Operational Intelligence product implemented on top of the
Track 19.40 engine MUST render its digest in the following 14-section
order. Sections may be marked *not applicable* with a canonical empty
state (`EMPTY_STATE_ITEM`) — never blank white space and never `N/A`
spam.

## The 14 sections (locked order)

| # | Section key | Title | Kind | Required contents |
|---|---|---|---|---|
| 1 | `executive_summary` | Executive Summary | kv | 3–7 top-line KV rows every leader can read in 10 seconds. |
| 2 | `operational_intelligence_score` | Operational Intelligence Score | kv | Overall Score · Attention Level · Confidence · Data Freshness (from the Score model). |
| 3 | `trend_direction` | Trend Direction | kv | Direction (▲/▼/→) · Tone · % Change · Current · Previous. Uses the Track 19.40 trend engine. |
| 4 | `top_wins` | Top Wins | list | 0–5 positive movements; empty-state marker when none. |
| 5 | `needs_immediate_attention` | Needs Immediate Attention | list | 0–5 items requiring action this week; empty-state marker when none. |
| 6 | `top_5_items` | Top 5 Items | table | Product-specific priority list (attention cases · open POs · overdue trainings · etc.). Not-applicable sentinel when no rows. |
| 7 | `core_metrics` | Core Metrics | kv | Domain-specific KPIs. Always populated. |
| 8 | `trend_table` | Trend Table | table | Multi-metric trend rows (current · previous · Δ · %). Not-applicable sentinel until history accumulates. |
| 9 | `recommendations` | Recommendations | list | Suggested follow-up actions; must be concrete and directly actionable. |
| 10 | `upcoming_risks` | Upcoming Risks | list | Forward-looking risk callouts. |
| 11 | `recent_changes` | Recent Changes | list | What moved in the last period (adds · closures · state changes). |
| 12 | `deep_links` | Deep Links | list | 2–5 `{href, text}` items into the platform. |
| 13 | `no_auto_decision_notice` | No-Auto-Decision Notice | list | Verbatim doctrine notice — attention signal only. |
| 14 | `audit_footer` | Audit | kv | Product · Period · Generated at · Notes. |

## Contract entry point

```python
from operational_intelligence import build_standard_layout

digest = build_standard_layout(
    product_id="my_product",
    subject="MASCI · My Product Digest",
    period_label="Weekly · Mon 14:00 UTC",
    executive_summary={...},
    score=score.to_dict(),
    trend_direction={"arrow": "▲", "tone": "up",
                     "pct_change": 5.2, "current": 12, "previous": 10},
    top_wins=[...],
    needs_immediate_attention=[...],
    top_5_items={"title": "...", "headers": [...], "rows": [...]},
    core_metrics={...},
    ...
)
```

## Enforcement

- `test_track_19_41_intelligence_standardization.py::test_build_standard_layout_emits_all_sections` — grep-check on section key order.
- `test_track_19_41_...::test_empty_states_use_canonical_marker` — no blank sections allowed.
- `test_track_19_41_...::test_po_digest_aggregator_produces_standard_layout` — production product proves the contract end-to-end.

## Zero-drift constraint

- ONE renderer (`engine.render_html`) — no product may bring its own template.
- ONE section shape — all products serialise into the same `sections: [{section_key, title, kind, rows|items|headers}]` structure.
- Products may add product-specific KV rows *within* a section — never a new top-level section.

## Non-goals

- Not a UI component library. Frontend renders the same section shape via any component (email · PDF · in-app) but is not required to visualize every section identically.
- Not a wire format contract. The `digest_object` is transient; the immutable payload is what's written to `operational_intelligence_history`.
