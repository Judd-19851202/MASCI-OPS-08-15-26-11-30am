# PHASE26_1_MONGO_DURABILITY_PLAN.md
## MASCI Operations Platform · Phase 26.1 · MongoDB Durability + Migration Plan
## iter427 · 2026-05-25

---

## Status — TODAY

| Concern | Today's reality |
|---|---|
| Mongo host | Running **inside the container** at `localhost:27017` |
| Data volume | `/data/db` (container-mounted disk) — **858 MB** |
| Survives container redeploy? | ❌ **No** — every redeploy destroys the local Mongo data |
| Mitigation | Hourly + nightly R2 archive (iter425 + iter426) · "backup-or-die" banner on `/admin/system` |
| Risk window | Up to 1 hour of operational data loss per redeploy if operator does not click manual backup beforehand |

This banner is already surfaced to the operator on `/admin/system`:

> ⚠ Your data will be deleted on the next redeploy.
> Permanent fix: switch the production app to MongoDB Atlas (free tier,
> 15-min setup). Once the Atlas connection string is in your
> production env vars, this banner will turn green and redeploys
> become safe forever.

---

## Target — MongoDB Atlas (recommended)

| Property | Value |
|---|---|
| Tier | Atlas free `M0` (sandbox, 512 MB storage) for pilot · **upgrade to `M10` `+$57/mo` for production once volume > 400 MB** |
| Region | Closest to Emergent deploy region (e.g., `us-east-1`) |
| Network | Public IP allowlist `0.0.0.0/0` initially (or restrict to Emergent egress IPs after smoke) |
| Replication | Free-tier 3-node replica set out of the box · automatic failover |
| Backup | Atlas continuous backups (paid tiers) · combined with our existing R2 archive = belt-and-suspenders |
| Connection | Standard SRV URI (`mongodb+srv://<user>:<pw>@<cluster>.mongodb.net/<dbname>`) |

---

## Migration checklist (PREPARATION ONLY · no destructive automation)

### Stage A · Atlas account setup (operator-driven · 15 min)

1. ☐ Operator visits https://www.mongodb.com/cloud/atlas/register and
   creates an account (or uses existing).
2. ☐ Create a new project named "MASCI Operations".
3. ☐ Build a free `M0` sandbox cluster (or `M10` for production).
4. ☐ Add a database user — credential for the cluster, not your
   Atlas account. Save user + password to your password manager.
5. ☐ Network Access → "Allow access from anywhere"
   (`0.0.0.0/0`) initially. Tighten later by restricting to
   Emergent egress IPs.
6. ☐ "Connect" → "Drivers" → copy the SRV URI. Replace `<password>`
   with the actual database-user password.

### Stage B · Pre-cutover verification (operator + agent · 10 min)

7. ☐ Test connection from a local shell:
   ```
   mongosh "mongodb+srv://<user>:<pw>@<cluster>.mongodb.net/<dbname>" \
           --eval "db.adminCommand({ping: 1})"
   ```
   Expected: `{ ok: 1 }`.
8. ☐ Confirm Emergent deploy environment can reach the Atlas SRV host
   (smoke test via a one-off curl from the production env).
9. ☐ Take a fresh **manual R2 archive** on `/admin/system`
   ("Backup + Email + Download Now") before any cutover.
10. ☐ Confirm the email-with-zip arrives.
11. ☐ Download the zip locally as a belt-and-suspenders restore source.

### Stage C · Production env-var cutover (operator-driven · 5 min)

12. ☐ In Emergent deploy dashboard, set:
    - `MONGO_URL=mongodb+srv://<user>:<pw>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority`
    - `DB_NAME=<dbname>` (must match what's in the URI / what the app
      expects)
13. ☐ Do **NOT** delete the existing `MONGO_URL` from
    `/app/backend/.env` yet — keep as comment for rollback.
14. ☐ Trigger redeploy.
15. ☐ Confirm `https://mascidocs.com/api/health` returns `{"ok":true}`.
16. ☐ Confirm `https://mascidocs.com/admin/system` banner turns **GREEN**.

### Stage D · Data restore into Atlas (operator + agent · 30 min)

The new Atlas cluster starts EMPTY. To populate it with the prior
operational data, follow `RESTORE_RUNBOOK.md` against the freshest R2
archive — pointing `mongoimport`'s `--uri` at the new Atlas URI.

17. ☐ Download the freshest archive from R2 (most recent
    `MASCI_full_backup_*.zip`).
