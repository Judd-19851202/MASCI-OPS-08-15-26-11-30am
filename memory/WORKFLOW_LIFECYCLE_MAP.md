# WORKFLOW LIFECYCLE MAP
**Audit date:** 2026-05-23

Maps every major operational record from its source collection to every downstream consumer. **WHERE** it originates, **HOW** it propagates, **WHO** sees it today, and **WHO SHOULD** based on operator policy.

Legend: ✅ = currently working · ⚠️ = partial / fragile · 🔴 = missing · 🆕 = added by iter350–iter353c stack

---

## 1 · Employee Master (`employees`) — Source of truth
| Stage | Owner | Collection | Status |
|---|---|---|---|
| Create | HR · Admin | `employees` (POST `/api/hr/employees`) | ✅ |
| Edit | HR · Admin | PATCH `/api/hr/employees/{id}` | ✅ |
| Soft-delete | Admin | DELETE `/api/admin/employees/{id}` (sets `deleted_at`) | ✅ |
| Lifecycle transitions | HR | `status_history[]` embedded array | ✅ |
| CDL / medical / approved-driver | HR · Admin | embedded fields on `employees` | ✅ |
| Bulk roster import (CDL) | HR · Admin | `/api/hr/driver-qualification/import/apply` 🆕 | ✅ preview · 🔴 prod |

**Downstream consumers**
| Consumer | Endpoint | Status |
|---|---|---|
| HR Employee Directory | `/api/hr/employees` | ✅ |
| HR Accountability Timeline 🆕 | `/api/hr/employees/{id}/accountability/timeline` | ✅ preview · 🔴 prod |
| HR Compliance Brief PDF 🆕 | `/api/hr/employees/{id}/accountability/brief.pdf` | ✅ preview · 🔴 prod |
| Safety Employee Profiles | `/api/safety/employees/*` | ✅ |
| Dispatch DQ 🆕 | `/api/dispatch/driver-qualification` | ✅ preview · 🔴 prod |
| FL DQ 🆕 (enriched) | `/api/field-leadership/portal/driver-qualification` | ✅ preview (rich) · ⚠️ prod (slim iter314 shape) |
| HR DQ Dashboard | `/api/hr/driver-qualification/dashboard` | ✅ both |
| PM (assigned crews) | (no per-PM employee surface) | 🔴 |

**Gaps**
- **PM-crew-visibility (GAP-PM-1):** PM has NO direct read of which active employees are assigned to their jobs as crew. Crew assignment happens implicitly via daily reports.

---

## 2 · Safety Training Records (`safety_training_records`)
| Stage | Owner | Endpoint | Status |
|---|---|---|---|
| Create | Safety · HR · Admin 🆕 | POST `/api/safety/training-records` (iter353a shared) | ✅ |
| List | Safety · HR · Admin | GET `/api/safety/training-records` | ✅ |
| Soft-delete / archive | Safety only (HR NO hard delete) | DELETE — Safety + Admin only | ✅ (HR uses notes-prefix archive) |
| Surface on Accountability Timeline | HR · Safety · Admin | `/api/hr/employees/{id}/accountability/timeline` 🆕 | ✅ preview |
| FL view | — | (none) | 🔴 **GAP-FL-TRAIN** |
| PM view | — | (none) | 🔴 **GAP-PM-TRAIN** |
| Notification fan-out on expiration | nightly cron | `notifications` | ⚠️ partial (cron not verified live this audit) |

---

## 3 · PPE / Equipment Issuance (`safety_equipment_issuances`)
| Stage | Owner | Endpoint | Status |
|---|---|---|---|
| Issue | Safety · safety-forms gate | POST `/api/safety-forms/equipment-issuances` | ✅ |
| List | Safety · HR · Admin | GET `/api/safety-forms/equipment-issuances` | ✅ (Safety + HR working) |
| Timeline aggregation | HR · Safety · Admin | timeline endpoint 🆕 | ✅ preview |
| PM view | — | (none) | 🔴 **GAP-PM-PPE** |
| FL view | — | (none) | 🔴 **GAP-FL-PPE** |

---

