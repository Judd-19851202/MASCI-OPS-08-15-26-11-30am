# FORGEDOPS · ATLAS USER INVENTORY (P1A · P1B · P1C combined)

**Date:** 2026-02-10 · **Status:** 🟡 **PRE-EXECUTION · OPERATOR ACTION REQUIRED · NOT VERIFIED**

> Inventory evidence gathered from inside the **preview pod** runtime using its current Mongo credential. Atlas Admin-level introspection (user list, role grants) is operator-only and is NOT in this document.

---

## 1A · Credential inventory (preview pod runtime)

| Field | Value | Source |
|---|---|---|
| Currently authenticated as | `admin_db_user` @ `admin` | `connectionStatus` runtime probe |
| Roles attached (visible from preview side) | `readWriteAnyDatabase`, `dbAdminAnyDatabase` (inferred from successful capability tests) | inferred — direct grant readout requires Atlas Admin API |
| `usersInfo` command | **Denied** (`not authorized on admin to execute usersInfo`) | tested |
| `masci_preview_user` exists? | **UNKNOWN** — cannot enumerate (Atlas Admin required) | n/a |
| `masci_prod_user` exists? | **UNKNOWN** — cannot enumerate | n/a |
| `admin_db_user` exists & active? | ✅ YES (we authenticate with it) | runtime |

## 1B · Environment inventory (preview pod)

| Field | Value | Source |
|---|---|---|
| `APP_ENV` | `preview` | `/app/backend/.env` |
| `DB_NAME` | `masci_safety_preview` | `/app/backend/.env` |
| `MONGO_URL` host | `masci-prod.1nduwmg.mongodb.net` (Atlas SRV) | masked from `/app/backend/.env` |
| `appName` query param | `MASCI-prod` | masked |
| `ENFORCE_DB_ISOLATION` | not set (failsafe in bridge mode) | `/app/backend/.env` |
| `SCHEDULER_ENABLED` | `false` | `/app/backend/.env` |
| `MAINTAINX_SYNC_ENABLED` | `false` | `/app/backend/.env` |
| `MAINTAINX_WRITE_ENABLED` | `false` | `/app/backend/.env` |

## 1C · Namespace inventory (visible to preview credential)

Result of `client.list_database_names()` from preview pod runtime (2026-02-10):

| DB namespace | Purpose | Should preview see it? |
|---|---|---|
| `masci_safety_preview` | Preview operational DB (intended target) | ✅ YES |
| `masci_safety` | **Production** operational DB | ❌ NO — VIOLATION |
| `masci_restore_drill_2026_05_30` | restore-drill scratch | 🟡 acceptable (preview-only) |
| `masci_restore_drill_auto_20260601_015003` | restore-drill scratch | 🟡 acceptable |
| 26 × `masci_test_autoresolve_*` / `masci_test_webhook_harden_*` | preview test fixtures | 🟡 acceptable |
| `sample_mflix` | Atlas example DB | ⚪ irrelevant |
| `admin` · `config` · `local` | Mongo internal | ⚪ expected |

Production read probe (control · 2026-02-10):
- `client["masci_safety"].equipment_master.count_documents({})` → **596** ⚠️ READ SUCCEEDED.
- `client["masci_safety"].list_collection_names()` → **159 collections** ⚠️ LIST SUCCEEDED.

## Deliverable
- This inventory · operator-runbook downstream consumes it.
- Raw runtime JSON: `/app/memory/p0_audit_atlas_users.json`.
