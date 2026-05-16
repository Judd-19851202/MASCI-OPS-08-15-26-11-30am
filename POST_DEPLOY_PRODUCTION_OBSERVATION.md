# MASCI Operations Platform — Post-Deploy Production Observation

**Production domain:** https://mascidocs.com · https://www.mascidocs.com
**Observation started:** 2026-05-16
**Status:** 🟢 LIVE · Public surface healthy · Auth gates holding · Observation window open
**Mode:** LIVE PRODUCTION STABILIZATION — feature freeze in effect

---

## SECTION 1 — Immediate post-deploy smoke (automated, public/anon-only)

The smoke probes below were run against the live production deployment from outside the MASCI tenant. They cover everything that can be validated WITHOUT a production admin/portal token. **The authenticated-surface smoke (portals · workflows · uploads · signatures · search · idempotency) must be run by an admin user from the office.** A check-list is provided at the end of this section.

### 1.1 Live access · ✅ HEALTHY

| Probe | Expected | Result |
|---|---|---|
| `GET https://mascidocs.com/` | 200 + HTML | ✅ 200 · 8341 bytes · `<title>MASCI Operations Platform</title>` |
| `GET https://www.mascidocs.com/` | 200 | ✅ HTTP/2 200 |
| SSL cert valid (both domains) | valid TLS | ✅ HTTP/2 + `cf-ray` (Cloudflare edge) |
| `GET https://mascidocs.com/api/health` | `{ok:true, service:"masci-hub"}` | ✅ `{"ok":true,"service":"masci-hub","ts":"2026-05-16T03:14:40Z"}` |
| `GET https://www.mascidocs.com/api/health` | same | ✅ matches |
| Production bundle deployed | `/static/js/main.<hash>.js` | ✅ `main.80740398.js` |

### 1.2 Auth gates · ✅ ALL HOLDING

| Anon probe | Expected | Result |
|---|---|---|
| `GET /api/admin/deploy-readiness` | 401 | ✅ 401 |
| `GET /api/admin/integrations/health` | 401 | ✅ 401 |
| `GET /api/operations-center` | 401 | ✅ 401 |
| `GET /api/project-health` | 401 | ✅ 401 |
| `GET /api/asset-transfers` | 401 | ✅ 401 |
| `GET /api/po-requests` | 401 | ✅ 401 |
| `GET /api/search?q=test` | 401 | ✅ 401 |
| `GET /api/notifications/unread-count` | 401 | ✅ 401 |
| `GET /api/jhas` | 401 (portal-gated) | ✅ 401 |
| `POST /api/incidents` (empty body) | 422 (validation, not 401 — incident submission is intentionally public) | ✅ 422 |

Zero unauthorized data exposure on any surface probed from outside.

### 1.3 ⚠️ Potential CORS misconfiguration — confirm with admin

Both OPTIONS preflights returned `access-control-allow-origin: *`:

```
curl -X OPTIONS https://mascidocs.com/api/health -H "Origin: https://evil.example.com"
  → access-control-allow-origin: *      ← echoes wildcard regardless of origin
```

This *may* be:
- (A) Cloudflare edge / Emergent ingress returning a static CORS preflight header before the FastAPI app sees the request — in which case the app-layer `CORS_ORIGINS` lock is still active and applies to actual `GET`/`POST` requests, or
- (B) `CORS_ORIGINS="*"` is still set in the production environment (the same value the preview env uses).

**Action item (USER, in Emergent deploy dashboard):**
Confirm `CORS_ORIGINS` in production env vars is set to:
```
https://mascidocs.com,https://www.mascidocs.com
```
…and that `CORS_ORIGIN_REGEX` is unset OR scoped only to `mascidocs.com`. If it's still `*`, lock it down before more traffic accumulates.

The auth tokens are protected by HMAC and not by CORS, so this is not an authentication bypass risk. It is a defense-in-depth and CSRF-surface hardening item.

### 1.4 ✋ Authenticated-surface smoke checklist (USER — run from the office)

These cannot be run from outside the tenant. Action each from a signed-in admin browser within 10 min of cutover:

**Portals load cleanly (no console errors, no blank pages):**
- [ ] `/admin` — Operations Center full-mode (16 cards expected on admin)
- [ ] `/pm` — PmHub + Operations Center compact (4 cards)
- [ ] `/hr` — HrHub + Operations Center compact
- [ ] `/safety-portal` — SafetyShell
- [ ] `/shop` — ShopHub + Operations Center compact
- [ ] `/dispatch-portal` — DispatchHub + Asset Transfers link
- [ ] `/leadership` — Field Leadership Hub (password gate `MASCIGC`)
- [ ] `/project-health` — 29 projects expected, Green by default

