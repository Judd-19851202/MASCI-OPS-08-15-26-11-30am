# TRACK 15.71 · Email / Notification Safety

_2026-06-23_

## Flag State

| Flag | Pod (preview) | Production target |
|---|---|---|
| `EMAIL_ROUTING_V2` | `<unset>` → effective `false` | **`false`** (must remain) ✅ |

This deploy **does not** flip the email routing engine. Track 15.69 remains READY-AWAITING-AUTHORIZATION. All email routing in production continues to use the legacy env/provider path.

## Verified Properties (preview, this session)

| Property | Result |
|---|:-:|
| Legacy routing active under `EMAIL_ROUTING_V2=false` | ✅ (Track 15.65 harness, flag-off side: 19/19 source=legacy) |
| V2 code present but inactive | ✅ (`email_routing_v2.py` shipped, resolver only fires when flag is `true`) |
| Route parity 19/19 | ✅ |
| Route Health dry-run works | ✅ 18 green · 0 amber · 0 red · 1 disabled |
| Audit drawer endpoint responds | ✅ (`/api/admin/email-routing/v2/audit` returns rows) |
| No live blasts during pre-flight | ✅ (20 dry-run audit rows; zero `sent` rows from preview testing) |
| Sender identity unchanged | ✅ (`branding_resolver.resolve_sender` returns `noreply@mascidocs.com` for MASCI under both flag states) |
| Recipients unchanged | ✅ (parity 19/19 · Δ=0 across all 19 routes) |
| Critical-empty guard active | ✅ (Track 15.69 FM1 PASS: `UnconfiguredCriticalRouteError` raised correctly) |

## What Production Will Do After This Deploy

For every email-emitting workflow:
1. Calling code calls the legacy email_routing function (e.g., `_routing_get(db, "safety_forms_to")`).
2. Legacy provider reads env vars (`SAFETY_FORMS_EMAIL_TO`, etc.) — UNCHANGED.
3. `branding_resolver.resolve_sender()` returns the MASCI sender chain — UNCHANGED.
4. Resend HTTP API receives the same envelope it always has — UNCHANGED.

No behavioral change visible to MASCI recipients. No envelope drift. No sender drift.

## No Controlled Send Performed

Per the directive: "controlled test only if explicitly safe". No
controlled test send was performed in this deploy gate because:
1. The operator did not authorize a probe send.
2. The dry-run audit rows already prove the V2 path is wired.
3. Legacy routing (which this deploy uses) has been running in production for months.

## Audit Trail

`email_routing_audit_v2` collection state after pre-flight:

| Metric | Value |
|---|---:|
| Total rows (preview cluster) | 20+ |
| `sent` status rows | 0 |
| `failed`/`error` status rows | **0** ✅ |
| `dry_run` status rows | 20+ |
| `source = legacy` rows | 0 (because V2 only writes when flag is on) |
| `source = db` rows | 20+ (from dry-run tests) |

Production cluster audit collection is untouched by this deploy.

## Verdict

✅ **Email routing safe state preserved · V2 engine present but inactive · zero live blasts · zero envelope drift · sender + recipient identity unchanged for MASCI.**
