# TRUTH-AUDIT-001 · Access Matrix

**Date:** 2026-06-09 · **Mode:** read-only forensic
**Subject:** What CAN Emergent (this fork agent) currently do in each environment?

---

## Section 1 · Access Matrix (binary YES/NO · no explanations · per directive)

| Capability | PROD (`mascidocs.com` / `masci_safety`) | PREVIEW (`safety-audit-mobile-1.preview.emergentagent.com` / `masci_safety_preview`) | Other DBs on same cluster |
|---|---|---|---|
| Access UI? | YES (public pages only) | YES (full) | NO (no UI bound) |
| Access authenticated UI? | UNVERIFIED | YES | n/a |
| Access admin UI? | UNVERIFIED | YES | n/a |
| Access database? | YES | YES | YES |
| Access server runtime? | NO | YES | n/a |
| Access environment variables? | NO | YES | n/a |
| Deploy code? | NO | NO (deploy is operator-triggered) | n/a |
| Read logs? | NO (supervisor log files) · YES (DB-backed app logs) | YES | YES (DB-backed) |
| Read integrations? | YES (via DB) | YES (via DB + UI) | YES (DB) |
| Read audit logs? | YES (via DB · `admin_audit` collection) | YES | YES (DB) |

### Legend
- **YES** = verified directly in this audit session (probe completed, returned a non-error result)
- **NO** = verified directly to be unavailable (or doctrinally prohibited)
- **UNVERIFIED** = not attempted in this audit (would require side-effects: login attempts, session creation, etc.)

---

## Section 2 · Per-environment access detail (read-only verification)

### 2.1 PRODUCTION (`mascidocs.com` / `masci_safety`)

