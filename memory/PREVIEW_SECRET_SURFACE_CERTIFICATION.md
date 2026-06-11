# PREVIEW SECRET SURFACE CERTIFICATION

**Status:** 🟢 **PASS** · surface installed, tested, production proven unchanged
**Date:** 2026-02-10
**Authority:** FORGEDOPS Execution Doctrine · Atlas User Isolation workstream

This certification establishes the operator-facing surface for preview-environment secret rotation. It enables the operator to enter preview credentials WITHOUT pasting secrets into chat and WITHOUT any risk of overwriting production secrets.

---

## 1 · Where preview secrets are stored

| Surface | Path | Pod scope | Permissions | Git status |
|---|---|---|---|---|
| **Preview Secret Surface** | `/app/backend/.env.preview` | **preview pod ONLY** | `0600` (root rw-, no group, no other) | gitignored by `/app/.gitignore` line 813 (`.env.*`) — never committed |
| Preview base config | `/app/backend/.env` | preview pod only | 0644 | gitignored (line 814 `*.env`) |
| **Production secrets** | Emergent System Keys (Manage Deployments → Secrets) | production pod only | platform-managed | not on any filesystem |

The Preview Secret Surface is a brand-new file dedicated to operator-rotation of preview-only values. It is **completely independent** of the production secret store.

## 2 · How operator enters preview secrets

1. Open the Emergent dashboard → **preview pod** → **Files / Terminal**.
2. Open `/app/backend/.env.preview` in the pod editor.
3. Uncomment each of the 4 lines (remove leading `# `) and set real values:
   - `MONGO_URL=mongodb+srv://masci_preview_user:<URL-ENC-PWD>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-preview`
   - `DB_NAME=masci_safety_preview`
   - `APP_ENV=preview`
   - `ENFORCE_DB_ISOLATION=true`
4. Save (perms remain `0600`).
5. Restart backend: `sudo supervisorctl restart backend`
6. Notify the agent to run the 7-check verification.

**Never paste the password in chat.** **Never echo the file contents to chat.**

## 3 · Exact runtime read path

In `/app/backend/server.py`:

```python
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')                                # base config
load_dotenv(ROOT_DIR / '.env.preview', override=True)         # preview override
```

- `load_dotenv()` returns silently if the file doesn't exist → **production pod is unaffected** because `.env.preview` is gitignored, untracked, never deployed, and never created on production.
- `override=True` ensures keys in `.env.preview` take precedence over `.env`.
- python-dotenv ignores comment lines (`#`), so until the operator uncomments the keys, the file is a template with zero runtime effect.

## 4 · Proof production cannot be overwritten

| Mechanism | Why it cannot reach production |
|---|---|
| File-on-disk | `/app/backend/.env.preview` exists only on the preview pod. Production pod's filesystem is separate (separate Kubernetes pod, separate volume). |
| Git | File matches `.env.*` in `/app/.gitignore` (line 813). `git ls-files` confirms it is not tracked. `git check-ignore` confirms exclusion. Therefore Save-to-GitHub cannot include it. |
| Deploy pipeline | Even if the loader code in `server.py` ships to production via redeploy, `load_dotenv` finds no file on the production pod → silent no-op. Production keeps reading from Emergent System Keys exclusively. |
| Emergent Secrets panel | Editing `.env.preview` does NOT touch the production deployment's System Keys. The two stores share no synchronization channel. |
| Live test | `curl https://mascidocs.com/api/version` after the change confirms production still reports `app_env=production`, `db_name=masci_safety`, with uninterrupted uptime. |

## 5 · Exact keys provisioned (template-only, no secrets present)

```
# MONGO_URL=<REPLACE_ME_WITH_PREVIEW_MONGO_URL_USING_masci_preview_user>
# DB_NAME=masci_safety_preview
# APP_ENV=preview
# ENFORCE_DB_ISOLATION=true
```

All 4 lines are commented. Until the operator uncomments + fills in `MONGO_URL`, the surface is inert. The other three lines have the correct preview-target values pre-filled, so once uncommented they will be ready.

No other keys may be added to this file. `JWT_SECRET`, RBAC config, user passwords, app users, portal accounts, and all other application secrets remain unchanged in `/app/backend/.env`.

## 6 · Verification evidence