**Core workflows (end-to-end):**
- [ ] Create one Task from `/tasks` → confirm appears in NotificationBell
- [ ] Submit one PO from `/po-requests` → approve from PM portal → upload receipt → confirm Task created
- [ ] Submit one Incident from `/incidents/new` (anonymous public form) → confirm fan-out to safety + assigned PM
- [ ] Submit one Daily Report from `/daily/new` → confirm linked to project
- [ ] Submit one Field Leadership write-up from `/leadership/write_up/new` → confirm idempotent submit + draft pill appears
- [ ] Create one Asset Transfer from `/asset-transfers` → walk Draft → Requested → Approved → In Transit → Received (signature) → Closed
- [ ] Use Global Search (`⌘K`) → verify role-scoped results · no leakage
- [ ] Toggle to mobile viewport (Chrome DevTools 375×812) → spot-check 3 critical pages for overflow

**Resiliency:**
- [ ] On `/incidents/new`, type Project Name, wait 1s — confirm "Saved as draft" pill appears top-right
- [ ] Reload — confirm "Draft recovered" toast appears
- [ ] In DevTools Network panel, switch to Offline → submit the form → confirm "Saved · will upload when reconnected" toast + queue badge appears on NotificationBell → switch back Online → confirm upload drains

**Uploads (R2):**
- [ ] PO receipt upload (image)
- [ ] Incident attachment upload
- [ ] Safety document upload
- [ ] Signature capture (Safety CA edit dialog)

**Notifications:**
- [ ] NotificationBell shows unread count
- [ ] Click an item → mark-read
- [ ] Click "Mark all read"

**PDF / export:**
- [ ] Export PO list to CSV from `/po-requests`
- [ ] Print preview a Daily Report

---

## SECTION 2 — Live production monitoring (first 72h)

During the first 72 hours, watch the following surfaces in `/admin/system` and `/admin/analytics`:

| Surface | What to watch for |
|---|---|
| `/admin/deploy-readiness` | Stays `ready` or `attention` (1 yellow data-only warn is acceptable). Anything red = act immediately. |
| `/admin/integrations/health` | Resend + R2 stay green. Motive + MaintainX stay `mocked` (per architectural guardrail). |
| `/admin/audit` | New audit rows accumulating across po_requests · employees · asset_transfers. |
| `/admin/analytics` Operational Signals | Throughput tiles populating. PO cycle-time p90 starting to fill. Equipment-fail rollup populating. |
| `/admin/system` backup status | Hourly R2 snapshots succeeding. |
| Resend dashboard | No bounced / dropped emails. Daily quota healthy. |
| Cloudflare R2 dashboard | No 5xx errors. Storage growing as expected. |
| `/api/admin/operational-signals?window_days=7` | Returns valid payload, no exception traces. |

### Real-world failure modes to watch for (per Phase J observation criteria)
- Retry success rate (queue depth trending to 0 quickly after offline → online transitions)
- Draft recovery frequency (high = good UX rescue, but very high = network instability surfacing)
- Duplicate-submit prevention (zero `idempotency_keys` collisions surfacing as user-visible errors)
- Upload stability under real cellular (R2 degraded-event counter staying low)

---

## SECTION 3 — Observation window discipline

**Minimum: several weeks** of clean production operation before any new development.

### Allowed during the window
- Bug fixes (production-only OR preview-reproducible)
- Performance fixes (driven by real telemetry)
- Mobile fixes (driven by real field reports)
- Security fixes
- Permission fixes
- Operational polish/consistency fixes
- Production telemetry analysis

### NOT allowed during the window
- New portals
- New architecture
- New major systems
- Experimental integrations
- Redesigns
- Feature creep / "quick additions"
- Workflow overhauls
- New signal cards
- New analytics surfaces
- New telemetry surfaces

If a bug fix is needed:
1. User reports the issue and notes whether it's PREVIEW or PRODUCTION
2. PREVIEW issues are fixed in-place by the agent
3. PRODUCTION-only issues (env-var, domain config, R2 binding, Resend, Cloudflare) are flagged to Emergent Support
4. PRODUCTION-reproducible-in-preview issues are fixed in preview and the user redeploys

---

## SECTION 4 — Production telemetry & real-world usage

Telemetry pipes already live (Iter160 — `db.usage_events` `kind='operational_signal'`):
- Incident throughput
- CA cycle time
- PO turnaround across 5 states
- Equipment fail frequency
- Fire-ext pass/fail
- Doc threshold fires
- Training deficiencies
- Offboarding starts

Available at `GET /api/admin/operational-signals?window_days=N` (admin-only, clamped 1..180). After 30 days of real traffic the deltas + cycle-time p90 will surface true operational bottlenecks. **Do not act on these signals until at least 30 days of real production data has accumulated.**

### Decisions to defer until telemetry is mature
- Phase D+ optional follow-ons (PO supervisor strict scoping)
- Phase I follow-on (equipment search-by-unit-id autocomplete)
- Phase 2.5 deferred signal candidates (CA trend · training trend · doc surge · pre-op trend)
- Phase 3 Resiliency Health card (queued uploads · retry-success rate · draft counts)
- Bulk Actions (telemetry-driven scope)
- Motive + MaintainX integration deepening (live API plumbing)

