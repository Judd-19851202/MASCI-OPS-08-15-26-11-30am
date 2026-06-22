# TRACK 15.64 — Migration Plan (Phase 5)

**Date:** 2026-06-22  
**Mode:** plan-only · no implementation in this track

Migration of the existing partially-DB-routed system to the **19-route, tenant-scoped, audit-first** design from Phase 4. Three waves so the platform never goes silent during rollout.

## 0. Pre-requisites
* **Track 15.64 is AUDIT/ARCHITECTURE only** — execution belongs to Track 15.65+.
* MASCI is the only tenant at execution start. The migration must (a) preserve MASCI's current routing exactly, and (b) leave the door open for a second tenant without further refactoring.

## 1. Wave 1 — Engine rewrite (backend, additive, behaviour-preserving)

### 1.1 New module: `backend/email_routing_v2.py`
* Implements `resolve(tenant_id, route_key, ctx) -> Recipients` per Phase 4 §4.
* Implements `resolve_branding(tenant_id) -> Branding`.
* Keeps the 60-s in-process cache for both.
* Re-exports `get_value(db, legacy_key)` as a thin wrapper over `resolve("masci", LEGACY_TO_NEW[legacy_key], {})` so every existing import keeps working.

### 1.2 Mongo collections + indexes
* `email_routes` — composite `_id`, plus secondary index on `tenant_id`.
* `tenant_branding` — one doc per tenant.
* `email_audit` (already exists) — index on `(tenant_id, ts)` if not present.

### 1.3 Per-route migration of every send site
For each of the 40 Resend send sites (Phase 1 inventory §6):
| Current Source | Future Source | Risk | Migration Method |
|---|---|---|---|
| `os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")` | `branding.sender_email` resolved at send time | low | replace inline literal with helper `current_sender(db)` |
| `os.environ.get("REPLY_TO_EMAIL")` | `branding.reply_to` | low | helper `current_reply_to(db)` |
| `os.environ.get("SAFETY_DIGEST_TO_EMAIL") or "safety@mascigc.com"` | `resolve("masci", "SAFETY_DIGEST_TO", {})` | low | helper `route_recipients(db, "SAFETY_DIGEST_TO")` |
| `os.environ.get("OPERATOR_DIGEST_RECIPIENTS")` | `resolve(..., "OPERATOR_DIGEST_RECIPIENTS", ...)` | low | helper |
| `os.environ.get("HEALTH_ALERT_RECIPIENTS")` | `resolve(..., "HEALTH_ALERT_RECIPIENTS", ...)` | medium — health alerts must never go silent | seed DB doc with current env value BEFORE the swap |
| `os.environ.get("OUTAGE_ALERT_TO")` | `resolve(..., "OUTAGE_ALERT_TO", ...)` | medium | same pre-seed pattern |
| `os.environ.get("PAYROLL_VARIANCE_EMAIL_TO")` | `resolve(..., "PAYROLL_VARIANCE_TO", ...)` | low | helper + pre-seed |
| `os.environ.get("ADMIN_DEAD_LETTER_EMAIL")` | `resolve(..., "ADMIN_DEAD_LETTER_TO", ...)` | low | helper + pre-seed |
| `os.environ.get("DISPATCH_EMAIL")` | `resolve(..., "DISPATCH_ROLE_TO", ...)` | low | helper + pre-seed |
| `os.environ.get("SUPER_ADMIN_EMAIL")` | `resolve(..., "SUPER_ADMIN_TO", ...)` | low | helper + pre-seed |
| `backend/routes/trench_safety/notifications.py:229` role map | absorb into `resolve` with `route_key="TRENCH_SAFETY_PULSE_BY_ROLE.<role>"` | medium — different shape | one PR; preserves the role→recipient contract |
| `backend/pm_routing.py:40-41` always-CC | `resolve(..., "COMPLIANCE_ALWAYS_CC", ...)` | low | already aliased |
| `backend/pm_routing.py:28-31` PM dict | DELETE; require `project_managers` collection populated | medium — needs verification | pre-seed check: refuse to start if `project_managers` is empty |
| `backend/pm_routing.py:216, 293` admin fallback | `resolve(..., "ADMIN_DEAD_LETTER_TO", ...)` | low | helper |
| `backend/auth.py:35-39` OWNER_SEED | env-driven seed list (`OWNER_SEED_EMAILS`) | low | env-driven; MASCI deploy sets it via env vars at boot |
| `backend/safety_users.py:72` | env-driven seed (`SAFETY_SEED_EMAILS`) | low | same |
| `backend/shop_users.py:73` | env-driven seed (`SHOP_SEED_EMAILS`) | low | same |
| `backend/hr_users.py:1` | env-driven seed (`HR_SEED_EMAILS`) | low | same |

### 1.4 Pre-seed migration script
`backend/scripts/track_15_65_seed_email_routes.py`:
* Reads every env var currently in use.
* Writes one `email_routes` doc per route key for `tenant_id="masci"`.
* Writes one `tenant_branding` doc for `masci`.
* Idempotent — re-running is safe.
* Refuses to run on `APP_ENV=production` unless `--allow-prod` flag is explicit.

### 1.5 Backward-compat shims
* `email_routing.load(db)` keeps its existing signature; new layer aliases it.
* `email_routing.get_value(db, key)` keeps its existing signature; new layer routes via `LEGACY_TO_NEW`.

### 1.6 Acceptance for Wave 1
* All 40 Resend send sites resolve recipients identically to today (proven by a comparison harness: run the resolver twice — once against env, once against DB — and assert equal recipient lists for every route).
* Lint clean.
* Existing pytest suites unmodified and passing.

