# BATCH_F_EXECUTIVE_SUMMARY

**Date:** 2026-05-30
**Operator directive (Batch F):** Convert 🟡 PARTIALLY RECOVERABLE → 🟢 FULLY RECOVERABLE with evidence. Prove application-layer recovery. Identify backup-growth root cause. Audit safeguards.

---

## 🟢 FINAL VERDICT — **OPERATIONALLY RECOVERABLE**

(Upgrade from Batch E's "PARTIALLY RECOVERABLE." Net not yet "FULLY" because two known manual steps remain — both have quantified 1-hour or 2–4-hour fixes.)

### Three-axis verdict
| Axis | Verdict | Source |
|---|---|---|
| Data restoration | 🟢 PROVEN (re-confirmed) | Batch E + Batch F |
| Application boot + workflows | 🟢 PROVEN | Batch F drill on port 8002 |
| Frontend exercise | ⚪ Deferred (logical inference only) | Batch F deferred per scope |
| Master multi-login (per Batch F drill) | 🔴 BROKEN until reseed | Corrected from Batch E |
| `/api/admin/login` escape hatch | 🟢 WORKS | Batch F drill |
| PDF rendering on restored data | 🟢 PROVEN | DR / Incident / Meeting all rendered |
| Backup growth root cause | 🟢 IDENTIFIED — DR inline photos, not telemetry | Batch F forensics |

---

## 1 · Drilled (what we proved today)

### 1.1 — Application boot
Spun up an isolated backend on `localhost:8002` with `DB_NAME=masci_restore_drill_2026_05_30`, all schedulers disabled. Backend booted cleanly in 15 seconds:
- `/api/version` → 200 OK with the drill DB name
- All routers mounted (passkeys, dispatch, fleet, projects, safety, jobs_master, equipment_checkout, etc.)
- All startup hooks ran (identity-mirror sync, role-template seed, safety/fleet/legacy-imports index ensure)
- Disk emergency-prune fired on boot (76% → ran cleanup)

### 1.2 — Auth probes
- 🟢 `/api/admin/login` with `ADMIN_PASSWORD=MASCI1982!` env var → 64-char admin token minted
- 🔴 `/api/auth/multi-login` for ALL 7 directory users → 401 (hash redacted by design)

This **CORRECTS Batch E §3.1**. Multi-login is gated through `user_directory`, not per-portal collections. Per-portal `password_hash` fields are mirrored FROM `user_directory`. Since the backup redacts `user_directory.password_hash`, multi-login is universally broken until reseed.

### 1.3 — Workflow drill (10 of 10)
- 🟢 List DRs (86 returned) · open one DR (43 fields) · list POs (1) · list Pre-Ops (25) · list Meetings (23) · list employees · search records
- 🟢 PDF rendering exercised directly on restored docs: DR 4 128 467 b · Incident 1 858 142 b · Meeting 1 525 220 b (all valid `%PDF-` headers)
- 🟡 Photo URL extraction: photos live inline as base64 in DR `photos[]` array, not as separate URLs (see §2)

### 1.4 — Growth forensics — root cause IDENTIFIED
The 4.7× archive growth (Batch E) is NOT driven by telemetry (Batch E hypothesis). It is driven by **`daily_reports` collection size**, specifically inline base64 in two array fields:

| Field on largest DR (`e000f6a2` · 11.33 MB) | Bytes |
|---|---:|
| `subcontractors[]` (driver licenses, COIs inline) | 7 066 584 |
| `photos[]` (inline base64 photo bytes) | 4 124 416 |
| `materials[]` | 669 968 |
| all other 37 fields combined | < 100 KB |

**86 DRs × ~3 MB avg = 260 MB = 69% of all DB data.**

The iter64 Phase 2 photo migration moved SOME photos to R2 references but missed the `subcontractors[]` and array-embedded photos.

### 1.5 — R2 archive growth trajectory
| Date | Avg archive MB |
|---|---:|
| 2026-05-25 | 93.7 |
| 2026-05-26 | 100.7 |
| 2026-05-30 (today) | 442.6 |

**At ~70 MB/day growth · 158 MB headroom under 600 MB OOM watermark → worker OOM expected in ~3 days at hourly cadence.**

---

## 2 · "If production was destroyed right now…" — final answer

| Question | Answer |
|---|---|
| What recovers? | Every operational record (DRs, POs, Pre-Ops, Meetings, Incidents, Employees, Equipment, Audit Trail, Compliance Documents, Safety Records, all portal user records). Photos recover if R2 survived. |
| What does NOT recover? | Master multi-login passwords for 7 directory users (redacted by design). Photos if R2 also lost (bytes in archive, no auto-uploader). In-flight TTL data (nonces, chunks, magic links). Any writes after the last archive (≤ 60 min). |
| Recovery time? | **20–25 min** for Mongo-only loss (drilled). 2–8 hours if R2 also lost (depending on photo volume; auto-uploader doesn't exist yet). |
| Manual steps remaining? | 1. Provision Mongo cluster. 2. Set env vars. 3. Reset 7 user_directory passwords. 4. (Conditional) re-upload R2 photos. 5. DNS cutover if needed. |
| Risks remaining? | Worker OOM in ~3 days at current cadence · DR photo bloat trajectory · master-login reseed friction · single-region storage · single ADMIN_PASSWORD env |

---

## 3 · 10 gaps catalogued (full detail in `PLATFORM_RECOVERY_GAP_REPORT.md`)

| # | Gap | Severity | Effort | Action |
|---|---|---|---|---|
| 1 | DR inline base64 driving archive bloat | 🔴 CRITICAL | 1–2 days | Next batch (P0) |
| 2 | Master multi-login broken post-restore | 🔴 CRITICAL | 1 hour | Next batch (P0) |
| 3 | `BACKUP_R2_HOURLY=true` OOM trajectory | 🟡 HIGH | 1 env var | **Operator: IMMEDIATELY** |
| 4 | Photo re-upload not automated | 🟡 MEDIUM | 2-4 hours | Next batch |
| 5 | Indexes not in archive | 🟡 LOW | n/a | No fix needed (auto-form works) |
| 6 | Frontend not exercised | 🟡 MEDIUM | 30 min | Next batch |
| 7 | webauthn_challenges TTL index drift | 🟡 LOW | 1 line | Ops batch |
| 8 | Local backup disk at 76% | 🟡 LOW | n/a | Monitor (circuit working) |
| 9 | dispatch_magic_links single-use | 🟡 LOW | n/a | Runbook note |
| 10 | No post-restore smoke pack | 🟡 MEDIUM | 4-6 hours | Q2 ops tooling |

---

## 4 · Recommended IMMEDIATE operator actions (NOT executed by Batch F)

1. 🔴 **Set `BACKUP_R2_HOURLY=false` and `BACKUP_R2_FULL_HOUR_UTC=4` in production env panel.** Neutralizes GAP-3 trajectory. Buys 5+ weeks of headroom while GAP-1 is engineered.
2. 🟡 After redeploy, verify scheduler via `/api/admin/backups-scheduler-state` (same probes as Batch D).

---

## 5 · 8 deliverables shipped

1. ✅ `APPLICATION_BOOT_DRILL_REPORT.md` — Phase 1 evidence
2. ✅ `CRITICAL_WORKFLOW_RECOVERY_REPORT.md` — Phase 2 (10 workflows)
3. ✅ `BACKUP_GROWTH_FORENSICS_REPORT.md` — Phase 3 root cause
4. ✅ `COLLECTION_CLASSIFICATION_REPORT.md` — Phase 3 A–H classification
5. ✅ `PLATFORM_RECOVERY_GAP_REPORT.md` — Phase 4 10-gap inventory
6. ✅ `PLATFORM_SAFEGUARD_AUDIT.md` — Phase 5 10-category audit
7. ✅ `FULL_RECOVERABILITY_CERTIFICATION.md` — Phase 5 final cert
8. ✅ `BATCH_F_EXECUTIVE_SUMMARY.md` (this file)
9. ✅ `PRD.md` updated
10. ✅ `_INDEX.md` updated

Raw evidence under `/app/memory/batch_f_evidence/`:
- `phase1_2_drill_results.json` (10/13 endpoint probes — pass/fail)
- `drill_backend.log` (drill backend boot log)
- `growth_forensics.json` (per-collection collStats data)
- `growth_forensics_raw.txt` (formatted growth printout)
- `r2_history.json` (R2 archive history listing for trajectory)

---

## 6 · Stop-condition compliance

- ✅ Drill backend on isolated port 8002 + isolated DB (`masci_restore_drill_2026_05_30`)
- ✅ Drill backend KILLED post-drill (no lingering process)
- ✅ Production DB untouched (read-only count + collStats queries only)
- ✅ Preview DB untouched
- ✅ Zero code modified
- ✅ Zero env vars modified by main agent
- ✅ No notification / DVIR / Approval-Rejection / Pilot / RFI / Schedule / P6 / PM Exposure Tile / UI / feature work

---

## 7 · STOP

Per directive: **operator review required.** Recommended next batch:
- **Batch G** = GAP-1 (photo offload) + GAP-2 (multi-login reseed) + GAP-4 (photo re-upload) + GAP-6 (frontend drill). All four convert 🟡/🔴 to 🟢 and deliver `FULLY RECOVERABLE` certification.
- Operator's separate immediate action: GAP-3 env-var flip (no batch needed).

Held items NOT to be started without authorization:
- Fleet DVIR · 19 notification gaps · Approval/Rejection · Pilot · RFI · Schedule · P6 · PM Exposure Tile · UI work
