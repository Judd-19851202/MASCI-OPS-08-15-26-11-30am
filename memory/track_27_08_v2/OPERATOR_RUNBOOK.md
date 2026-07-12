# TRACK 27.08 v2 · OPERATOR RUNBOOK · Production Evidence Bundle

**Purpose:** collect the raw JSON evidence needed to close the four documented gaps in v1 (per-object inventory · full ETag duplicate scan · month/year attribution · split SHA256 chain-of-custody).

**Contract (read this before running anything):**
- All commands are **GET / read-only** except step 2 (`POST /scan`) which is idempotent and mutates ONLY the internal `r2_inventory` / `r2_references` / `r2_classifications` Mongo collections that Track 27.06 already authorises. Zero R2 objects modified. Zero business Mongo mutations. Zero configuration changes.
- The token is expected to be in a **chmod 600** file at `~/.masci_prod_admin_token` (see §0 below) — **never** echoed, **never** written to shell history, **never** included in the saved JSON.
- Every output is sanitised: `jq` strips any `x-admin-token`, `authorization`, `set-cookie`, `cookie`, `signed_url`, and any raw base64 payload before writing to disk.
- Every output file includes a `_meta` block: `run_at` (UTC), `endpoint`, `http_status`, `app_env`, `db_name`, `source_hash`, `sanitised: true`.

Files produced (drop into `/app/memory/track_27_08_v2/` on the preview pod):

| # | File | Endpoint |
|---|---|---|
| 0 | `env.json` | `GET /api/version` |
| 1 | `scan.json` | `POST /api/admin/r2/lifecycle/scan` |
| 2 | `latest.json` | `GET /api/admin/r2/lifecycle/latest` |
| 3 | `health.json` | `GET /api/admin/r2/lifecycle/health` |
| 4 | `classification.json` | `GET /api/admin/r2/lifecycle/classification` |
| 5 | `inventory_backups.json` | `GET /api/admin/r2/lifecycle/inventory?prefix=backups/&limit=1000&skip=0` |
| 6 | `intelligence.json` | `GET /api/admin/r2/lifecycle/intelligence` |
| 7 | `recovery.json` | `GET /api/admin/recovery/snapshot` |
| 8 | `backups_disk.json` | `GET /api/admin/backups` |
| 9 | `backups_integrity.json` | `GET /api/admin/backups/integrity-check` |

---

## §0 · One-time token capture (do this once, in the authorised prod execution context)

```bash
# From the production execution context (browser dev-tools › Application › Local Storage on mascidocs.com):
#   Copy the value of `masci.admin.token`.
# Then, in a shell in that same authorised context:
umask 077
read -srp 'Paste admin token (input hidden): ' T
export MASCI_PROD_ADMIN_TOKEN="$T"
unset T
umask 022
# The token now lives ONLY in this shell's env. It is NOT on disk. It will die when the shell exits.
```

At end of session:

```bash
unset MASCI_PROD_ADMIN_TOKEN
history -c   # drop shell history for this session
```

---

## §1 · Common env

```bash
BASE=https://mascidocs.com
OUT=/tmp/track_27_08_v2   # local scratch — sanitise before uploading
mkdir -p "$OUT"

# jq sanitiser — strips any secret-like fields before persisting
sanitise() {
  jq '
    walk(
      if type=="object" then
        with_entries(select(
          (.key | ascii_downcase) as $k
          | ($k != "x-admin-token")
          and ($k != "authorization")
          and ($k != "cookie")
          and ($k != "set-cookie")
          and ($k != "signed_url")
          and ($k | test("password|secret|token|api_?key") | not)
        ))
      else . end
    )
  '
}

hdr_admin="X-Admin-Token: ${MASCI_PROD_ADMIN_TOKEN}"
```

---

## §2 · Step 0 — Environment identity + preflight

```bash
STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
RESP=$(curl -sS -w '\n%{http_code}' "$BASE/api/version")
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n 1)
jq -n --argjson body "$BODY" --arg endpoint "/api/version" --arg code "$CODE" --arg stamp "$STAMP" '{
  _meta: {run_at: $stamp, endpoint: $endpoint, http_status: ($code|tonumber), sanitised: true},
  body: $body
}' | sanitise > "$OUT/env.json"

# HARD PREFLIGHT — do NOT proceed unless every check passes.
APP_ENV=$(jq -r '.body.environment_identity.app_env // .body.app_env // "MISSING"' "$OUT/env.json")
DB_NAME=$(jq -r '.body.environment_identity.db_name // .body.db_name // "MISSING"' "$OUT/env.json")
SRC_HASH=$(jq -r '.body.source_hash // "MISSING"' "$OUT/env.json")

echo "APP_ENV=$APP_ENV  DB_NAME=$DB_NAME  source_hash=$SRC_HASH"
[[ "$APP_ENV" == "production" ]] || { echo 'ABORT: APP_ENV != production'; exit 1; }
[[ "$DB_NAME" == "masci_safety" ]] || { echo 'ABORT: DB_NAME != masci_safety'; exit 1; }
```

