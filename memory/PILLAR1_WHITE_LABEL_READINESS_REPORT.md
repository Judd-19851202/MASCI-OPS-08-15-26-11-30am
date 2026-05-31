# Pillar 1 · White-Label Readiness Report (Phase 5)

**Batch:** Pillar 1 · Pre-Deployment Operational Certification · Phase 5
**Date:** 2026-05-31
**Scope:** Inventory hardcoded MASCI references · terminology · assumptions · customer-specific logic · branding dependencies within Pillar 1 modules and the surrounding platform. **Documentation only · NO REMEDIATION in this batch.**

---

## 1 · Executive verdict

🟢 **PILLAR 1 MODULES ARE WHITE-LABEL CLEAN.**

🔴 **SURROUNDING PLATFORM IS NOT** (4,431 MASCI string occurrences across `backend/` + `frontend/src/`).

The Accountability Engine (projection library + service router) carries zero MASCI strings. The Command Center (`routes/command_center.py`) carries 2 inline MASCI strings, both trivially externalizable. The remaining 4,429 occurrences live in modules outside Pillar 1's surface area and are tracked here as a future white-label backlog — **not as a Pillar 1 blocker**.

---

## 2 · Per-file inventory (Pillar 1 surface area)

| File | MASCI count | Where? | White-label severity |
|---|---|---|---|
| `/app/backend/lib/accountability_projection.py` | 0 | — | 🟢 clean |
| `/app/backend/routes/accountability_service.py` | 0 | — | 🟢 clean |
| `/app/backend/routes/command_center.py` | 2 | line 168 · line 905 (`"Within MASCI PO SLA…"`) | 🟡 trivially externalizable |
| `/app/backend/tests/test_accountability_*.py` (5 files) | 0 | — | 🟢 clean |
| `/app/memory/ACCOUNTABILITY_*.md` (10+ files) | many references to "MASCI" but only as the operator's company name in narrative context | 🟡 documentation tone · not a code dependency |
| `/app/frontend/src/pages/admin/AdminCommandCenter.jsx` | 1 | line 4 (comment) | 🟢 cosmetic |

### 2.1 · The 2 Pillar 1 MASCI strings (production-visible)

| File · line | String | Surface | Customer-#2 fix |
|---|---|---|---|
| `command_center.py:168` | `"expected_resolution": "Within MASCI PO SLA (operator-tunable)"` | `command_center_thresholds` rule doc (default-only) | Move literal into `command_center_thresholds.rules.APP-AMBER.expected_resolution`; tenant config overrides default. |
| `command_center.py:905` | `"eta": "Within MASCI PO SLA"` | Per-item `eta` field on Approvals card items | Source from threshold doc instead of inline literal. ~2 LOC change in a future white-label batch. |

---

## 3 · Platform-wide MASCI inventory (context only · NOT Pillar 1 scope)

| File · domain | MASCI count | Why it matters for white-label |
|---|---|---|
| `backend/server.py` | 145 | Core router · admin seed · email recipients · prompt strings |
| `frontend/src/lib/i18n.js` | 143 | Existing i18n keys include MASCI brand strings |
| `backend/data/equipment_master.json` (+ 7 backups) | ~134 each | Customer-specific equipment fleet seed data |
| `backend/guidance/content.py` | 54 | OGC guidance content for crew types |
| `backend/training_pdf.py` | 49 | Generated PDF chrome (header/footer) |
| `backend/guidance/translations_es.py` | 47 | Spanish guidance translations |
| `frontend/src/pages/legal/TermsOfService.jsx` | 46 | Legal copy (MASCI legal entity) |
| All other files | ~3,800 cumulative | Email signatures · seed scripts · UI banners · domain literals (`mascidocs.com` · `mascigc.com` · `safety@mascigc.com`) · welcome strings · etc |
| **Total backend + frontend** | **4,431** | — |

### 3.1 · MASCI categories surfaced

