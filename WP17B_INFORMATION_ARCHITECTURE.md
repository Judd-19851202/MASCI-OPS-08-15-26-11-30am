# WP-17B Information Architecture

## Standard Used
Every portal must answer one question immediately:
1. what is this portal for,
2. what needs attention first,
3. what action should happen next,
4. where do less-frequent tasks live,
5. what is hidden intentionally versus merely hard to find.

## Portal-by-Portal IA Readiness
| Portal | Mission clarity | Landing-page purpose | IA gap | Readiness | WP-17 dependency |
|---|---|---|---|---|---|
| Admin | Medium | Broad platform command | Too many concepts share one rail; governance/config/ops blur together | Ready with heavy IA debt | `WP-17C`, `WP-17D` |
| PM | High | “What needs PM attention today?” is clear | Companion routes and route aliases still dilute certainty | Ready | `WP-17C` |
| HR | High | Workforce readiness is explicit | Historical-record lanes sit beside core daily work without stronger grouping | Ready | `WP-17C`, `WP-17F` |
| Safety | High | Safety action queues are clear | Benchmark trench workflows coexist with parallel portal naming | Ready | `WP-17C`, `WP-17E` |
| Shop | Medium | Command-center intent is strong | Too many layers on one page; archival and active work compete | Ready with debt | `WP-17C`, `WP-17E` |
| Dispatch | High | Dispatcher attention is clear | Companion hub + classic route relationship still needs formal canon | Ready | `WP-17C` |
| Transportation | Medium | Shared operational shell exists | Dual prefixes and nested subtabs increase relearning cost | Ready with structure debt | `WP-17C`, `WP-17D` |
| Field Leadership | Medium | Functional but not fully role-first | Naming and route family sprawl reduce confidence | Ready with content debt | `WP-17F` |
| Executive | Medium | Useful surfaces exist | Discoverability relies on Admin knowledge more than executive mental model | Ready with discoverability debt | `WP-17C`, `WP-17F` |
| Public / Shared | Medium | Capture flows are functional | Alias route volume and parallel create/submit patterns are high | Ready with governance debt | `WP-17E` |

## IA Findings Locked
1. **Admin is the only portal where mission, configuration, governance, monitoring, and business operations still compete at the same hierarchy level.**
2. **PM, HR, Safety, Dispatch, and Shop hubs are directionally correct** because they lead with queue-first task framing.
3. **Transportation is structurally strong but mentally expensive** because the same domain exists under two mount prefixes and multiple nested tab systems.
4. **Executive surfaces are present but not canonically introduced as an executive journey.**
5. **Built functionality is reachable, but not always through the first expected path.** That is an IA problem, not a missing-feature problem.

## Canonical IA Rules to Carry into WP-17C
- One canonical landing purpose per portal
- One primary navigation family per portal
- One canonical title for each business object
- Daily-use tasks above archive/report/configuration surfaces
- Companion and preview lanes intentionally hidden, never casually discoverable
- Every portal must feel like MASCI, but no user should need to relearn where queues, records, and help live