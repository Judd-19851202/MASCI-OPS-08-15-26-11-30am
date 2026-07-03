# TRACK 19.45A · Score & Trend Certification

## Score Model Audit (per-product)

| Product | Contributors (P/N) | False-positive risk | False-negative risk | Verdict |
|---|---|---|---|---|
| Safety Morning | 2P / 3N | LOW · closure pace vs open pace prevents FP | LOW · CAPA + evidence gap catch FN | 🟢 |
| Executive Ops | 2P / 3N | LOW · HIGH-case count is authoritative | LOW · CAPA + days-open catch FN | 🟢 |
| PO Weekly | 1P / 2N | LOW · open PO volume is directly observable | LOW · wide-PM impact catches distributed load | 🟢 |
| Transportation | 4P / 6N | MEDIUM · positive "clean" contributors could inflate an empty environment score; mitigated by `insufficient_data_score()` guard | LOW · vehicle-incident weight (-35) dominates | 🟢 |
| Fleet | 4P / 7N | LOW · critical-defect weight (-35) dominates on real risk | LOW · safety hold + OOS aging catch FN | 🟢 |
| HR | 3P / 3N | MEDIUM · `all_current` grants +15 even in small orgs | LOW · expired-quals (-35 cap) dominates FN | 🟢 |
| Training | 3P / 5N | LOW · expired cert weight dominates | LOW · missing/approval-backlog catches FN | 🟢 |
| Project | 4P / 6N | LOW · HIGH-attention case count is authoritative | LOW · missing DR + aging constraints catch FN | 🟢 |

## Confidence thresholds

- `insufficient_data` when zero signals populated — hard-coded in every aggregator.
- `medium` when signals present but volume below a per-product threshold.
- `high` when volume ≥ threshold.
- **Never** returns `high` on an empty environment (grep-locked).

## Trend Certification

- Single engine (`compute_trend`) — up/down/flat arrow · % change · division-by-zero safe.
- Trend arrow currently → flat on most products because history accumulation started at Track 19.42.
- **Never fake previous-period data.** `pct_change=None` when history unavailable.
- Trend metric semantics documented per product (`TRACK_19_44_TRAINING_SCORE_MODEL.md`, etc.).

## Edge cases proven

| Case | Behaviour | Test |
|---|---|---|
| Score < 0 (over-weighted negatives) | Clamped to 0 · attention=CRITICAL | Track 19.41 lock |
| Score > 100 (over-weighted positives) | Clamped to 100 · attention=LOW | Track 19.41 lock |
| prev=0 · curr>0 | pct_change=100.0 · arrow=▲ | Track 19.40 lock |
| prev=0 · curr=0 | pct_change=None · arrow=→ | Track 19.40 lock |
| None-safe | pct_change=None · arrow=→ | Track 19.40 lock |
| Insufficient data | CRITICAL + `insufficient_data` confidence | Every aggregator has this branch |

## Recommendations

- **Track 19.46+** persist previous-period digest rows into `operational_intelligence_history` and wire real trend math on every product.
- **Consider a "score explainability" preview endpoint** that returns the raw contributor list without the full digest for cockpit UI use.
