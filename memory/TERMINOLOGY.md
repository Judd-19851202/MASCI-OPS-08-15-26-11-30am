# MASCI Platform · TERMINOLOGY.md

**Status:** v1.0 · authoritative · Track 14.0-BT (2026-06-13)
**Scope:** Every user-facing word on the MASCI Operations Platform.
**Audience:** Developers · agents · designers · translators · operators.

> One concept = one term. No competing synonyms. No engineering language on operator surfaces.

---

## 1. Action Dictionary

See **[BUTTONS_DICT.md](./BUTTONS_DICT.md) §2** for canonical verb labels. Summary of approved action vocabulary:

`Submit · Save · Save Changes · Save Draft · Cancel · Close · Discard Changes · Back · Return to {Place} · Home · Add · Add {Entity} · Create · Edit · Remove · Delete · Clear · Reset · Open · Open Profile · View · View Details · Upload · Upload Document · Download · Export CSV · Generate PDF · Print · Review · Approve · Needs Revision · Verify · Acknowledge · Assign · Transfer · Complete Work · Repair Complete · Return to Service · Place Out of Service · Hold for Maintenance · Sign In · Sign Out · Continue · Previous`

---

## 2. Status Dictionary

### Asset readiness

| Status | Definition | Color/chip |
|---|---|---|
| **Ready** | All required documents current · no open defects · no maintenance hold · canonical taxonomy verified | green |
| **Warning** | One or more soft conditions (e.g. renewal expiring within 30 days · stale photo) | amber |
| **Not Ready** | Hard blocker (e.g. expired registration · maintenance hold · OOS · failed Pre-Op) | red |
| **Needs Review** | Asset record is incomplete or canonical taxonomy is unverified | slate |

### Document / renewal

| Status | Definition |
|---|---|
| **Current** | Document on file · not expired |
| **Expiring Soon** | Within 30 days of expiration |
| **Expired** | Past expiration date |
| **Missing** | No document on file for a required slot |
| **Verified** | Document inspected and confirmed by Asset Admin |
| **Pending Verification** | Uploaded but not yet verified |
| **Uploaded** | File received but not yet processed |

### Workflow

| Status | Definition |
|---|---|
| **Action Required** | User must do something to proceed |
| **Open** | Generic open state |
| **Closed** | Generic closed state |
| **Reopened** | Closed item brought back to Open |
| **Pending Closure** | Awaiting closure approval |
| **Needs Review** | Generic review-queue state |
| **Needs Revision** | Sent back for changes (NOT "Rejected") |

### Asset lifecycle

| Status | Definition |
|---|---|
| **Available** | Ready to be assigned |
| **Assigned** | Currently assigned to a crew/employee/project |
| **In Transit** | Moving between locations |
| **Pending Transfer** | Transfer initiated, not yet received |
| **Maintenance Hold** | Held by Shop pending work |
| **Out of Service** | Cannot be assigned · Dispatch authority |
| **Repair Complete** | Shop has finished work — **does NOT mean back in service** |
| **Return to Service** | Dispatch / Admin transition that releases asset back to Available |

### Admin reconciliation (rare exception)

| Status | Definition |
|---|---|
| **Verified** | Admin confirmed |
| **Rejected** | Admin **explicitly rejected** during reconciliation (geofence · asset-mapping · legacy import). NOT used as a user-blame term. NOT used for review workflows. |
| **Pending** | Awaiting admin decision |

---

## 3. Entity Dictionary