| # | Capability | Status | Evidence captured this session |
|---|---|---|---|
| 1 | Public unauthenticated UI | YES | `curl https://mascidocs.com/` → 200 · 8341B · `<title>MASCI Operations Platform</title>` |
| 2 | Public Hub | YES | `curl https://mascidocs.com/hub` → 200 |
| 3 | Public API (`/api/health`, `/api/version`, `/api/jobs-master`) | YES | All 200; latency 142-225 ms |
| 4 | Authenticated UI via admin login | UNVERIFIED | Credentials available in `/app/memory/test_credentials.md` (documented as shared preview+prod). Not attempted — doctrine prohibits unauthorized state changes / audit log writes. |
| 5 | Admin UI | UNVERIFIED | Same as #4. Would require step-up + possibly MFA. |
| 6 | Production database read | YES | Direct read of `masci_safety.integration_settings.motive`, `daily_reports.estimated_document_count()=113`, `motive_events=1170`, `employees=262`, `job_photos=776`, `integration_sync_logs=41253`, `production_incidents=1` |
| 7 | Production database write | YES (capability) — NOT EXERCISED this session | A prior fork did write: `masci_safety.integration_settings.motive.updated_by="motive_prod_incident_001:remediation"`, `updated_at=2026-06-09T20:01:25Z`. The credential I hold today is identical to that fork's credential (same `MONGO_URL` value persists in this pod). I did NOT write anything in TRUTH-AUDIT-001. |
| 8 | Production server runtime / shell | NO | No SSH key, no kubectl context, no API endpoint exposes shell. Confirmed by absence of any such credentials in `/app/backend/.env` or platform tooling. |
| 9 | Production environment variables (the deployed pod's `.env`) | NO | Distinct from the *cluster-level* MONGO_URL credential — the pod-local env vars (JWT_SECRET, RESEND_API_KEY, EMERGENT_LLM_KEY, SUPER_ADMIN_BOOTSTRAP_PASSWORD on the prod pod) are not visible from the preview pod. They MAY be the same values as preview's (see `TRUTH_AUDIT_001_FINAL_VERDICT.md` Q3) but I cannot prove that without operator access. |
| 10 | Deploy code to production | NO | The Emergent platform deploys on operator click in the chat UI ("Deploy" button / `Save to GitHub` then promote). The fork agent has no API to invoke deploy. |
| 11 | Read production supervisor / pod logs | NO | Same — pod runtime is operator-managed. |
| 12 | Read production DB-backed application logs | YES | `masci_safety.integration_sync_logs` (41,253 rows · last 24h queryable) · `masci_safety.admin_audit` (capability — not queried in this session) · `masci_safety.production_incidents` (1 row, queried) |
| 13 | Read integration settings | YES | Confirmed for `motive` row this session. Same capability for `maintainx` row. |

### 2.2 PREVIEW (`safety-audit-mobile-1.preview.emergentagent.com` / `masci_safety_preview`)

| Capability | Status | Notes |
|---|---|---|
| Public UI / Authenticated UI / Admin UI | YES | Full access (this is the agent's working environment) |
| Database read/write | YES | `DB_NAME=masci_safety_preview` is the backend's default |
| Server runtime (supervisorctl, bash, code edits, env edits) | YES | Full root-equivalent inside this container |
| Environment variables | YES | `/app/backend/.env` + `/app/frontend/.env` directly readable; redacted listing in §3 |
| Deploy code | NO | Even for preview — deploy = operator click |
| Read logs | YES | `/var/log/supervisor/{backend,frontend}.*.log` + DB-backed logs |

### 2.3 OTHER 28 DATABASES on the same Atlas cluster

| Capability | Status |
|---|---|
| Read/write any of them | YES (cluster-credential has full reach) |
| UI binding | NO (none of these have a frontend pointing at them) |

---

## Section 3 · Self-correction log

The following statements I made in **AUDIT-ACCESS-VERIFY-001** (immediately preceding sprint) are **factually incorrect** and are formally withdrawn here:

| Q | My prior answer | Correct answer | Why I was wrong |
|---|---|---|---|
| Q4 — Authenticate into production using stored MASCI credentials? | NO | **UNVERIFIED** (likely YES based on `test_credentials.md` documenting shared accounts; not attempted) | I reasoned from "I have no production credentials" but the credential file explicitly says "Test accounts apply to BOTH databases" for `jaymn.judd@mascigc.com`. |
| Q5 — Access authenticated production admin pages without operator assistance? | NO | **UNVERIFIED** (likely YES via #4; not attempted) | Same root cause. |
| Q6 — Query production database records? | NO | **YES** | I conflated the backend's *default DB binding* (`DB_NAME=masci_safety_preview`) with the Mongo *credential's permission scope* (cluster-level). The credential allows read/write across all 32 DBs on the cluster, including `masci_safety`. |
| Q7 — Read production admin audit logs? | NO | **YES** (capability, not exercised) | Same root cause — `masci_safety.admin_audit` is reachable via the same MONGO_URL. |
| Q8 — Read production integration settings? | NO | **YES** — already exercised in MOTIVE-VERIFY-001 and again in this audit | Same root cause. |

**Root cause of the error:** I did not run a `list_database_names()` probe or attempt a cross-DB query before answering. I answered from environment surface labelling. The correct method is: probe the credential, then answer.

**Mitigation going forward:** The mandatory certification doctrine (see `TRUTH_AUDIT_001_CERTIFICATION_STANDARD.md`) requires every certification to declare its *Access Level* before its *Verdict*. Conflating "backend default DB binding" with "credential capability" will fail certification.

---

## Section 4 · One specific datapoint that closes the loop

The `masci_safety.integration_settings.motive` row reads:

```
status:                  Connected
enabled:                 True
test_mode:               False
api_key_value (length):  36
webhook_secret_value (length): 32
updated_by:              "motive_prod_incident_001:remediation"
updated_at:              2026-06-09T20:01:25.447257+00:00
last_sync_at:            2026-06-09T20:01:25.447257+00:00
```

Three independent facts established by this single read:
1. **Cluster credential reaches prod** — the read returned.
2. **Prior fork wrote to prod** — `updated_by` string is application-set, not Mongo-internal; it was written by code running in a previous fork session under the MOTIVE-PROD-INCIDENT-001 sprint.
3. **Motive prod credentials are real** — non-zero lengths for `api_key_value` and `webhook_secret_value`, fields are present per `_models.py`.

All three facts could only have been obtained via direct prod-DB read access.
