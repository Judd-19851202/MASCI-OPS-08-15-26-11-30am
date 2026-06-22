# TRACK 15.64 — Routing Architecture (Phase 4)

**Date:** 2026-06-22  
**Mode:** DESIGN-ONLY · no implementation

## 1. Goal
Promote the existing `backend/email_routing.py` from a 6-key DB override into a **complete, tenant-scoped, audit-first routing engine** that covers every notification, escalation, alert, digest, welcome, and reset email the platform emits. Keep backward compatibility for every existing route so the migration is non-disruptive.

## 2. Naming convention
Routes are referenced by **stable, human-readable, ALL_CAPS_SNAKE keys** so admins, deploy docs, and audit rows all use one vocabulary.

```
SAFETY_FORMS_TO                LEADERSHIP_ALWAYS_TO
INCIDENT_SEVERE_CC             COMPLIANCE_ALWAYS_CC
PRE_OP_FAIL_FALLBACK
BACKUP_EMAIL_TO                BACKUP_VERIFICATION_TO
HEALTH_ALERT_RECIPIENTS        OUTAGE_ALERT_TO
SAFETY_DIGEST_TO               OPERATOR_DIGEST_RECIPIENTS
PAYROLL_VARIANCE_TO            ADMIN_DEAD_LETTER_TO
DISPATCH_ROLE_TO               SUPER_ADMIN_TO
EXECUTIVE_DIGEST_TO            ACCOUNT_INVITES_FROM
PASSWORD_RESET_MONITORING_TO
TRENCH_SAFETY_PULSE_BY_ROLE  (sub-map)
```

The existing 6 keys map onto the new names:

| Legacy key | New key |
|---|---|
| `always_cc` | `COMPLIANCE_ALWAYS_CC` |
| `safety_forms_to` | `SAFETY_FORMS_TO` |
| `leadership_always_to` | `LEADERSHIP_ALWAYS_TO` |
| `shop_manager_fallback` | `PRE_OP_FAIL_FALLBACK` |
| `severe_incident_cc` | `INCIDENT_SEVERE_CC` |
| `backup_email_to` | `BACKUP_EMAIL_TO` |

(Backward compatibility: the old keys remain readable via aliasing; admin UI updates labels but write-through accepts both.)

## 3. Per-route schema

Each route is a document in `email_routes` (single collection, one doc per route per tenant):

```json
{
  "_id":           "<tenant_id>::<ROUTE_KEY>",
  "tenant_id":     "masci",
  "route_key":     "SAFETY_FORMS_TO",
  "display_name":  "Safety Forms Distribution",
  "description":   "Equipment issuance / training / return reports.",
  "category":      "compliance",
  "to":            ["safety@mascigc.com", "jaymn.judd@mascigc.com"],
  "cc":            [],
  "bcc":           [],
  "enabled":       true,
  "severity_floor":"info",
  "test_route_at": "2026-06-22T14:30:00Z",
  "updated_at":    "2026-06-22T14:30:00Z",
  "updated_by":    "admin",
  "audit_id":      "ev_..."
}
```

Field semantics:
* `_id` is composite (`tenant::key`) so a single collection serves all tenants without index gymnastics.
* `to` / `cc` / `bcc` are case-insensitively de-duped on save.
* `enabled=false` silences the route without losing config (acts as kill-switch for that route only).
* `severity_floor` (`info` / `warn` / `critical`) lets admins suppress informational fan-out without disabling the route.
* `test_route_at` records the last "Send Test" timestamp for the route — surfaces freshness on the admin UI.

## 4. Resolution algorithm

```python
def resolve(tenant_id: str, route_key: str, ctx: dict) -> Recipients:
    # 1. DB doc (per-tenant) -> highest precedence
    doc = db.email_routes.find_one({"_id": f"{tenant_id}::{route_key}"})
    if doc and doc.get("enabled", True):
        return Recipients(to=doc["to"], cc=doc["cc"], bcc=doc["bcc"])
    # 2. Tenant default
    tenant_doc = db.email_routes.find_one({"_id": f"{tenant_id}::DEFAULTS"})
    if tenant_doc and route_key in tenant_doc.get("defaults", {}):
        return Recipients(**tenant_doc["defaults"][route_key])
    # 3. Env fallback (no MASCI strings — env keys only)
    env_value = os.environ.get(f"ROUTE_{route_key}_TO", "")
    if env_value:
        return Recipients(to=env_value.split(","))
    # 4. Hard fail — surfaced in the admin UI as a red banner
    raise UnconfiguredRouteError(route_key, tenant_id)
```

