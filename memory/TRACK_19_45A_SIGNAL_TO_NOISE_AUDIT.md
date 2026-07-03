# TRACK 19.45A · Signal-to-Noise Audit

Systematic per-section review across the 8 IMPLEMENTED products.

## Ranking key

- 🟢 **Critical** — changes decisions daily · would be missed within 24h
- 🟡 **High** — actionable weekly
- 🟠 **Medium** — useful trend context
- 🔴 **Low** — vanity or repeat of another section
- ⛔ **Noise** — DELETE or REDESIGN

## Section-by-section verdicts

| Section | Verdict | Rationale |
|---|---|---|
| `executive_summary` | 🟢 Critical | 7-second overview per product; delete would break the "two-minute rule". |
| `operational_intelligence_score` | 🟢 Critical | Single number owners rally around; drives escalation. |
| `trend_direction` | 🟡 High (once history accumulates) | Currently → flat on first-run for most products. Not noise · will strengthen. |
| `top_wins` | 🟡 High | Morale + confirmation the platform notices positive movement. |
| `needs_immediate_attention` | 🟢 Critical | The single most-read section — direct action bucket. |
| `top_5_items` | 🟢 Critical | Table with deep links; converts "know" → "click and act". |
| `core_metrics` | 🟠 Medium | Detail follow-up · often skimmed. Kept because it feeds Score explainability. |
| `trend_table` | 🟠 Medium (currently not-applicable) | Engages once ≥ 2 history rows accumulate. |
| `recommendations` | 🟢 Critical | Concrete actions; short list only. |
| `upcoming_risks` | 🟡 High | Currently populated only when signals warrant (avoid noise). |
| `recent_changes` | 🟠 Medium | Confirms cadence · shortest section. |
| `deep_links` | 🟢 Critical | Every product has 3–5 deep links; forms the click surface. |
| `no_auto_decision_notice` | 🟢 Critical | Doctrine + legal/regulatory protection. |
| `audit_footer` | 🟠 Medium | Ops confidence; small. |

## Overall

**No section ranked ⛔ Noise.** The 14-section standard survived audit intact. `core_metrics` and `recent_changes` are the lowest-signal, but both feed the "explainability" and "cadence confirmation" needs that the two-minute rule requires — deleting them would push Score explanations underground.

## Empty-state discipline

Canonical `EMPTY_STATE_ITEM` marker (Track 19.41) prevents ugly blank/N-A sections. When a product has no applicable content for `top_wins`, `needs_immediate_attention`, `recommendations`, etc., the canonical marker fires — never blank white space, never repeated `N/A`.

## Recommendations

- **Once trend history accumulates (Track 19.47+)**, elevate `trend_direction` from 🟡 → 🟢.
- **Never** add a section that cannot pass the "would leadership miss this in 24h?" test.
- **Never** re-add the raw-metric dump section that appeared in early prototypes.
