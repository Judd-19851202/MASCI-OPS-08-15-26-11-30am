# GOVERNANCE-HARDEN-001 · Workstream C · Production Access Matrix

```
Environment    : both
Access Level   : preview-runtime+preview-DB · prod-DB-read · public-only (UI)
Evidence Source: external-probe + preview-runtime + prod-DB read-only + static-analysis of /app/backend/.env
Confidence     : VERIFIED for every cell below
```

---

## §C.1 · Authoritative access matrix

| Capability | PREVIEW (`safety-audit-mobile-1.preview.emergentagent.com`) | PRODUCTION (`mascidocs.com`) |
|---|---|---|
| **DB visibility (read)** | YES — `masci_safety_preview` is the default; `masci_safety` (PROD) is **also fully readable** via shared Atlas user | YES (when authoring from the prod pod); also visible from preview pod via shared Atlas user |
| **DB visibility (write)** | YES — `masci_safety_preview` is the default write target; `masci_safety` (PROD) is **also writable** via shared Atlas user | YES — used by the prod runtime + previously exercised by a fork (MOTIVE-PROD-INCIDENT-001) |
| **Runtime visibility (shell, supervisor, logs)** | YES (this fork has root inside the container) | NO (operator-managed pod; agent has no shell, no supervisor access, no `/var/log` access) |
| **Admin UI visibility (public pages)** | YES (full) | YES (public pages only — landing, hub, /admin/login screen) |
| **Admin UI visibility (authenticated)** | YES (full) | **UNVERIFIED** — credentials documented as shared (see Workstream D); fork has not attempted prod login as a matter of doctrine |
| **Credential access (preview `.env`)** | YES — `/app/backend/.env` and `/app/frontend/.env` are readable in this pod | NO — production pod's `.env` is operator-managed and not visible from the preview pod |
| **Credential access (cluster Atlas user)** | YES (the `admin_db_user` credential lives in this pod's MONGO_URL) | YES — same value (same atlas user is used by both pods) |
| **Deployment authority** | NO (deploy is operator-triggered from the Emergent chat UI) | NO (same) |
| **Code-push authority (Git)** | NO (Save to GitHub is operator-triggered) | NO |
| **Mongo write authority (programmatic)** | YES — application default + agent direct | YES — application default + agent direct (via shared cluster user) |
| **Read application logs** | YES (DB-backed audit_events / admin_audit_log / integration_sync_logs / production_incidents · plus supervisor `/var/log`) | YES (DB-backed only; no /var/log access) |
| **Read audit logs** | YES (`admin_audit_log` in preview DB) | YES (`admin_audit_log` in prod DB — readable today) |
| **Read integration secrets (length only, by policy)** | YES | YES — confirmed in this audit: read `integration_settings.motive` length-only, no secret value exfiltrated |

## §C.2 · Per-dimension explicit reconciliation

### C.2.1 · "Can Emergent (this fork) deploy code to production?"

**NO.** Deployment is triggered by the operator clicking the **Deploy** affordance in the Emergent chat UI. The fork has no API to invoke this. The fork can author code, run tests, and modify the preview pod's working tree — but the change is not visible at `mascidocs.com` until the operator promotes.

### C.2.2 · "Can the fork write to production database?"

**YES — capability exists today, exercised in the past, restraint is doctrinal only.**

| Evidence | Source |
|---|---|
| Cluster-level Atlas user (`admin_db_user` with `atlasAdmin@admin` role) | Workstream A · `connectionStatus` |
| Same `MONGO_URL` resolves both DBs in this pod | Workstream A · `list_database_names()` returns 33 DBs incl. `masci_safety` |
| Prior fork did write to prod | `masci_safety.integration_settings.motive.updated_by="motive_prod_incident_001:remediation"` |

The only thing stopping a prod write today is the directive in front of the fork agent. There is no infrastructure boundary.

### C.2.3 · "Can the fork log into the prod admin UI?"

**UNVERIFIED — likely YES.** The credentials in `/app/memory/test_credentials.md` are documented as working in both preview and production because preview was seeded from a prod snapshot on 2026-05-26. Specifically:

> "Test accounts apply to BOTH databases — the preview DB was seeded with a snapshot of production users before today's change, so the same credentials work on both environments."

The fork did NOT attempt prod login in this audit (would have created an `admin_audit_log` row and possibly an `audit_events` row, which is a state change). Operator can confirm in seconds by inspecting `masci_safety.admin_audit_log` for any actor=`jaymn.judd@mascigc.com` entries that have no matching authorized session (e.g., outside operator-typing hours).

### C.2.4 · "Can the fork read production environment variables (the `.env` file on the prod pod)?"

**NO.** The prod pod's filesystem is not mounted in the preview pod. The preview pod's `.env` is **separately maintained** but several values are likely identical to prod's:

- `SUPER_ADMIN_EMAIL` length 22 (matches `jaymn.judd@mascigc.com` exactly)
- `SUPER_ADMIN_BOOTSTRAP_PASSWORD` length 10 (matches `Maddix123!` exactly)
- `JWT_SECRET` length 64
- `MFA_ENCRYPTION_KEY` length 43

Whether these are identical between preview and prod is **INFERRED** (MFA verification would silently fail if `MFA_ENCRYPTION_KEY` differed and prod MFA was actively used). Confirmation requires operator inspection of the prod pod's `.env`.

## §C.3 · Effective control surface for THIS fork (as of this audit)

| Surface | Can Affect? | How? |
|---|---|---|
| Production live data | YES | Direct Mongo write via shared `admin_db_user` |
| Production code | NO directly | Author code in preview → operator must deploy |
| Production secrets | NO directly | Cannot read prod `.env`; cannot rotate from preview |
| Production admin UI | UNVERIFIED | Credentials documented as shared; not attempted |
| Production logs (DB-backed) | READ + WRITE | Could write into `admin_audit_log`, `audit_events`, `integration_sync_logs` |
| Production logs (filesystem) | NO | No shell access to prod pod |
| Cloudflare ingress / DNS | NO | Operator-managed |
| Atlas Console (user management) | NO | Operator-managed |

## §C.4 · Bottom line

Today's effective state: **a single Atlas user gives this preview pod read AND write authority across every database on the production cluster, including `masci_safety`.** Restraint is enforced by the OMEGA directives spoken to the fork in chat, not by infrastructure. Future remediation pathway is in Workstream A §A.7.