## 2. Wave 2 — Admin UI expansion

### 2.1 Frontend changes
* Expand `AdminEmailRoutingPanel.jsx` to render the 19-row table from Phase 4 §7.
* Add `TenantBrandingPanel.jsx` for sender / reply-to / display / support email / phone / colours.
* Add per-route drawer for to/cc/bcc/enabled/severity-floor + "Send Test" + "Show audit".
* Add `RouteAuditDrawer.jsx` reading `GET /api/admin/email-routing/audit?route_key=...`.

### 2.2 Backend endpoints
* `GET  /api/admin/email-routing` — return all 19 routes + branding.
* `PUT  /api/admin/email-routing/{ROUTE_KEY}` — replace bulk PUT with per-route PUT.
* `POST /api/admin/email-routing/{ROUTE_KEY}/test` — per-route test send.
* `POST /api/admin/email-routing/preview` — dry-run resolver without sending.
* `GET  /api/admin/email-routing/audit` — slice of `email_audit` by route_key.
* `GET/PUT /api/admin/tenant-branding` — branding doc.

### 2.3 Acceptance for Wave 2
* Admin can edit every route, test it, and see the audit row appear in the audit drawer within ~3 seconds.
* Audit row is written for every send in Wave 2, regardless of route.
* No regression in any of the 40 Resend send sites.

## 3. Wave 3 — Multi-tenant separation

### 3.1 Tenant resolution middleware
* Add `Depends(resolve_tenant)` that returns `tenant_id` from one of: subdomain (`acme.mascidocs.com` → `acme`), JWT claim, or a per-deploy env default.
* For the MASCI deploy, default tenant is always `masci`.

### 3.2 Per-tenant scope checks
* All routes resolve against the requesting tenant only.
* All audit rows carry `tenant_id`.
* Branding is resolved against `tenant_branding` per request, with 60-s cache.

### 3.3 Onboarding flow for tenant #2
* New admin endpoint `POST /api/super-admin/tenants` (super-admin only).
* Provisions:
  - tenant row
  - empty branding doc (admin must fill before first email send)
  - 19 empty route docs
  - bootstrap super-admin account for the new tenant
* Until branding + at least the P0 routes are filled, the system refuses to send the tenant's emails (the admin UI shows a red banner enumerating what's missing).

### 3.4 Acceptance for Wave 3
* MASCI continues to work unchanged.
* A second-tenant smoke test (`tenant_id="demo"`) can send an email through every route after only DB-driven configuration.
* No MASCI email leaks to the second tenant's recipients (proven by audit-row tenant_id discriminator + an integration test that creates the demo tenant, sends one of each route, and asserts no recipient list contains a MASCI email).

## 4. Risk register

| Risk | Probability | Mitigation |
|---|---|---|
| Pre-seed misses an env var → silent route | low (script is idempotent, env audit is the inventory) | DRY-RUN mode prints the diff before writing |
| Admin disables a route and a real alert is missed | medium | enabled=false logs a `status=disabled` audit row; admin UI surfaces "disabled" badges |
| Wave 1 deploys with caller still importing `email_routing.get_value` | low | shims preserve the old API exactly |
| Resend rate-limit on a per-route test storm | low | test endpoint already accepts a single recipient |
| `project_managers` collection empty on a fresh second tenant | medium | onboarding refuses to send until at least one PM exists; admin UI red banner |
| Email-audit collection growth | low | retention TTL via existing `usage_events` pattern (optional Wave 3 add-on) |

## 5. Rollback profile

* Wave 1: revert `email_routing_v2.py` + restore inline `os.environ.get` calls. The pre-seed DB docs are harmless if left in place (the old code ignores them).
* Wave 2: revert frontend panel + admin endpoints. Pre-existing `AdminEmailRoutingPanel.jsx` still works against the 6 legacy keys.
* Wave 3: revert middleware. Tenant-scoping defaults to `masci` and existing behaviour persists.

## 6. Effort estimate

| Wave | Backend LOC | Frontend LOC | DB collections touched | Estimated effort |
|---|---|---|---|---|
| Wave 1 | ~600 (engine + 40 site rewrites + seed script) | 0 | 2 | 2-3 sessions |
| Wave 2 | ~250 (5 new endpoints, drawer pagination) | ~500 (panel expand + drawer + branding panel) | 0 | 1-2 sessions |
| Wave 3 | ~250 (middleware + tenant CRUD) | ~150 (super-admin tenant switcher) | 1 (tenants) | 1-2 sessions |
| **Total** | **~1,100 LOC backend · ~650 LOC frontend** | | **3 collections** | **4-7 implementation sessions** |

Plus regression: full Playwright sweep of the 8 portal logins + 14 representative workflows after each wave.

## 7. GO criteria for execution (Track 15.65+)

1. ✅ Phase 1-4 deliverables reviewed and signed off.
2. ✅ Backup of `email_routing_config` (current 6-key collection) + `email_audit` taken.
3. ✅ Pre-seed dry-run produces a recipient diff of **zero** versus current behaviour.
4. ✅ Operator confirms `MASCI` will be the only live tenant during Wave 1.

## 8. Hard-rule compliance (Phase 5)
* ✅ Migration is backward compatible at every wave boundary.
* ✅ Safe migration path — pre-seed before swap so nothing goes silent.
* ✅ Rollback profile written for every wave.
* ✅ No notification outage during rollout — each wave is additive then swap, not destructive.
* ✅ No implementation in this track. Plan only.