18. ☐ Unzip locally.
19. ☐ For each `.jsonl` collection file inside `collections/`, run:
    ```
    mongoimport --uri "mongodb+srv://..." \
                --db <dbname> \
                --collection <name> \
                --file collections/<name>.jsonl
    ```
20. ☐ Verify counts match the manifest:
    ```
    mongosh "<atlas-uri>" --eval \
      "db.getCollectionNames().forEach(c => print(c, db[c].countDocuments()))"
    ```
21. ☐ Restore disk-files trees:
    - `disk_files/storage/*` → `/app/backend/storage/`
    - `disk_files/static/*` → `/app/backend/static/`
    - `disk_files/data/*` → `/app/backend/data/`
    - `disk_files/memory/*` → `/app/memory/` (doctrine docs · iter426)
22. ☐ Run the post-restore smoke checklist in `RESTORE_RUNBOOK.md`
    sections 13-15.

### Stage E · Cutover verification (operator + agent · 10 min)

23. ☐ Operator signs in to `/sign-in` with super-admin creds → lands
    on `/admin` cleanly.
24. ☐ Operator confirms admin's enrolled passkey still works
    (`/api/passkeys/list` returns the prior credential).
25. ☐ Operator visits `/shop` → Shop Recovery hub renders with the
    pre-cutover dispatch / breakdown state intact.
26. ☐ Driver picks a shift, takes a test photo, confirms the photo
    persists across a page reload.
27. ☐ Confirm `_backup_drift_watch` runs cleanly on the next archive
    tick — no spurious WARN.

### Stage F · Lock-in (operator-driven · 2 min)

28. ☐ Tighten Atlas IP allowlist from `0.0.0.0/0` to Emergent egress
    IPs only.
29. ☐ Update `/app/memory/test_credentials.md` to record the Atlas
    URI lives in env, NOT in code.
30. ☐ Document the migration date in `/app/memory/PRD.md`.

---

## Rollback (if cutover smoke fails)

In the Emergent deploy dashboard:

1. Revert `MONGO_URL` to the pre-cutover value (the in-container
   `mongodb://localhost:27017` form).
2. Trigger redeploy.
3. The container-local Mongo data may already be lost, but R2 archive
   restore via `RESTORE_RUNBOOK.md` brings the platform back to the
   pre-cutover state within 30 min.
4. Investigate the Atlas-side failure (connectivity, auth, IP allowlist,
   tier capacity).
5. Retry Stage C once the root cause is fixed.

---

## Connection verification snippets (for the agent during cutover)

```bash
# Quick health probe
curl -s "$URL/api/health"

# Verify Mongo collection count matches archive manifest
python3 -c "
import os; from pymongo import MongoClient
client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
print(f'Collections: {len(db.list_collection_names())}')
"
```

---

## Backup continuity guarantee post-Atlas

The existing R2 archive pipeline is **independent of where Mongo
lives**. It uses `db.list_collection_names()` (iter425
auto-discovery), which works identically against an in-container
Mongo and an Atlas cluster.

After Atlas migration:

- 🟢 Hourly R2 archive continues
- 🟢 Nightly fallback at 03:00 UTC continues
- 🟢 `_backup_drift_watch` continues to log calm WARN on collection
  disappearance
- 🟢 MFA secret + password_hash redaction continues
- 🟢 RESTORE_RUNBOOK.md remains the single restore source of truth
- 🟢 Atlas adds its own continuous backup tier (paid) as a third
  copy

---

## GO / WATCH / ACTION REQUIRED

| Concern | Status |
|---|---|
| Today's container-mongo redeploy survivability | 🔴 **ACTION REQUIRED** in production · platform self-flags this |
| Migration path documented | 🟢 GO · 30-step checklist above · `RESTORE_RUNBOOK.md` complements |
| Migration is safe + reversible | 🟢 GO · all stages preserve old env-var values · R2 archive is the safety net |
| Atlas cost | 🟢 GO · free `M0` tier covers pilot · `M10` ≈ $57/mo covers production volume |
| Backup pipeline post-Atlas | 🟢 GO · pipeline is Mongo-location-agnostic |

---

## Doctrine adherence

| Restraint | Status |
|---|---|
| No migration dashboard | ✅ none built · operator runs the checklist |
| No destructive automation | ✅ this doc is **preparation only** |
| No new env var | ✅ uses existing `MONGO_URL` + `DB_NAME` |
| No new admin UI | ✅ |
| Migration is operator-led, agent-assisted | ✅ |

---

End of Phase 26.1 Mongo Durability Plan.