| Term | Canonical use | Avoid using as |
|---|---|---|
| **Asset** | System-of-record entity (canonical taxonomy_verified record in `equipment_master`) | Generic noun for any object |
| **Unit** | Field/shop-facing label matching unit number (e.g., "Unit 4221") | The canonical system-of-record term |
| **Equipment** | Field operator vernacular ("equipment inspection") | Canonical system-of-record term |
| **Vehicle** | Specifically a road-licensed asset (truck · trailer · car) | A general substitute for Asset |
| **Truck** | Specifically a truck-class Vehicle | A generic Vehicle synonym |
| **Trailer** | Specifically a trailer-class Vehicle | A generic Vehicle synonym |
| **Employee** | HR record (canonical) | A worker on a one-off field form |
| **Worker** | Field-form participant (may not be a permanent Employee) | The canonical HR record |
| **Operator** | Role label for equipment-running Worker | The Employee record |
| **Driver** | Role label for DVIR/Driver-magic-link Worker | The Employee record |
| **Foreman** | Role label for crew-leading Worker | Not a portal role |
| **Superintendent** | Role label for senior field leadership | Not a portal role |
| **Supervisor** | Role label for supervisory worker | Not a portal role |
| **Manager** | Role label for portal-level manager (e.g., Shop Manager) | A generic noun |
| **Project** | Customer-facing canonical project | Job (use "Job" for crew-level work) |
| **Job** | Crew-level work unit within a Project | Project (canonical work) |
| **Work Order** | PM/Shop work order | A Job |
| **Defect** | Reported issue on an Asset (Pre-Op/DVIR finding) | Generic problem |
| **Issue** | Generic operator-reported problem (broader than Defect) | A canonical Defect |
| **Document** | File attached to an Asset/Employee/Project with metadata | Photo |
| **Photo** | Image attached to a record (no other metadata) | Document |

---

## 4. Workflow Dictionary

| Term | Definition |
|---|---|
| **Daily Report** | Foreman/Superintendent daily project report (labor · subs · materials · weather · photos) |
| **Pre-Op** | Public equipment inspection submitted by Operator before use |
| **DVIR** | Driver Vehicle Inspection Report (Driver-side · trucks/trailers) |
| **Incident** | Safety event report |
| **Safety Meeting** | Toolbox Talk / safety meeting capture |
| **Excavation** / **Trench** | OSHA-driven trench-safety field record |
| **PM** | Preventive Maintenance schedule + work orders |
| **Asset Care** | Operational portal for Asset Administrator (`/shop/asset-care`) |
| **Dispatch** | Dispatch portal · Map-First |
| **Shop** | Shop Command Center · Shop Manager / Mechanic surfaces |
| **HR** | Human Resources portal |
| **Field Leadership** | Field Leadership portal (Superintendent · executive ops) |
| **Asset Administration** | Admin Console tab for Asset Admin config (`/admin/asset-admin`) |
| **Renewal Alerts** | 5-bucket renewal fan-out (critical · high · medium · low · info) |
| **Required Docs** | Per-asset-class document matrix (Asset Admin Settings) |
| **Smart Pre-Op** | Taxonomy-driven dynamic Pre-Op template |
| **Readiness Engine** | Advisory readiness state for Assets (Track 13.33ABC) |

---

## 5. Forbidden Operator-Visible Terms

Never appear on operator/field UI. Acceptable in code comments only.

| Forbidden | Use instead |
|---|---|
| API · endpoint · schema · backend · frontend · migration | (operator does not need these words) |
| Track 13 · Track 14 · TRACK_* | (internal track names — never surface) |
| HTTP {code} · stack trace · exception | Approved toast pattern from TOAST_DICTIONARY.md |
| RESEND_API_KEY · MAINTAINX_API_KEY · env-var names | "Email delivery is disabled" / "MaintainX is not connected yet" |
| Rejected · Denied (as workflow-blame term) | Needs Revision |
| Failed (as workflow status) | Could not {verb} · Action Required |
| Invalid (as user-blame) | Check required fields · {Field} is not valid |
| Deprecated · Legacy | (do not surface · admin-tool exception OK) |
| undefined · null · NaN | (operator never sees raw JS values) |
| /api/ paths | (URL constants stay in code only) |
| 500 · 404 · 401 · 403 | Use approved toast patterns |
| Refresh the page (without context) | Try again, or contact your administrator if it keeps failing |

---

## 6. Role-Specific Vocabulary

### Admin
- Surfaces: `/admin/*`
- Vocabulary: "Console" · "Settings" · "Configuration" · "Audit" · "Reconciliation"
- Power-user tone acceptable. Avoid Spanish-burden text — admin is typically EN-first.

### Asset Administrator
- Surfaces: `/shop/asset-care` (operational home) + `/admin/asset-admin` (configuration tab)
- Vocabulary: "Asset" · "Readiness" · "Renewals" · "Required Docs" · "Document Vault" · "Review Queue"

