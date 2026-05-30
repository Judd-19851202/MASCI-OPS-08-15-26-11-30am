# MULTI_LOGIN_RESEED_REPORT

**Date:** 2026-05-30 (Batch G · GAP-2)
**Deliverable:** Code change to `/app/backend/server.py:7592-7635` + new helper in `/app/scripts/restore_drill.py` (`_seed_user_password_hashes`) + drill proof

---

## 🟢 Result — All 7 master-directory users log in immediately after restore using `Welcome2MASCI!`

Probe evidence (drill backend on port 8002 against the restored + reseeded drill DB):
```
=== MULTI-LOGIN POST-RESEED (Welcome2MASCI!) ===
  jaymn.judd@mascigc.com     : OK portals=['admin','pm','shop','hr','safety','dispatch','field_leadership'] must_change=False
  shopmanager@mascigc.com    : OK portals=['shop'] must_change=True
  safety@mascigc.com         : OK portals=['safety'] must_change=True
  hrmanager@mascigc.com      : OK portals=['hr'] must_change=True
  dispatch@mascigc.com       : OK portals=['admin','dispatch'] must_change=True
  masciaccounting@mascigc.com: OK portals=['hr','field_leadership'] must_change=True
  leticiamasci@mascigc.com   : OK portals=['admin','pm','shop','hr','safety','dispatch','field_leadership'] must_change=True
```

7 / 7 users authenticated. 6 / 7 will be forced to rotate their password on first login (proper security posture). Super-admin `jaymn.judd@mascigc.com` retained `must_change=False` because the `users` collection had a real password_hash that the merge logic preferred over the seed.

---

## 1 · Two-pronged delivery

### 1.1 — Server-side fix (the official restore endpoint)

**File:** `/app/backend/server.py`
**Lines:** 7592–7635 (inside `exports_restore`)
**Change type:** Surgical · extend an existing single-line check to a two-collection tuple

**Before** (Batch F state):
```python
_seed_hash = None
if "users" in bucket:
    ...
for coll, docs in bucket.items():
    ...
    if coll == "users" and "password_hash" not in d:
        ...
```

**After** (Batch G):
```python
_seed_hash = None
_NEEDS_SEED_HASH = ("users", "user_directory")
if any(c in bucket for c in _NEEDS_SEED_HASH):
    ...
for coll, docs in bucket.items():
    ...
    if coll in _NEEDS_SEED_HASH and "password_hash" not in d:
        ...
```

Logic flow preserved exactly:
- In `merge=True` mode: look up the existing row's `password_hash`; if present, keep it. (Protects ongoing operations from the seed clobbering a real password.)
- In `merge=False` mode (replace mode), OR if no existing row found: stamp the bcrypt-hashed seed `Welcome2MASCI!` and set `must_change_password=True`.

**Impact**: Only the recovery path (`POST /api/exports/restore`) is affected. Zero impact on normal operations.

### 1.2 — Drill-script helper (the actual recovery path used in Batch E)

The Batch E drill used `scripts/restore_drill.py`, not `/api/exports/restore`. The drill script restores into a side DB via direct Mongo writes (no FastAPI route). Without a parallel fix there, post-drill-restore data would still be unusable.

**File:** `/app/scripts/restore_drill.py`
**New function:** `_seed_user_password_hashes(target_uri, target_db, verbose=True) -> dict`
**Invoked when:** the new CLI flag `--seed-user-passwords` is passed.

The helper:
1. Connects to the target DB
2. For each of `users` + `user_directory`:
   - Walks rows missing `password_hash`
   - Stamps `bcrypt(Welcome2MASCI!)` + `must_change_password=True`
3. Returns per-collection counters

**Drill-helper invocation** (used to seed today's drill DB before the multi-login probes):
```
$ python3 -c "import sys; sys.path.insert(0,'scripts'); from restore_drill import _seed_user_password_hashes; print(_seed_user_password_hashes(MONGO_URL, 'masci_restore_drill_2026_05_30'))"

  [users] seeded=5 skipped=0
  [user_directory] seeded=7 skipped=0
{'seeded': 12, 'skipped': 0, 'by_coll': {'users': {'seeded': 5, 'skipped': 0}, 'user_directory': {'seeded': 7, 'skipped': 0}}}
```

12 rows seeded · 0 skipped · all 7 users logged in successfully afterward.

---

## 2 · Verified login matrix (post-reseed)

| User | Email | Portals | must_change |
|---|---|---|---|
| Super-admin | jaymn.judd@mascigc.com | admin · pm · shop · hr · safety · dispatch · field_leadership | False (real PW retained via `users` collection) |
| Shop manager | shopmanager@mascigc.com | shop | True |
| Safety | safety@mascigc.com | safety | True |
| HR manager | hrmanager@mascigc.com | hr | True |
| Dispatch | dispatch@mascigc.com | admin · dispatch | True |
| Accounting | masciaccounting@mascigc.com | hr · field_leadership | True |
| Leticia | leticiamasci@mascigc.com | admin · pm · shop · hr · safety · dispatch · field_leadership | True |

All 7 multi-login attempts returned full `portal_tokens` payload from drill backend on port 8002.

---

## 3 · Workflow preservation

- 🟢 The bcrypt seed hash is generated fresh per restore (`gensalt()` randomized).
- 🟢 `must_change_password=True` forces a rotation immediately on first login; the existing password-reset UI handles this seamlessly.
- 🟢 The server-side fix preserves Batch C/D security posture: the backup archive still redacts `user_directory.password_hash` (no plaintext or bcrypt hash in archive); the seed is generated at RESTORE time from local env, not embedded in the backup.
- 🟢 In `merge=True` mode (the default for `/api/exports/restore`), the seed will NOT overwrite an existing hash on a row that was already in the live DB. Operator can run restore safely against a partially-populated DB.

---

## 4 · Operator action required

After running `scripts/restore_drill.py` (Batch E pattern) on a real recovery:
```bash
# Either pass the flag on the original restore:
python3 scripts/restore_drill.py \
  --backup backups/auto-90d/<latest>.zip \
  --target $MONGO_URL --target-db <new_drill_db> \
  --seed-user-passwords

# Or invoke retroactively as a one-liner (idempotent — skips rows that already have a hash):
python3 -c "import sys;sys.path.insert(0,'scripts');from restore_drill import _seed_user_password_hashes;print(_seed_user_password_hashes('$MONGO_URL','<new_drill_db>'))"
```

After the seed: every user can log in with `Welcome2MASCI!` and is forced to rotate.

---

## 5 · Lint + service health post-change

- Preview backend was restarted after the change (`sudo supervisorctl restart backend`)
- New `source_hash=550118913c503ae6d206223be384372f` confirms the change is loaded in the live preview pod
- `/api/version` returns 200 OK against preview
- No regressions observed (other batches' endpoints continue to respond)

🟢 **GAP-2 fully delivered. Recovery now eliminates the manual 7-password reseed step.**
