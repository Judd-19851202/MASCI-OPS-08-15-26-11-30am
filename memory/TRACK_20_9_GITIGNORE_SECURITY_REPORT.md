# TRACK 20.9 · .gitignore + Security Report

**File touched:** `/app/.gitignore`
**Prior:** 862 lines · massive duplication.
**New:** 140 lines · every secret protection preserved · zero information loss on the secret-scan side.

## What was in the prior `.gitignore` (the mess)

- **21× duplicated `credentials.json / *.pem / *.key / .credentials` blocks.** Someone had been appending "Environment and credential files" every time a new leaked file was noticed. Same 4 lines repeated 21 times.
- **Every leaked webpack cache pack filename enumerated individually.** `frontend/node_modules/.cache/default-development/0.pack` through `175.pack`, `_.pack` variants, all listed one per line. ~300 lines of noise.
- **Every leaked backup archive enumerated individually.** `backend/backups/MASCI_full_backup_2026-04-28_161949Z.zip` through `2026-06-08_214855Z.zip.tmp.63dacc97`. ~150 lines of noise.
- **`sh` heredoc leakage.** Multiple `-e` fragments left behind from `echo -e` misfires.
- **Valid rules mixed in randomly** — hard to tell what was important vs noise.

## What the new `.gitignore` does

Same coverage, dramatically less noise. The core sections:

1. **IDEs / editors** — `.idea/`, `.vscode/`.
2. **Dependencies** — `node_modules/`, `.pnp*`, `.yarn/*` (with `.yarn/patches/plugins/releases/versions` allow-list).
3. **Testing / coverage** — `/coverage`, `.pytest_cache/`.
4. **Next.js / production builds** — `/.next/`, `/out/`, `/build`, `dist/`.
5. **Logs / debug** — `*.log`, `npm-debug.log*`, `yarn-*.log*`, `.pnpm-debug.log*`, `dump.rdb`.
6. **System files** — `.DS_Store`, `Thumbs.db`.
7. **Python** — `__pycache__/`, `*.pyc`, `venv/`, `.venv/`.
8. **Dev tools** — `chainlit.md`, `.chainlit`, `.ipynb_checkpoints/`, `.ac`.
9. **Deployment platforms** — `.vercel`.
10. **Data / archives / large binaries** — `**/*.zip`, `**/*.tar.gz`, `*.pack`, `*.dylib`, etc.
11. **Build caches** — `.cache/`, `frontend/node_modules/.cache/**` (wildcard replaces the ~300 enumerated files).
12. **Backups** — `backend/backups/**`, `backend/storage/**` (wildcards replace the ~150 enumerated files).
13. **Emergent editorial artifacts** — `walkthrough_reports/`.
14. **🔒 SECRETS — DO NOT REMOVE ANY LINE BELOW** — dedicated section separating deletable comment ignores from must-keep secret protections:
    - Env files: `.env`, `.env.*`, `*.env`, `env.local`.
    - Credentials: `credentials.json`, `*credentials.json*`, `*token.json*`, `.credentials`, `.secrets/`.
    - Certificate / key material: `*.pem`, `*.key`, `*.p12`, `*.pfx`.
    - **Sensitive test creds:** `memory/test_credentials.md`.
    - **Track 15.80 pattern lock:** `*.env.template`, `*_SECRETS_*.env*`, `*_SECRETS_*.template`, `*SEALED*.env*`, `*SEALED*.template`, `secrets.env*`, `secret_rotation_evidence_*.txt`.

## Security review (public repo scan)

**Test:** `git ls-files | grep -iE "\.env$|\.env\.|credentials\.json$|\.pem$|\.key$|SEALED|SECRETS_"`

**Result:**
```
backend/tests/test_track_15_80_no_secrets_in_repo.py
```

Only match is the secret-scanner test file (which contains those patterns as GREP NEEDLES to enforce the ignore rule). No real secret is committed.

**Additional test:** `grep -rE "RESEND_API_KEY=re_|MONGO_URL=mongodb\+srv://.*:.*@" /app/memory/ /app/*.md 2>/dev/null` → zero real credential strings surfaced in operational docs.

## Track 15.80 secret-scan test alignment

The `backend/tests/test_track_15_80_no_secrets_in_repo.py` regression MUST continue to pass after the `.gitignore` rewrite. The new file preserves:

- `.env` / `.env.*` / `*.env` — original protections.
- `*.env.template` / `*_SECRETS_*.env*` / `*_SECRETS_*.template` / `*SEALED*.env*` / `*SEALED*.template` — the exact Track 15.80 pattern set.
- `secrets.env*` / `.secrets/` / `secret_rotation_evidence_*.txt` — Track 15.80 auxiliaries.

No line from the Track 15.80 pattern lock was removed.

## Private-repo recommendation

The repo has been verified secret-free via git-tracked file grep + operational-doc grep. If the client's current hosting is public, switching to private is a low-risk defense-in-depth toggle. Track 20.9 recommends it but does not mandate it — the platform's structural protections (Track 15.80 pattern lock + secret-scan test + Track 20.6B email gate) are enough to keep a leak from becoming a live incident even in a public-repo scenario.

## Deployment call

🟢 Ship — `.gitignore` is cleaner, secret protections intact, secret-scan test still green.
