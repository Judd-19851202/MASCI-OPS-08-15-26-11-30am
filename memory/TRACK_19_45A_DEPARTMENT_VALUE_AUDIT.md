# TRACK 19.45A · Department Value Audit

| Department | Product | Daily/Weekly/Never? | Missing? | Too much? | Wrong audience? | Verdict |
|---|---|---|---|---|---|---|
| Safety | Safety Morning | Weekly | Trend history (Track 19.46+) | No | No | 🟢 |
| Executive | Executive Ops | Weekly | Trend history | No | No | 🟢 |
| Accounting / PMs / HR | PO Weekly | Weekly | Nothing new — already relied upon | No | No | 🟢 |
| Transportation | Transportation | Weekly | Motive event surfacing (Track 19.47) | No | No | 🟢 |
| Fleet | Fleet | Weekly | MaintainX + FleetWatcher (Track 19.47) | No | No | 🟢 |
| HR | HR | Weekly | Non-driver employee qualification schema (Track 19.48) | No | No | 🟢 |
| Training | Training | Weekly | Meeting attendance rosters (Track 19.48) | No | No | 🟢 |
| Project / PMs | Project | Weekly | Schedule system integration (on-time / off-track — needs authoritative schedule) | No | No · admin_only until PM-scoped variant ships | 🟡 |
| Shop | Shop Intelligence | Not-yet-shipped (CONTRACT_REGISTERED) | Full aggregator (Track 19.46+) | n/a | n/a | ⚠️ CONTRACT_REGISTERED |
| Corporate | Corporate Intelligence | Not-yet-shipped | Full aggregator (Track 19.46+) | n/a | n/a | ⚠️ CONTRACT_REGISTERED |
| Operations | Weekly Operations Digest | Not-yet-shipped | Full aggregator (Track 19.46+) | n/a | n/a | ⚠️ CONTRACT_REGISTERED |

## Right-audience rule

- Safety products (`safety_morning_digest`, `transportation_intelligence`, `fleet_intelligence`) allow **Safety** users.
- HR-sensitive products (`hr_intelligence`, `training_intelligence`) **admin_only**.
- Financial products (`po_weekly_digest`, `executive_operations_brief`, `project_intelligence`) **admin_only** until PM-scoped variants ship.

## Wrong-audience risk

None currently. Every product is gated appropriately. When Track 19.47 ships a PM-scoped Project Intelligence, that variant will move to `safety_or_admin` with server-side project-scope filtering.
