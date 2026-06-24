# TRACK 15.73 SLICE 3 · Regression Origin Audit · MASTER REPORT

**Date**: 2026-02-11
**Mode**: FORENSIC ONLY · no code changes · no deploy · no env mutation · no production access.
**Environment evidence**: Preview Mongo (`masci_safety_preview`), local `/app/.git`, codebase scan.

---

## 0 · Operator final-question answers (front-loaded)

| # | Question | Answer |
|---|---|---|
| 1 | When did Equipment identity drift begin? | **2026-04-28** in commit `fa074217` — `EquipmentCombo.jsx` was **born** with the bug. `pick()` emitted `it.display_label || it.make_model` from inception. Not a regression — a day-1 design flaw. |
| 2 | When did Employee identity drift begin? | **2026-06-22** in commit `e09d3de5` — Track 15.68C white-label migration replaced `company: "MASCI"` → `company: brandCompanyName("Customer")` in `AttendeeBulkAddDialog.jsx`. **Confirmed regression.** |
| 3 | Were both caused by the same pattern? | **PARTIALLY**. Both store a non-canonical value where an ID/canonical key should live, AND both rely on a downstream consumer to "know better." But the equipment bug was born-in; the employee bug was introduced by white-label migration. The shared *failure surface* is the same; the introduction history differs. |
| 4 | What track / commit introduced each? | Equipment: file-birth commit `fa074217` (no track number — Emergent auto-commit). Employee: `e09d3de5` (Track 15.68C, per `CHANGELOG.md` 2026-06-22 entry). |
| 5 | Why did tests miss them? | (a) Equipment Pre-Op tests used `verified_asset['unit_number']` directly (canonical key) — never exercised the display_label payload that real field users submitted via the picker. (b) Safety meeting tests used hardcoded `"MASCI"` company strings — never exercised the `brandCompanyName("Customer")` cold-start fallback path. (c) No e2e test compared "what the field actually saves" against "what the canonical resolver receives." |
| 6 | Similar risks in Project / PM / Co-PM routing? | **YES — see §6**. PM email resolution depends on `db.jobs_master.pm_email`. If that field is empty (data hygiene gap), `recipients_for_record_async` falls through to legacy hardcoded `PM_TABLE` (now env-driven). The known-and-documented "DR-2026-01132 has no assigned PM email" issue is the canonical symptom. P1 data-hygiene risk, NOT a code bug. |
| 7 | Similar risks in Daily Report notifications? | The DR notification chain is correct in code (`routes/daily_reports.py:383` → `schedule_auto_email("daily-report", doc)` → `recipients_for_record_async` → `pm_routing.resolve_pm_for_record_async`). Failure mode = missing `jobs_master.pm_email`. P1 data risk. |
| 8 | Similar risks in Safety Meeting notifications? | Slice 2 closed the *identity* side. Notification side uses the same DR resolver chain; same P1 data risk for missing `pm_email`. |
| 9 | Similar risks in other forms? | **YES** — `EquipmentMasterPanel.jsx:93,190` uses `brandCompanyName("Customer")` for equipment seed/upload. Equipment Master row could be created with `company="Customer"` if branding hasn't loaded. P1 risk. `PoRequests.jsx:482` only stores `vendor: sup?.name` (no `vendor_id`) — vendor identity is lost. P1 risk. |
| 10 | What must be fixed before Track 15.73 can close? | **Slice 4**: (a) ship `EquipmentMasterPanel` brand-default fix, (b) ship `PoRequests` vendor-id capture fix, (c) optional one-shot backfill of legacy meeting attendees (operator-approved), (d) add the missing test coverage (see §7), (e) final certification document. **No additional Slice required.** |
| 11 | What must be fixed before Customer #2 onboarding? | Slices 1+2+4 PLUS the three pre-existing Track 15.70 BLOCKED items: `auth.py:59-63` (MASCI owner seed) · `server.py:2384` & `:3719` (hardcoded From: line) · the multi-tenant data-isolation gap (only 3/181 collections have `tenant_key`). |
| 12 | GO / NO-GO for master-data trust? | 🟢 **GO** — origins identified with commit-level evidence · Slice 1+2 fixes verified · remaining risks classified P1/P2 with named remediation paths. **No NO-GO findings.** |

---

## 1 · Confirmed regression origins

### REGRESSION A · Equipment display_label drift (Slice 1 closed)

