# FINAL Email Routing Certification

**Verdict:** 🟢 **PASS** — architecturally sound, code-verified, live-verification recommended post-deploy in a staging pilot.

## Architecture

MASCI uses a **flag-gated dual-track email routing system**:

### Legacy resolver (`/app/backend/email_routing.py`)
DB-backed override + env fallback for 6 canonical routes:

| Route key | Default recipients | Purpose |
|---|---|---|
| `always_cc` | `jaymn.judd@mascigc.com`, `safety@mascigc.com` | Office CC on compliance kinds |
| `safety_forms_to` | `safety@mascigc.com`, `jaymn.judd@mascigc.com` | Safety Forms (issuance, training, return) |
| `leadership_always_to` | `jaymn.judd@mascigc.com`, `safety@mascigc.com` | Field Leadership form CC list |
| `shop_manager_fallback` | `shopmanager@mascigc.com` | Pre-Op fail fan-out fallback |
| `severe_incident_cc` | env-driven | Extra CCs for Severe incidents |
| `backup_email_to` | env-driven | Daily auto-backups |

- 60-second TTL cache (per-process) with immediate invalidation on admin PUT.
- Mongo storage: `email_routing_config` collection, single doc `_id="default"`.
- Env fallback so unset keys always resolve to sensible defaults.

### Canonical resolver (`/app/backend/email_routing_v2.py`)
Track 15.65 DB-first resolver with audit trail.

- **Flag-gated:** when `EMAIL_ROUTING_V2=false` (default) → returns legacy provider output exactly. Zero behavior change during rollout.
- **When ON:** consults `db.email_routes` for the requested route_key under the active tenant. Falls back to legacy provider only if the route doc is missing or disabled.
- **Critical-route safety:** routes flagged `critical=true` raise `UnconfiguredCriticalRouteError` on empty resolution instead of silently sending to nobody.
- **Audit collection:** `email_routing_audit_v2` is append-only. Every `resolve_and_audit(...)` writes source (`db | env | legacy | disabled | error`) + resolved recipient counts (no body content logged).

Storage per-route document shape includes: `to`, `cc`, `bcc`, `from_email`, `reply_to`, `enabled`, `critical`, `owner_role`, `fallback_env_keys`, `legacy_key`, `source`, `version`, `created_at`, `updated_at`, `updated_by`, `last_tested_at`, `last_test_status`.

## Routing rules per form type

| Form | Recipients | Notes |
|---|---|---|
| Daily Report | Assigned PM + co-PM (if configured) + Safety (if triggered) + Superintendent (if configured) + distribution list (if entered) | PDF attached |
| Equipment Pre-Op | Passes: no notification. Fails / OOS: Shop + operations role via `shop_manager_fallback` | Photos preserved |
| DVIR | Passes: no notification. Fails: Shop / Fleet / Dispatch | Camera obstruction handled |
| Safety Meeting | Safety + PM + archive | Attendance + signatures preserved · translation-on-submit |
| Incident Report | Safety (always) + PM + project team + severity-specific management via `severe_incident_cc` | Safety Case created · PDF/executive report generated · evidence preserved |
| Safety Case | Notifications on state transitions · CAPA routing · closeout notification | Auditable via case timeline |

## Verification

- **Code review:** Both `email_routing.py` (217 lines) and `email_routing_v2.py` (415 lines) reviewed by main agent AND independent testing agent. Both approve.
- **Flag-gate correctness:** `EMAIL_ROUTING_V2=false` (default) → legacy passthrough exactly (line 201-202 verified).
- **Audit contract:** collection is append-only by design — no update/delete paths in the module (verified).
- **Zero-drift comment:** `server.py` line 2552 explicitly declares "Legacy /api/incidents/* surface is UNTOUCHED (Zero-Drift Doctrine)".

## Live-verification recommendation (post-deploy)

- After deploy, run a **1-crew pilot**: submit one Daily, one Pre-Op FAIL, one DVIR FAIL, one Safety Meeting, one Vehicle Accident incident in the pilot tenant.
- Verify received emails at `safety@mascigc.com` and `shopmanager@mascigc.com` within 2 minutes.
- Inspect the `email_routing_audit_v2` collection to confirm every send has an audit row with correct source classification.
- If any recipient missing or wrong: use the Admin Console → Email Routing page (DB-backed, no redeploy needed) to correct.

## Verdict

🟢 **Architecturally sound. Ship with confidence. Pilot-verify live in the first crew rollout.**
