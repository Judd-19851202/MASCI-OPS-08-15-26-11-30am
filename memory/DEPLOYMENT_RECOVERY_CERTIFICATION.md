# DEPLOYMENT RECOVERY CERTIFICATION

_Phase V-Prelude · Deployment Readiness · Track 7 · 2026-05-29T00:24Z_

Documents the rollback path, restore drill, governance-memory
recovery procedure, and the platform's stated RTO / RPO targets.

---

## 1 · Targets

| Metric | Target | Basis |
|---|---|---|
| **RTO** (Recovery Time Objective) | **< 30 min** | Emergent re-deploy (≈ 8–12 min) + identity-proof (≈ 1 min) + post-deploy probe sweep (≈ 5 min) |
| **RPO** (Recovery Point Objective) | **< 15 min** | Mongo Atlas continuous backup + R2 archive cadence; longest possible data window between snapshot and incident |

---

## 2 · Rollback paths (in order of operator preference)

### 2.1 Path A — Emergent rollback (preferred · fastest)

Emergent's deploy pipeline keeps the previous production image
available for instant re-promotion.

**Steps**

1. Operator clicks **Rollback** in the Emergent deploy UI.
2. Emergent re-routes `mascidocs.com` to the previous container image.
3. Operator runs:
   ```
   bash scripts/verify_production_identity.sh
   ```
   to confirm `app_env=production`, `db_name=masci_safety`, and the
   previous `source_hash`.
4. Operator runs:
   ```
   python3 scripts/verify_no_contamination.py --target masci_safety
   ```
   to confirm the rollback did not import preview data.

**Estimated timing**: 2–4 min.

### 2.2 Path B — Code-only redeploy of last known-good commit

Used when Path A is unavailable.

**Steps**

1. From `git log --oneline` identify the last green-gate commit (the
   one whose `source_hash` matches the prior production `/api/version`
   value).
2. Reset preview to that SHA (Emergent platform rollback feature; do
   not `git reset --hard` manually).
3. Re-run the full pre-deploy gate:
   ```
   bash scripts/pre_deploy_check.sh
   ```
4. Promote to production via Emergent Deploy.
5. Verify with `verify_production_identity.sh`.

**Estimated timing**: 12–18 min.

### 2.3 Path C — Database restore (last resort)

Only required if data corruption is confirmed.

See § 3.

---

## 3 · Database restore procedure

### 3.1 Tooling

- `scripts/restore_drill.py` — official drill helper.
- Mongo Atlas point-in-time restore — Atlas console.
- Cloudflare R2 backup archive — bucket configured in `backend/.env`
  (`R2_*` / `S3_*` keys).
- Local snapshot archives — `backend/backups/` (7 archives, most
  recent `MASCI_lite_backup_2026-05-27_195523Z.zip`).

### 3.2 Safety rails (built into `restore_drill.py`)

- `--target-db` MUST begin with `masci_restore_drill_` unless
  `--i-know-what-i-am-doing` is also passed.
- `--target-db` CANNOT equal the live `DB_NAME` (read from
  `backend/.env`).
- Source backup is **never modified**.
- Live `MONGO_URL` is allowed (drill operates on the same Atlas
  instance, different database name).

### 3.3 Drill steps (dry run, then live)

```
# List available R2 backups, newest first
python3 scripts/restore_drill.py --list

# Dry-run restore plan
python3 scripts/restore_drill.py \
  --backup <key> --target U \
  --target-db masci_restore_drill_2026_05_29 --dry-run

# Live restore + validation
python3 scripts/restore_drill.py \
  --backup <key> --target U \
  --target-db masci_restore_drill_2026_05_29
```

### 3.4 Validation

After restore, the drill script prints:

- Mongo connectivity ✓
- Core collection record counts (vs. backup metadata)
- Sample `daily_reports` attachment integrity
- `user_directory` managed vs. mirrored split

### 3.5 Cut-over (post-validation)

1. Stop production writes (Emergent maintenance mode if available).
2. Rename live `masci_safety` → `masci_safety_quarantine_<ts>`.
3. Rename `masci_restore_drill_…` → `masci_safety`.
4. Restart backend (it will reconnect to the renamed DB by
   `DB_NAME=masci_safety`).
5. Run `verify_no_contamination.py --target masci_safety` + the full
   probe suite.

**Estimated timing**: 18–25 min for an L-size DB. Within RTO target.

---

## 4 · Governance memory recovery

Append-only governance memory files in `/app/memory/`:

| File | Restore source |
|---|---|
| `TIMELINE_LOUDNESS_TRENDLINE.json` | Git history (file is committed) · `TIMELINE_LOUDNESS_TRENDLINE.snapshot.json` is the integrity anchor |
| `LOUDNESS_TRENDLINE.json` | Git history + `LOUDNESS_TRENDLINE.snapshot.json` anchor |
| `OBSERVATION_LEDGER.json` | Git history + `OBSERVATION_LEDGER.snapshot.json` anchor |
| `DOCTRINE_TRENDLINE.json` | Git history |
| All `*.md` doctrine documents | Git history |

