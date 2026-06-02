# CUSTOMER #2 TABLETOP RISK REGISTER
## OCEP Operational Completion Sprint · Phase 5 (companion to EXECUTION GUIDE)

**Date**: 2026-06-02
**Authority**: OMEGA · OPERATIONAL COMPLETION SPRINT
**Mode**: READ-ONLY · risk register · AI-seeded CANDIDATEs awaiting tabletop confirmation
**Companion**: `CUSTOMER2_TABLETOP_EXECUTION_GUIDE.md`

---

## 0 · How this register is filled

Two types of rows live here:

1. **AI-seeded CANDIDATEs** (§3) — drawn from source-direct read of the current platform. These are risks the AI agent can identify without running a tabletop, because they're observable in source. Each row is marked CANDIDATE until the tabletop confirms or refutes.
2. **Tabletop-derived CONFIRMED rows** (§4) — added by the recorder during/after a real tabletop session. Each row references the tabletop file and step.

The AI agent CANNOT promote a CANDIDATE to CONFIRMED. Only the operator (post-tabletop).

---

## 1 · Risk taxonomy

| Field | Definition |
|---|---|
| **ID** | `C2-NNNN` |
| **Category** | JAYMN_KNOWLEDGE · EMERGENT_KNOWLEDGE · DEVELOPER_KNOWLEDGE · HIDDEN_CONFIG · MISSING_DOCUMENTATION · OPERATIONAL_RISK |
| **Severity** | BLOCKER · CRITICAL · HIGH · MEDIUM · LOW |
| **Affected step** | 1-12 from EXECUTION GUIDE · or `cross` |
| **Evidence** | Source file + line OR tabletop file + step |
| **Status** | CANDIDATE · CONFIRMED · REFUTED · CLOSED |
| **Recommended action** | TRAIN · DOCUMENT · COACH · LABEL · NOOP-WITH-REASON · BUILD-CANDIDATE (FOCP-gated) |

---

## 2 · Severity rubric

| Severity | Customer #2 onboarding cost |
|---|---|
| **BLOCKER** | Acme cannot proceed; Jaymn/Emergent/dev intervention required to unblock |
| **CRITICAL** | Acme proceeds but will call Jaymn within 7 days |
| **HIGH** | Significant tribal knowledge transfer required (≥ 2h onboarding) |
| **MEDIUM** | Empty-state UX unclear (≤ 1h onboarding) |
| **LOW** | Friction only · no real blocker |

---

## 3 · AI-seeded CANDIDATEs (source-direct · 32 rows)

All status = CANDIDATE until tabletop confirms.

### 3.1 · Multi-tenancy / brand (Steps 1-2)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0001 | Platform is **single-tenant** — no Acme/MASCI segregation in any collection | DEVELOPER_KNOWLEDGE | **BLOCKER** | No `tenant_id` field exists in any collection (verified by grep across `/app/backend/`) | 1 |
| C2-0002 | "MASCI" appears hardcoded in multiple frontend surfaces (logo, headers, e-mail templates, JHP poster QR) | DEVELOPER_KNOWLEDGE | **BLOCKER** | `MasciLogo.jsx` · `pdf_branding.py` · email subjects with "MASCI" literal | 2 |
| C2-0003 | No brand config surface exists | HIDDEN_CONFIG | **CRITICAL** | No `/admin/branding` route; no brand env vars | 2 |
| C2-0004 | Domain restriction not configurable per tenant (email domain assumptions in employee resolver) | HIDDEN_CONFIG | **HIGH** | `routes/jha_acknowledgements.py` matches email case-insensitively against `db.employees` · global pool | 4 |

### 3.2 · Tenant / account creation (Step 1)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0005 | First-admin provisioning is not self-serve · `ADMIN_PASSWORD` is a backend `.env` variable | HIDDEN_CONFIG | **BLOCKER** | `server.py:225` `_is_valid_admin_token` derives from `ADMIN_PASSWORD` env | 1 |
| C2-0006 | PM-token password (`PM_PASSWORD`) is a single shared secret across all PMs · not per-PM | DEVELOPER_KNOWLEDGE | **CRITICAL** | `server.py` PM auth uses single env-derived token | 1 |
| C2-0007 | No tenant-bootstrap workflow — Acme cannot create their universe through any UI surface | DEVELOPER_KNOWLEDGE | **BLOCKER** | No `/admin/tenant-setup` or equivalent | 1, 3 |

### 3.3 · Empty-state onboarding (Step 3)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0008 | AdminHub / PmHub / HrHub default to empty grids with no "start here" coaching | MISSING_DOCUMENTATION | **HIGH** | Hub source files; no empty-state coaching component embedded | 3 |
| C2-0009 | No onboarding checklist (per-role) anywhere on the platform | MISSING_DOCUMENTATION | **HIGH** | grep returns 0 for "onboarding checklist" | 3 |
| C2-0010 | First-login experience for admin is identical to a returning admin | OPERATIONAL_RISK | **MEDIUM** | No first-login flag on admin token | 3 |

