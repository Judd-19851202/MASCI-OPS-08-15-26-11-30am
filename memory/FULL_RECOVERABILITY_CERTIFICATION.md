# FULL_RECOVERABILITY_CERTIFICATION

**Date:** 2026-05-30 (Batch F · Phase 5 — final certification)
**Reissue of:** `RECOVERABILITY_CERTIFICATION.md` (Batch E) with Batch F drill evidence

---

## 🟢 FINAL VERDICT — **OPERATIONALLY RECOVERABLE** with two known manual steps

This is an upgrade from Batch E's "🟡 PARTIALLY RECOVERABLE" because Batch F **drilled the application layer end-to-end** and proved the recovery path works. The two manual steps (password reseed + photo re-upload if R2 was also lost) are quantified, time-boxed, and survivable.

### Per-axis breakdown:
| Recovery axis | Batch E verdict | Batch F verdict | Why upgraded? |
|---|---|---|---|
| Data layer (Mongo collections) | 🟢 | 🟢 | Unchanged · re-confirmed |
| Application boot | ⚪ UNKNOWN | 🟢 | Proven by drill |
| API endpoints | ⚪ UNKNOWN | 🟢 | 13 endpoints exercised |
| PDF rendering | ⚪ UNKNOWN | 🟢 | DR/Incident/Meeting all rendered with valid `%PDF-` headers |
| Search workflow | ⚪ UNKNOWN | 🟢 | `/api/admin/search` 200 OK |
| Portal-user multi-login | 🟢 (Batch E claim) | 🔴 | CORRECTED — multi-login broken until reseed |
| Admin login (env-based) | 🟢 (Batch E claim) | 🟢 | Confirmed — `ADMIN_PASSWORD` env path is the escape hatch |
| DB indexes | 🟢 (Batch E claim) | 🟢 | Confirmed — auto-form on backend boot |
| Photos (R2 surviving) | 🟢 (Batch E claim) | 🟢 | Unchanged |
| Photos (R2 also lost) | 🟡 | 🟡 | Unchanged — bytes are in archive, no auto re-upload |
| Frontend exercise | ⚪ UNKNOWN | ⚪ | Logical inference only (rebuild + Playwright deferred) |

---

## 1 · "If production was completely destroyed right now…"

### 1.1 — What would be recovered?

🟢 **Every operational record**: all 86 Daily Reports (with full 40+ fields including inline photos), all 25 Equipment Pre-Op inspections, all 23 Safety Meetings, all 7 Incidents, all 1 PO Request, all 245 employees, all 534 operational events, all PMs/Shop/HR/Dispatch/Safety/FL portal user records (with bcrypt password hashes intact for per-portal mirror copies), all 6 safety documents, all 4 safety training records, all 27 field leadership records, the full audit ledger (10 k audit events + 1.9 k admin audit rows), all backup_health history (200 rows), all 102 cluster capacity samples.

🟢 **Photos**: If R2 survived, every photo at its original R2 key is immediately accessible. If R2 also lost, the bytes are in the archive's `photos/` directory but currently no automated re-upload path exists.

🟢 **Database indexes**: Auto-form on first backend boot (10–30 s).

### 1.2 — What would NOT be recovered?

🔴 **Master multi-login passwords** for 7 directory users. Encrypted bcrypt hashes for `user_directory` collection are redacted from the backup by design (security posture). The 7 affected users:
- `jaymn.judd@mascigc.com` (super-admin)
- `shopmanager@mascigc.com`
- `safety@mascigc.com`
- `masciaccounting@mascigc.com`
- `dispatch@mascigc.com`
- `hrmanager@mascigc.com`
- `leticiamasci@mascigc.com`

🟡 **Per-portal session tokens** (`directory_sessions`, `session_activity`) — recoverable in data terms but logically dead (sessions need to re-authenticate).

🟡 **In-flight uploads / chunks / nonces** (`temp_upload_chunks`, `webauthn_challenges`, `admin_step_ups`, `dispatch_magic_links`, `idempotency_keys`) — by design TTL/short-lived; not preserved across recovery.