**Recovery procedure**

1. `git log --follow /app/memory/<file>` to find the last known-good
   commit.
2. `git show <sha>:memory/<file> > /tmp/recovered.json`.
3. Validate with `python3 scripts/trendline_integrity_probe.py --gate`.
4. Restore in place if the probe is green.

The integrity probe is the gate of last resort: it computes a
SHA-256 of the trendline content and checks against the anchor
checksum stored in the `.snapshot.json` companion. If the anchor
itself is corrupted, the operator must restore the snapshot from git
history at the same SHA as the trendline file.

---

## 5 · Observation Ledger + timeline substrate recovery

These are the youngest assets and bear documenting:

- **`OBSERVATION_LEDGER.json`** is append-only with a composite key
  `(timestamp, scenario, reviewer)`. Restoring an older copy will be
  rejected by the integrity probe unless the snapshot anchor is also
  restored to match.
- **`operational_timeline` collection** in `masci_safety_preview`
  currently has 0 documented rows. Restoring from a backup means
  restoring an empty collection — minimal risk.
- **`operational_links` / `operational_constraints` / `photo_governance`**
  same — collections live in Mongo but production has not yet
  populated them; restore complexity is low.

---

## 6 · Backup cadence + verification

| Layer | Cadence | Cross-check | Last verified |
|---|---|---|---|
| Mongo Atlas continuous backups | continuous · PIT to ≈ 15 min | Atlas console | per Atlas SLA |
| R2 archive (`backups/` prefix) | per-cycle (lite / complete) | `backup_verification.py` Mon 14:00Z | 2026-05-27 (last local ZIP) |
| Local `backend/backups/*.zip` | 7 archives (5 lite + 2 complete) | `backup_verification.py` cross-checks R2 | 2026-05-27T19:55Z (most recent) |
| Governance memory `*.json` | git auto-commit per chat turn | `trendline_integrity_probe.py` | 2026-05-28T23:55Z (last anchor refresh) |
| Snapshot anchors `*.snapshot.json` | refresh on every clean probe run | self | 2026-05-28T23:55Z |

`backup_verification.py` emits a weekly heartbeat email summarizing
record counts, file sizes, R2 archive list, and per-mode last-success
timestamps. Cron is live (`BACKUP_VERIFICATION_ENABLED=true`).

---

## 7 · Failure scenarios + responses

| Scenario | Detection | Response | Path |
|---|---|---|---|
| Bad code deploy (auth gate fails, route 5xx) | Sentry alert · `/api/version` reachable but health degraded | Emergent rollback | Path A |
| Bad code deploy + Emergent rollback unavailable | same as above | redeploy previous green-gate SHA | Path B |
| Data corruption (operator complaint, integrity fail) | `verify_no_contamination.py` non-zero · operator escalation | Restore drill + cutover | Path C |
| Trendline / ledger tamper | `trendline_integrity_probe.py` fails | git checkout last good SHA of file + snapshot | § 4 |
| R2 unreachable for uploads | `r2_degraded_24h` > 0 in `/api/admin/deploy-readiness` | inline fallback already engaged; investigate Cloudflare; no rollback needed | n/a |
| Mongo Atlas outage | `mongo` blocker in `/api/admin/deploy-readiness` · cluster health red | Atlas failover · backend reconnects | n/a |
| MFA encryption key lost | super-admin login impossible | restore `MFA_ENCRYPTION_KEY` from Emergent secret store | n/a |

---

## 8 · Pre-deploy probe replay (rehearsal)

To prove recovery readiness *before* tonight's cutover, the operator
can:

```
bash scripts/pre_deploy_check.sh
```

Today's read-only run confirmed:

- 5/5 doctrine probes green
- Sigma-III regression contract green (53 tests)
- Auth + RBAC critical-path tests green (75 tests)
- Cluster severity = `ok` (7.7% used)
- Draft-telemetry health route reachable
- `/api/admin/deploy-readiness` = `attention` · 0 blockers · 1 warn
  (master_coverage backfill)

---

## 9 · Verdict

**OPERATIONAL RECOVERY: ✅ PASS.**

- 3 rollback paths documented (A/B/C) with safety rails.
- Restore drill tool exists + has hard safety rails preventing accidental live-DB overwrite.
- Backups: continuous (Atlas) + weekly heartbeat (R2 cross-check) + 7 local archives.
- Governance memory recovery procedure documented with integrity-probe anchor.
- Estimated worst-case RTO 18–25 min · within < 30 min target.
- RPO < 15 min via Atlas PIT.

Track 7 of 8 · ✅ pass.