### 3.4 · HR seeding (Step 4)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0011 | Employee CSV import format is not documented in-app | MISSING_DOCUMENTATION | **HIGH** | `routes/hr_*.py` accept CSV but format lives only in tribal knowledge / sample files | 4 |
| C2-0012 | `lifecycle_status` seeding for imported employees is non-obvious | DEVELOPER_KNOWLEDGE | **MEDIUM** | Phase Alpha doctrine sets defaults but UX doesn't surface this | 4 |
| C2-0013 | Role assignment (foreman / super / PM) requires understanding of `roles` field that has no in-app explanation | MISSING_DOCUMENTATION | **HIGH** | `db.employees.roles` array · no doctrine doc accessible from admin chrome | 4 |
| C2-0014 | Employees without email cannot acknowledge JHPs post-FOCP R2 (email is the identity key) | OPERATIONAL_RISK | **HIGH** | `routes/jha_acknowledgements.py:_resolve_employee` requires email or id; Spanish-only crews often lack work email | 4, 11 |

### 3.5 · Projects / jobs seeding (Step 5)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0015 | `project_number` is a free-form string; no constraint or master list | MISSING_DOCUMENTATION | **MEDIUM** | Many collections key by `project_number` string; no canonical projects collection | 5 |
| C2-0016 | Sub-vendor / supplier relationships are not self-onboarding (TR-0003 active) | DEVELOPER_KNOWLEDGE | **HIGH** | Truth Register TR-0003 ACTIVE · no archive workflow for subs | 5 |
| C2-0017 | Job mobilization checklist not present | MISSING_DOCUMENTATION | **MEDIUM** | No `/jobs/{n}/mobilize` workflow surface | 5 |

### 3.6 · Equipment / fleet seeding (Step 6)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0018 | Fleet import requires understanding of severity-tier model not surfaced anywhere | MISSING_DOCUMENTATION | **HIGH** | iter251 doctrine + `fleet.repair` form_keys but no admin-side intro | 6 |
| C2-0019 | Equipment categories (truck / yellow iron / small tool) are not standardized as enum | DEVELOPER_KNOWLEDGE | **MEDIUM** | `db.equipment.type` is free-form | 6 |

### 3.7 · JHP library (Step 7)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0020 | JHP upload is one-at-a-time · no bulk upload | OPERATIONAL_RISK | **MEDIUM** | `routes/job_hazard_files.py` POST per-file | 7 |
| C2-0021 | Acknowledgement ledger (FOCP R2) is brand-new; no in-app primer for admin | MISSING_DOCUMENTATION | **HIGH** | Post-2026-06-02 release; `/admin/jha-acknowledgements` not yet linked from AdminHub | 7 |

### 3.8 · Safety / training records (Step 8)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0022 | Driver Qualification records are HR-side; Training records are HR-side; ownership boundary with Safety is convention only | DEVELOPER_KNOWLEDGE | **MEDIUM** | iter288 + iter312 doctrine; no admin-side rules surface | 8 |
| C2-0023 | Expiration cron / digest schedule is not user-configurable | HIDDEN_CONFIG | **LOW** | `operator_digest` cron lives in `cron.py` with hardcoded schedule | 8 |

### 3.9 · Dispatch ramp (Step 9)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0024 | Dispatch board first-build UX is empty-state with no entry-point coaching | MISSING_DOCUMENTATION | **HIGH** | Tips registry has no `dispatch` parent (Phase 2 finding) | 9 |
| C2-0025 | Driver qualification thresholds (e.g., 30-day warning) are constants in code · not configurable | HIDDEN_CONFIG | **MEDIUM** | iter288 constants; no per-tenant override | 9 |

### 3.10 · Daily Report (Step 10)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0026 | DR routing assumes Office reviews → Admin closes; no per-tenant configurable routing | DEVELOPER_KNOWLEDGE | **MEDIUM** | `workflow_state_machine.py:230` `_DR_ROLES` hardcoded admin-only on review states | 10 |
| C2-0027 | "Pending Office Review" verbiage assumes MASCI's office structure exists at Acme | OPERATIONAL_RISK | **MEDIUM** | Status labels in `statusBadges.js` post-FOCP R1 use "Office" terminology | 10 |

### 3.11 · Incident (Step 11)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0028 | OSHA-recordable attestation requires understanding of OSHA 300/301 forms · no in-app primer | MISSING_DOCUMENTATION | **HIGH** | iter451 closure contract enforces attestation flags but doesn't teach OSHA forms | 11 |
| C2-0029 | Incident classification (severity) has no in-app definitions | MISSING_DOCUMENTATION | **HIGH** | `incident.severity` tip set partial; classification rules not in tips | 11 |

### 3.12 · Payroll Variance (Step 12)

| ID | Risk | Category | Severity | Evidence | Affected step |
|---|---|---|---|---|---|
| C2-0030 | Variance finalization requires admin authority · Acme's HR cannot self-finalize | DEVELOPER_KNOWLEDGE | **CRITICAL** | iter452 doctrine + `_PV_ROLES` FINALIZE = admin/super_admin only | 12 |
| C2-0031 | Variance scheduling assumes Friday weekly run · not per-tenant configurable | HIDDEN_CONFIG | **LOW** | Cron pattern in code | 12 |
| C2-0032 | Universal Undo authority (FOCP R2) is admin-only — Acme HR can't undo even their own variance finalization | DEVELOPER_KNOWLEDGE | **HIGH** | `routes/workflow_undo.py` `require_admin_dep=require_admin` · FOCP R2 doctrine | 12, cross |

