# ATLAS_PASSWORD_ROTATION_RUNBOOK.md
## MongoDB Atlas Database User Password Rotation
## iter430 · 2026-05-25

---

## Why rotate

The current Atlas database-user password (`admin_db_user` · `f3Dv7FBQZMFY4JRp`) was pasted in chat during the migration and may have been logged in agent transcripts. Rotating once now restores credential hygiene.

After rotation, the old password becomes invalid and the new one lives only in:
- Atlas's hashed credential store
- Your password manager
- The preview pod's `MONGO_URL` env var
- The production deployment's `MONGO_URL` env var

---

## Pre-flight

| Item | Confirm |
|---|---|
| You have access to the Atlas console at `https://cloud.mongodb.com` | ☐ |
| You have access to the preview pod (this chat workspace) | ☐ |
| You have access to the Emergent production deploy dashboard for `mascidocs.com` | ☐ |
| You have a password manager open to capture the new password | ☐ |

---

## 11 operator steps

### Step 1 · Open Atlas Database Access

1. Browser → https://cloud.mongodb.com
2. Sign in to your Atlas account
3. Left sidebar → **Security → Database & Network Access**
4. Top tab → **Database Users**

You should see the `admin_db_user` row.

### Step 2 · Edit the production DB user

1. Click the **Edit** (pencil) button next to `admin_db_user`
2. Under "Password Authentication", click **Edit Password**

### Step 3 · Generate a new strong password

1. Click **Autogenerate Secure Password**
2. Click **Show** so you can read it
3. Copy it to your password manager (label: "MASCI Atlas admin_db_user · 2026-05-25 rotation")
4. **Do NOT close this dialog yet** — you need the password in steps 4 + 5

### Step 4 · Update PREVIEW MONGO_URL

In this chat workspace, drop me a message with **only the new password** (you can mask it like `NEWPW=<actual-password>` — I will treat it as sensitive). I will:

1. Update `/app/backend/.env` MONGO_URL to use the new password
2. Restart preview backend supervisor
3. Verify `/api/health` returns 200
4. Verify Atlas is reachable via the new credential
5. Confirm `/admin/system` still shows the GREEN banner

*(Alternative if you'd rather do it manually: edit `/app/backend/.env` line `MONGO_URL=mongodb+srv://admin_db_user:<NEWPW>@masci-prod.1nduwmg.mongodb.net/?appName=MASCI-prod&retryWrites=true&w=majority`, then `sudo supervisorctl restart backend`.)*

### Step 5 · Update PRODUCTION MONGO_URL

In the Emergent deploy dashboard for `mascidocs.com`:

1. Open Environment Variables section
2. Find `MONGO_URL`
3. Click Edit
4. Replace the password portion only — keep the `admin_db_user:` prefix and `@masci-prod...` suffix untouched
5. Save

### Step 6 · Save the new password in Atlas

Back in the Atlas Edit Password dialog from Step 3:

1. Click **Update User**
2. Wait 30 seconds for Atlas to propagate the new credential

### Step 7 · Trigger production redeploy

1. Emergent deploy dashboard → click **Redeploy**
2. Watch the deployment progress indicator
3. Wait ~5-10 minutes for the new pod to come up

### Step 8 · Verify production `/api/health`

```
curl https://mascidocs.com/api/health
→ {"ok":true,"service":"masci-hub","ts":"..."}
```

If 200 returned → production is connecting to Atlas with the new password.
If 500/502 → check production logs; most likely cause is a typo in the new password copy-paste.

### Step 9 · Verify GREEN banner on /admin/system

1. Browser → https://mascidocs.com/admin/system
2. Sign in as super-admin
3. Confirm the "Persistent database connected — MongoDB Atlas. Redeploys will not wipe your data." card is **green**

### Step 10 · Verify backups still run

Trigger a manual archive to verify the pipeline:

```
POST https://mascidocs.com/api/admin/backups/run-complete-now
  (with X-Admin-Token header)
```

After ~60 seconds, refresh `/admin/system` and confirm the new archive appears in the archive list.

### Step 11 · Verify old password no longer works

In a fresh terminal (or right here, message me):

```
# secret-scan: allow-line
python3 -c "
from pymongo import MongoClient
import os
OLD = os.environ.get('OLD_ATLAS_URL')  # operator supplies via env var · never commit
try:
    c = MongoClient(OLD, serverSelectionTimeoutMS=5000)
    c.admin.command('ping')
    print('🔴 OLD PASSWORD STILL WORKS — rotation NOT complete')
except Exception as e:
    print(f'🟢 Old password rejected: {type(e).__name__}')
"
```

**How to run**: export `OLD_ATLAS_URL` in your shell with the
pre-rotation connection string (then `unset` it afterwards — never
commit). Track 15.80 forensic remediation removed the previously
literal connection string that lived on this line.

Expected: 🟢 **Authentication failed** (this is what we want — confirms the old password is dead).

---

## Rollback (if Step 7 / 8 fails)

| Symptom | Action |
|---|---|
| Production `/api/health` returns 500/502 | Revert `MONGO_URL` env var in Emergent dashboard to use the OLD password (Atlas is still accepting it for ~24 h after a rotation in some tiers · for free M0 it switches instantly so revert won't work — instead, re-edit the Atlas password back to the OLD value and re-redeploy) |
| Atlas dialog says "user not found" | The Atlas user was accidentally renamed — go back to Step 2 and re-verify the username is `admin_db_user` |
| Preview backend won't start | Check `/var/log/supervisor/backend.err.log` for the connection error · most likely typo in the new password |

---

## What does NOT change

- Atlas cluster name (`masci-prod`)
- Atlas cluster hostname (`masci-prod.1nduwmg.mongodb.net`)
- Database name (`masci_safety`)
- Atlas connection-string suffix (`?appName=MASCI-prod&retryWrites=true&w=majority`)
- IP allowlist (will tighten separately per `PHASE26_2_PRODUCTION_GO_NO_GO.md` operator action #4)

---

## Sign-off

| Step | Completed |
|---|---|
| Atlas password rotated | ☐ |
| Preview MONGO_URL updated + verified | ☐ |
| Production MONGO_URL updated | ☐ |
| Production redeployed | ☐ |
| Production /api/health green | ☐ |
| /admin/system banner still green | ☐ |
| Manual backup verified | ☐ |
| Old password rejected | ☐ |

Date completed: _______________________
Operator: ______________________________

---

End of Atlas Password Rotation Runbook.