### Shop Manager / Mechanic
- Surfaces: `/shop/*`
- Vocabulary: "Work Order" · "Defect" · "Repair Complete" · "Maintenance Hold" · "OOS" (acceptable abbreviation in shop chrome)
- "OOS" is acceptable on Shop Hub; spelled "Out of Service" on operator-facing surfaces

### Dispatcher
- Surfaces: `/dispatch-portal/*`
- Vocabulary: "Map" · "Live Fleet" · "Recovery" · "Transfer" · "Return to Service" (RTS authority)

### PM
- Surfaces: `/pm/*`
- Vocabulary: "Project" · "Daily Report" · "Submission" · "Revision" · "RFI" (where applicable)

### Safety
- Surfaces: `/safety-portal/*` · `/safety/*`
- Vocabulary: "Incident" · "JHP/JHA" (per MASCI standard: JHP) · "Stop-Work" · "Coaching, not punishment"

### HR
- Surfaces: `/hr/*`
- Vocabulary: "Employee" · "Onboarding" · "Offboarding" · "Time-Off" · "Issuance" · "Asset/PPE"

### Field Leadership / Superintendent / Executive
- Surfaces: `/field-leadership/*` · `/leadership/*`
- Vocabulary: "Project" · "Crew" · "Daily Report" · "Production"

### Public Submitter / Operator / Foreman / Driver
- Surfaces: `/equipment/submit` · `/fleet/dvir/submit` · `/daily/submit` · `/incidents/submit` · `/meetings/submit` · `/trench-safety/excavation/new`
- Vocabulary: simplest possible. No portal labels. No admin language. Identify form by purpose ("Pre-Op", "DVIR", "Daily Report", "Field Excavation Record").

---

## 7. Capitalization & Style

- **Headings**: Title Case ("Asset Care Command Center", "Renewal Alerts")
- **Buttons**: Title Case for noun-actions ("Add Asset"), sentence verb-actions ("Submit", "Save")
- **Status chips**: Title Case ("Ready", "Needs Review")
- **Toast text**: Sentence case, end with period ("Saved." "Could not save. Try again.")
- **Validation**: Sentence case, often without trailing period for single-fragment validations ("Name required")
- **Empty states**: Sentence case, one or two short sentences
- **Never** ALL CAPS for body copy. Caps reserved for eyebrows (font-mono uppercase tracking-[0.18-0.25em]).

---

## 8. Spanish Translation Notes (for 14.0-S1)

- All action verbs (Submit · Save · Cancel · etc.) — translate via single i18n key, used everywhere.
- All status chip names (Ready · Warning · Not Ready · Needs Review · etc.) — translate via single i18n key per chip.
- All entity nouns (Asset · Unit · Employee · Project · Document) — translate via single i18n key.
- Workflow names (Daily Report · Pre-Op · DVIR · Incident · Safety Meeting · Excavation) — translate consistently; do not vary.
- Role-specific shop abbreviation "OOS" → leave as-is in Shop chrome; Spanish operator-facing surfaces always use "Fuera de servicio".
- "JHP" is MASCI standard — preserve as JHP across EN and ES. Do not translate to "AST" / "ATS".
- "Repair Complete" ≠ "Return to Service" — preserve this distinction in Spanish. The current platform locks the doctrine "Repair Complete does NOT return asset to service." Spanish must lock the same: "Reparación Completa" ≠ "Volver a Servicio."

---

## 9. Doctrine Reminders

- **Coaching, not punishment.** All workflow language preserves this tone (Safety · Incident · Pre-Op · DVIR).
- **Repair Complete ≠ Return to Service.** Only Dispatch/Admin role has RTS authority. Shop completes work; Dispatch returns to service.
- **Asset Admin is operational, not Admin.** Asset Admin lands on `/shop/asset-care`, not the Admin Console.
- **MaintainX / FleetWatcher are honestly dormant.** Never claim "Connected" until credentials exist.
- **Photos and documents are never required for submission.** Field operators can submit forms without attachments.
- **Sensitive doc gates** (Insurance · Title · Purchase) require admin role.

---

**End of TERMINOLOGY.md v1.0.**