🟡 **Anything written to Mongo after the most recent archive snapshot.** Currently ≤ 60 min (hourly cadence). Recommended ≤ 24 hr (nightly cadence).

🔴 **R2-only data** if R2 cluster itself is lost AND no parallel mirror exists.

### 1.3 — How long would recovery take?

| Scenario | RTO estimate | Confidence |
|---|---:|---|
| Mongo-only loss · R2 healthy | **20–25 minutes** | 🟢 Drilled |
| Mongo + R2 both lost | **2-8 hours** (depends on photo volume) | 🟡 Photos re-upload path doesn't exist yet |
| Mongo + R2 + email service all lost | **4-12 hours** | 🟡 Resend re-init |
| Full regional outage (cluster + R2 region down) | days | ❌ No cross-region today |

**Detailed RTO for "Mongo-only loss":**
1. Provision target Mongo cluster — 5 min
2. Download R2 archive — 10 sec (442 MB · ~7 MB/s)
3. Restore via `restore_drill.py` — 60 sec
4. Boot backend with env vars — 15 sec
5. Operator logs in via `/api/admin/login` — 30 sec
6. Reset 7 master multi-login passwords via admin UI — 5–10 min
7. Smoke test (login + post DR + render PDF) — 5 min

### 1.4 — What manual steps would still exist?

| Step | Eliminable? | How |
|---|---|---|
| Provision new MongoDB cluster | 🟡 Yes with Terraform/IaC | Add IaC config (out of scope of this batch) |
| Set ~15 production env vars on new backend | 🟡 Yes with secret-management tool | E.g., Doppler/Vault — deferred |
| Reset 7 user_directory passwords | 🟢 YES via `_seed_hash` extension (1 hour code) | Fix GAP-2 |
| Re-issue dispatch magic links to mid-flight drivers | 🔴 Inherent — magic links are single-use | Runbook note |
| R2 photo re-upload (if R2 also lost) | 🟢 YES via `--restore-photos` flag (2–4 hours code) | Fix GAP-4 |
| DNS cutover (if changing hostname) | 🟡 Yes with Route53/Cloudflare API | Operational tooling |
| Smoke test (login + DR + PDF) | 🟢 YES with `post_restore_smoke.py` | Fix GAP-10 |

After GAP-2 and GAP-4 are fixed, manual steps reduce to: provisioning + env-var stamping + DNS cutover. **The recovery becomes scriptable in ~30 minutes.**

### 1.5 — What risks remain?

| Risk | Severity | Mitigation status |
|---|---|---|
| Worker OOM on next-hour archive build (~3 days from now at current growth) | 🔴 Imminent | 1 env-var flip away (GAP-3) |
| Daily Report photo bloat continuing to grow | 🔴 Chronic | Engineering effort required (GAP-1) |
| Master multi-login broken post-restore | 🔴 Material | 1-hour code change (GAP-2) |
| Cross-region disaster | 🟡 Tail risk | No mitigation today |
| Single Atlas cluster | 🟡 Tail risk | Atlas does internal redundancy; full-cluster loss is rare |
| Single R2 bucket | 🟡 Tail risk | Could mirror to S3 nightly |
| Operator forgets `ADMIN_PASSWORD` env | 🔴 If true, recovery impossible | Documentation in `test_credentials.md` |

---

## 2 · Bottom line

**🟢 MASCI is OPERATIONALLY RECOVERABLE. The recovery procedure has been drilled end-to-end at the data, API, PDF, and search layers. Two material gaps (multi-login reseed + R2-loss photo re-upload) are quantified and have known fixes. One acute risk (`BACKUP_R2_HOURLY=true` + DR photo bloat → worker OOM in ~3 days) needs the operator to flip an env var IMMEDIATELY to neutralize.**

**Verdict upgrade since Batch E:** 🟡 PARTIALLY RECOVERABLE → 🟢 **OPERATIONALLY RECOVERABLE** with two named manual steps.

**Verdict expected after next batch fixes (GAP-1, GAP-2, GAP-3, GAP-4 closed):** 🟢 **FULLY RECOVERABLE**.
