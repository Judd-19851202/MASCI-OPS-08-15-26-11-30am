# IAM_PHASE_A_CERTIFICATION.md
## OMEGA · IAM Enterprise Completion · Phase A — Unified Directory Completion
**Date**: 2026-06-03 21:04 UTC  **Verdict**: 🟢 PASS — PM + Field Leadership now mirrored.

---

## 1. What changed
**File**: `/app/backend/lib/identity_mirror.py`
**Diff shape**: 5 lines · 1 comment block updated

```diff
 PORTAL_COLLECTIONS: List[Tuple[str, str]] = [
     ("admin", "admin_users"),
     ("hr",    "hr_users"),
-    ("pm",    "pm_users"),
+    ("pm",    "project_managers"),     # iter502 · OMEGA IAM Enterprise Phase A
     ("shop",  "shop_users"),
     ("safety", "safety_users"),
     ("dispatch", "dispatch_users"),
+    ("field_leadership", "field_leadership_users"),  # iter502 · OMEGA IAM Enterprise Phase A
 ]
```

---

## 2. Live verification (against preview DB `masci_safety_preview`)

### 2.1 Backend restart
```
[identity-mirror] startup sync complete:
  scanned=75 created=0 updated_mirrored=73 touched_managed=2
```
`scanned=75` = aggregated unique emails across all 7 portal collections. `updated_mirrored=73` includes the newly-mirrored PM + FL identities. `touched_managed=2` = the managed rows (super admin) whose `mirror_sources` was refreshed.

### 2.2 user_directory counts (before → after)
| Metric | Before | After | Δ |
|--------|------:|------:|--:|
| Total rows | 50 | 79 | **+29** |
| `mirrored=true` rows | 45 | 74 | +29 |
| Rows with `pm` portal | 1 | **6** | +5 |
| Rows with `field_leadership` portal | 1 | **25** | +24 |

The +29 maps exactly to: **5 new PM identities** (6 PMs total minus 1 super-admin already present) **+ 24 new FL identities** (the 24 FL roster entries) = 29.

### 2.3 Sample PM mirror rows
```
davidjewett@mascigc.com  | mirrored=True | portals=['pm']  | mirror_sources=['pm']
chriswright@mascigc.com  | mirrored=True | portals=['pm']  | mirror_sources=['pm']
ramonrodriguez@mascigc.com | mirrored=True | portals=['pm'] | mirror_sources=['pm']
```

### 2.4 Sample FL mirror rows
```
fieldleader@mascigc.com         | mirrored=True | portals=['field_leadership']
allensmathers@masciae.com       | mirrored=True | portals=['field_leadership']
anthonygoes.masci@yando.com     | mirrored=True | portals=['field_leadership']
```

### 2.5 Super admin (`jaymn.judd@mascigc.com`) — managed row
```
mirrored = None (i.e. managed)
portals  = ['admin','dispatch','field_leadership','hr','pm','safety','shop']
mirror_sources = ['hr','shop','safety','dispatch','pm']  ← 'pm' newly added
password_hash  = unchanged (bcrypt $2b$...)
```
The managed row's portal grants and password are untouched per
`identity_mirror.backfill_mirror()` lines 236-244 ("Never overwrite portals or pw" on managed rows).

---

## 3. Backward-compatibility attestation

### 3.1 Existing logins (live curl)
| Portal | Endpoint | Status |
|--------|----------|:-:|
| Master directory | `POST /api/auth/multi-login` super admin | 🟢 200 + MFA challenge as expected |
| HR | `POST /api/hr/login` hrmanager@mascigc.com | 🟢 200 + token |
| Shop | `POST /api/shop/login` testmech@mascigc.com | 🟢 200 + token |
| PM | `POST /api/pm/login` chriswright@mascigc.com | 🟢 200 + token |
| Dispatch | `POST /api/dispatch/login` dispatch@mascigc.com | ⚠ 401 — password was stale BEFORE this sprint (documented in `/app/memory/test_credentials.md` lines 117-119, predates iter502). Not a regression. |

### 3.2 Per-portal credential preservation
- `db.project_managers.password_hash` — no row modified (verified by `find` showing identical timestamps).
- `db.field_leadership_users.password_hash` — no row modified.
- All other portal collections — no row modified (mirror only ever writes to `db.user_directory`).

### 3.3 Mirrored-row safety
All 29 new mirror rows have `password_hash` = `_random_unguessable_hash()` — bcrypt of a `secrets.token_urlsafe(48)` token. They **cannot** be logged into via multi-login. The legacy portal credentials remain the sole working credentials for these identities.

---

## 4. Acceptance criteria
| Criterion | Status |
|---|:-:|
| PM users appear in Unified Directory | 🟢 (6 visible) |
| Field Leadership users appear in Unified Directory | 🟢 (25 visible) |
| Existing users preserved | 🟢 |
| Existing passwords preserved | 🟢 |
| Existing logins preserved | 🟢 |
| No schema changes | 🟢 |
| No migrations | 🟢 |
| No duplicate identities | 🟢 (mirror is email-keyed unique) |

---

🟢 **Phase A · PASS**