**No silent fallback to MASCI emails.** If a tenant's route is unconfigured, the admin gets a red banner on `/admin/email`. This is the explicit replacement for the current `safety@mascigc.com` / `jaymn.judd@mascigc.com` hardcoded literals.

## 5. Sender / branding resolution

Sender + reply-to + from-display-name + support-email move to a sibling `tenant_branding` doc:

```json
{
  "_id":            "masci",
  "tenant_id":      "masci",
  "sender_email":   "noreply@mascidocs.com",
  "from_display":   "MASCI Operations Platform",
  "reply_to":       "jaymn.judd@mascigc.com",
  "support_email":  "safety@mascigc.com",
  "support_phone":  "+1-XXX-XXX-XXXX",
  "logo_url":       "https://...",
  "primary_color":  "#C8102E",
  "updated_at":     "2026-06-22T...",
  "updated_by":     "admin"
}
```

Existing `SENDER_EMAIL` / `REPLY_TO_EMAIL` env vars become **boot-time bootstrap only** — they seed the MASCI tenant on first start but are NOT read at send time once the tenant doc exists.

## 6. Audit posture

Every send writes a row to `db.email_audit` with:
```
{
  tenant_id, route_key, send_id (Resend), to, cc, bcc,
  workflow, source_collection, source_record_id,
  sender_email, reply_to, from_display,
  severity, subject, body_size_bytes,
  status: ok|failed|skipped|disabled,
  reason: <if not ok>,
  ts
}
```

Coverage gaps closed:
* Outage alert — currently no audit row.
* Health alert — partial audit row.
* Trench-safety role fan-out — currently no audit row.

## 7. Admin UI (`/admin/email`)

Expand the existing `AdminEmailRoutingPanel.jsx`:

```
┌─────────────────────────────────────────────────────────────────────┐
│ EMAIL ROUTING · MASCI Operations Platform                           │
├─────────────────────────────────────────────────────────────────────┤
│ Tenant: [MASCI ▼]                          Last config change: …     │
├─────────────────────────────────────────────────────────────────────┤
│ Branding                                                            │
│   Sender:     noreply@mascidocs.com           [Edit]                │
│   Reply-to:   jaymn.judd@mascigc.com          [Edit]                │
│   Display:    MASCI Operations Platform       [Edit]                │
├─────────────────────────────────────────────────────────────────────┤
│ Routes (14)                                                         │
│ ┌────────────────────────────┬───────────────┬────────────┬───────┐ │
│ │ Key                        │ Recipients    │ Last Test  │ State │ │
│ ├────────────────────────────┼───────────────┼────────────┼───────┤ │
│ │ COMPLIANCE_ALWAYS_CC       │ 2 to · 0 cc   │ 12d ago    │ on    │ │
│ │ SAFETY_FORMS_TO            │ 2 to          │ 12d ago    │ on    │ │
│ │ INCIDENT_SEVERE_CC         │ 0             │ never      │ off   │ │
│ │ … (11 more rows) …         │               │            │       │ │
│ └────────────────────────────┴───────────────┴────────────┴───────┘ │
│ [+ Add custom route]    [Send test from selected route]    [Audit]  │
└─────────────────────────────────────────────────────────────────────┘
```

Each row is click-to-edit. The drawer:
* Description field (human-readable purpose).
* To / CC / BCC chip editors with email-format validation.
* Enabled toggle.
* Severity floor selector.
* "Send Test" button → calls `POST /api/admin/email-routing/{ROUTE_KEY}/test`.
* "Show audit history" → opens the route-scoped slice of `email_audit`.

## 8. API surface