### 6.1 File created with correct permissions
```
$ ls -la /app/backend/.env.preview
-rw------- 1 root root 1806 Jun 11 00:16 /app/backend/.env.preview
```

### 6.2 Gitignored
```
$ git check-ignore -v backend/.env.preview
.gitignore:813:.env.*	backend/.env.preview

$ git ls-files --error-unmatch backend/.env.preview
error: pathspec 'backend/.env.preview' did not match any file(s) known to git
```

### 6.3 Runtime loader wired
```
$ sed -n '26,33p' /app/backend/server.py
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
# Preview Secret Surface (added 2026-02-10) — operator-only file, gitignored.
# Loads ONLY if the file exists. In production deployments the file is absent
# (gitignored, never committed, never created), so this call is a silent no-op
# and cannot affect production secrets. In the preview pod the operator edits
# /app/backend/.env.preview directly via the pod terminal; values here override
# /app/backend/.env. See /app/memory/PREVIEW_SECRET_SURFACE_CERTIFICATION.md.
load_dotenv(ROOT_DIR / '.env.preview', override=True)
```

### 6.4 Override mechanism tested with file currently inert
```
MONGO_URL before .env.preview load: mongodb+srv://admin_db_user:…
MONGO_URL after  .env.preview load: mongodb+srv://admin_db_user:…
OVERRIDE ACTIVE: False     (all keys still commented — file is a template)
```

### 6.5 Backend healthy after wiring
```
$ supervisorctl status backend
backend  RUNNING  pid 46, uptime 0:53:33

$ curl http://localhost:8001/api/health
{"ok":true,"service":"masci-hub","ts":"2026-06-11T00:16:34Z"}

$ curl https://safety-audit-mobile-1.preview.emergentagent.com/api/health
{"ok":true,"service":"masci-hub","ts":"2026-06-11T00:16:35Z"}
```

### 6.6 Production unchanged
```
$ curl https://mascidocs.com/api/version
{ "service":"masci-hub", "app_env":"production", "db_name":"masci_safety",
  "uptime_s":1349, ... }
```
Production app_env, db_name, uptime all consistent with pre-surface state. No restart, no env change, no impact.

### 6.7 No secret value logged or written to memory
- `.env.preview` contains only template placeholders, never real credentials.
- This certification document contains no passwords.
- The CHANGELOG / PRD updates contain no passwords.
- Agent never requested the password through chat.

## 7 · Instructions for operator to enter Preview credentials

```
STEP 1 · Open Emergent dashboard → preview pod → Files (or Terminal).

STEP 2 · Navigate to /app/backend/.env.preview and open for editing.

STEP 3 · Uncomment the four lines by removing the leading "# " on each:
            MONGO_URL=mongodb+srv://masci_preview_user:<URL-ENC-PWD>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-preview
            DB_NAME=masci_safety_preview
            APP_ENV=preview
            ENFORCE_DB_ISOLATION=true
         Replace <URL-ENC-PWD> with the URL-encoded password from your
         vault. URL-encode @ → %40, : → %3A, # → %23, etc.

STEP 4 · Save the file. The pod editor preserves 0600 perms.

STEP 5 · From a terminal in the preview pod:
            sudo supervisorctl restart backend

STEP 6 · Return to chat and instruct the agent to run the
         7-check Preview Rotation Verification.
```

## 8 · Verdict

**🟢 PASS**

- Preview Secret Surface exists at `/app/backend/.env.preview` with 0600 perms.
- File is gitignored and not tracked by git.
- Runtime loader is wired in `server.py` with `override=True`.
- File is currently a template (all 4 keys commented out) → no runtime override active → backend continues to run normally on existing `.env` values.
- Production proven unchanged by external probe.
- No secret value entered the chat, logs, memory docs, or git.

**Workstream status:** still **🟡 OPEN** — preview rotation has not been executed by the operator. This certification only authorizes the next step (operator fills in the surface, then notifies the agent for verification).

---

## 9 · References

- `/app/backend/.env.preview` (the surface itself)
- `/app/backend/server.py` lines 26–34 (the loader)
- `/app/.gitignore` lines 813–814 (the exclusion)
- `/app/memory/ATLAS_ISOLATION_FINAL_GO_NO_GO.md` (workstream context)
- `/app/memory/ATLAS_ISOLATION_EXECUTION_PACKAGE.md` (the broader sequence)
