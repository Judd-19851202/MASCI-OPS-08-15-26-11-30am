# TRUTH-AUDIT-001 · Deployment Chain

**Date:** 2026-06-09 · **Mode:** read-only forensic
**Subject:** How code, data, and credentials move (or do not move) between environments

---

## Section 1 · Canonical deployment workflow (what is verifiable)

```
┌────────────────────────────────┐
│  FORK CONTAINER (this pod)     │
│  /app                          │
│  • /app/backend (FastAPI)      │
│  • /app/frontend (React/Craco) │   ← Code authored here by E1 agent
│  • /app/backend/.env (preview) │
│  • DB_NAME=masci_safety_preview│
│  • APP_ENV=preview             │
│  • supervisor-managed services │
└────────────────────────────────┘
              │
              │  "Save to GitHub" (operator click in Emergent chat)
              ▼
┌────────────────────────────────┐
│  GIT REMOTE (operator-owned)   │
│  • commit history              │
│  • branch protection (TBD)     │
└────────────────────────────────┘
              │
              │  Operator clicks "Deploy" → Emergent platform pulls
              ▼
┌────────────────────────────────┐
│  PRODUCTION POD                │
│  • mascidocs.com               │
│  • /app/backend/.env (prod)    │   ← Operator-managed secrets
│  • DB_NAME=masci_safety        │
│  • APP_ENV=production          │
│  • supervisor-managed services │
└────────────────────────────────┘

ATLAS CLUSTER (shared)
┌────────────────────────────────────────────────────────────────┐
│  masci-prod.1nduwmg.mongodb.net                                │
│  • masci_safety           ← PROD writes from prod pod          │
│  • masci_safety_preview   ← PREVIEW writes from this pod       │
│  • + 30 other DBs (restore drills · test isolation · system)   │
│  Credential: single Atlas user with cluster-level read/write   │
└────────────────────────────────────────────────────────────────┘
```

## Section 2 · Step-by-step "code-to-prod" flow

| # | Step | Actor | Credential required | What changes | What does NOT change |
|---|---|---|---|---|---|
| 1 | Agent edits files in `/app` | E1 fork | container root (provided by Emergent) | preview pod's source tree | git remote, prod pod, prod DB, preview DB |
| 2 | Agent restarts services as needed | E1 fork | `sudo supervisorctl` (provided) | preview backend / frontend processes | nothing else |
| 3 | Agent's edits become "savable" | E1 fork | (none — automatic) | a pending diff visible in the Emergent UI | nothing else |
| 4 | **Operator clicks "Save to GitHub"** | Operator | GitHub OAuth (held by operator) | git remote receives commits | prod pod still runs old code |
| 5 | **Operator clicks "Deploy" (or merges + deploy)** | Operator | Emergent platform deploy permission | production pod pulls new code, restarts | preview pod unchanged; preview & prod DB unchanged at deploy time |
| 6 | Prod startup runs `ensure_indexes()` blocks | Prod backend (auto) | already in prod `.env` | prod DB gets new indexes if any (idempotent) | application data unchanged |
| 7 | Prod runtime continues | Operator + real users | all production credentials (JWT/MFA/passkeys/etc.) | prod DB receives live writes | preview DB unaffected |

## Section 3 · What credentials are required at each step

| Step | Credential | Held by |
|---|---|---|
| Code authoring | Container root | Emergent platform (granted to fork agent) |
| GitHub push | GitHub OAuth token | Operator only — via the in-chat "Save to GitHub" affordance |
| Deploy promotion | Emergent deploy permission | Operator only |
| Production env vars (`/app/backend/.env` on prod pod) | Stored in Emergent's secrets panel | Operator only — not visible from fork |
| Atlas Mongo (prod DB read/write) | `MONGO_URL` in preview pod's `.env` | **Currently shared with prod via the same Atlas user.** This is the governance gap surfaced by TRUTH-AUDIT-001. |
| Admin login on `mascidocs.com` | super-admin bootstrap creds in `test_credentials.md` | **Documented as shared between preview and prod.** Likely usable but not verified in this audit. |

## Section 4 · What databases change vs. what does not

| Action | preview DB (`masci_safety_preview`) | prod DB (`masci_safety`) | other 30 DBs |
|---|---|---|---|
| Operator deploy | no change | no change at deploy moment (only on next migration or write) | no change |
| Operator pushes new index in `ensure_indexes()` | next preview restart adds it | next prod restart adds it (idempotent) | no change |
| Operator schema-altering migration script | runs against whatever DB the pod points at | runs against whatever DB the pod points at | no change |
| **Fork agent direct Mongo write** | YES — agents do this daily | YES — capability exists; exercised once (MOTIVE-PROD-INCIDENT-001) | YES — capability exists |
| Public user actions on mascidocs.com | no | yes | no |
| Test pytest fixture | yes (preview default) | typically no, but no enforcement prevents a mis-pointed fixture | yes (some tests create ephemeral DBs — see §5) |

## Section 5 · Observed test-isolation drift

`motor.list_database_names()` returned 21 DBs matching `masci_test_*` or `scheduler_test_*` patterns — pytest fixtures from prior fork agents that did NOT drop their isolation DBs. This is operationally harmless (they're small, named, idle) but it confirms that **agent test runs already create new DBs on the production Atlas cluster**. This is a separate (low-severity) governance observation worth noting.

## Section 6 · What the deployment chain explicitly does NOT do

1. **Does not isolate Mongo credentials between preview and prod.** A single Atlas user is used by both pods. Compromising the preview pod = capability to write the production DB.
2. **Does not isolate `test_credentials.md`.** The same file is read by every fork session and includes admin accounts documented as working in both environments.
3. **Does not have a separate staging environment.** Code goes from fork → git → prod with no intermediate staging tier.
4. **Does not enforce APP_ENV consistency on the prod pod.** Per MOTIVE-VERIFY-001 §APP_ENV-LABEL-001, prod was historically shipped with `APP_ENV="preview"` causing telemetry mis-labeling. POST-DEPLOY-003 claims this was fixed (APP-ENV-001 deploy), and the live `/api/version` returns `"production"` today, but the *defect-by-default-template* in the .env file remains.

## Section 7 · Evidence captured

Listed above. No new commands run in §3-6; all assertions are restatements of evidence already captured in:
- `TRUTH_AUDIT_001_ENVIRONMENT_MATRIX.md` § 4
- `TRUTH_AUDIT_001_ACCESS_MATRIX.md` § 4
- `/app/memory/test_credentials.md` (lines 1-30)
- `/app/memory/MOTIVE_VERIFY_001_FORENSIC_RECONCILIATION.md` (timeline)