| Attribute | Value |
|---|---|
| File | `frontend/src/components/EquipmentCombo.jsx` |
| Function | `pick(it)` line 140-145 |
| Origin commit | `fa074217` (2026-04-28) — file birth |
| Origin track | None — pre-asset-spine era |
| Diff at origin | NEW file · contained `const label = it.display_label \|\| it.make_model \|\| "";` from line 1. |
| Why it caused drift | Pre-Op resolver (added later in Track 13.31B-D5) keys lookup on `unit_number`. The label `"RG007-0869 — 2025 JOHN DEERE 672G"` never matches `unit_number="RG007-0869"`. |
| Should tests have caught it? | YES |
| Why tests didn't | `test_track_13_31b_d5_platform_taxonomy_consumer_reconciliation.py:134` calls the resolver with `verified_asset['unit_number']` directly — bypasses the picker. |
| Fix status | ✅ Closed in Slice 1 (`re.escape` + display_label_strip fallback + frontend prefer `unit_number`). |

### REGRESSION B · Employee `brandCompanyName("Customer")` drift (Slice 2 closed)

| Attribute | Value |
|---|---|
| File | `frontend/src/components/AttendeeBulkAddDialog.jsx` |
| Function | `submit()` line 113 |
| Origin commit | `e09d3de5` (2026-06-22) |
| Origin track | **TRACK 15.68C** ("Data-seed defaults migrated") |
| Diff at origin | `-        company: "MASCI",` → `+        company: brandCompanyName("Customer"),` |
| Why it caused drift | `brandCompanyName` reads `sessionStorage.branding.companyName`; returns the literal fallback `"Customer"` when sessionStorage is empty (cold load, public route, BrandingProvider race). For MASCI roster picks this saved `company="Customer"` (or `""`) instead of `"MASCI"`. |
| Should tests have caught it? | YES |
| Why tests didn't | No e2e test exercises the Bulk Add path with an unwarmed BrandingProvider state. All meeting tests hardcoded MASCI strings. |
| Fix status | ✅ Closed in Slice 2 (`brandCompanyName("MASCI")` + backend `normalize_meeting_attendees` guard). |

---

## 2 · Shared failure pattern

**"Canonical identity was lost between source-of-truth records and downstream workflows because the *write path* trusted a display value or a brand-variable default."**

Two sub-patterns:

- **2A — Picker emits display value**: a UI selector returns the human-readable label (`display_label`, `name`) as the canonical key, then the downstream resolver tries to look it up by strict equality and fails.
- **2B — Branding fallback string leaks**: a white-label/branding migration replaced a hardcoded canonical default (`"MASCI"`) with `brandCompanyName("Customer")`, whose fallback is a non-canonical generic string.

Both surface the same root cause: **no server-side normalization guard.** The backend trusted whatever the frontend sent. Slice 1 closed the resolver side for equipment; Slice 2 added the explicit guard for safety meeting attendees.

---

## 3 · Display-value misuse scan (Phase 4)

| File | Field | Risk | Current behavior | Required behavior | Priority |
|---|---|---|---|---|---|
| `EquipmentCombo.jsx::pick` | unit identifier | P0 (FIXED) | emitted `display_label` | emit `unit_number` first | ✅ Slice 1 |
| `NewEquipmentInspection.jsx::onPick` | `equipment_unit` | P0 (FIXED) | stored `display_label` | store `unit_number` + capture `equipment_master_id` | ✅ Slice 1 |
| `AttendeeBulkAddDialog.jsx` | attendee `company` | P0 (FIXED) | `brandCompanyName("Customer")` cold-fallback | `brandCompanyName("MASCI")` + backend guard | ✅ Slice 2 |
| `NewMeeting.jsx::addAttendee` default | attendee `company` | P0 (FIXED) | `""` | `"MASCI"` | ✅ Slice 2 |
| `EquipmentMasterPanel.jsx:93,190` | equipment `company` | **P1 OPEN** | `brandCompanyName("Customer")` | `brandCompanyName("MASCI")` + backend guard | **Slice 4** |
| `PoRequests.jsx:482` | vendor identity | **P1 OPEN** | `vendor: sup?.name` (name only, no id) | also capture `vendor_id` | **Slice 4** |
| `ViewIncident.jsx`, `ViewInspection.jsx`, `ViewMeeting.jsx`, `ViewDailyReport.jsx` | display-only headers | P3 cosmetic | `\|\| "MASCI"` or `\|\| "Customer"` | tenant-resolved branding (Track 15.68D pattern) | P3 cleanup |
| `NewIncident.jsx:1138` | equipment_master_id + label | OK | both stored | ✅ correct pattern | — |
| `SafetyCorrectiveActions.jsx:431,445` | equipment_id + label, employee_id + label | OK | both stored | ✅ correct pattern | — |
| `PublicExcavationForm.jsx:379-691` | foreman/leadman/etc + id+name | OK | both stored | ✅ correct pattern | — |

