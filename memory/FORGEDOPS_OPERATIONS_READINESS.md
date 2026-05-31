# ForgedOps Operations Readiness · Forensic Phase 7

**Batch:** OMEGA Forensic Platform Certification · Phase 7
**Date:** 2026-05-31
**Scope:** Identify everything the platform requires to support a ForgedOps multi-customer operations surface: Support Portal · Support Tickets · Multi-customer management · Release management · Customer configuration · Branding · Platform health · Tenant management · Customer onboarding.

> Companion to `WHITE_LABEL_BLOCKERS.md`. White-label = "can it look like Customer #2?" ForgedOps readiness = "can ForgedOps **operate** Customer #1 + Customer #2 + ... from a single platform-ops surface?"

---

## 1 · Readiness summary

| Area | Status | Gap |
|---|---|---|
| Support Portal (ForgedOps-facing UI for incidents/tickets) | 🔴 NOT BUILT | No surface exists |
| Support Tickets (customer-raised issues) | 🔴 NOT BUILT | No collection · no route · no UI |
| Multi-customer management | 🔴 NOT POSSIBLE | Single-tenant DB · no tenant_id column |
| Release management | 🟡 MANUAL | Operator clicks Emergent Deploy button per redeploy |
| Customer configuration management | 🟡 PARTIAL | `command_center_thresholds` and `command_center_calendar` are operator-tunable but per-deployment |
| Branding management | 🔴 NOT BUILT | Brand chrome hardcoded (see `WHITE_LABEL_BLOCKERS.md`) |
| Platform health monitoring | 🟢 PARTIAL READY | `/api/admin/recovery/snapshot` · `/api/admin/backups-scheduler-state` exist · single-tenant |
| Tenant management | 🔴 NOT BUILT | No tenant collection · no provisioning flow |
| Customer onboarding | 🔴 NOT BUILT | No onboarding wizard · no seed scripts per-tenant |

🔴 **NOT READY.** ForgedOps would require a substantial dedicated build effort.

---

## 2 · What exists today that ForgedOps can use

### 2.1 · Health & monitoring

| Surface | Purpose | ForgedOps reuse |
|---|---|---|
| `/api/health` | Basic up/down | 🟢 reusable per-tenant URL |
| `/api/version` | Build identity (`source_hash` · `started_at` · `app_env` · `db_name`) | 🟢 reusable per-tenant URL |
| `/api/admin/backups-scheduler-state` | Scheduler liveness | 🟢 reusable; admin token required |
| `/api/admin/recovery/snapshot` | RPO/RTO + backup health | 🟢 reusable |
| `/api/admin/command-center/snapshot` | Operational RAG | 🟢 reusable |
| `/api/admin/accountability/snapshot` (Pillar 1) | Aged-item view | 🟢 reusable |
| `audit_events` collection | Per-tenant audit | 🟡 needs tenant_id |
| `usage_events` collection | Per-tenant usage | 🟡 needs tenant_id |
| `system_health_events` collection | Platform events | 🟡 needs tenant_id |
| `admin_audit` collection | Admin action audit | 🟡 needs tenant_id |

### 2.2 · Configuration

| Surface | Purpose |
|---|---|
| `command_center_thresholds` | Operator-tunable rule thresholds (15 rules) |
| `command_center_calendar` | Working calendar (timezone · hours) |
| `digest_settings` | Operator digest config |
| `integration_settings` | Per-provider integration config (`motive` · `maintainx`) |
| `email_routing_config` | Email routing (currently empty) |
| `role_templates` | Permission templates (31 across 7 portals) |

🟡 These are all single-tenant configs. To support multi-tenant, each would need a `tenant_id` field and the read paths would need to scope queries by tenant.

### 2.3 · Audit & observability

| Collection | Rows (prod) | Per-tenant scope? |
|---|---|---|
| `audit_events` | 10,155 | 🔴 no |
| `admin_audit` | 1,899 | 🔴 no |
| `admin_audit_log` | 142 | 🔴 no |
| `events` | 0 | n/a |
| `operations_events` | 0 | n/a |
| `system_health_events` | (count varies) | 🔴 no |
| `mfa_audit_events` | (count varies) | 🔴 no |
| `login_attempts` | (count varies) | 🔴 no |
| `brute_force_blocks` | (count varies) | 🔴 no |