Existing endpoints (keep, evolve):
* `GET  /api/admin/email-routing` — return all routes + branding for current tenant.
* `PUT  /api/admin/email-routing/{ROUTE_KEY}` — replaces today's bulk PUT.
* `POST /api/admin/email-routing/{ROUTE_KEY}/test` — replaces today's generic test endpoint.
* `GET  /api/admin/email-routing/audit?route_key=&since=&until=` — new, route-scoped audit slice.

New endpoints:
* `GET/PUT /api/admin/tenant-branding` — sender / reply-to / display / colours / logo.
* `POST /api/admin/email-routing/preview` — body `{ route_key, ctx }` → returns the recipients the resolver would pick **without** sending an email.

## 9. Migration backward-compat

* Existing callers continue to import `email_routing.get_value(db, "always_cc")` — the new layer aliases legacy keys to the canonical names so no caller breaks.
* `email_routing.env_defaults()` is rewritten to return `{}` when no env override exists, **not** the MASCI literals. Empty values surface the "unconfigured route" red banner instead of leaking MASCI's safety inbox.
* `pm_routing.py`'s hardcoded PM dict is deleted; PM resolution requires the `project_managers` collection to be populated. (MASCI's preview/production already have it populated.)
* `OWNER_SEED` in `auth.py` becomes empty by default; the MASCI tenant supplies its 5 owners via a tenant-scoped admin form on first boot.

## 10. Routes catalogue (final)

| Route key | Category | Trigger | Default tenant scope |
|---|---|---|---|
| COMPLIANCE_ALWAYS_CC | compliance | inspection / meeting / JHA / DR / incident / qaqc | always CC |
| SAFETY_FORMS_TO | compliance | equip issuance / training / return | always TO |
| LEADERSHIP_ALWAYS_TO | leadership | 10 FL forms | always CC |
| PRE_OP_FAIL_FALLBACK | shop | Pre-Op FAIL/OOS when shop_users empty | TO |
| INCIDENT_SEVERE_CC | safety | WV / PI / severe incident | additional CC |
| BACKUP_EMAIL_TO | platform | daily auto-backup + manual backup | TO |
| BACKUP_VERIFICATION_TO | platform | backup verify probe | TO |
| HEALTH_ALERT_RECIPIENTS | platform | scheduler dead / backup stale / DB unreachable | TO |
| OUTAGE_ALERT_TO | platform | platform-wide outage alert | TO |
| SAFETY_DIGEST_TO | digest | weekly safety digest | TO |
| OPERATOR_DIGEST_RECIPIENTS | digest | daily operator digest | TO |
| PAYROLL_VARIANCE_TO | digest | weekly payroll variance | TO |
| EXECUTIVE_DIGEST_TO | digest | weekly exec digest (new) | TO |
| ADMIN_DEAD_LETTER_TO | platform | unresolved submitter identity | TO |
| DISPATCH_ROLE_TO | operations | dispatch alerts | TO |
| SUPER_ADMIN_TO | platform | platform-admin escalation | TO |
| ACCOUNT_INVITES_FROM | branding | per-portal welcome sender | sender |
| PASSWORD_RESET_MONITORING_TO | security | optional CC on reset-link send (off by default) | CC |
| TRENCH_SAFETY_PULSE_BY_ROLE | sub-map | safety / shop / dispatch / admin | per-role TO |

**19 routes total** = the existing 6 + 13 new.

## 11. Non-goals (explicitly OUT of scope)
* Do not invent a parallel email-template registry. Existing per-workflow HTML stays where it is.
* Do not refactor the 40 Resend send sites. The wrapper they call (`fsi_email_sender.py`, `_send_via_resend`, inline calls) is the only thing that needs the new resolver.
* Do not change the Resend account or Resend webhook secret.
* Do not introduce a queue / retry layer in Track 15.64 — current synchronous send is acceptable for the first cut.

## 12. Hard-rule compliance (Phase 4)
* ✅ Design only — zero code change.
* ✅ Backward compatible — every existing caller continues to work.
* ✅ Multi-tenant first — `tenant_id` threads through every resolver.
* ✅ Audit trail mandatory — every send writes a row in `email_audit`.
* ✅ No hidden recipients — empty/missing route raises a visible admin banner, not a silent send-to-MASCI.