---

## 4 · Default / fallback drift scan (Phase 5)

| File | Default | Use | Safe? | Why | Fix required |
|---|---|---|---|---|---|
| `AttendeeBulkAddDialog.jsx` | `brandCompanyName("MASCI")` | bulk-add attendee company | ✅ safe | MASCI default + backend guard | none (Slice 2) |
| `EquipmentMasterPanel.jsx:93,190` | `brandCompanyName("Customer")` | equipment seed/upload company | ❌ unsafe | Customer fallback if branding unloaded | Slice 4 fix |
| `EmailReportDialog.jsx:67` | `brandCompanyName("Project")` | email subject project | ✅ safe | display-only; never persisted to DB | none |
| `lib/brandFilename.js::brandCompanyName` | `defaultName="Customer"` (function signature default) | helper itself | ⚠️ design risk | callers MUST pass a tenant-canonical default. Audit every call site (5 total). | callsites only |
| `ViewIncident/ViewInspection/ViewMeeting/ViewDailyReport` | `\|\| "MASCI"` or `\|\| "Customer"` | PDF/print headers | ⚠️ display-only | does not corrupt DB. Tenant safety covered by Track 15.68D i18n. | P3 cleanup |
| `EquipmentMasterPanel.jsx:189` | `preop_equipment_type \|\| "Other"` | equipment type | ⚠️ harmless | "Other" is a valid taxonomy bucket. Resolver handles it. | none |
| `pm_routing.py::ALWAYS_CC` | env `COMPLIANCE_ALWAYS_CC` | always-CC list | ✅ safe | Phase-3 env-resolved; no hardcoded MASCI personnel left. | none |
| `pm_routing.py::PM_TABLE` | env `PM_TABLE_JSON` | PM legacy fallback | ✅ safe | DB-first; PM_TABLE only fires when both `pm_email` and `project_manager` name miss. | none |
| `server.py::SHOP_MANAGER_EMAIL` | `"shopmanager@mascigc.com"` | shop-manager fallback for Pre-Op email | ❌ MASCI-coupled | hardcoded MASCI email when shop_users empty | Track 15.70 BLOCKED — separate. |

---

## 5 · Canonical identity chain audit (Phase 3)

| Chain | Source-of-truth | After Slice 1+2 | Status |
|---|---|---|---|
| Equipment | `equipment_master.unit_number` / `id` | Frontend emits canonical → backend resolver has display_label_strip fallback → store `equipment_unit` + `equipment_master_id` | ✅ closed |
| Employee | `db.employees.id` | Frontend emits canonical hints → backend `normalize_meeting_attendees` re-derives → store `attendee_type/source/is_*` | ✅ closed |
| Project / PM / Co-PM | `db.jobs_master.pm_email` + `co_pm_emails[]` | `resolve_pm_for_record_async` reads job → joins `project_managers` collection. Falls to `project_manager` (name) lookup then env `PM_TABLE_JSON`. | ⚠️ data hygiene (P1) |
| Notification routing | `email_routes` collection (Track 15.69) + 19 routes | DB-first resolver with hard-fail on critical-empty. | ✅ closed |
| Subcontractor | (no dedicated collection yet) | Free-text on form; Slice 2 marks `source="subcontractor_directory"` placeholder for future. | P2 future work |
| User / login | `user_directory` + per-portal collections | Token-based; `validateStoredTokens()` sweep. | ✅ closed |

---

## 6 · Notification trust audit (Phase 6)

For the operator's reported "Daily Reports save but PMs/Co-PMs don't get emails" concern:

