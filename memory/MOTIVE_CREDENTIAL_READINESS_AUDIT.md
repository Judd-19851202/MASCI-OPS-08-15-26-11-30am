# MASCI · Motive Credential Readiness Audit

**Date**: 2026-02-12 · **Mode**: Read-only · **Authorized**: NO BUILD · NO CHANGES · NO DEPLOY · NO HELPDESK
**Scope**: Verify whether MASCI already possesses everything required to begin M-1 (real Motive API client) without requesting new credentials.

---

## 1 · Executive Summary

> **No Motive credentials exist anywhere in the MASCI codebase, database, environment, or production secrets. No FleetWatcher integration exists either. The only Motive-related env reference (`MOTIVE_API_KEY` read in `integration_health.py:128`) currently resolves to an empty string in every environment.**

The integration framework is fully built and waiting; the credentials simply do not exist yet. M-1 cannot begin until an operator obtains and provisions a Motive API key. There is no "reuse" path available because there is no existing key to reuse.

---

## 2 · Existing Credential Evidence

### Q1 · Does MASCI already possess a Motive API key?

**Verdict: DOES NOT EXIST.**

| Where I looked | Result |
|---|---|
| `/app/backend/.env` | No `MOTIVE_*` line. Verified via `grep -ni "^MOTIVE" backend/.env`. |
| `/app/frontend/.env` | No `MOTIVE_*` line. |
| Production secrets template (`/app/memory/PRODUCTION_SECRETS_SEALED.env.template`) | Zero matches for "motive". The template carries `MONGO_URL`, `JWT_SECRET`, `RESEND_API_KEY`, `S3_*`, `ADMIN_HMAC_SECRET`, `SUPER_ADMIN_BOOTSTRAP_PASSWORD`, `MFA_ENCRYPTION_KEY`, but **no Motive line**. |
| `integration_settings` collection (preview Mongo) | Direct query: `db.integration_settings.find_one({"provider": "motive"})` → returns **None**. The seed function in `_storage.py:103-115` is supposed to insert a default row, but no row exists in preview — implying the seed has not run on this DB OR was never persisted. |
| All `*.md` documentation in `/app/memory/` | No Motive credential. Only descriptive references in the recent audit reports. |
| Stored secrets, integration center docs, deployment notes | None. |

### Q2 · Is FleetWatcher currently configured to use Motive?

**Verdict: NO — FleetWatcher does not exist in this codebase.**

`grep -rni "fleetwatcher\|fleet_watcher\|fleet-watcher" backend/ frontend/src/` returns **only** references inside my own audit document `/app/memory/MOTIVE_API_CAPABILITY_AUDIT.md`. No FleetWatcher integration module · no FleetWatcher env vars · no FleetWatcher config · no FleetWatcher service class · no FleetWatcher database collection.

Implication: there is no shared FleetWatcher↔Motive key inside MASCI Docs. If MASCI operates a FleetWatcher account at the company level, the Motive API key (if any) used by that account lives in FleetWatcher's vendor portal, **not** in this codebase.

### Q3 · If FleetWatcher uses a Motive API key, can MASCI Docs use the same key?

**Verdict: UNKNOWN at the code level — TECHNICALLY YES, ORGANIZATIONALLY REQUIRES OPERATOR DECISION.**

| Constraint | Evidence |
|---|---|
| Technical | Motive issues **one API key per organization** (per `developer-docs.gomotive.com/docs/authentication`). The same key works for any backend, so MASCI Docs *could* technically share the key with FleetWatcher. |
| Organizational | Sharing a single key across vendors is the operator's prerogative. **Rotation risk**: if FleetWatcher rotates its key (or vice-versa), the other consumer breaks. Cleanest practice is one key per consumer. |
| Motive limitation | None published — Motive does not prohibit multiple consumers using the same key. |

This question cannot be answered from inside MASCI's codebase. It requires the operator to confirm whether FleetWatcher is in fact using a Motive API key and whether they wish to share it.

### Q4 · Does the platform already contain Motive credential placeholders?

| Placeholder | Status | Location |
|---|---|---|
| `MOTIVE_API_KEY` | **PARTIALLY FOUND** | Read at `backend/routes/integration_health.py:128` only. Resolves to `""` when unset. No `.env` line. No production-secrets template line. |
| `MOTIVE_API_BASE` | **NOT FOUND** | Zero matches in code or docs. |
| `MOTIVE_WEBHOOK_SECRET` | **NOT FOUND as an env var** | Webhook secret is held PER-PROVIDER inside the `integration_settings` Mongo collection (`webhook_secret_value` field), not in a Motive-specific env var. This is by design — the existing framework reads it from Mongo, not env. |
| `MOTIVE_ENABLED` | **NOT FOUND as an env var** | The platform uses `integration_settings.enabled` (per-provider Mongo field) instead. |
| `MOTIVE_AUTO_TRANSITION` | **NOT FOUND** | Does not exist in code or env. Was proposed in the M-1 audit, never implemented. |
| `MOTIVE_POLL_INTERVAL_SECONDS` | **NOT FOUND** | Same — proposed, not implemented. |

