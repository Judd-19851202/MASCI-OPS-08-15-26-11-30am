# TRACK 19.40 · TREND ENGINE

`compute_trend(current, previous)` returns:
```
{ current, previous, delta, pct_change, arrow: ▲|▼|→, tone: up|down|flat }
```

Deterministic. No timestamps · no randomness. Zero-division safe (`previous==0` yields `pct_change=None` when both are zero, else 100.0).

Consumers render `trend` objects as `<value> <arrow> <±pct%>` with `class="trend-up|down|flat"` (CSS in the engine). Never inferred, never fabricated.
