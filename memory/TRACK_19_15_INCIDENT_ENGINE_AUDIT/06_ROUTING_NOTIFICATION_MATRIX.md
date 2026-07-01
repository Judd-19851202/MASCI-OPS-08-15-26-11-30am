# Track 19.15 · 06 · Routing & Notification Matrix

## Doctrine

Different incident types touch different stakeholders. Routing MUST be classified per type, not one-size-fits-all.

## Notification matrix per incident type

| Incident Type | Safety | PM | Superintendent | HR | Shop | Fleet | Exec | Owner/GC flag | OSHA | Police | Utility Owner | Insurance | Workers Comp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Injury / Illness** | 🔔 | 🔔 | 🔔 | 🔔 | — | — | 🔔 if hospital/fatal | Owner if high-vis | Safety-triggered | — | — | Safety-triggered | Safety-triggered |
| **Near Miss** | 🔔 | 🔔 | 🔔 | — | if equipment | if vehicle | monthly digest | — | — | — | — | — | — |
| **Property / Equipment Damage** | 🔔 | 🔔 | 🔔 | — | 🔔 | if fleet asset | if > $10K | if third-party property | — | — | — | Safety-triggered | — |
| **Vehicle / Mobile Equipment** | 🔔 | 🔔 | 🔔 | — | — | 🔔 | if fatal / criminal | — | if DOT-reportable | if police called | — | Safety-triggered | if driver injured |
| **Environmental Release / Spill** | 🔔 | 🔔 | 🔔 | — | — | — | if agency notified | if on GC land | — | — | — | if damages | — |
| **Utility Strike** | 🔔 | 🔔 | 🔔 | — | — | if damage | if service outage | 🔔 | — | if traffic | 🔔 (utility company) | Safety-triggered | — |
| **Public / Third Party** | 🔔 | 🔔 | 🔔 | — | — | — | 🔔 | 🔔 | if OSHA-visible | if police called | — | Safety-triggered | — |
| **Security** | 🔔 | 🔔 | 🔔 | 🔔 if internal | — | — | 🔔 | — | — | 🔔 | — | if theft | — |
| **Fire** | 🔔 | 🔔 | 🔔 | — | — | — | 🔔 | 🔔 | — | if arson | — | Safety-triggered | — |
| **Workplace Violence / Threat** | 🔔 | 🔔 | 🔔 | 🔔 | — | — | 🔔 | — | — | Safety-triggered | — | — | — |

Legend: `🔔` = automatic notification; `—` = not applicable; `Safety-triggered` = Safety enables from the case workspace, not automatic.

## Notification channels

Per stakeholder:
- Email (existing `email_routing_v2.py`)
- In-app inbox notification
- Optional SMS (future — not in this track)
- Dashboard badge

## Cadence

- **Immediate** (within 5 min of submit): Safety + PM + Superintendent
- **Same day**: HR (injury), Shop (equipment), Fleet (vehicle)
- **Monthly digest**: Exec (unless flagged high-vis)
- **On status transition**: original stakeholders re-notified with lifecycle status

## Preservation

- Existing `email_routing_v2.py` matrix — keep, extend
- `X-Safety-Token` requests to `/api/incidents` (server.py:2520) — keep untouched
- Historical notifications — never re-fire (idempotency guaranteed by transition events)

## Future implementation location

Track 19.16 backend adds a routing configuration table (or extends `email_routing_v2` config) so this matrix is data-driven, not hardcoded.
