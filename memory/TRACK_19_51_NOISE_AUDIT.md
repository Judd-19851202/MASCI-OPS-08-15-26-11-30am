# TRACK 19.51 · Noise Audit

Every widget/card/tile on every portal home evaluated against six survival questions:
1. Does this help the user decide what to do next?
2. Does it explain **why** it matters?
3. Does it point to an action?
4. Does it use real data (not demo / fabricated)?
5. Does the user understand it in 10 seconds?
6. Would removing it make the user worse off?

## Ratings key
- **CRITICAL** — must stay
- **HIGH** — keep / refine
- **MEDIUM** — useful but not primary
- **LOW** — optional
- **NOISE** — remove or redesign
- **UNKNOWN** — needs owner decision

## Aggregate findings

| Portal | # tiles | CRITICAL | HIGH | MEDIUM | LOW | NOISE | UNKNOWN |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Admin (v1) | ~34 | 6 | 8 | 7 | 4 | 6 | 3 |
| Admin (v2) | ~24 | 8 | 9 | 4 | 2 | 1 | 0 |
| **OI Cockpit** | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| **OI Recipients** | 8 | 5 | 3 | 0 | 0 | 0 | 0 |
| Safety Hub | ~18 | 4 | 4 | 4 | 3 | 3 | 0 |
| HR Hub | ~14 | 3 | 3 | 3 | 2 | 3 | 0 |
| PM Hub / Command Center | ~22 | 5 | 6 | 5 | 3 | 2 | 1 |
| Shop Hub | ~12 | 3 | 3 | 3 | 2 | 1 | 0 |
| Dispatch Hub V2 / CC | ~16 | 6 | 5 | 3 | 1 | 1 | 0 |
| Fleet Visibility | ~14 | 4 | 4 | 3 | 2 | 1 | 0 |
| Field Section / Leadership | ~10 | 2 | 3 | 2 | 2 | 1 | 0 |
| Guidance / Help | ~6 | 1 | 2 | 1 | 1 | 1 | 0 |

Total NOISE items: **20**. Detailed per-tile removal / redesign proposals live in the Remediation Roadmap.

## Common noise patterns identified
- Raw counts with no context ("42 records") — appears on Admin v1, HR, Shop.
- Duplicate "Total X" tiles that appear again inside the sub-page.
- Stale documentation cards pointing to retired workflows.
- Decorative charts that never change decisions.
- "Recent activity" logs with no time-bounded operational signal.
- Cards existing because a data source exists, not because the user needs the signal.

## Reference standard
The OI Cockpit (`/admin/operational-intelligence`) achieved **6/6 CRITICAL · 0 NOISE**. It is the reference implementation for every future command center — see `TRACK_19_51_COMMAND_CENTER_STANDARD.md`.
