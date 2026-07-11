# TRACK 28.09C · FRESH PRE-DEPLOY BACKUP CAPTURE

**Issued:** 2026-07-11
**Mode:** attempted autonomous execution → HALTED at Phase 2 — production admin authentication required.
**No production changes made. No preview activity. No R2 mutations.**

---

## Executive verdict

### 🟡 **FAIL — BACKUP NOT READY VIA AUTONOMOUS AGENT.**

**This is not a code defect.** The autonomous agent (this session) cannot authenticate to production from the preview pod. Production admin endpoints correctly reject unauthenticated requests (401), which is exactly the security posture we want. Phases 3-7 require **operator action** taking approximately 2 minutes. An exact playbook is provided in Section 8 below.

**When the operator completes the playbook, verdict flips to PASS.**

---

## 1. Production backup system inventory (Phase 1 · complete)

The canonical MASCI production backup system is registered at these endpoints (all confirmed present in the live production commit `6ab72474cc20`):

| Endpoint | Method | Purpose | Live prod probe |
| --- | --- | --- | --- |
| `/api/admin/backups` | GET | List all backup objects | **401** (endpoint exists, auth-gated) |
| `/api/admin/backups/run-now` | POST | Trigger a fresh backup (returns 202) | **405** without POST body / auth (endpoint exists) |
| `/api/admin/backups/integrity-check` | GET | Integrity metadata for latest | ✅ registered in code (`server.py:9061`) |
| `/api/admin/backups-scheduler-state` | GET | Live scheduler + next-fire + last-run | ✅ registered in code (`occ_health_aggregator.py:411`) |
| `/api/admin/backups/{filename}` | GET | Per-object metadata + download | ✅ registered in code (`server.py:9111`) |
| `/api/admin/backup-verification/run-now` | POST | Run + email backup report | ✅ registered in code (`backup_verification_routes.py:6`) |
| `/api/admin/backup-verification/state` | GET | Last verification run | ✅ registered in code (`backup_verification_routes.py:7`) |

**Backup service module:** `/app/backend/services/operations_control/backups.py`
**Regression suite for backup subsystem** (10 tests across prior iterations):
`test_backup_hours_iter27.py`, `test_iter427_legacy_backup_prune.py`, `test_deploy_fix_001_backup_hardening.py`, `test_backup_fix_001.py`, `test_track_22_1i1_backup_scheduler_migration.py`, `test_iter425_backup_auto_discovery.py`, `test_iter62_backup_resiliency.py`, `test_iter182_backup_email_storm_fix.py`

**Storage identity:**
| Item | Preview value | Production value | Evidence |
| --- | --- | --- | --- |
| R2 bucket | `masci-hub` | `masci-hub` (assumed same, prefix-isolated) | preview `.env`; prod value auth-gated |
| Backup prefix | operator-configured (typically under `backups/` prefix in the bucket) | operator-configured | code convention |
| Delete engine | **DISABLED** | **DISABLED** | Track 27.07 permanent gate |

---

## 2. Why the agent cannot execute Phases 2-5 autonomously

Three security layers correctly prevent autonomous production backup execution from the preview pod:

1. **Atlas per-user isolation** (Track 28.09A) — the preview `masci_preview_user` cannot access `masci_safety` (production DB). Even if we somehow reached the production API, our credentials scope is preview-only.
2. **Production admin credentials are operator-held** — this session has preview admin token only. Production requires the operator's separate credentials at `https://mascidocs.com/admin/login`.
3. **Preview `SCHEDULER_ENABLED=false`** (Track 28.09A) — even if we tried to run a backup locally, the preview scheduler is intentionally disabled so we cannot mutate production.

**All three are working correctly.** The agent respecting these boundaries IS the safety posture we designed.

---

## 3-7. Missing evidence (blocked pending operator action)

The following evidence fields will be populated **by the operator** using the playbook in Section 8:

| Field | Status |
| --- | --- |
| Backup request/start time | ⏳ pending operator |
| Backup completion time | ⏳ pending operator |
| Backup age at verdict | ⏳ pending operator |
| Job/run ID | ⏳ pending operator |
| Object key | ⏳ pending operator |
| Object size | ⏳ pending operator |
| ETag / checksum | ⏳ pending operator |
| Job status (COMPLETED?) | ⏳ pending operator |
| Scheduler/worker status | ⏳ pending operator |
| Independent R2 HEAD/list proof | ⏳ pending operator |
| Integrity validation result | ⏳ pending operator |

---

## 8. Operator playbook (READ-ONLY probes + one authorized POST · ~2 minutes)

Copy-paste-ready. Operator must be signed into `https://mascidocs.com/admin/*` as super admin, then run these from anywhere with `curl` or execute via the Admin OS "Storage & Recovery → Run Backup Now" button if preferred.

### 8a. If using the Admin OS UI (recommended, easiest)

