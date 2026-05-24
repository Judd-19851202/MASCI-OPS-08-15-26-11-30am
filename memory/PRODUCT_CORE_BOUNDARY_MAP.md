# Product Core Boundary Map · Phase 10 · Document 2 of 5

**Date:** 2026-05-24
**Purpose:** Identify what is **platform infrastructure** (reusable across any general contractor customer) vs. what is **MASCI layer** (per-tenant).

Use this map to answer: *if a second customer signed tomorrow, what carries over unchanged and what needs swapping?*

---

## Product Core (carries over unchanged for any general contractor)

### A. Cross-portal RBAC + auth chain
- `backend/routes/integrations/_deps.py` — `make_require_any_portal_token` (accepts all 8 portal header variants including FL per-user from Phase 5D)
- `backend/safety_users.py`, `backend/hr_users.py`, `backend/field_leadership_users.py`, etc. — per-portal user models
- `frontend/src/lib/directoryAuth.js` — multi-login token fan-out (Phase 5D closure)
- `frontend/src/components/RequireAdmin.jsx`, `RequireSafety.jsx`, `RequirePm.jsx`, `RequireHr.jsx`, `RequireDispatch.jsx`, `RequireFL.jsx` — route guards
- **Carries over:** 100% reusable. The 7-portal model + per-portal token fan-out is generic.

### B. Lifecycle infrastructure
- **Incidents** — `routes/safety.py` (POST/GET/PATCH); severity escalation safety net; idempotency-key dedup
- **CAPA pipeline** — `routes/safety_portal/corrective_actions.py`; status pipeline Open → In Progress → Pending Review → Verified → Closed; second-reviewer rule
- **Daily Reports** — `routes/daily_reports.py`; safety-escalation auto-incident proposal
- **PPE** — `routes/safety_portal/ppe.py`; roster-backed selector pattern
- **Training records** — `routes/safety_portal/training.py`; expiration cron + governance finding
- **DQ files** — `routes/hr_portal/driver_qualification.py`; FMCSA-regulated; approval lock by different reviewer
- **Toolbox talks** — `routes/safety_portal/toolbox_talks.py`
- **Pre-Op inspection** — `routes/safety_portal/pre_op.py`
- **QA/QC** — `routes/qaqc.py`
- **Shop defects** — `routes/shop_portal/defects.py`
- **Carries over:** 100%. The schemas + status pipelines are construction-industry generic, not MASCI-specific.

### C. Governance + accountability infrastructure
- `backend/routes/governance.py` — convergence score; finding pipeline
- 8 detector rules: `EMP_LINK_UNRESOLVABLE`, `CAPA_AWAITING_VERIFICATION`, `INCIDENT_NO_CAPA`, `DRIVER_QUAL_EXPIRED`, `IDENTITY_DRIFT`, `SAFETY_DR_INC_MISMATCH`, `TRAINING_OVERDUE_ASSIGNED`, convergence-score-drop
- Accountability Timeline (`/api/safety/employees/{id}/timeline`)
- **Carries over:** 100%. All 8 detector rules are generic cross-portal contradictions, not MASCI-named.

### D. Notification infrastructure
- `backend/routes/tasks_notifications.py` — unified `/api/notifications` surface
- `backend/lib/event_fanout.py` — emit pipeline with `recipient_role` filter
- `NOTIFICATION_DISCIPLINE_MATRIX.md` — 19-event matrix; 3-tier classification
- **Carries over:** 100%. Tier definitions + aggregation rules are tenant-neutral.

### E. Smart Operational Disclosure UX pattern
- `frontend/src/components/CollapseCard.jsx` — including Phase 6 `attentionOpen` prop
- Daily Report compression pattern (Phase 5C)
- Incident form compression + Tier-2 lock (Phase 5C.1 + Phase 6)
- Phase 6 operational completion banners (slate/rose/emerald)
- Phase 5D ViewIncident follow-up banner (3-state)
- **Carries over:** 100%. The disclosure logic is contractor-agnostic.

### F. Lifecycle coaching infrastructure
- `frontend/src/components/LifecycleGuide.jsx` — 8 instances across detail pages
- Operational glossary (16 entries in `AdminOperationalLanguage.jsx`)
- All glossary terms (CAPA · Verified · Accountability Timeline · Closeout · Archived · Follow-Up Required · Investigation Open · Operationally Complete · Pending Review · Roster-Linked · Roster-Backed Selector · Operational Readiness · Lifecycle Guide · Governance Score · Governance Finding · Identity Drift)
- **Carries over:** 100%. All 16 glossary terms are industry-standard, not MASCI-internal.

### G. Audit + audit trail mechanics
- `created_by_name` + `updated_by_name` + `created_at` + `updated_at` + `source_module` fields across every collection
- `status_history` arrays on lifecycle records
- Idempotency-key pattern
- Soft delete with `_archive` retention
- **Carries over:** 100%.

### H. Mobile field reliability
- `useDraftSync` autosave + draft recovery
- Photo upload state visibility + submit-disabled gate
- Payload-size warning (≥ 30 attachments)
- 390 px verified layout patterns
- **Carries over:** 100%.

### I. Bilingual coverage
- `frontend/src/lib/i18n.js` — `t()` helper with EN↔ES dictionary
- ~600 translation pairs (most of which DO NOT name MASCI; 134 do)
- ES translation cron / build-time check
- **Carries over:** Mostly. The 134 MASCI-naming translation pairs would need brand-name token substitution.