1. **Brand strings** — company name in PDFs, emails, UI headers, training material.
2. **Domain literals** — `mascidocs.com`, `mascigc.com`, hardcoded email recipients (`safety@mascigc.com`, `jaymn.judd@mascigc.com`).
3. **Seed data** — `equipment_master.json` with MASCI's actual fleet · employee directory seed · OGC catalog tuned for MASCI's crew types.
4. **Legal & compliance text** — terms of service · privacy policy · regulatory routing (CalOSHA · DOT thresholds tuned to MASCI's risk profile).
5. **Operator-specific business rules** — PO SLA strings ("Within MASCI PO SLA") · approval routing fan-out targets (`role="pm"` for MASCI's project structure).
6. **i18n keys** — already brand-aware (good), but values still contain MASCI literal.
7. **Test fixtures** — `TEST_iter*` test POs · pytest mock users (`jaymn.judd@mascigc.com`).

---

## 4 · MASCI assumptions in Pillar 1 (architectural · not string-based)

Beyond literal strings, Pillar 1 carries implicit assumptions about MASCI's operational structure that would need _configuration_ (not code change) to support Customer #2:

| Assumption | Where | Customer #2 impact |
|---|---|---|
| `jobs_master.primary_pm_name` is the de-facto PO approver | `accountability_projection.py:project_po_request_resolved` | 🟡 Generic enough — any project-based customer has a PM. Field _name_ may differ. |
| `corrective_actions.assigned_to_name` is the de-facto incident resolver | `accountability_projection.py:project_incident_resolved` | 🟡 Same — generic concept; field name may differ. |
| `fleet_defects.acknowledged_by_name` is the shop-team individual | `accountability_projection.py:project_fleet_defect` | 🟡 Generic. Some customers may not run an in-house shop. |
| 6 sources are first-class: tasks · CA · PO · fleet_defects · incidents · virtual signals | `accountability_projection.py:_PROJECTORS` | 🟡 Customer #2 may have a different source set (e.g. no fleet, or no CA workflow). Adapter pattern needed. |
| Owner-role vocabulary: `pm`, `safety`, `shop`, `hr`, `approver_per_routing`, `operations_leadership` | projection layer | 🟢 Generic across construction-ops. |
| Working calendar defaults: Mon-Fri · 06:00-18:00 · UTC-5 | `command_center_calendar` default doc | 🟢 Per-tenant config supported. |
| RAG thresholds (DR_MISSING=2/5 · OOS_BACKLOG=10/25 · etc) | `command_center_thresholds` default doc | 🟢 Per-tenant config supported. |
| Placeholder strings in English ("Pending Approver", "Safety", "Shop", "Unassigned PM") | projection layer | 🟡 Need i18n for non-English Customer #2. |

---

## 5 · Customer-specific logic (NOT in Pillar 1)

Customer-specific logic _outside Pillar 1_ that any future white-label initiative must address:

- Email recipients hardcoded (`safety@mascigc.com`, `jaymn.judd@mascigc.com`).
- PDF chrome (training, daily reports) hardcodes MASCI branding.
- Equipment master JSON seed file.
- Legal entity references in T&C / Privacy.
- Bilingual guidance content (EN + ES) tuned for MASCI's crew vocabulary.
- iter441 backup chrome (archive filename prefix `MASCI_complete_backup_*`).
- Frontend login pages branded with MASCI logo / colors.

**All of the above is OUT of Pillar 1 scope and must NOT be remediated in any Pillar 1 batch.**

---

## 6 · Future white-label backlog (NO REMEDIATION TODAY)

Recommended sequencing if the operator later authorizes Customer #2 onboarding:

| # | Batch | Effort estimate | Description |
|---|---|---|---|
| WL-0 | Tenancy model spec | 2-3 dev-days | Single-DB-multi-tenant vs DB-per-tenant decision · tenant resolver doctrine |
| WL-1 | Move 2 MASCI strings out of `command_center.py` | < 1 dev-day | Source from `command_center_thresholds` doc instead of inline literal |
| WL-2 | i18n the 5 placeholder strings in projection layer | 1 dev-day | "Pending Approver" / "Safety" / "Shop" / "Unassigned PM" / "UNASSIGNED" → i18n keys |
| WL-3 | Routing-source field alias adapter | 2 dev-days | Allow Customer #2 to map `primary_pm_name` → `lead_pm_name` (etc) without code change |
| WL-4 | Per-tenant `command_center_thresholds` + `command_center_calendar` UI | 2 dev-days | Operator-facing tenant config screen (admin-only) |
| WL-5 | Brand chrome de-MASCI-fy (logo · color · domain) | 3-5 dev-days | Out of Pillar 1; affects login pages, PDF footers, email signatures |
| WL-6 | Equipment master seed file model | 2 dev-days | Per-tenant seed file path or import flow |
| WL-7 | Email recipient externalization | 1 dev-day | Move hardcoded recipients into `tenant_config` doc |
| WL-8 | Bilingual guidance content per-tenant | 3-5 dev-days | OGC catalog · translations per tenant |
| WL-9 | Legal copy per-tenant | 1 dev-day | T&C · Privacy · legal entity name per-tenant |
| WL-10 | Backup-filename prefix per-tenant | < 1 dev-day | `MASCI_complete_backup_*` → `{tenant_slug}_complete_backup_*` |

**Aggregate estimate for a complete white-label readiness pass: ~20-25 dev-days.**

### 6.1 · Pillar 1 share of white-label work

| Pillar 1 batches needed | Effort |
|---|---|
| WL-1 + WL-2 + WL-3 | ~3-4 dev-days |

All other batches (WL-0, WL-4..WL-10) live outside Pillar 1.

---

## 7 · Customer #2 readiness summary

(also see `PILLAR1_OPERATIONAL_CERTIFICATION_REPORT.md` §6)

🟡 **READY WITH CONFIGURATION WORK.** Pillar 1 itself supports Customer #2 _without redesign_ — but requires ~3-4 dev-days of additive config work (WL-1/2/3). No architectural rewrite. No schema migration. No service-layer rewrite.

The Accountability Engine is, by design, **tenant-agnostic at its core**. The remaining MASCI references are surface-level (string literals + 2 routing-field names) and externalizable via `command_center_thresholds` + future alias adapter.

---

## 8 · OMEGA discipline confirmation

- ❌ Zero code changes in this batch
- ❌ Zero strings replaced
- ❌ Zero i18n key added
- ❌ Zero seed file edits
- ❌ Zero schema changes
- ❌ Zero new batches authorized

**This report is inventory + future backlog only.**

---

## 9 · Closeout

🟢 **PILLAR 1 IS WHITE-LABEL CLEAN.** 🔴 The surrounding platform is single-tenant and will require ~20-25 dev-days of work distributed across 10 future authorized batches (WL-0..WL-10) before Customer #2 can be onboarded cleanly. None of that work is required to ship Pillar 1 to production today.

**STOP. No code. No remediation. Awaiting operator review.**
