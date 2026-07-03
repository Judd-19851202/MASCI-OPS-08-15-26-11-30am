# TRACK 19.46 · Operational Value Certification

Every section of Weekly Operations was subjected to the survival test:

> **"If this section disappeared, would leadership make a worse operational decision Monday morning?"**

Sections that failed the test were removed before shipping.

| Section | Survives? | Justification |
|---|:-:|---|
| Executive Summary (6 KPIs) | ✅ | Answers "how many domains scored / declined / are in HIGH-CRITICAL" — the frame for the whole read. |
| Operational Intelligence Score | ✅ | Cross-domain baseline. If it moves, leadership acts. |
| Trend Direction | ✅ | WoW percent mean change · true one-glance signal. |
| Top Wins | ✅ | Improvers with concrete point deltas · not vanity metrics. |
| Needs Immediate Attention | ✅ | HIGH/CRITICAL domains + biggest decliners + one concrete signal each. |
| Top 5 (cross-domain priorities) | ✅ | Ranked by attention bucket then WoW delta — the "look here first" table. |
| Core Metrics (compact list) | ✅ | Scored domains · improvers · decliners — one line each. Keeps the JSON API useful for the future Cockpit. |
| Trend Table (per-domain last 4 scores) | ✅ | Every domain shows score-now, attention, WoW Δ, up-to-4-week history — a boardroom-quality mini spark. |
| Recommendations | ✅ | Every recommendation is specific ("Executive review of X"). Never "monitor". |
| Upcoming Risks | ✅ | MEDIUM domains sliding toward HIGH. Emerging (not existing) issues. |
| Recent Changes | ✅ | The one-glance WoW headline. |
| Deep Links | ✅ | Every link goes to a page leadership actually uses. No junk links. |
| No-Auto-Decision Notice | ✅ | Cements the "discussion prompt only" contract. |
| Audit Footer | ✅ | Traceability · required by the 14-section standard. |

## Sections rejected before shipping (per spec)
- "All raw metrics from Mongo" — noise, removed.
- "Every graph possible" — noise, removed.
- "Bar chart of email delivery" — infra noise, not operational, removed.
- "Chart of Weekly Ops send history" — meta-tracking, not operational, removed.
- "Full-portfolio table of every case" — that's what individual product previews are for.

## Bar the future Cockpit UI must clear
When the Cockpit UI is built (Track 19.47), it MUST render every
Weekly Operations section without adding decorative widgets that fail
the survival test. Value-first, boardroom quality, or don't ship it.