**Interpretation**: the platform's design pattern is *Mongo-stored* per-provider settings (already shipped via `integration_settings`), not env vars. The env var read in `integration_health.py` is the ONE exception — and only used for the lightweight health probe.

---

## 3 · Existing Webhook Evidence

### Q5 · Does the existing webhook receiver require additional setup?

**Verdict: RECEIVER IS LIVE BUT GATED. Awaiting only (a) `enabled=true` and (b) `webhook_secret_value` on the `integration_settings` row.**

Evidence from `backend/routes/integrations/webhooks.py:38-75`:

| Stage | Behavior today | Required to flip live |
|---|---|---|
| Route mounted | ✅ `POST /api/integrations/motive/webhook` is registered (verified by mounting in `routes/integrations/__init__.py`) | none |
| Read settings row | ✅ reads `enabled`, `test_mode`, `webhook_secret_value` from `db.integration_settings.find_one({"provider":"motive"})` | The row must exist (seed didn't fire on this preview pod — needs one insert) |
| No-secret short-circuit | ✅ Returns `{"ok": False, "status": "awaiting_credentials"}` if secret missing AND not in test_mode | set `webhook_secret_value` |
| Signature verify | ✅ `verify_webhook_signature_stub()` uses `HMAC-SHA256(secret, raw_body) → hex` and `hmac.compare_digest` against header | confirm Motive's actual scheme matches HMAC-SHA256 hex; if not, replace this one function (10 LOC) |
| Dispatch to service | ✅ `MotiveService(db, doc).process_webhook(raw_body, headers, test_mode)` | service is stubbed — this is the M-1 work |
| Error logging | ✅ Writes to `integration_error_logs` on bad signature | none |
| Sync logging | ✅ Writes to `integration_sync_logs` on every hit | none |

**Net**: the receiver is "complete + stubbed at the last mile". Filling in `MotiveService.process_webhook()` is part of M-1; the webhook plumbing is not.

---

## 4 · Existing Configuration Evidence

| Component | State |
|---|---|
| Integration framework (14 modules) | ✅ shipped — `backend/routes/integrations/` |
| `MotiveService` class | 🔴 6 methods stubbed (`services/motive_service.py`) |
| `integration_settings` collection | ⚠️ schema exists, indexes exist (`_storage.py:88`), but **no `motive` row in preview Mongo** today |
| `motive_events` collection | ✅ indexed at startup (`event_at` index) — ready to receive |
| `asset_mappings` / `employee_mappings` | ✅ shipped — `motive.vehicle_id`, `motive.driver_id`, `motive.device_id`, `motive.gps_enabled`, `motive.dashcam_enabled` fields all in `_models.py` |
| Webhook receiver | ✅ live + signature-gated |
| Admin Integration Center UI | ✅ shipped — 1 221 LOC at `frontend/src/pages/admin/AdminIntegrationCenter.jsx` |
| Dispatch integration tab UI | ✅ shipped — `DispatchIntegrationsTab.jsx` already renders Motive KPIs from the existing API shape |
| Existing scheduler pattern for polling | ✅ shipped — `lib/singleton_scheduler.py` + the D-1.4 reminder loop is the model |
| Dispatch state machine geo-event seam | ✅ `_record_transition(actor, geo)` already accepts a Motive actor |

---

## 5 · Actual M-1 Blockers

| # | Item | Class | Resolvable by |
|---|---|---|---|
| **B1** | No Motive API key anywhere in env / Mongo / template / docs | **MISSING CREDENTIAL** | Operator obtaining a key from Motive (Help Center → request) |
| **B2** | No `integration_settings` row for `provider:"motive"` on this Mongo (preview at minimum) | **MISSING CONFIG** | One row insert — happens automatically the moment the operator opens the Admin Integration Center and saves any setting (the existing seed function fires too on next deploy where it hasn't yet) |
| **B3** | `MotiveService` 6 methods are stubs | **MISSING CODE** (the M-1 sprint itself) | The M-1 sprint |
| **B4** | Webhook signature scheme — current implementation assumes HMAC-SHA256 hex; Motive's actual scheme is unconfirmed | **MISSING CONFIG** (low risk · 10 LOC patch if different) | Verifiable at first webhook receipt with credentials |
| **B5** | `jobs_master` has no `lat/lng` (geofence auto-create requires geocoding) | **MISSING CODE** (M-3 within the M-1 sprint plan) | M-3 sub-task |

**No "BLOCKER" class items**. All five are either credential, config, or scoped code work — not architectural showstoppers.

---

## 6 · Fastest Path To M-1

### Q6 · What exactly prevents M-1 from starting today?

**Strictly speaking — only B1 (the API key).** Everything else is either deferrable to within the M-1 sprint or auto-resolves once the key lands and a setting row gets saved.

### Q7 · Can M-1 begin immediately if operator pastes an existing Motive API key?

**YES** — with two clarifications:

1. **If the operator already has a Motive API key** (from any source — Motive Console, an existing FleetWatcher account, a prior integration project) and pastes it into the Admin Integration Center → `integration_settings.api_key`, **M-1 can begin the same day**. The framework will save the row, the webhook will activate, and the sprint can start filling in `MotiveService` methods.
2. **If no key exists anywhere yet**, the operator must request one from Motive (Help Center ticket → article 6177129182621 → 1 business day turnaround typical). M-1 starts the day the key arrives.

There is no MASCI-side code change required to "accept" the key — the field is already wired in `integration_settings.api_key` and read by the existing `MotiveService.__init__`.

### Q8 · Operator action minimization

| Option | Status | Action required | Speed | Safety | Risk |
|---|---|---|---|---|---|
| **A · Reuse existing credentials** | ❌ **NOT AVAILABLE** in this codebase. No prior Motive key found in env, Mongo, secrets, or docs. If the operator has a key from outside this codebase (Motive Console, FleetWatcher portal, etc.) it can be pasted; that's still **Option B from MASCI's perspective**. | n/a — there is nothing to reuse | n/a | n/a | n/a |
| **B · Use an existing key the operator already holds** (Motive Console / FleetWatcher portal) | ✅ **VIABLE if operator has one** | Paste into Admin Integration Center → save | **Fastest · same-day** | **Safe** — one key, scoped to org | Low — single key shared between FleetWatcher and MASCI carries a coordination risk on rotation |
| **C · Request a new Motive API key** | ✅ **VIABLE always** | Submit Motive Help Center ticket → request API key → wait ~1 business day → paste into Admin Integration Center | 1–2 business days | **Safest** — separate keys per consumer = independent rotation | Lowest operational risk · no coordination with FleetWatcher |

**Ranking**:
- **Fastest**: B (if a key already exists outside MASCI) → C (if not)
- **Safest**: C (separate key per consumer)
- **Lowest operational risk**: C (key rotation independence)

---

## 7 · Operator Actions Required

Choose ONE path:

### Path 1 — fastest (if a Motive key already exists somewhere)
1. Operator locates an existing Motive API key (Motive Console → Account → API · or FleetWatcher account manager).
2. Operator opens Admin Integration Center → Motive → paste the API key → save.
3. **M-1 sprint begins same-day.**

### Path 2 — cleanest (separate key per consumer)
1. Operator submits Motive Help Center ticket → request API key (article 6177129182621).
2. ~1 business day later, Motive issues the key.
3. Operator pastes into Admin Integration Center → save.
4. **M-1 sprint begins.**

In either path, the operator does NOT need to:
- Modify any .env file
- Touch the production deployment
- Wire any new endpoint
- Change any code

The only operator surface for credential entry is the existing Admin Integration Center UI.

---

## 8 · Final Verdict

# **M-1 REQUIRES NEW KEY**

**Justification**:
- No Motive API key exists in this codebase, environment, database, production secrets template, or documentation.
- No FleetWatcher integration exists either, so there is no existing key to "share".
- Every other prerequisite — webhook receiver, mapping schema, integration framework, dispatch state-machine seam, UI tiles, scheduler pattern — is **already shipped and waiting**.

**However**, "REQUIRES NEW KEY" does NOT mean "requires Motive approval beyond standard key request". It means the operator must obtain a Motive API key — either:
- by retrieving one the operator already holds in an external system (Motive Console / FleetWatcher portal) → **same-day start**, or
- by submitting a Motive Help Center request (article 6177129182621) → **~1 business day start**.

No new code, no new deploy, no new env var pass, no new Motive approval. Once the key is pasted into the existing Admin Integration Center UI, **the M-1 sprint can begin immediately**.

---

**End of audit. No code changed. No env changed. No deploy. Awaiting operator credential action.**
