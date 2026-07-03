# TRACK 19.45A · Cockpit Readiness Report

**Status:** 🟡 SPEC-READY (backend surfaces available · frontend Cockpit UI deferred to Track 19.46).

## Backend surfaces already available for the Cockpit

| Cockpit tile | Backend endpoint (existing) |
|---|---|
| Every Product | `GET /api/operational-intelligence/products` |
| Implementation Status | Included in `products` response (`status`) |
| Score & Attention (per product) | `POST /api/operational-intelligence/{id}/dispatch?dry_run=true` returns `history_id` with score |
| Preview | `GET /api/operational-intelligence/{id}/preview` |
| Dry-Run Send | `POST /api/operational-intelligence/{id}/dispatch?dry_run=true` |
| Production Send | `POST /api/operational-intelligence/{id}/dispatch?dry_run=false` (admin only for admin_only products) |
| Recipients (per product) | `GET /api/operational-intelligence/recipients?product_id={id}` |
| Recipient CRUD | Track 19.45A endpoints |
| Group CRUD | Track 19.45A endpoints |
| History | `operational_intelligence_history` collection (needs new list endpoint · Track 19.46) |
| Audit | `operational_intelligence_audit` collection (needs new list endpoint · Track 19.46) |
| Failures / Delivery Status | Included in dispatch response `delivery` array |
| Schedule | Included in `products` response (`schedule_freq`, `schedule_iso_day`, `schedule_hour_utc`) |
| Owner / Health | Derived — Cockpit UI concern |

## Missing surfaces (to build in Track 19.46)

- `GET /api/operational-intelligence/{id}/history?limit=N` — paginated history rows.
- `GET /api/operational-intelligence/{id}/audit?limit=N` — paginated audit rows.
- `GET /api/operational-intelligence/{id}/last-sent` — last dispatch snapshot.
- Frontend `/admin/operational-intelligence` Cockpit page.

## Cockpit UI spec (Track 19.46)

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Operational Intelligence Cockpit                                         │
│  ──────────────────────────────────────────────────────────────────────── │
│                                                                            │
│  [11 product cards in a grid]                                              │
│  ┌────────────────────────┐  ┌────────────────────────┐                    │
│  │ Safety Morning         │  │ Executive Ops          │                    │
│  │ Score: 78 · MEDIUM     │  │ Score: 92 · LOW        │                    │
│  │ Trend: → flat          │  │ Trend: ▲ +5%           │                    │
│  │ Last sent: 3 hours ago │  │ Last sent: 3 hours ago │                    │
│  │ [Preview] [Dry-run]    │  │ [Preview] [Dry-run]    │                    │
│  └────────────────────────┘  └────────────────────────┘                    │
│  ...                                                                       │
│                                                                            │
│  Recipient Management                                                      │
│  ──────────────────────────────────────────────────────────────────────── │
│  [Search bar] [Filter by product] [+ Add] [Bulk import]                    │
│  [Table with columns: Email · Name · Role · Product · Active · Actions]    │
│                                                                            │
│  Groups                                                                    │
│  ──────────────────────────────────────────────────────────────────────── │
│  [Group cards with member counts + product subscriptions]                  │
│                                                                            │
│  Recent Activity                                                           │
│  [Audit rows · dispatches · deduped skips · errors]                        │
└───────────────────────────────────────────────────────────────────────────┘
```

## Design constraints

- Boardroom quality (Tailwind + Shadcn/UI).
- Left-aligned layout · asymmetric grid.
- No purple/violet gradients.
- Dominant colors: deep navy + amber accents (matches existing MASCI palette).
- Every card has data-testid.
- 2–3× more spacing than feels comfortable.
- Micro-animations on hover / status changes.

## Verdict

Track 19.45A backend is 90% Cockpit-ready. Remaining backend endpoints are 3 additive routes. UI shipping in Track 19.46.
