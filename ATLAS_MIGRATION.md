# MongoDB Atlas Migration — 15-Minute Setup

> When the red banner on `/admin` says **"⚠ Your data will be deleted on the next redeploy"** (or in Spanish: **"⚠ Sus datos se borrarán en el próximo redespliegue"**), it's because production Mongo is running **inside the Emergent container**. Every redeploy wipes the container — meaning everything in `db.daily_reports`, `db.equipment_inspections`, `db.docs`, `db.users`, the Crew Hub messages, the Oxford 24-12 Basecamp import, etc. all disappears unless you backup first.

The fix is to point the production app at **MongoDB Atlas** (free tier, hosted by MongoDB themselves). After that, redeploys are safe forever — Atlas runs outside the container.

---

## Step 1 — Sign up (5 min)

1. Go to **https://www.mongodb.com/cloud/atlas/register**
2. Sign up with the same email you use for Emergent (e.g. jaymn.judd@mascigc.com).
3. When asked "What is your goal today?" pick **"Build a new application"**.
4. **Create a free cluster**:
   - Tier: **M0 (Free, 512 MB)** — plenty for years of safety records.
   - Provider: **AWS**
   - Region: **us-east-1 (N. Virginia)** — closest latency to Emergent.
   - Cluster name: `MASCI-Production`

It takes ~3 minutes to provision. While you wait:

## Step 2 — Add a database user (1 min)

1. In the Atlas left sidebar: **Database Access** → **+ Add New Database User**
2. Authentication Method: **Password**
3. Username: `masci-app`
4. Password: click **Autogenerate Secure Password** → **copy it somewhere safe** (you can't see it again).
5. Built-in role: **Read and write to any database**
6. **Add User**.

## Step 3 — Allow Emergent to connect (1 min)

1. Atlas left sidebar: **Network Access** → **+ Add IP Address**
2. Click **Allow Access from Anywhere** (`0.0.0.0/0`).
   *(Emergent's container IPs change on each redeploy, so locking this down further requires a static-IP add-on. Atlas is still safe — you still need the username + password.)*
3. **Confirm**.

## Step 4 — Get the connection string (1 min)

1. Atlas left sidebar: **Database** → click **Connect** on your `MASCI-Production` cluster
2. Choose **Drivers**
3. Driver: **Python**, Version: **3.12 or later**
4. Copy the connection string. It looks like:
   ```
   mongodb+srv://masci-app:<password>@masci-production.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-Production
   ```
5. **Replace `<password>`** with the password you saved in Step 2.

## Step 5 — Wire it into Emergent (5 min)

In your **Emergent production app dashboard** → **Environment Variables** → set:

```
MONGO_URL = mongodb+srv://masci-app:<your-password>@masci-production.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-Production
DB_NAME   = masci_production
```

> ⚠ Don't change `DB_NAME` once data is written to it — Atlas will create the database the first time the app inserts a record. If you change it later, you'll be looking at an empty database (your old data is still there under the old name).

Then **redeploy the production app**.

## Step 6 — Verify

1. Visit `https://<your-prod-app>/admin` and log in.
2. The red banner should now be **green**: **"Persistent database connected · MongoDB Atlas"** / **"Base de datos persistente conectada"**.
3. The first time it boots, the safety / equipment / employees / suppliers seeds run automatically (idempotent — safe to re-run on every boot).

## Step 7 — Restore your data (one-time)

If you have an existing `.zip` backup downloaded from the old (in-container) admin:

1. Visit `/admin` → big green **"RESTORE FROM FILE"** button → pick the latest `.zip`.
2. Wait ~30 seconds. You'll see a toast: `✓ Restored N records across M collections`.
3. Done — every safety record, photo, signature, Crew Hub message, todo, and project doc is back.

For the Oxford project (193 Basecamp files, ~744 MB) the disk-backed PDFs at `/app/backend/storage/project_docs/24-12/` will need to be re-uploaded individually OR re-imported via `python /app/backend/scripts/basecamp_import.py` + `basecamp_import_big.py`. The import scripts are idempotent — safe to re-run.

---

## Free-tier limits (so you know what to expect)

| Limit | Free tier | When you'd hit it |
|---|---|---|
| Storage | 512 MB | Maybe 2-3 years of safety records + base64 photos. The Oxford doc archive doesn't count — it's on disk. |
| Concurrent connections | 500 | Never. |
| Cluster RAM | 1 GB shared | Never. |

When you outgrow the free tier (years away), bump to **M10 ($57/mo)** — same connection string, no migration needed.

---

## Cost summary

- **MongoDB Atlas Free Tier**: $0 forever
- **Optional upgrade later**: $57/mo when you outgrow 512 MB
- **Your time today**: ~15 min one-time setup