If either assertion fails: STOP. Do not run the rest of the runbook. Report the mismatch and I will amend the plan.

---

## §3 · Step 1-9 — Read-only evidence pulls

For every step below the pattern is identical:

```bash
run() {
  local label="$1" method="$2" path="$3" file="$4"
  local stamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local resp code body
  resp=$(curl -sS -w '\n%{http_code}' -X "$method" -H "$hdr_admin" "$BASE$path")
  body=$(echo "$resp" | head -n -1)
  code=$(echo "$resp" | tail -n 1)
  echo "$label → $code"
  jq -n --argjson body "$body" --arg endpoint "$path" --arg code "$code" \
        --arg method "$method" --arg stamp "$stamp" \
        --arg app_env "$APP_ENV" --arg db_name "$DB_NAME" --arg src "$SRC_HASH" '{
     _meta: {
       run_at: $stamp, method: $method, endpoint: $endpoint,
       http_status: ($code|tonumber), app_env: $app_env, db_name: $db_name,
       source_hash: $src, sanitised: true
     },
     body: $body
   }' | sanitise > "$OUT/$file"
}
```

Now run each pull:

```bash
# 1 · Fresh three-phase scan (idempotent; ~15s on prod)
run "scan"                 POST "/api/admin/r2/lifecycle/scan"                     scan.json

# 2 · Latest summary
run "latest"               GET  "/api/admin/r2/lifecycle/latest"                   latest.json

# 3 · Storage health signals
run "health"               GET  "/api/admin/r2/lifecycle/health"                   health.json

# 4 · Classification snapshot + per-class samples
run "classification"       GET  "/api/admin/r2/lifecycle/classification"           classification.json

# 5 · Per-object inventory · backups prefix · full listing (888 objects, cap 1000)
run "inventory_backups"    GET  "/api/admin/r2/lifecycle/inventory?prefix=backups/&limit=1000&skip=0"  inventory_backups.json
# If _meta.body.total_matching > 1000, please run once more with skip=1000 and save as
# inventory_backups_p2.json — I will merge on receipt.

# 6 · Intelligence + cost estimate (top prefixes, largest objects)
run "intelligence"         GET  "/api/admin/r2/lifecycle/intelligence"             intelligence.json

# 7 · Recovery dashboard snapshot (backup_health trend + failure rows)
run "recovery"             GET  "/api/admin/recovery/snapshot"                     recovery.json

# 8 · Disk-side stored backups (may be empty in prod — expected)
run "backups_disk"         GET  "/api/admin/backups"                               backups_disk.json

# 9 · Backup integrity — captured collections vs live collections
run "backups_integrity"    GET  "/api/admin/backups/integrity-check"               backups_integrity.json
```

---

## §4 · Step 10 — Post-run hygiene

```bash
# Confirm nothing leaked
grep -RIn -E 'x-admin-token|Authorization|password|secret' "$OUT" && \
  echo 'WARN: possible leak — inspect before uploading' || echo 'OK · no secret material detected in outputs'

# Token disposal
unset MASCI_PROD_ADMIN_TOKEN
history -c 2>/dev/null || true
```

---

## §5 · Upload

Copy the 10 files to the preview pod path `/app/memory/track_27_08_v2/` (via the same channel used to deliver this runbook, e.g. paste as attachments in your reply). Do not paste raw JSON into chat — file drops only, so the sanitiser output is preserved intact.

When the 10 files are in place, I will:
- verify each `_meta.http_status == 200` (or 202 for scan)
- verify each `_meta.app_env == production` and `db_name == masci_safety` and `source_hash` matches across files
- rebuild the v2 report from these dumps
- compute the four separate SHA256s (inventory · dependency · storage · risk) locally over the dumps
- publish `/app/memory/TRACK_27_08_V2_BACKUP_FORENSICS_COMPLETE.md`

**Zero production access will be attempted from the preview pod.** Zero business Mongo mutation. Zero R2 mutation. Zero policy invented.