## 4 · Incidents (`incidents`) — 43 records in preview
| Stage | Owner | Endpoint | Status |
|---|---|---|---|
| Create | Public field form | POST `/api/incidents` | ✅ |
| List | Safety · PM · Admin | GET `/api/incidents` | ✅ |
| **HR list** | — | (HR REJECTED with 401) | 🔴 **GAP-HR-INC-LIST** |
| **FL list** | — | (FL REJECTED with 401) | 🔴 **GAP-FL-INC-LIST** |
| **Dispatch list** | — | (Dispatch REJECTED) | 🔴 |
| Embedded in accountability timeline | HR · Safety · Admin | timeline endpoint 🆕 | ✅ preview |
| Corrective Actions | Safety | `/api/corrective-actions` (under safety_exports gate) | ✅ Safety-only |
| Closeout/Approval chain | Safety | (no explicit approval ladder discovered this audit) | ⚠️ **GAP-INC-CLOSEOUT** |

---

## 5 · Daily Reports (`daily_reports`)
| Stage | Owner | Endpoint | Status |
|---|---|---|---|
| Submit | Public field form (any device) | POST `/api/daily-reports` | ✅ |
| List | PM (scoped) · Admin · safety-forms | GET `/api/daily-reports` | ✅ |
| **HR view** | — | 401 | 🔴 (HR needs payroll/labor visibility) |
| **FL view** | — | 401 | 🔴 (FL submits, can't audit own) |
| **Dispatch view** | — | 401 | 🔴 |
| Payroll variance | Admin / scheduled task | `/api/payroll-variance/*` | ✅ exists |
| Rediscoverability past 90d | (TBD — no archive UI surfaced) | — | ⚠️ |

---

## 6 · Field Leadership Records (`field_leadership_records`)
| Stage | Owner | Endpoint | Status |
|---|---|---|---|
| Create | Leadership portal (legacy shared pw) + FL portal (per-user) | POST `/api/leadership/*` | ✅ |
| List | HR · Admin · FL · PM (scoped) | GET `/api/hr/field-leadership` etc. | ✅ |
| Surface on accountability timeline 🆕 | HR · Safety · Admin | timeline endpoint | ✅ preview |
| Email fan-out | assigned PM + safety@ + jaymn.judd@ | Resend (gated by `AUTO_EMAIL_REPORTS`) | ✅ |

---

## 7 · Equipment Inspections / Pre-Op (`equipment_inspections`)
| Stage | Owner | Status |
|---|---|---|
| Submit | Public field form | ✅ |
| Shop list / sign-off | Shop · Admin | ✅ |
| PM list (scoped) | PM | ✅ |
| Failed-Pre-Op auto-email fan-out | All shop users + SHOP_MANAGER_EMAIL | ✅ |
| HR/Safety visibility | (none) | 🔴 (HR cannot tie equipment failure to operator accountability) |
| Tie to operator employee (`employee_id`) | (not enforced consistently) | ⚠️ **GAP-OP-LINK** |

---

## 8 · QA/QC Inspections (`qaqc_inspections`)
| Stage | Owner | Status |
|---|---|---|
| Submit | Field form | ✅ |
| PM scoped list | PM · Admin | ✅ |
| Notification fan-out on `fail_count > 0` | Safety + PM (recipient_role) | ✅ (verified — 2 live notifications observed) |
| **FL view** | (none) | 🔴 |

---

## 9 · Notifications (`notifications`)
**Observed types:** `qaqc.deficiency` (Safety + PM recipients).
**Observed recipient_role values:** `safety`, `pm`.
**MISSING recipient roles:** `hr`, `fl`, `dispatch`, `shop`. FL never gets a notification today — even though FL is the closest field accountability layer.

---

## Lifecycle continuity verdict
| Domain | Lifecycle complete? | Notes |
|---|---|---|
| Employee onboarding → CDL/medical → expiration | ✅ preview · ⚠️ prod | Production lacks iter353c timeline |
| Employee → training → cert expiration → notification | ⚠️ | Cron live but FL/PM blind |
| Employee → incident → CAPA → closeout | ⚠️ | CAPA exists; closeout chain not enforced |
| Employee → daily report → payroll → audit | ⚠️ | Payroll variance exists; HR cannot list daily reports |
| Equipment → Pre-Op fail → shop → operator accountability | 🔴 | No operator-employee linkage enforced |
| QA/QC fail → Safety + PM → CAPA → closeout | ⚠️ | First step works; closeout not verified |
| FL accountability records → HR → archive | ✅ | Works end-to-end |
| Dispatch driver readiness → FL crew assignment | ⚠️ | Both portals see DQ; no shared "today's roster" |
