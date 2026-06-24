# TRACK 15.75 · Phase 2 — Responsible-Party Matrix

Evidence: `pm_routing.recipients_for_record_async` traces, `email_routes` DB rows.

Legend: ✅ required & wired · ➕ CC/visibility · 📋 dashboard surface · 🟡 visibility-only (no notify) · ❌ excluded by design

| Workflow | PM (To) | Co-PM (CC) | Safety | HR | Shop | Admin | Submitter | Field Lead | Dashboard | Dead-letter Fallback |
|---|---|---|---|---|---|---|---|---|---|---|
| **Daily Report** | ✅ primary | ➕ CC if assigned | 📋 dashboard | 📋 labor/time view | ❌ | ➕ dead-letter only when PM missing | ➕ `field_submitter_bindings` | 📋 | PM portal + admin DR list + `/admin/pm-email-coverage` | ✅ `ADMIN_DEAD_LETTER_TO` (`safety@mascigc.com`) |
| **Safety Meeting** | ✅ if job-linked | ➕ if job-linked | ✅ `COMPLIANCE_ALWAYS_CC` (`safety@`+jaymn) | 📋 attendance dashboard | ❌ | ➕ CC | ➕ bind | 📋 | Safety admin + meeting list | ✅ same path |
| **Equipment Pre-Op** | ✅ if project-linked (operational, no office CC) | ➕ CC if assigned | 📋 if safety-critical defect | ❌ | ✅ `PRE_OP_FAIL_FALLBACK` (`shopmanager@`) on fail | ➕ exception view | ➕ | 📋 | Equipment dashboard + Shop portal | ✅ same path |
| **Incident** | ✅ if job-linked | ➕ if job-linked | ✅ ALWAYS_CC | 🟡 readable from HR portal | ❌ | ✅ ALWAYS_CC (jaymn) | ➕ bind | 📋 | Safety admin + incident list | ✅ same path |
| **QA/QC** | ✅ if job-linked | ➕ | ✅ ALWAYS_CC | ❌ | ❌ | ➕ ALWAYS_CC | ➕ | 📋 | QA/QC list | ✅ same path |
| **Inspection** | ✅ | ➕ | ✅ ALWAYS_CC | ❌ | ➕ if equip-related | ➕ | ➕ | 📋 | Inspection list | ✅ same path |
| **JHA / JHP** | ✅ | ➕ | ✅ ALWAYS_CC | ❌ | ❌ | ➕ ALWAYS_CC | ➕ | 📋 | Safety admin → JHP | ✅ same path |
| **Time Off / HR Request** | ❌ | ❌ | ❌ | ✅ HR portal queue | ❌ | ➕ readable | ➕ requester | ❌ | HR portal | n/a |
| **Dispatch Assignment** | 📋 if PM-job-linked | 📋 | ❌ | 📋 if HR labor view | ❌ | ✅ `DISPATCH_ROLE_TO` (jaymn) | ➕ dispatcher | ❌ | Dispatch portal | n/a (in-app) |
| **Equipment Maintenance / Shop Request** | 📋 if project-linked | ❌ | 📋 if safety-critical | ❌ | ✅ Shop portal | ➕ | ➕ | ❌ | Shop portal | n/a (in-app) |
| **Trench Safety Inspection** | ✅ if job-linked | ➕ | ✅ `TRENCH_SAFETY_PULSE_SAFETY` | ❌ | ✅ `TRENCH_SAFETY_PULSE_SHOP` | ➕ digest | ➕ | 📋 | Trench portal + leadership digest | digest fallback |
| **Active Job / Employee / Equipment Update** | n/a | n/a | n/a | 📋 employee | 📋 equipment | ✅ admin only | n/a | n/a | admin panel | n/a |
| **Health Alert** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ `HEALTH_ALERTS` (jaymn) | ❌ | ❌ | System health dashboard | env fallback |
| **Backup Alert** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ `BACKUP_ALERTS` (jaymn) | ❌ | ❌ | Admin backup card (R2-aware) | env fallback |
| **Outage Alert** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ `OUTAGE_ALERTS` (jaymn) | ❌ | ❌ | System health dashboard | env fallback |

### Routing rules confirmed (`pm_routing.py`):
* `PM_ONLY_KINDS = {"daily-report", "equipment-inspection"}` → primary in To, co-PMs in CC, **no office CC**.
* All other compliance kinds → primary in To, co-PMs + `COMPLIANCE_ALWAYS_CC` in CC.
* Unresolved PM → `ADMIN_DEAD_LETTER_TO`; co-PMs remain in CC where applicable.
* Co-PM-only path: confirmed for `20-07` (53 DRs, co-PM `pm.demo@mascigc.com` visible in CC even when To = dead-letter).