1. Sign in at `https://mascidocs.com/admin/login` as super admin.
2. Navigate to **Storage & Recovery** (`/admin/storage-recovery`).
3. Click **Run Backup Now** (calls `POST /api/admin/backups/run-now`).
4. Wait 60–90 seconds. The page will refresh scheduler-state.
5. Note the new object key, size, and timestamp shown in the Trust Gaps / Backups table.
6. Paste those three values into Section 9 below (or reply here) and Track 28.09C flips to PASS.

### 8b. If using curl (equivalent, scriptable)

```bash
# Step 1 — obtain a fresh production admin token
ADMIN_TOKEN=$(curl -s -X POST https://mascidocs.com/api/auth/multi-login \
  -H "Content-Type: application/json" \
  -d '{"email":"<production-admin-email>","password":"<production-admin-password>"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['portal_tokens']['admin'])")

# Step 2 — capture the CURRENT latest backup timestamp BEFORE triggering (for delta comparison)
echo "PRE-TRIGGER latest backup:"
curl -s -H "X-Admin-Token: $ADMIN_TOKEN" \
  https://mascidocs.com/api/admin/backups-scheduler-state | python3 -m json.tool

# Step 3 — trigger fresh backup (returns 202 immediately, backup runs ~60s)
echo "TRIGGERING backup..."
BACKUP_START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl -s -X POST -H "X-Admin-Token: $ADMIN_TOKEN" \
  "https://mascidocs.com/api/admin/backups/run-now" | python3 -m json.tool
echo "backup_start_time: $BACKUP_START"

# Step 4 — poll every 15s for up to 3 min for completion
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  sleep 15
  STATE=$(curl -s -H "X-Admin-Token: $ADMIN_TOKEN" \
    https://mascidocs.com/api/admin/backups-scheduler-state)
  echo "poll $i: $(echo $STATE | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get(\"last_run\",{}))')"
done

# Step 5 — list latest backup objects (independent R2 proof)
echo "LATEST BACKUP OBJECTS:"
curl -s -H "X-Admin-Token: $ADMIN_TOKEN" \
  "https://mascidocs.com/api/admin/backups?limit=3" | python3 -m json.tool

# Step 6 — integrity check on the newest backup
echo "INTEGRITY CHECK:"
curl -s -H "X-Admin-Token: $ADMIN_TOKEN" \
  https://mascidocs.com/api/admin/backups/integrity-check | python3 -m json.tool
```

### 8c. Values operator must record

| Field | Where to find it |
| --- | --- |
| `backup_start_time` | `$BACKUP_START` in Step 3 |
| `backup_completion_time` | `last_run.completed_at` from Step 4 final poll |
| `job_run_id` | `last_run.run_id` from Step 4 |
| `object_key` | `items[0].key` from Step 5 (first item = newest) |
| `object_size` | `items[0].size` from Step 5 |
| `etag` | `items[0].etag` from Step 5 |
| `job_status` | `last_run.status` — must be `COMPLETED` or `SUCCESS` |
| `integrity_result` | `ok: true` from Step 6 |

---

## 9. Rollback checkpoint (fields populated at operator time)

**Fixed values (already known):**
- Production URL: `https://mascidocs.com`
- Current live commit BEFORE deployment: `6ab72474cc20` (built 2026-07-10T13:13:27Z, 14.3+ hours uptime as of audit)
- Frozen release candidate to be deployed: `fb30633cc1e6a31a379751ecad16e97f71d42b75`
- Production database identity: `masci_safety` (verified via `/api/version.db_name`)
- Delete engine: **DISABLED** (Track 27.07 permanent gate)
- Rollback source commit/artifact: `6ab72474cc20` — Emergent platform commit-based rollback available in chat UI

**Operator-populated fields (pending):**
- Backup completion timestamp: `___________`
- Backup object key: `___________`
- Backup size (bytes): `___________`
- ETag / checksum: `___________`
- Backup job/run ID: `___________`
- Latest restore-drill date: `___________` (leave blank if unknown; not deployment-blocking)
- RPO/RTO reference: `___________`
- Operator name / actor identity: `___________`

Once these fields are filled, Track 28.09C's verdict flips to **PASS — BACKUP READY**.

---

## 10. Warnings and honesty statements

- The agent did NOT trigger any production API call requiring authentication.
- The agent did NOT probe any preview production-adjacent surface.
- The agent did NOT modify any environment variable in either environment.
- The agent did NOT attempt to acquire production credentials from any source.
- The agent DID make 10 unauthenticated GET/POST probes to `https://mascidocs.com/api/admin/backup*` — all returned 401/404/405 as expected and did NOT mutate anything.
- The agent DID NOT run the R2 delete engine or any deletion operation; delete engine remains **DISABLED**.

---

## 11. What must happen next

1. **Operator:** run Section 8a or 8b (~2 minutes).
2. **Operator:** paste the 8 recorded values back into this file (Section 9) or into chat.
3. **Track 28.09C** verdict flips to PASS — Deployment then has full pre-deploy backup evidence.
4. **Only then:** proceed with `git push` / Emergent Deploy for RC `fb30633cc1e6…`.

**Until operator completes Section 8, the recorded verdict remains FAIL — BACKUP NOT READY.** This is the correct, honest state — not a code defect, just an authentication boundary the agent must respect.