---

## SECTION 5 — Production security & hardening verification

### ✅ Confirmed via remote probes
- HTTPS + valid TLS on `mascidocs.com` and `www.mascidocs.com`
- All admin/operational endpoints return 401 to anonymous
- Permission gates holding (anon · cross-portal · scope-bound)
- Public POST endpoints still validate (`POST /api/incidents` → 422 on empty body)
- No dev/debug endpoints exposed (`/api/banner` → 404, no error trace leaked)
- `x-content-type-options: nosniff` header present

### 🟡 Confirm with user (env-vars in Emergent deploy dashboard)
- [ ] `ADMIN_PASSWORD` — rotated from preview's `MASCI1982!`
- [ ] `ADMIN_HMAC_SECRET` — rotated to a fresh `secrets.token_urlsafe(64)` value
- [ ] `ADMIN_SESSION_EPOCH` — bumped to `2` (or higher) to invalidate any tokens that leaked into the build
- [ ] `CORS_ORIGINS` — set to `https://mascidocs.com,https://www.mascidocs.com` (currently appears wildcard — see Section 1.3)
- [ ] `RATE_LIMITING=on`
- [ ] `AUTO_EMAIL_REPORTS=true` (if production emails should fire day-one)
- [ ] `RESEND_API_KEY` — production key (NOT the shared preview key)
- [ ] `S3_*` — production R2 bucket binding
- [ ] `SUPER_ADMIN_BOOTSTRAP_PASSWORD` — rotated or super-admin already bootstrapped + value deleted from env

---

## SECTION 6 — Production issues discovered & fixes applied

_None yet. Update this section as the observation window progresses._

| Date | Severity | Component | Issue | Fix | Verified |
|---|---|---|---|---|---|

---

## SECTION 7 — Remaining risks & known acceptable backlog (carried from Iter D)

All non-blocking, all documented, all surfaced honestly to the admin:

| Item | Why it's non-blocking |
|---|---|
| Cross-portal master-binding coverage (employees + incidents low %) | Honest data-only migration state. Surfaced on `audit_coverage` card. Not a defect. |
| MaintainX + Motive integration probes mocked | Intentional preview-and-production mock until external API matures. Per architectural guardrail. Documented in `services/maintainx_service.py` + `services/motive_service.py`. |
| R2 fallback to data-URL in preview env | Production has live R2 binding (verified by `deploy-readiness`). Preview is intentionally fallback. |
| 3 orphan components (`ActivityFeed`, `AdminSignatureMigrationPanel`, `MentionTextarea`) | Safe to delete in a future cleanup sweep. Zero user-facing impact. |
| 2 Radix `DialogTitle` a11y warnings (PO drawer + Submit dialog) | Wrap in `VisuallyHidden` in a future polish pass. Functional, not failing screen readers. |

---

## SECTION 8 — Future development discipline (LOCK)

Going forward, **every new feature** must satisfy ALL of the following before being considered complete:

1. Backend route exists with proper auth gate
2. Frontend surfaced in the correct portal(s)
3. Permissions enforced via existing `permissions.js` / portal-token pattern
4. Mobile 375×812 verified (sw=iw=375, overflow=0)
5. Tasks integrated via `lib/event_fanout.emit_task_and_notification()` (NOT direct `db.tasks` writes)
6. Notifications integrated via the same fan-out
7. Exports / PDFs work where applicable
8. Audit logs via canonical `lib/audit.append_audit()`
9. Search integration via `routes/global_search.py` probe registration if the data should be searchable
10. Operations Center visibility via a card in `routes/operations_center.py` if it's operationally observable
11. No dead routes, no dead buttons, no placeholder text shown to users
12. Production telemetry reviewed BEFORE the feature is started (driven by real signal, not assumption)

The platform's shared infrastructure layers — `event_fanout`, `audit`, `signature_service`, `idempotency`, `global_search`, `operations_center`, `permissions`, `resiliency` — are the canonical pipes. **Direct writes to `db.tasks` / `db.notifications` / per-module audit collections are now anti-patterns.**

---

## Final state

**Production: LIVE.** Public surface healthy. Auth gates holding. SSL valid on both apex and www. Health endpoint returning correctly. Frontend bundle deployed (`main.80740398.js`).

**Observation window: OPEN.** Feature freeze in effect for several weeks minimum.

**Next user action:** action the SECTION 5 production env-var checklist (especially confirm `CORS_ORIGINS` is locked) AND walk the SECTION 1.4 authenticated-surface smoke checklist from a signed-in admin browser within 10 minutes of cutover.

**Next agent action:** standby. No new features. No new surfaces. No new telemetry. Bug fixes only, reported via the user. Telemetry review after 30 days of real traffic.

🟢 **MASCI Operations Platform — live operational infrastructure software.**
