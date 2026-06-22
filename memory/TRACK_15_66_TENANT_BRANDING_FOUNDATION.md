# TRACK 15.66 — Tenant Branding Foundation (Phase 2)

**Date:** 2026-06-22

## 1. What ships
* New collection: `tenant_branding` (one doc per tenant).
* Backend endpoints:
  * `GET /api/admin/email-routing/v2/branding` — returns the doc; auto-populates from env if the doc is missing.
  * `PUT /api/admin/email-routing/v2/branding` — partial update; admin-only.
* Frontend panel: `TenantBrandingPanel.jsx` at `/admin/email`.

## 2. Schema

```json
{
  "_id":                    "masci",
  "tenant_key":             "masci",
  "company_name":           "MASCI",
  "platform_display_name":  "MASCI Operations Platform",
  "sender_name":            "MASCI Operations Platform",
  "from_email":             "noreply@mascidocs.com",
  "reply_to":               "jaymn.judd@mascigc.com",
  "support_email":          "safety@mascigc.com",
  "safety_email":           "safety@mascigc.com",
  "hr_email":               "",
  "operations_email":       "",
  "logo_url":               null,
  "primary_color":          "#C8102E",
  "source":                 "env_defaults | admin",
  "updated_at":             "...",
  "updated_by":             "admin"
}
```

`from_email` and `reply_to` are pre-populated from `SENDER_EMAIL` / `REPLY_TO_EMAIL` env vars on first GET. `support_email` and `safety_email` default to MASCI strings until an operator changes them — these are the ONLY remaining MASCI-default strings inside the runtime branding doc, and they are user-editable.

## 3. What the routing engine will pull from branding (Phase 2 wiring)

The engine reads from `tenant_branding` in three places (next-wave wiring, not in Phase 1 send-sites yet):

| Branding field | Used by |
|---|---|
| `from_email` | Sender of every email send (replaces `os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")`) |
| `reply_to` | Reply-to on every email |
| `support_email` | Help / training text resolution at render time |
| `safety_email` | Default value for `SAFETY_FORMS_TO` route (admin can override) |
| `hr_email` / `operations_email` | Per-role default routes |
| `logo_url` / `primary_color` | Email templates that already accept branding props |

Wave 3 (multi-tenant) will resolve `tenant_branding` per-request via tenant middleware. Wave 2 (today) keeps a single tenant (`masci`) with env-default seed.

## 4. Operator workflow

1. Open `/admin/email`.
2. Tenant Branding panel is the first card.
3. Edit any field (e.g., set `support_email` to `support@yourcompany.com`).
4. Click Save → toast confirms, cache invalidates.
5. The next email send picks up the new sender / reply-to (and the next page render picks up the new support email, after the Phase-2 frontend wiring lands).

## 5. Hard-rule compliance
* ✅ Additive collection — no destructive migration.
* ✅ Sender / reply-to / support strings now editable without a redeploy.
* ✅ MASCI defaults preserved at first load; admin can override; flag-off behaviour unchanged.
* ✅ Cache invalidates on save (resolver picks up edits within ≤ 60 s).