---

## 4 · Tabletop-derived CONFIRMED rows (operator fills after each tabletop)

| ID | Risk | Category | Severity | Step | Tabletop file | Status |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Append rows as tabletop sessions complete. Each row must reference the tabletop file in `/app/memory/customer_2_tabletop_*.md` and the step number where the finding emerged.

---

## 5 · Aggregate counts (operator updates after tabletop)

| Category | CANDIDATE | CONFIRMED | OPEN | CLOSED |
|---|---:|---:|---:|---:|
| JAYMN_KNOWLEDGE | 0 |  |  |  |
| EMERGENT_KNOWLEDGE | 0 |  |  |  |
| DEVELOPER_KNOWLEDGE | 11 |  |  |  |
| HIDDEN_CONFIG | 6 |  |  |  |
| MISSING_DOCUMENTATION | 9 |  |  |  |
| OPERATIONAL_RISK | 6 |  |  |  |
| **Total** | **32** |  |  |  |

| Severity | CANDIDATE | CONFIRMED | OPEN | CLOSED |
|---|---:|---:|---:|---:|
| BLOCKER | 4 |  |  |  |
| CRITICAL | 4 |  |  |  |
| HIGH | 11 |  |  |  |
| MEDIUM | 10 |  |  |  |
| LOW | 3 |  |  |  |
| **Total** | **32** |  |  |  |

---

## 6 · Customer #2 Readiness Score formula

```
Score = 100
      - 25 × BLOCKER_open
      -  8 × CRITICAL_open
      -  3 × HIGH_open
      -  1 × MEDIUM_open
      -  0.25 × LOW_open
```

Floor at 0.

Threshold for Phase 6 PASS: **≥ 70 AND BLOCKER_open == 0 AND CRITICAL_open ≤ 2**.

### 6.1 · As of 2026-06-02 (CANDIDATE-only baseline)
- Assuming every CANDIDATE were CONFIRMED unchanged: `100 - 25×4 - 8×4 - 3×11 - 1×10 - 0.25×3 = 100 - 100 - 32 - 33 - 10 - 0.75 = -75.75` → floor 0
- **Customer #2 Readiness Score (pre-tabletop confirmation upper bound)**: **0 / 100**

This is the worst-case ceiling. The tabletop's job is to refute false-positives and produce the real number. If the operator's tabletop confirms the 4 BLOCKER candidates, **Customer #2 cannot onboard without engineering work** — which is OUT OF SCOPE under the FOCP Final Directive without separate 7-test + 4-proof clearance per BLOCKER.

---

## 7 · Truth Register classification of candidates

Per the OMEGA TRUTH REGISTER RULE:

| Candidate cluster | Classification | Reason |
|---|---|---|
| C2-0001, C2-0002, C2-0005, C2-0007 (single-tenancy / hardcoded brand / hidden admin password / no tenant bootstrap) | **ACTIVE** (multi-tenancy is a White-Label work surface, currently FROZEN by FOCP Final Directive) | Engineering surface required for Customer #2; not approved |
| C2-0011, C2-0013, C2-0017, C2-0024, C2-0028, C2-0029 (missing documentation) | **DEFERRED** (operator-owned content; doctrine task) | Documentation, not engineering |
| C2-0006, C2-0010, C2-0019, C2-0022, C2-0026, C2-0032 (developer-knowledge / labels) | **DEFERRED** (operator decision required on whether label/coaching is sufficient) | Eligible for coaching-class build IF operator authorizes via 7-test + 4-proof |
| C2-0003, C2-0004, C2-0023, C2-0025, C2-0031 (hidden config) | **DEFERRED** (config surfaces are White-Label work) | Out of scope under FOCP Final Directive |
| C2-0014 (employees without email cannot ack JHP) | **ACTIVE** if confirmed by Phase 1 Spanish-only crew interviews | Operator validation needed |
| C2-0021 (FOCP R2 surface not linked from AdminHub) | **DEFERRED** (label / link addition is a build, not a defect) | Operator decision |
| C2-0030 (Acme HR can't finalize variance) | **DOCTRINE EXEMPT** | Variance finalization being admin-only is the iter452 doctrine ("NO AUTO FINALIZE" carries to "no PM/HR finalize either") |

No candidate moves to ACTIVE engineering work without operator authorization through the FOCP gate.

---

## 8 · Refusal conditions

The AI agent MUST refuse to:
- Promote any CANDIDATE to CONFIRMED without a tabletop file
- Recommend a build action without 7-test + 4-proof clearance per item
- Compute a Customer #2 Readiness Score from CANDIDATEs alone and present it as final
- Add new candidates outside source-direct evidence (AI inference is not evidence)

---

**End of CUSTOMER #2 TABLETOP RISK REGISTER · OCEP Phase 5**
