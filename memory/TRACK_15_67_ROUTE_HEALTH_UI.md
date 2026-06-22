# TRACK 15.67 · Phase 3 · Route Health UI

_Status: ✅ SHIPPED · 2026-06-22_

## Goal
Surface the `POST /api/admin/email-routing/v2/route-health` backend
endpoint (Phase 1) through a one-click button in the Email Routing V2
panel so an operator can validate every route for the active tenant
without leaving the admin surface.

## Backend (already in place from Phase 1)
`server.py · admin_v2_route_health()`:
- Dry-runs every route for the active tenant — NO Resend send.
- Writes a `email_routing_audit_v2` row per route with
  `subject="[ROUTE HEALTH] dry-run"`, `calling_module="route_health"`,
  `dry_run=true`.
- Classifies each route:
  - **🔴 red** — critical route with empty TO (cannot deliver).
  - **🟡 amber** — empty recipients on a non-critical route, or
    explicitly disabled, or never-tested / stale (>30 days).
  - **🟢 green** — healthy.
- Returns `{tenant_key, ts, summary: {green, amber, red}, total,
  results: [{route_key, status, reason, last_tested_at, …}]}`.

## Frontend (`components/EmailRoutingV2Panel.jsx`)

### New button
```jsx
<Button data-testid="v2-route-health-run" onClick={runRouteHealth}>
  <Stethoscope /> Run Route Health
</Button>
```

Placed in the panel header, beside the "19 routes" pill. Disabled
while loading or while a request is in flight.

### Summary bar
On click, the result populates a header strip with three colour pills:

```
[Last route health]  [🟢 16 green]  [🟡 3 amber]  [🔴 0 red]
Tenant masci · 19 routes · 2026-06-22 16:53:14
[Show failing routes ▾]   ← collapsible details when amber/red exist
```

The "Show failing routes" details list each non-green route by key +
reason (e.g. `🟡 SAFETY_FORMS_TO — never tested / stale (>30d)`).

### Test IDs added
- `v2-route-health-run` — the trigger button
- `v2-route-health-summary` — the result strip container
- `v2-route-health-green`, `v2-route-health-amber`, `v2-route-health-red` — the count pills

## Proof
Backend health endpoint is exercised by the existing second-tenant
simulation; the UI button calls the same endpoint with admin auth.

### MASCI tenant smoke test (curl)
```bash
curl -X POST "$API/api/admin/email-routing/v2/route-health" \
  -H "X-Admin-Token: ..."
```
Returns summary + per-route results. Each route gets an audit row
visible in the existing audit drawer (`v2-audit-drawer`).

### Hard rules honoured
- ✅ NO real Resend send. Every route is dry-run.
- ✅ Each route generates exactly one audit row per Route Health click.
- ✅ Stale routes (>30 days since last test) downgrade to amber so
   the operator notices.
- ✅ Critical-route empty TO surfaces as red — blocks cutover.