### J. Email + PDF rendering infrastructure
- `backend/pdf_render.py` — HTML→PDF helpers; letterhead layout primitives
- `backend/lib/event_fanout.py` Resend integration
- `backend/branded_portal_emails.py` — invitation + reset templates (scaffold reusable; copy needs per-tenant)
- **Carries over:** Scaffolding (100%) + copy (per-tenant override needed).

### K. Backup + restore + health monitoring
- `backend/backup_verification.py` — backup verification finding
- `backend/health_monitor.py` — health-task cron
- `backend/outage_alerts.py` — outage notification
- **Carries over:** 100%. The verification + monitor patterns are tenant-neutral; the alert recipient email is env-var-driven.

### L. Public-mode field entry
- `/incidents/submit` + `/daily/submit` public-mode forms
- Idempotency-key + rate-limit hardening
- Roster-backed employee selector (uses public `/api/employees`)
- **Carries over:** 100%.

---

## MASCI Layer (per-tenant — would need swap)

### M. Brand & identity (see `MASCI_LAYER_AUDIT.md § 1`)
- App titles, HTML title, logo SVG, brand footer text
- Per-tenant config needed: `TENANT_NAME`, `TENANT_LEGAL_NAME`, `TENANT_LOGO_URL`, `TENANT_PHONE`, `TENANT_ADDRESS`, `TENANT_WEBSITE`

### N. PDF / export filenames (see `MASCI_LAYER_AUDIT.md § 2`)
- ~15 hardcoded `MASCI_HUB_*.pdf/docx/zip/xlsx/csv` filename literals
- Per-tenant config needed: `TENANT_FILENAME_PREFIX` (default = `TENANT_NAME` with underscores)

### O. Email recipient defaults (see `MASCI_LAYER_AUDIT.md § 3`)
- 7 env vars baked with MASCI emails (`SENDER_EMAIL`, `REPLY_TO_EMAIL`, `BACKUP_EMAIL_TO`, `OUTAGE_ALERT_TO`, `SUPER_ADMIN_EMAIL`, etc.)
- `backend/email_routing.py` — hardcoded fallback recipient lists
- Per-tenant config needed: each env var sourced per-tenant `.env`

### P. Email body copy (see `MASCI_LAYER_AUDIT.md § 3`)
- ~20 email templates with MASCI brand in copy
- Per-tenant treatment: replace literal `MASCI` with `{{ TENANT_NAME }}` Jinja-style placeholder OR full per-tenant template override

### Q. Training & guidance content (see `MASCI_LAYER_AUDIT.md § 5`)
- `backend/guidance/content.py` + `tips.py` + `translations_es.py` + frontend `data/training.js`
- ~150-200 MASCI references in training/guidance copy
- Per-tenant treatment: starter content collection per tenant; OR per-tenant CMS

### R. Operational data (see `MASCI_LAYER_AUDIT.md § 6`)
- `backend/data/equipment_master.json` (128 hits) — fleet inventory
- `backend/data/jobs_master.json` — real project numbers
- Per-tenant treatment: per-tenant collections (not code)

### S. Holiday / observance banners (see `MASCI_LAYER_AUDIT.md § 9`)
- ~10 references in i18n.js + content
- Per-tenant treatment: per-tenant CMS

### T. Legal documents
- TermsOfService.jsx + PrivacyPolicy.jsx (legitimately MASCI-specific)
- Per-tenant treatment: per-tenant copy; KEEP MASCI-specific for MASCI deploys

---

## Tenant Data (already separated; just needs tenant_id filter)

### U. All Mongo collections
Every business collection: `incidents`, `corrective_actions`, `employees`, `daily_reports`, `compliance_findings`, `notifications`, `training_records`, `ppe_issuances`, `equipment`, `suppliers`, `projects`, `toolbox_talks`, `pre_op_inspections`, `qaqc_reports`, `shop_defects`, `dq_files`, etc.
- **Treatment:** Per-tenant DB (Path A) OR `tenant_id` row-level filter (Path B). Detailed in `COMMERCIALIZATION_BLOCKERS.md`.

### V. User collections
`users`, `safety_users`, `hr_users`, `field_leadership_users`, etc.
- **Treatment:** Per-tenant scoping (Path A or B above).

---

## Boundary map at a glance

```
┌───────────────────────────────────────────────────────────────────┐
│  PRODUCT CORE — carries over unchanged                            │
│  (RBAC · lifecycles · governance · notifications · UX patterns ·  │
│   audit trail · mobile · bilingual scaffold · backup · health)    │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼  swap via env vars + per-tenant content
┌───────────────────────────────────────────────────────────────────┐
│  MASCI LAYER — per-tenant                                          │
│  (brand · PDF filenames · email defaults · copy · training ·       │
│   operational seed data · holidays · legal docs)                   │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼  swap via tenant_id filter or per-tenant DB
┌───────────────────────────────────────────────────────────────────┐
│  TENANT DATA — per-tenant                                          │
│  (all Mongo collections · all users)                               │
└───────────────────────────────────────────────────────────────────┘
```

---

## Approximate boundary ratio

If we measure by LOC + asset count + collection count:
- Product Core: ~80% of codebase
- MASCI Layer: ~15% (brand + content + email copy)
- Tenant Data: ~5% (collection definitions; the DATA is per-tenant by nature)

**~80% of the engineering work is already done for any future tenant.** The remaining 20% is the productization swap.

---

## Conclusion

The product core is large, mature, and contractor-agnostic. The MASCI layer is bounded, volumetric (~890 references), and treatable via standard SaaS patterns (env vars + content collections + tenant_id filter).

The platform's true intellectual property — operational discipline, governance findings, lifecycle continuity — is in the product core. The MASCI layer is a configuration shell around that core.

This is exactly the boundary that makes future productization tractable.