🔴 Every audit row would need a `tenant_id` to support ForgedOps multi-customer reporting.

---

## 3 · What must be built (gap inventory)

### 3.1 · Tenant management

| Item | Effort estimate |
|---|---|
| `tenants` collection (id · slug · brand · domain · timezone · contact) | 1 d |
| Tenant provisioning API (`POST /api/forgedops/tenants`) | 2 d |
| Per-tenant DB-or-collection-prefix doctrine | 3 d (decision-dependent) |
| `tenant_id` propagation through every collection write path | 5-10 d |
| Tenant-scoped index strategy | 2 d |
| Per-tenant secret/key vault (Stripe · ElevenLabs · etc) | 3 d |

### 3.2 · Support Portal

| Item | Effort estimate |
|---|---|
| `support_tickets` collection | <1 d |
| Ticket CRUD API (admin + customer-portal) | 3 d |
| ForgedOps Support Portal UI (admin-side) | 5-8 d |
| Customer-side "Submit Ticket" surface | 2 d |
| Ticket fanout (email · in-app notification · ForgedOps Slack/Teams hook) | 3 d |
| Ticket SLA / escalation rules | 3-5 d |

### 3.3 · Release management

| Item | Effort estimate |
|---|---|
| Per-tenant release pinning (currently every customer redeploys together) | 3 d |
| Release notes generation tied to `source_hash` | 1 d |
| Per-tenant deploy gates (e.g. "Customer A is paused on iter441; deploy iter456 only to Customer B") | 5 d |
| Canary deploy support | 5 d |

### 3.4 · Customer configuration management

| Item | Effort estimate |
|---|---|
| Per-tenant `command_center_thresholds` UI (currently default-only) | 2 d |
| Per-tenant `command_center_calendar` UI | 1 d |
| Per-tenant integration_settings UI | 2 d |
| Per-tenant role_templates UI | 2 d |
| Per-tenant email_routing_config UI | 1 d |

### 3.5 · Branding management

| Item | Effort estimate |
|---|---|
| `tenant_brand` config (logo · colors · domain · favicons · email-sender) | 2 d |
| Frontend brand-aware chrome (current `<MasciLogo />` → `<TenantLogo brand={...} />`) | 5 d |
| Per-tenant T&C / Privacy copy storage | 2 d |
| Per-tenant PDF chrome (training certs · daily reports · payroll variance) | 3 d |

### 3.6 · Platform health monitoring (multi-tenant)

| Item | Effort estimate |
|---|---|
| Aggregate health dashboard (all tenants) | 3 d |
| Per-tenant RPO/RTO surface | 1 d (extend existing recovery dashboard) |
| Tenant-scoped audit timeline | 3 d |
| ForgedOps "tenant outage" alerting | 3 d |

### 3.7 · Customer onboarding

| Item | Effort estimate |
|---|---|
| Onboarding wizard (admin-side) | 5-8 d |
| Per-tenant seed scripts (equipment_master · role_templates · default thresholds) | 3 d |
| Tenant deactivation + data-export flow | 3 d |
| Per-tenant trial / billing gate | 5 d |

---

## 4 · Total ForgedOps build estimate

| Category | Days |
|---|---|
| Tenant management | 16-23 |
| Support portal | 16-22 |
| Release management | 14 |
| Customer configuration | 8 |
| Branding | 12 |
| Health monitoring | 10 |
| Customer onboarding | 16-19 |
| **Total** | **~92-108 dev-days** |

🔴 **Roughly 4-5 calendar months** of full-time work for ForgedOps multi-customer operations to be live.

---

## 5 · Closeout

🔴 **NOT READY for ForgedOps multi-customer operations.** The platform is single-tenant by design. A ~92-108 dev-day build is required across 7 capability areas. **No remediation in this batch.**

🛑 STOP.