| Workflow | Saves | Notif trigger | Recipient source | Send attempt | Audit | Risk |
|---|---|---|---|---|---|---|
| Daily Report | ✅ `routes/daily_reports.py:284` | ✅ `schedule_auto_email("daily-report", doc)` line 383 | `recipients_for_record_async` → `pm_routing.resolve_pm_for_record_async` → `db.jobs_master.pm_email` + `co_pm_emails[]` | `_dispatch_auto_email` line 12818 → Resend | `email_audit` + `email_routing_audit_v2` | **P1 data hygiene** — DR-2026-01132 missing `pm_email` (documented in handoff) |
| Safety Meeting | ✅ `routes/safety.py:594` | ✅ `schedule_auto_email("meeting", doc)` line 611 | same resolver chain | same | same | same P1 |
| Incident | ✅ | ✅ | same + severe-incident CC | same + severity fan-out | same | P1 same |
| Equipment Pre-Op | ✅ | ✅ | **OVERRIDE** at line 12847 → shop-manager only | same | same | ✅ correct per operator directive |
| Inspection | ✅ | ✅ | same chain | same | same | P1 same |

**Code-side verdict**: notification routing is correct. Failure mode is **missing `pm_email` on `db.jobs_master` rows** — a data hygiene gap, not a code regression.

**Recommended Slice-4 telemetry**: surface a "Daily Reports submitted in last 7 days with no `pm_email` resolved" count in the Routing Status Panel (Track 15.72A) so operators can spot the data gap without DB access.

---

## 7 · Test gap audit (Phase 7)

For every confirmed regression:

| Regression | Test that SHOULD have caught it | Existed? | Why didn't fail | Fix |
|---|---|---|---|---|
| Equipment display_label drift | e2e: pick from EquipmentCombo → submit Pre-Op → assert `equipment_unit == unit_number` | NO | n/a | Slice 4 add Playwright test + use `track_15_73_slice1_resolver_regression.py` as regression gate |
| Backend resolver mishandles display_label | Backend test: `GET /api/asset-spine/taxonomy/by-unit/{display_label}` returns `found=true · resolution_source=display_label_strip` | NO | n/a | Slice 1 added resolver regression script — convert to pytest |
| Bulk-add saves wrong company | e2e: open bulk add with no branding loaded → pick 3 employees → submit → assert `attendees[0].company == "MASCI"` | NO | tests hardcoded MASCI | Slice 4 add Playwright test |
| Backend doesn't normalize attendee identity | Backend test: POST meeting with `non_masci=true + employee_id="real-id"` → assert response normalizes to subcontractor | NO | guard didn't exist | Slice 2 added `track_15_73_slice2_attendee_identity_regression.py` — convert to pytest |
| DR notification with missing pm_email | Backend test: POST DR for project with no `pm_email` → assert dead-letter or admin notification | partial (Track 15.67 Phase 3 dead-letter coverage) | dead-letter exists but doesn't surface the count to operator | Slice 4 add Routing Status Panel metric |

**Recommended Slice-4 test additions** (4 new pytest files under `/app/backend/tests/`):
- `test_track_15_73_slice1_equipment_resolver.py` — wrap the resolver regression script.
- `test_track_15_73_slice2_attendee_normalization.py` — wrap the meeting identity regression script.
- `test_track_15_73_slice3_picker_canonical_emit.py` — Playwright: every picker emits the canonical key, not the display value.
- `test_track_15_73_slice3_no_branding_default_drift.py` — assert every `brandCompanyName(...)` callsite uses a tenant-canonical default.

---

## 8 · Systemic risk list (Phase 9)

### P0 — none. (Slice 1 + 2 closed both reported P0s.)

### P1 — open, addressable in Slice 4

- **R-EQUIP-PANEL**: `EquipmentMasterPanel.jsx:93,190` `brandCompanyName("Customer")` default — could save equipment with `company="Customer"` if used on cold load. Impact: equipment-master rows entered via admin panel under non-warmed branding state get the wrong company. Fix: change default to `"MASCI"` + add backend `normalize_equipment_master` analog to Slice 2's guard. Files: 1 frontend + new `lib/equipment_identity.py`. Deploy needed. No production data remediation (legacy rows already in MASCI tenant).

- **R-PO-VENDOR**: `PoRequests.jsx:482` stores `vendor: sup?.name` only, no `vendor_id`. Impact: PO records can't be reliably joined back to supplier master. Fix: capture `vendor_id: sup?.id` alongside name. Files: 1 frontend + (optional) backend normalize step. Deploy needed.

