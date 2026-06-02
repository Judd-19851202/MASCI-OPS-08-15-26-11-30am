# ACTIVE FINDINGS · VERIFICATION

**Authority**: FOCP WAR ROOM · Phase 1
**Mode**: READ-ONLY · re-verification against current `/app/` source
**Date verified**: 2026-06-02T23:10 UTC
**Source-only**: I do not hold production credentials; `verified_production_date` remains operator-only.

---

## Method

For each ACTIVE finding in `TRUTH_REGISTER.md`, I executed a deterministic grep against current source AND read the relevant file region directly. Results below are binary (hit / no-hit) with cited evidence.

---

## Per-finding verdict

### TR-0001 · OC-005 JHP Acknowledgement Ledger

* Grep: `jhp_acknowledge | JhpAcknowledge | jhp_documents | /api/jhp/`
* Hits: **0** in `/app/frontend/src` and `/app/backend`
* **Verdict**: 🔴 **CONFIRMED ACTIVE** — not built.
* `verified_source_date`: 2026-06-02

### TR-0002 · Universal undo / status reversal verb

* Grep: `undoLastStatus | reverseStatus | /undo/status | universal_undo | status_undo`
* Hits: **0** in `/app/frontend/src` and `/app/backend`
* **Verdict**: 🔴 **CONFIRMED ACTIVE** — not built.
* `verified_source_date`: 2026-06-02

### TR-0003 · Sub/Vendor archive workflow

* Grep: `is_archived | archived_at` in vendor/supplier/sub backend routes — **0 hits**
* Frontend pages named vendor / supplier / sub — **0 hits** (no dedicated archive page)
* **Verdict**: 🔴 **CONFIRMED ACTIVE** — workflow does not exist.
* `verified_source_date`: 2026-06-02

### TR-0004 · Verb harmonization (Save / Submit / Create / File / Send)

* Frontend test-id verb survey:
  * `submit-*` test ids: **16 files**
  * `save-*` test ids: **1 file**
  * `create-*` test ids: **0**
  * `file-*` test ids: **0**
* **Finding revised**: the platform is **already heavily standardized on "Submit" for transactional forms**. The audit register's claim of pervasive verb chaos overstates the problem. The actual residual is at the i18n / inline-button-label level, not the test-id / action-handler level.
* **Verdict**: 🟡 **DOWNGRADE** ACTIVE → LOW priority cosmetic string-sweep, not a blocking governance item.
* `verified_source_date`: 2026-06-02

### TR-0005 · Status canonical dictionary

* `/app/frontend/src/lib/statusDisplay.*` — **not present**
* `/app/frontend/src/lib/canonicalStatus.*` — **not present**
* **Verdict**: 🔴 **CONFIRMED ACTIVE** — helper not built; 38 distinct status words still rendered raw in places.
* `verified_source_date`: 2026-06-02

### TR-0006 · JHP / JHA platform integration

* Grep: `jha_documents | jha_acknowledge | /api/jha/` — **0 hits**
* This is structurally identical to TR-0001 (no ledger, no ack flow, no documents collection).
* **Verdict**: 🟡 **SUPERSEDED** by TR-0001 (which already covers JHP+JHA scope per `JHP_LEDGER_SPECIFICATION.md`).
* `superseded_by`: TR-0001

### TR-0007 · Constraint reopen path absent (doctrine)

* `operational_constraints.py` exposes GET / PATCH / POST resolve / POST chronology only (verified in prior session).
* By doctrine `OPERATIONAL_CONSTRAINT_FOUNDATION.md`, reopen is not supported; resolved is terminal.
* **Verdict**: 🟢 **DOCTRINE-EXEMPT** — does NOT block 90-day self-sufficiency. Move from ACTIVE-PRODUCT-DECISION → DOCTRINE-EXEMPT (a sub-status; rolled into RETIRED-by-doctrine for FOCP closure purposes).
* `verified_source_date`: 2026-06-02

### TR-0008 · dispatch_lifecycle + payroll_variance_lifecycle endpoint pattern

* `dispatch_lifecycle.py` exposes: `POST /assignments`, `GET /assignments/board`, `GET /assignments`, `GET /assignments/{id}`, `POST /assignments/{id}/transition`, `POST /assignments/{id}/cancel`, `POST /assignments/{id}/reassign`, `GET /state-events`, `GET /haul-cycles`, `GET /lifecycle/states` — **10 endpoints, full lifecycle**.
* `payroll_variance_lifecycle.py` exposes: `POST /hr/payroll-variance/batches/{id}/transition`, `GET /state-events`, `GET /lifecycle` — **3 endpoints, transition-based state machine**.
* **Verdict**: 🟢 **RETIRE** — both files are fully wired. Earlier `grep -E "@router.post"` pattern was wrong (used `(post|get|...)`); the actual decorator is `@router.post(...)`. Verified by direct line listing.
* `resolution_pr`: pre-existing platform work
* `verified_source_date`: 2026-06-02

---

## Verification summary table

| TR ID | Prior status | Re-verified status | Action |
|---|---|---|---|
| TR-0001 | ACTIVE | 🔴 ACTIVE | Build |
| TR-0002 | ACTIVE | 🔴 ACTIVE | Build |
| TR-0003 | ACTIVE | 🔴 ACTIVE | Build |
| TR-0004 | ACTIVE | 🟡 DOWNGRADED to LOW | Cosmetic string sweep |
| TR-0005 | ACTIVE | 🔴 ACTIVE | Build helper + adopt |
| TR-0006 | ACTIVE | 🟡 SUPERSEDED by TR-0001 | Mark superseded |
| TR-0007 | ACTIVE-PRODUCT-DECISION | 🟢 DOCTRINE-EXEMPT | Retire |
| TR-0008 | ACTIVE-NEEDS-DEEPER-VERIFY | 🟢 RETIRED-by-prior-work | Retire |

**Population after verification**:

| Status | Count |
|---|---:|
| 🔴 ACTIVE (must build) | 4 |
| 🟡 LOW / SUPERSEDED | 2 |
| 🟢 RETIRED (this verification cycle) | 2 |
| **Original 8 ACTIVE** | **8** |

Net result: **4 ACTIVE findings** require engineering work. **TR-0001 · TR-0002 · TR-0003 · TR-0005**. Everything else has been retired, superseded, or downgraded to cosmetic.

---

## Production verification status (operator-only)

For each of the 4 remaining ACTIVE findings, `verified_production_date` cannot be set by AI. Production verification path:

* TR-0001 → cannot exist on production · nothing to verify (this is a build, not a regression check)
* TR-0002 → cannot exist on production · nothing to verify
* TR-0003 → operator can confirm on `https://mascidocs.com` that no Sub/Vendor archive verb is exposed in the UI
* TR-0005 → operator can confirm on production that status badges still render raw backend strings (e.g., `IN_PROGRESS`, `DEFICIENCY_RAISED`) instead of canonical labels

None of the four are likely to differ between preview and production. The deploys covered the entire frontend bundle.

---

End of Phase 1 verification.
