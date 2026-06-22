# TRACK 15.66 — Admin Routing UI (Phase 2)

**Date:** 2026-06-22  
**Components shipped:**
* `frontend/src/components/EmailRoutingV2Panel.jsx` (~500 LOC) — manages all 19 V2 routes.
* `frontend/src/components/TenantBrandingPanel.jsx` (~140 LOC) — manages sender + branding identity.
* `frontend/src/pages/admin/AdminEmail.jsx` — now mounts both new panels alongside the existing legacy panel + auto-routing panel.

## 1. What admins can do at `/admin/email`

| Capability | Surfaced in | data-testid |
|---|---|---|
| See all 19 routes grouped by category | `EmailRoutingV2Panel` | `email-routing-v2-panel`, `v2-routes-count` |
| Inspect every route — display name, description, severity pill, critical badge, recipient count, last tested | per route row | `v2-route-{ROUTE_KEY}` |
| Edit `to`, `cc`, `bcc` (comma- or whitespace-separated lists) | inline editor drawer | `v2-edit-{ROUTE_KEY}-to/cc/bcc` |
| Enable / disable non-critical routes | editor checkbox | `v2-edit-{ROUTE_KEY}-enabled` |
| Save changes (with server-side validation echoed via toast) | Save button | `v2-save-{ROUTE_KEY}` |
| Cancel edits | Cancel button | — |
| Dry-run a route test (no email sent; audit row written) | "Dry-run test" | `v2-dryrun-{ROUTE_KEY}` |
| Controlled real test (send to an explicit test inbox only) | "Controlled send" + input | `v2-controlled-addr-{ROUTE_KEY}`, `v2-controlled-send-{ROUTE_KEY}` |
| Open per-route audit drawer | "Audit" button | `v2-audit-{ROUTE_KEY}` |
| Inline display of last-failure timestamp + error | red banner | `v2-last-failure-{ROUTE_KEY}` |
| View tenant branding (company, sender, reply-to, support, safety, HR, ops, logo, primary color) | `TenantBrandingPanel` | `tenant-branding-panel`, `branding-field-{KEY}`, `branding-save` |

## 2. Validations enforced by the UI (client + server)

| Rule | Where enforced | Behaviour |
|---|---|---|
| Email format on every list item | Server PUT (`_validate_email_list`) | 400 with reason; toast displays |
| Duplicate recipients filtered (case-insensitive) | Server PUT | Saved list is de-duped |
| Critical route cannot be disabled | Server PUT | 400; UI hides the "Enabled" checkbox for critical routes |
| Critical route cannot be saved with empty `to` while enabled | Server PUT | 400; toast shows the message |
| Controlled test requires a valid `test_recipient` | UI + server | UI guards on `@`; server validates again |

## 3. Visual design
* Routes grouped by category (`compliance`, `safety`, `platform`, `digest`, `branding`, `security`, `leadership`, `operations`, `shop`) — matches the seed catalog.
* Severity pills (info / warn / critical) with consistent colour palette.
* Critical badge with `ShieldAlert` icon and "CRITICAL" label.
* Disabled badge for routes with `enabled=false`.
* Last-tested timestamp shown as relative time ("12d ago").
* Audit drawer is a right-side panel with sticky header + table of the last 100 rows; row colors reflect status (failed = rose, dry-run = sky, sent/resolved = emerald).

## 4. Cache invalidation
Every successful PUT and every successful branding PUT calls `email_routing_v2.invalidate_cache()` on the server, so the resolver picks up edits within 60 seconds at most (and immediately for the next call after the cache flush).

## 5. Out of scope for Phase 2 (deferred to Track 15.67)
* Tenant switcher (single-tenant deploy today; the panel implicitly targets the active `EMAIL_ROUTING_TENANT`).
* Per-route severity-floor editor (currently read-only from seed).
* Bulk import / export of route configs.
* Side-by-side multi-tenant comparison.

## 6. Hard-rule compliance (Phase 2 UI)
* ✅ Critical routes cannot be disabled through the UI.
* ✅ Empty enabled critical routes refused on save.
* ✅ Controlled test will not blast production recipients — explicit `test_recipient` required.
* ✅ Lint clean on both new components.