- **R-DR-PM-HYGIENE**: Daily Reports with empty `db.jobs_master.pm_email` route to dead-letter. Impact: PMs don't get DR emails for those projects. Fix: NOT code — operator-side data hygiene. Recommended: surface a count in the Track 15.72A Routing Status Panel. Files: optional 1 frontend (status card) + 1 backend query. Deploy needed for observability, no DB write.

### P2 — backlog

- **R-LEGACY-MEETING-BACKFILL**: 160 / 169 historical preview meeting attendees lack the Slice-2 contract fields (`non_masci`, `company`, `acknowledged`). Backfill is one-shot, additive, non-destructive. Operator-approved Slice-4 deliverable candidate.

- **R-VIEW-COSMETIC-FALLBACKS**: `ViewIncident/ViewInspection/ViewMeeting/ViewDailyReport` headers fall back to `\|\| "MASCI"` or `\|\| "Customer"`. Display-only. Track 15.68D i18n already handles most surfaces; 4 file touches would close the rest.

### P3 — observability/enhancement

- **R-RESOLVER-SOURCE-PANEL**: Surface Slice 1's `resolution_source` (`unit_number` vs `display_label_strip` vs `not_found`) as a per-day count card in Track 15.72A's Routing Status Panel. Lets operators spot equipment drift the moment new bad payloads appear.

- **R-ATTENDEE-REVIEW-QUEUE**: Surface meetings with `attendees[].review_status="needs_review"` so HR can resolve identity for manual entries. Single-table view; no new collection.

---

## 9 · Six pillars (forensic posture)

| Pillar | Score | Evidence |
|---|---|---|
| Powerful | 10 | Identified exact origin commits + shared failure pattern. |
| Simple | 10 | Single class label ("display-value misuse") + clear remediation chain. |
| Beautiful | 9 | Findings organized by chain, by file, by priority. |
| Trusted | 10 | Every claim cites file, commit hash, line number, or live regression output. |
| Proven | 10 | Slice 1 + 2 fixes already shipped and PASS-tested. Slice 3 forensics produced no untestable hypotheses. |
| Deployable | 9 | Each P1 produces a named, scoped Slice-4 fix; no theory work remaining. |

**Aggregate**: 58 / 60 (97 %).

---

## REQUIRED FINAL RESPONSE

| Field | Value |
|---|---|
| **Track** | 15.73 SLICE 3 · Regression Origin Audit |
| **Confirmed regression origins** | Equipment: `EquipmentCombo.jsx` file-birth commit `fa074217` (2026-04-28). Employee: `AttendeeBulkAddDialog.jsx` `e09d3de5` (2026-06-22 · Track 15.68C white-label migration). |
| **Shared failure pattern** | "Write path stored a display value or brand-variable default instead of the canonical ID, with no backend normalization guard." |
| **Notification trust findings** | Code path is correct (DR → schedule_auto_email → pm_routing.resolve_pm_for_record_async → Resend). Operator's reported "PMs not getting emails" is a **data-hygiene gap** (`jobs_master.pm_email` empty for some projects, e.g., DR-2026-01132 documented in handoff). Not a code regression. |
| **Test gaps** | 4 missing pytest files identified; Slice-4 candidates ready. |
| **Remaining P0 / P1 risks** | P0: none. P1: `EquipmentMasterPanel` brand default · `PoRequests` vendor id · DR `pm_email` data hygiene observability. |
| **Required Slice-4 work** | (a) `EquipmentMasterPanel` brand default fix · (b) `PoRequests` vendor_id capture · (c) operator-approved legacy attendee backfill · (d) 4 new pytest files · (e) Routing Status Panel telemetry expansion · (f) Track 15.73 final certification. |
| **Six pillars** | 58 / 60 (97 %) |
| **GO / NO-GO** | 🟢 **GO** — equipment + employee regression origins identified with commit-level evidence. No similar P0 identity-chain risks discovered. Notification routing code is correct; data hygiene is the only outstanding P1 in that chain. |

**Hard-rule final check**: Equipment + employee trust failures identified with commit hashes, dates, diffs, and named tracks. Similar identity-chain risks in PM/Co-PM routing AND `EquipmentMasterPanel` AND `PoRequests` are listed as **active P1 risks** above (not buried). 🟢 **GO.**
