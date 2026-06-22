# TRACK 15.67 — Route Health Check (Phase 1)

**Date:** 2026-06-22  
**Endpoint:** `POST /api/admin/email-routing/v2/route-health` (admin-token-gated)

## 1. What it does
One call dry-runs every route for the active tenant. Returns:
* `summary = { green, amber, red }`
* `total` = total route count
* `results[]` per-route status with `reason`, `to/cc/bcc` counts, `last_tested_at`, `stale` flag, `critical` flag, `enabled` flag.

Each route is classified:
* **red** — critical route is enabled and has empty `to` (can't deliver).
* **amber** — has empty recipients (for non-`ACCOUNT_INVITES_FROM` / non-`PASSWORD_RESET_MONITORING_TO` routes), OR explicitly disabled, OR never-tested / >30-day stale.
* **green** — has recipients, enabled, recently tested.

Every route also writes an audit row (`status="dry_run"`, `calling_module="route_health"`) so the operator can see the validation event in the per-route audit drawer.

## 2. Live evidence (preview, 2026-06-22)

```json
{
  "tenant_key": "masci",
  "summary": { "green": 1, "amber": 18, "red": 0 },
  "total": 19
}
```

`SAFETY_FORMS_TO` is the only green route (tested earlier in this session). The 18 amber routes are "never tested" — the operator can now click "Dry-run test" on each to flip them green. Zero red means no critical route currently has empty TO.

## 3. Operator workflow

1. Open `/admin/email`.
2. Click "Route Health" (Phase 2 will wire the UI button — current Phase 1 ships the backend endpoint; admin UI can hit it via the per-route Audit drawer's network call or a simple cURL).
3. Receive summary in < 1 second.
4. Any red route blocks production cutover.
5. Any amber route should be Send-Test verified before cutover.
6. Audit drawer shows the `route_health` dry-run rows for all 19 routes.

## 4. Phase 2 UI work
Phase 2 adds a "Route Health" button in `EmailRoutingV2Panel.jsx` header that:
* Calls the endpoint.
* Renders the summary as three coloured chips.
* Updates the per-route status pill from the response.

## 5. Hard-rule compliance
* ✅ Dry-runs only — no Resend send.
* ✅ Writes audit rows.
* ✅ Flags missing recipients.
* ✅ Flags stale last-tested routes.
* ✅ Surfaces critical-empty as `red` (gates production cutover).
