# Legacy Operational Records Import & Operational Continuity System
## Architecture · Workflow · Governance Proposal — iter248 (Planning Phase Only)

**Status:** DESIGN ONLY · NO IMPLEMENTATION
**Posture:** Compatible with extended stabilization · Phased rollout · Single document type proven end-to-end before any expansion
**Operator core principle honored throughout:** Imported records become **first-class operational records** after human approval — not a passive archive.

---

## 0 · Executive Summary

This document proposes a **single unified ingestion pipeline** that turns paper operational records into structured, live, operationally-active records inside MASCI Operations Platform. The system is built around three non-negotiable guarantees:

1. **Human approval is the only path to operational activation.** OCR/AI surfaces suggestions; humans approve.
2. **Approved imported records live in the same collections as native records** (with a `source` discriminator), so they participate in termination workflows, expiration tracking, accountability searches, and dashboards exactly like live records.
3. **Original source evidence (PDF/image) is permanently attached to every promoted record** in R2, with an immutable audit chain.

The architecture is intentionally **conservative**: one pipeline · one reconciliation queue · one promotion contract · one set of metadata fields · all reused across every supported document type. No parallel importers. No silent flows.

**Recommended rollout cadence:** ship **one document type end-to-end (Equipment Checkout)** before adding a second. Prove the pipeline operationally with one type, then expand. The cost of getting this wrong on multiple types simultaneously is far higher than the cost of going slow.

---

## 1 · Core Operational Philosophy (matches operator brief verbatim)

| Principle | What this means in code |
|---|---|
| OCR/AI **assists** operators | OCR/AI never writes directly to live collections. It writes to `legacy_imports` (staging) only. |
| **Never** silently creates official records | No code path promotes a staging record to a live record without a `reviewer_user_id` being set. |
| **Never** auto-approves | `status: "approved"` is settable only by an HR/Safety/Admin-token-authenticated endpoint with explicit confirmation body. |
| **Never** bypasses human review | Reviewer must be the same actor that performs the explicit `POST /api/legacy-imports/{id}/approve`. |
| **Never** mutates employee histories autonomously | No background job ever calls `approve`. The cron only handles OCR re-tries and stale-import sweeps. |
| **Never** creates operational flags without approval | Equipment-accountability, expiration alerts, compliance flags fire only off live-collection records — and only after promotion. |

This philosophy is enforced architecturally (not just procedurally) by separating two collections: `legacy_imports` (mutable, review-state) and the destination live collections (write-only via promote path).

---

## 2 · Unified Data Model

### 2.1 Staging collection · `legacy_imports`

One collection holds every uploaded document, regardless of document type. Discriminator field: `document_type`.

```
{
  id:                  "uuid",
  document_type:       "equipment_checkout" | "training_record" | "osha_card" | "toolbox_talk"
                       | "fit_test" | "medical_card" | "cdl_license" | "certification"
                       | "safety_orientation" | "signed_acknowledgement" | "write_up"
                       | "onboarding_packet" | "hr_record" | "qualification_record"
                       | "unknown",                         // ← classifier confidence < threshold
  status:              "uploaded" | "ocr_in_progress" | "ocr_failed" | "needs_review"
                       | "approved" | "rejected" | "promoted" | "duplicate",
  source_files:        [                                    // Multi-page support
    {
      r2_key:          "legacy-imports/2026/05/{batch}/{uuid}.pdf",
      original_name:   "EQ-checkout-Jake-Smith-2019-03-15.pdf",
      mime:            "application/pdf",
      size_bytes:      482103,
      sha256:          "...",                               // ← duplicate dedupe key
      uploaded_by_id:  "{hr_or_safety_or_admin_user_id}",
      uploaded_by_name:"Leticia Masci",
      uploaded_at:     "2026-05-19T14:00:00Z",
    }
  ],
  upload_portal:       "hr" | "safety" | "admin",          // ← RBAC origin (immutable)
  batch_id:            "uuid",                              // ← bulk-upload grouping
  ocr: {
    provider:          "claude_vision" | "manual",
    completed_at:      "2026-05-19T14:00:30Z",
    raw_text:          "...",                               // full extracted text
    extracted_fields:  { /* type-specific · see §6 */ },
    confidence:        0.0–1.0,                             // overall doc confidence
    field_confidences: { employee_name: 0.92, serial_number: 0.51, ... },
    classifier_score:  0.0–1.0,                             // doc-type guess confidence
    error:             null | "low_resolution" | "no_text_detected" | ...
  },
  matches: {
    employee:    { suggested_id, suggested_name, confidence, alternatives: [...] },
    equipment:   { suggested_id, suggested_name, confidence, alternatives: [...] },
    project:     { suggested_id, suggested_number, confidence },
    duplicate_of:{ existing_record_id, collection, confidence }
                                                            // null if no duplicate suspected
  },
  review: {
    reviewer_user_id: null | "uuid",
    reviewer_name:    null | "Leticia Masci",
    reviewed_at:      null | "2026-05-19T14:30:00Z",
    decision:         null | "approved" | "rejected" | "needs_more_info",
    corrections:      { /* overrides operator made vs. OCR */ },
    reject_reason:    null | "illegible" | "wrong_employee" | "duplicate" | "out_of_scope"
                            | "wrong_document_type" | "other",
    notes:            ""
  },
  promotion: {
    promoted:                false,
    promoted_to_collection:  null | "equipment_checkouts" | "training_records" | ...,
    promoted_record_id:      null | "uuid",
    promoted_at:             null | "2026-05-19T14:30:05Z",
  },
  created_at:          "2026-05-19T14:00:00Z",
  updated_at:          "2026-05-19T14:30:05Z",
}
```

**Index plan:**
- `{ status: 1, upload_portal: 1, created_at: -1 }` — reconciliation queue lists
- `{ "source_files.sha256": 1 }` — duplicate-upload short-circuit
- `{ document_type: 1, status: 1 }` — per-type review dashboards
- `{ "matches.employee.suggested_id": 1 }` — employee timeline integration

### 2.2 Promoted records · live collections

Each promoted record lives in the **same collection** as native records (e.g. `equipment_checkouts`, `training_records`, `hr_disciplinary_actions`, `safety_qualifications`). Every promoted record carries a fixed metadata block:

```
{
  // …existing native-record fields…
  source: "legacy_imported",                  // ← required discriminator
  legacy_import: {
    import_id:        "uuid",                 // ← back-reference to legacy_imports
    batch_id:         "uuid",
    imported_by_id:   "uuid",                 // uploader
    imported_by_name: "Leticia Masci",
    imported_at:      "2026-05-19T14:00:00Z",
    reviewer_user_id: "uuid",                 // approver
    reviewer_name:    "Leticia Masci",
    reviewed_at:      "2026-05-19T14:30:00Z",
    ocr_confidence:   0.87,
    extraction_method:"claude_vision_v1",
    original_file_url:"https://r2.../legacy-imports/2026/05/{batch}/{uuid}.pdf",
    import_notes:     ""
  }
}
```

Native records keep `source: "live_native"` (or simply omit the field — promotion path is what sets `"legacy_imported"`).

**Why same collection, not parallel:** This is the single most important architectural decision. Same-collection = imported records appear automatically in every existing query, search, dashboard, expiration scan, termination workflow, and audit report — **without touching any of those code paths**. A parallel collection would require ~30+ existing queries to be widened, doubling the surface area of regression risk.

### 2.3 Immutable audit log · `legacy_import_audit`

Every state transition on a `legacy_imports` record is written as an audit row:

```
{
  id, import_id, batch_id,
  actor_user_id, actor_name, actor_role,
  action: "uploaded" | "ocr_completed" | "ocr_failed" | "reviewed" | "approved" | "rejected" | "promoted" | "unpromoted" | "metadata_corrected",
  before: {...}, after: {...},
  timestamp,
  ip:    "1.2.3.4",
  user_agent: "..."
}
```

Append-only · indexed by `import_id`, `actor_user_id`, `timestamp`. Powers HR/legal audit reports.

---

## 3 · Single Ingestion Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UPLOAD SURFACES                           │
│  HR Portal (HR docs)  ·  Safety Portal (Safety docs)        │
│  Admin Portal (bulk / repair / oversight)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         POST /api/legacy-imports/upload (multi-file)         │
│  • RBAC checks (origin portal vs. document_type)             │
│  • sha256 dedupe check                                       │
│  • R2 upload (chunked) → returns blob URL                    │
│  • Creates legacy_imports row · status="uploaded"            │
│  • Schedules OCR job (background)                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              OCR + EXTRACTION (async worker)                 │
│  • Pulls blob from R2                                        │
│  • Calls Claude Vision (per §6)                              │
│  • Updates ocr.* + matches.*                                 │
│  • status → "needs_review"                                   │
│  • On failure → status="ocr_failed" + error reason           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│        RECONCILIATION DASHBOARD (HR / Safety / Admin)        │
│  • Side-by-side: original blob + editable extracted fields   │
│  • Suggested matches with confidence + alternatives          │
│  • Reviewer corrects, confirms matches, decides              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         POST /api/legacy-imports/{id}/approve                │
│  • require_admin_strict OR appropriate HR/Safety token       │
│  • Validates required fields present                         │
│  • PROMOTES to live collection (same-collection contract)    │
│  • Writes audit row                                          │
│  • Returns promoted_record_id                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│       LIVE OPERATIONAL SYSTEMS (no code change required)     │
│  Termination accountability  ·  Expiration dashboards         │
│  Employee timeline  ·  Compliance reports  ·  HR history     │
└─────────────────────────────────────────────────────────────┘
```

**Critical:** the pipeline is a **finite-state machine**. No state skips ahead. No external code path can promote a `legacy_imports` row without going through `/approve`.

---

## 4 · RBAC · Upload Ownership Model

| Document type | Upload portal | Reviewer role(s) | Notes |
|---|---|---|---|
| Equipment Checkout | Safety + HR | Safety / Admin | Safety owns equipment accountability; HR uploads when found in onboarding files |
| Training Record | Safety | Safety / Admin | Safety owns training |
| OSHA Card | Safety | Safety / Admin | |
| Toolbox Talk | Safety | Safety / Admin | |
| Fit Test | Safety | Safety / Admin | |
| Safety Orientation | Safety + HR | Safety / Admin | Often found in onboarding packets |
| Certification | Safety + HR | Safety / HR / Admin | Depends on cert type |
| Medical Card / CDL | HR | HR / Admin | PHI sensitivity → HR-only |
| Signed Acknowledgement | HR | HR / Admin | |
| Write-Up / Discipline | HR | HR / Admin | Sensitive — HR scope |
| Onboarding Packet | HR | HR / Admin | |
| Licensing | HR | HR / Admin | |
| HR Record (other) | HR | HR / Admin | |
| Qualification Record | Safety + HR | Safety / HR / Admin | |
| Unknown (classifier-low) | Admin | Admin | Routed to Admin for reclassification |

**PM portals: NO upload access** (per operator). Future limited PM intake — if approved later — routes through HR/Safety review queue, never direct promotion. Deferred until **after Phase F**.

**Enforcement:**
- Endpoint `/api/legacy-imports/upload` accepts only HR-token, Safety-token, or Admin-token (strict).
- Upload payload must include `document_type`; backend validates `(upload_portal, document_type)` is in the allow-list above.
- `/api/legacy-imports/{id}/approve` validates the approver's role matches the reviewer table for that document type.
- `upload_portal` field on the legacy_imports row is **immutable** after creation (only Admin can override via a "Re-route to other portal" repair workflow that writes an audit row).

---

## 5 · Reconciliation Dashboard UX

### 5.1 Routing
- **HR Portal** → `/hr/legacy-imports` — Only `upload_portal: "hr"` rows
- **Safety Portal** → `/safety/legacy-imports` — Only `upload_portal: "safety"` rows
- **Admin Portal** → `/admin/legacy-imports` — All rows + repair workflows

### 5.2 Sections (left rail)
| Section | Query |
|---|---|
| Pending Review | `status: "needs_review"`, ordered by `created_at` |
| Low Confidence | `status: "needs_review"`, `ocr.confidence < 0.7` |
| Requires Employee Match | `matches.employee.confidence < 0.7` |
| Requires Equipment Match | `matches.equipment.confidence < 0.7` |
| Duplicate Suspected | `matches.duplicate_of != null` |
| OCR Failed | `status: "ocr_failed"` |
| Approved (last 30d) | `status: "promoted"` |
| Rejected (last 30d) | `status: "rejected"` |

### 5.3 Per-row review modal layout
```
╔═══════════════════════════════════════════════════════════╗
║  ORIGINAL DOCUMENT       │  EXTRACTED FIELDS               ║
║  ┌─────────────────────┐ │  Employee Name: [Jake Smith  ] ║
║  │                     │ │  ☆ Match: Jake Smith (0.92)    ║
║  │   PDF preview       │ │  ○ Alt: Jake Smithson (0.51)   ║
║  │   (zoom · pan)      │ │                                 ║
║  │                     │ │  Equipment: [Hilti TE-3000   ] ║
║  │                     │ │  ☆ Match: Hilti TE-3000 (0.88) ║
║  └─────────────────────┘ │  Serial: [SN-48201          ]   ║
║                          │  Issue Date: [2019-03-15    ]   ║
║                          │  Return Date: [— blank —    ]   ║
║                          │  ⚠️ Outstanding (no return)     ║
║                          │                                 ║
║                          │  OCR confidence: 0.87           ║
║                          │  Notes: [optional reviewer notes]║
║                          │                                 ║
║                          │  [ REJECT ]   [ APPROVE & IMPORT]║
╚═══════════════════════════════════════════════════════════╝
```

All extracted fields are **editable** by the reviewer. Approve button is **disabled** until required fields (per doc type) are non-empty. Approve fires `/api/legacy-imports/{id}/approve` with the reviewer's final field values (which override OCR values).

### 5.4 Bulk operations
- Admin-only · "Approve N rows where confidence ≥ 0.95 and no duplicate suspected"
- Always confirmed twice · always writes per-row audit · never operates on >50 rows in one batch

---

## 6 · OCR / Extraction Strategy

### 6.1 Provider recommendation: **Claude Sonnet 4.5 Vision** (via Emergent LLM key · already in stack)

**Rationale:**
- Already integrated (iter120 auto-translate path uses Claude Haiku 4.5)
- Multi-modal vision in one call: image → structured JSON
- No new vendor relationship · no new SDK · no new keys
- Excellent on handwritten + low-quality scans relative to traditional OCR
- Cost: ~$0.003 per page at Sonnet rates · ~$0.0006 at Haiku rates
- For an estimated 5,000-document backlog: **$3-15 total OCR spend** over the lifetime of the import campaign

**Why not Textract / Document AI / Tesseract:**
- New vendor + new credentials + new SDK + new failure modes
- Textract handwriting recognition not meaningfully better at this scale
- Tesseract is free but ~30% worse on phone-camera scans and handwriting
- Decision rule: **start with Claude Vision. Only if real-field failure rate >15% on a given doc type, evaluate a specialized OCR fallback for that type.**

### 6.2 Extraction contract per document type

Each document type has a **typed extractor** with a known schema. Example:

```python
EXTRACTORS = {
    "equipment_checkout": EquipmentCheckoutExtractor,
    "osha_card": OshaCardExtractor,
    # …
}

class EquipmentCheckoutExtractor:
    fields = ["employee_name", "employee_id", "equipment_name",
              "serial_number", "asset_id", "issue_date",
              "return_date", "project_number", "supervisor_name",
              "signatures_present"]
    required = ["employee_name", "equipment_name", "issue_date"]
    prompt   = """You are reading a paper equipment-checkout form…"""
```

The extractor sends one Claude Vision call per upload with the form image attached + a strictly-templated JSON schema in the system prompt. Response is parsed; missing fields are flagged for review.

### 6.3 Confidence calculation

- Per-field confidence: Claude Vision returns a 0.0–1.0 score per field (in the structured response).
- Overall document confidence = harmonic mean of required-field confidences.
- Classifier confidence: separate Claude call (or first part of extractor) that confirms `document_type`. If <0.6, route to Admin "Unknown" queue.

### 6.4 Failure handling

| Failure | Behavior |
|---|---|
| OCR call timeout / rate-limit | Retry up to 3× with exponential backoff; on final fail, status=`ocr_failed` |
| Parser cannot parse Claude response as JSON | status=`ocr_failed`, error=`malformed_response`, raw_text saved for manual rescue |
| Required fields all empty | status=`needs_review`, flagged "manual entry required" — reviewer fills fields themselves; the OCR pass is not a hard gate to promotion |
| Document is illegible | Reviewer can still reject with reason=`illegible` and re-upload a better scan |

**Critical:** the system **never** discards an import because OCR failed. Manual field entry is always available. OCR is an accelerator, not a gatekeeper.

---

## 7 · Matching Engine Design

### 7.1 Employee matching

**Inputs:** extracted `employee_name`, optional `employee_id`, optional last-4-of-SSN.

**Algorithm:**
1. If `employee_id` extracted with confidence ≥0.85 → exact-match on `employees.employee_id` → confidence 1.0 if found.
2. Else fuzzy-match `employee_name` against `employees.name` using normalized Levenshtein + soundex.
3. Boost score if `extracted_date` falls within employee's `hire_date…termination_date` window.
4. Penalize score if multiple employees share a similar name (ambiguity flag).
5. Return top 5 alternatives + confidence per alternative.

### 7.2 Equipment matching

**Inputs:** extracted `equipment_name`, `serial_number`, `asset_id`.

**Algorithm:**
1. `serial_number` exact → confidence 1.0
2. `asset_id` exact → confidence 0.95
3. Fuzzy `equipment_name` against `equipment_master.name` → confidence 0.5–0.9
4. If 0 matches and `equipment_name` is non-empty → flag "Possible new equipment — verify and add to master" (Admin tab for adding new equipment)

### 7.3 Duplicate detection

**Per doc type, compute a content hash:**
- Equipment Checkout: `sha256(employee_id + equipment_serial + issue_date)`
- Training Record: `sha256(employee_id + training_title + completion_date)`
- OSHA Card: `sha256(employee_id + osha_type + issue_date)`

**On upload:**
- Check if any existing **promoted** record in the destination collection has the same content hash → `matches.duplicate_of` populated, status=`needs_review` with "Duplicate Suspected" flag.
- Reviewer decides: reject as duplicate, OR confirm not-a-duplicate (rare — same training day, two different sessions).

### 7.4 Confidence thresholds (defaults, env-tunable)

| Threshold | Default | Behavior |
|---|---|---|
| `EMPLOYEE_MATCH_HIGH` | 0.85 | Auto-suggest as the primary match |
| `EMPLOYEE_MATCH_MEDIUM` | 0.60 | Show as alternative; require explicit confirmation |
| `EMPLOYEE_MATCH_LOW` | <0.60 | Flag as "Requires Employee Match" |
| `EQUIPMENT_MATCH_HIGH` | 0.85 | Auto-suggest |
| `EQUIPMENT_MATCH_LOW` | <0.60 | Flag |
| `OCR_CONFIDENCE_LOW` | <0.70 | "Low Confidence" queue |
| `CLASSIFIER_CONFIDENCE` | <0.60 | Route to Admin "Unknown" |

---

## 8 · Operational Integration Map

**This is the most important table in the document.** For each supported document type, exactly which live collection it promotes into and exactly which operational workflows it then participates in.

| Document Type | Promotes To | Termination Workflow | Expiration Tracking | Compliance Dashboard | Employee Timeline | HR History |
|---|---|---|---|---|---|---|
| Equipment Checkout | `equipment_checkouts` | ✅ Flagged with live checkouts | — | — | ✅ | — |
| Training Record | `training_records` | — | ✅ if `expiration_date` set | ✅ | ✅ | — |
| OSHA Card | `training_records` (osha_type subtype) | — | ✅ (3-yr cycle) | ✅ | ✅ | — |
| Toolbox Talk | `meetings` (kind=`toolbox_talk`, source=`legacy_imported`) | — | — | ✅ count toward attendance | ✅ | — |
| Fit Test | `safety_qualifications` | — | ✅ (1-yr cycle) | ✅ | ✅ | — |
| Medical Card | `hr_employee_documents` (kind=`medical_card`) | — | ✅ (date-of-exp on card) | — | ✅ | ✅ |
| CDL License | `hr_employee_documents` (kind=`cdl`) | — | ✅ (expiration) | — | ✅ | ✅ |
| Certification | `safety_qualifications` (kind=cert) | — | ✅ if dated | ✅ | ✅ | — |
| Safety Orientation | `safety_qualifications` (kind=`orientation`) | — | — | ✅ first-completed | ✅ | — |
| Signed Acknowledgement | `hr_acknowledgements` | — | — | — | ✅ | ✅ |
| Write-Up / Discipline | `hr_disciplinary_actions` | — | — | — | ✅ | ✅ |
| Onboarding Packet | `hr_employee_documents` (kind=`onboarding`) | — | — | — | ✅ | ✅ |
| HR Record (generic) | `hr_employee_documents` | — | — | — | ✅ | ✅ |
| Licensing | `hr_employee_documents` (kind=`license`) | — | ✅ if dated | — | ✅ | ✅ |
| Qualification Record | `safety_qualifications` | — | ✅ if dated | ✅ | ✅ | — |

**Read this carefully:**
- The Termination Workflow only needs to query `equipment_checkouts WHERE employee_id=X AND return_date IS NULL` — and it will automatically pick up imported legacy checkouts because they live in the same collection with the same field names. **Zero changes to the termination code path.**
- Same principle for every other column. The Expiration Tracking cron already scans `training_records WHERE expiration_date < now()+60d` — it will pick up imported OSHA cards automatically.
- The `source: "legacy_imported"` field is purely informational — every dashboard / list view can optionally show a badge ("Legacy" pill) but the operational logic doesn't branch on it.

---

## 9 · Employee Lifecycle Integration Map

When an employee is hired / terminated / suspended / promoted, the system must consult their full operational history.

| Lifecycle Event | Query change required | Imported records participate |
|---|---|---|
| **Hire** | No change | (No imported records yet for new hire) |
| **Termination** | No change — `equipment_checkouts WHERE employee_id=X AND return_date IS NULL` already covers both | ✅ Outstanding legacy checkouts flagged |
| **Recertify** | No change — `training_records WHERE employee_id=X AND kind=X` already covers both | ✅ Last imported cert is visible |
| **Audit / Investigation** | No change — employee timeline already queries all collections by `employee_id` | ✅ Full timeline (live + imported) |
| **Disciplinary review** | No change — `hr_disciplinary_actions WHERE employee_id=X` already covers both | ✅ Historical write-ups visible |
| **Project assignment qualifications check** | No change — `safety_qualifications WHERE employee_id=X` already covers both | ✅ Imported certs satisfy the qualification |

**This is the operational continuity payoff.** The cost of building it correctly once (same-collection promotion) is repaid every time a workflow runs.

---

## 10 · Equipment Accountability Integration Map

Specific to the termination/accountability workflow operator highlighted ("Jake terminated with 2 live + 3 legacy checkouts → workflow must flag all 5"):

**Existing query (pseudocode):**
```python
async def outstanding_equipment_for(employee_id):
    return await db.equipment_checkouts.find({
        "employee_id": employee_id,
        "return_date": {"$in": [None, ""]}
    }).to_list(None)
```

**Required query change: NONE.** As long as promoted legacy checkouts go into `equipment_checkouts` with `employee_id` populated and `return_date` empty (operator may need to mark "returned but no record of date" via reviewer correction), the existing query picks them up.

**Required UI change: small.** Add a "Legacy" pill next to checkouts where `source: "legacy_imported"`, plus a clickable link to view the original scan. ~10 lines of frontend.

---

## 11 · Imported Record Metadata · Required Display

Operator's brief explicitly requires every imported record visibly displays:

| Field | Display location |
|---|---|
| Source: Legacy Imported | Pill badge next to record in every list view |
| Imported By | Detail view + audit log |
| Imported At | Detail view + sorting |
| OCR Confidence | Detail view (Admin-only by default · Safety/HR via env flag) |
| Review/Approval User | Detail view + audit log |
| Original File | Always linkable from detail view (R2 signed URL · short TTL) |
| Import Notes | Detail view |
| Extraction Method | Detail view + audit log |
| Import Batch ID | Audit reports + Admin batch view |

**Implementation pattern:** A reusable `<LegacyImportBadge import={record.legacy_import}/>` component renders the pill + opens a small popover with all fields. Same component used across every collection's list view.

---

## 12 · Source Evidence Storage (R2)

### 12.1 Bucket structure
```
masci-legacy-imports/
  ├── 2026/05/{batch_id}/{import_id}.pdf
  ├── 2026/05/{batch_id}/{import_id}.jpg
  └── ...
```

### 12.2 Access controls
- Bucket is **private** (no anonymous reads).
- Access via signed URLs with **5-minute TTL**, generated by the backend on demand.
- Signed-URL generation is gated by RBAC: only the upload-portal + reviewer + Admin can request a signed URL for a given import.

### 12.3 Immutability
- Object versioning enabled in R2.
- Lifecycle policy: **never delete**. Move to colder tier after 1 year if cost becomes meaningful.
- Audit row written on every signed-URL issuance (HR/legal can ask "who accessed this scan and when").

### 12.4 Storage cost projection
- Assumption: **5,000 historical documents** · average 500 KB after PDF compression
- Total: **~2.5 GB**
- R2 cost: **~$0.04/month** (well within stabilization-phase budget)
- Even at 10× growth (50,000 docs / 25 GB) → **$0.40/month** — negligible

---

## 13 · Search · Visibility Integration

Operator brief: imported records must appear in employee, equipment, HR, Safety, compliance, expiration, flag, and timeline searches.

**Implementation rule:** every existing search that filters by `employee_id` (or `equipment_id`, `serial_number`, etc.) **automatically** sees imported records — because they live in the same collections.

**One add-on:** an Admin-only "Source filter" toggle on big list views — `All / Live Only / Imported Only` — for audits. Default = All. Implementation cost: ~3 lines per list view.

---

## 14 · Governance · Security · Audit Model

| Surface | Control |
|---|---|
| Upload endpoint | RBAC: HR/Safety/Admin token only |
| RBAC matrix enforcement | `(upload_portal, document_type)` whitelist (§4) |
| Approve endpoint | Token role matches reviewer table; reviewer cannot self-approve their own upload unless they are Admin |
| Source files | Private R2 bucket · signed URLs · 5-min TTL · access audited |
| Promotion | Single code path (`legacy_imports.promote()`) · always writes audit row · never callable outside `/approve` endpoint |
| Rollback | Admin-only `POST /api/admin/legacy-imports/{id}/unpromote` — marks promoted record as `archived: true` (does not delete), audit row required |
| Rejection | Stores reject_reason · scans **never** deleted from R2 (legal preservation) |
| Audit log retention | Indefinite · `legacy_import_audit` is append-only · never updated |
| Dispute workflow | Detail view shows full audit trail · HR/legal can pull a complete chain-of-custody report |
| Test data isolation | Same hygiene as iter246 F3: production excludes `.test` / `@example.*` recipients from any digest of import activity |

**Anti-self-approval guard:** the same human cannot upload + approve the same record (except Admin role, who has explicit override authority — logged in audit). This is HR/legal best-practice for separation of duties.

---

## 15 · Storage · Performance Plan

### 15.1 Storage growth
- Year 1 (backlog ingestion): ~2-3 GB
- Steady state (ongoing operational uploads): ~50 MB/month
- 5-year horizon: <10 GB

### 15.2 OCR processing throughput
- Claude Vision call: ~3-8 seconds per page
- Async background worker (one or two concurrent calls) handles the load fine
- Backlog batch of 100 docs: completes overnight
- No queue infrastructure needed (Mongo `status="uploaded"` row IS the queue) · same pattern as iter120 safety_digest_history if it existed · same pattern as existing auto_email queue

### 15.3 Mongo load
- Negligible · `legacy_imports` will hold ~5K-50K rows over the system's lifetime · all indexed
- No impact on existing collection performance

### 15.4 Backup
- `legacy_imports` + `legacy_import_audit` join the existing nightly Mongo backup
- R2 objects are durable by design (Cloudflare 11×9 durability) · no additional backup needed
- Existing MASCI archive zip can include the R2 manifest (object keys + sha256) so a complete operational snapshot is portable

---

## 16 · Phased Rollout Plan

The most important section. Operator-stated principle: **prove one document type end-to-end before any expansion**.

### Phase A · Foundation (~3-5 days · code + infra)
- `legacy_imports` collection + indexes
- `legacy_import_audit` collection
- R2 bucket + signed-URL helper
- RBAC matrix enforcement helper
- Generic `/api/legacy-imports/upload` endpoint
- Background OCR worker scaffold (no Claude call yet · uses a stub)
- Admin-only `/admin/legacy-imports` empty dashboard
- Tests · audit · pre-deploy gate

**Deliverable:** Upload arrives, lands in `legacy_imports` with `status="needs_review"` (stub OCR), reviewer can manually fill all fields, approve promotes to a stub destination collection (test).

### Phase B · First document type: Equipment Checkout (~5-7 days)
- `EquipmentCheckoutExtractor` (Claude Vision prompt + JSON schema)
- Matching engine for employee + equipment
- Reconciliation modal UI (one type, one screen)
- Promote path → `equipment_checkouts` with `source: "legacy_imported"`
- "Legacy" badge in existing Equipment Accountability list views
- Termination workflow verified to surface legacy + live checkouts in one query
- 50-document pilot batch · operator approves all manually · validates real-world feel

**Why Equipment Checkout first:** highest operational continuity payoff (termination workflow), clearest field structure (date + employee + equipment), most observable success criteria.

### Phase C · OSHA Cards (~3-4 days)
- `OshaCardExtractor`
- Promote path → `training_records` (kind=`osha`)
- Expiration tracking automatically picks them up
- Compliance dashboard automatically picks them up

**Why OSHA Cards second:** simple field structure, high compliance value, clear expiration semantics.

### Phase D · Reconciliation dashboard polish (~3-5 days)
- All queue sections wired (Low Confidence, Requires Match, Duplicate Suspected, etc.)
- Admin bulk-approve workflow (with all guardrails)
- Audit report endpoint + admin export
- Repair workflows (re-route portal, unpromote, re-OCR)

### Phase E · Bulk batch upload (~2-3 days)
- HR/Safety can drag-drop 20-100 PDFs at once
- Batch ID groups them
- Progress UI · per-row OCR status

### Phase F · Remaining document types (~1-2 days each · ~10-14 days total)
- Add extractors one at a time:
  Toolbox Talks · Fit Tests · Medical Cards · CDL · Certifications · Safety Orientation · Acknowledgements · Write-Ups · Onboarding Packets · HR Records · Licensing · Qualifications
- Each ships independently with its own pilot batch

### Phase G · Future · PM-side intake (DEFERRED · operator decides later)
- PM can upload project-specific docs · ROUTED to HR/Safety review queue
- PM never promotes directly
- Phase G is not on the current roadmap; only listed for completeness

### Cumulative timeline
- Phases A+B+C+D: **~3 weeks of focused dev** (one document type proven operational with full reconciliation)
- Phases E+F: **~3 additional weeks** for full coverage
- **Hard expectation: do not start Phase B until Phase A is in production for >7 days with zero defects.** Same cadence for B→C→D.

---

## 17 · Risk Assessment

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **OCR hallucination** (Claude invents a field value) | Medium | High if undetected | Mandatory human review · field-level confidence display · "no record exists" reject path |
| **Duplicate creation** (same scan uploaded twice) | High over time | Medium (cleanup work) | sha256 dedupe on upload · content-hash dedupe on promote · "Duplicate Suspected" queue |
| **Wrong employee/equipment match approved by tired reviewer** | Medium | High (HR dispute) | Confidence colors · alternatives always visible · audit log lets HR/legal trace + reverse |
| **Imported record leaks into wrong portal's view** | Low | Medium | Same-collection promotion + RBAC at read time (existing iter241/242 invariants apply) |
| **OCR cost spike** | Very low | Low | Cost projection ($3-15 total) is well-bounded · per-call logging |
| **R2 storage growth out of control** | Very low | Very low | <10 GB over 5 years · cost <$0.20/mo |
| **Legal/HR challenge to imported-record validity** | Low but consequential | High | Immutable source evidence + audit log + reviewer signature + chain-of-custody report |
| **Reviewer self-approval** (uploader = approver) | Medium | Medium | §14 anti-self-approval guard (Admin override only, logged) |
| **Termination workflow misses an imported checkout** | Low (same-collection design eliminates) | Critical | Phase B explicit verification test: terminate a test employee with mixed live+imported checkouts → workflow returns all of them |
| **Scope creep into "AI document magic"** | Medium under feature pressure | High | This document's §1 philosophy section · phased rollout discipline · "one doc type proven before next" rule |
| **PM portal pressure to upload directly** | Medium over time | Medium | Phase G deferred · explicit operator gate · routing-only model |
| **OCR worker crashes silently** | Low | Medium | Status-based queue means a crashed worker leaves rows in `ocr_in_progress`; stale-sweeper cron resets to `uploaded` after 10 minutes |
| **Confidence threshold drift** (operators auto-trust 0.9 without looking) | Medium | Medium | UX shows the original scan side-by-side **always** — reviewer must literally see the source before approving · no "approve from list" without opening |

---

## 18 · UI / UX Flow Concepts

### 18.1 Upload screen (HR + Safety + Admin)
- Drag-drop zone (multi-file)
- Document-type picker (defaults to "Auto-classify" — Claude infers)
- Optional batch label
- "Upload" button → progress bar → toast on completion
- Auto-redirects to that batch's review queue

### 18.2 Reconciliation list (per portal)
- Left rail: queue sections
- Center: card-per-import list
- Each card shows: thumbnail · doc type · uploaded by · OCR confidence pill · suggested match name · age
- Click → opens reconciliation modal

### 18.3 Reconciliation modal (§5.3 layout)
- Side-by-side scan + editable fields
- Suggested matches with confidence pills (green ≥0.85 · amber 0.6-0.85 · red <0.6)
- "Approve & Import" disabled until required fields filled
- "Reject" requires reason

### 18.4 Promoted-record detail view (in existing portals)
- Existing detail view + new `LegacyImportBadge` showing source metadata
- "View original scan" button → opens R2 signed URL in new tab
- "View import audit trail" → Admin-only popover

### 18.5 Admin batch view
- Table of batches · per-batch progress bars · click → batch's import list
- Bulk operations (approve/reject) with confirmation

---

## 19 · Open Decisions for Operator

These need explicit operator answers before Phase A starts:

1. **R2 bucket name + region** — confirm operator wants a dedicated bucket `masci-legacy-imports` or reuse existing MASCI archive bucket.
2. **Anti-self-approval rule** — confirm uploader ≠ approver (Admin override permitted)?
3. **Default classifier behavior on unknown** — route to Admin queue (proposed) OR auto-reject with operator-readable error?
4. **OCR provider final call** — Claude Sonnet vs. Haiku (Sonnet = better accuracy on handwriting at 5× cost; Haiku = fine for typed forms)? Recommendation: **start Haiku, fall back to Sonnet on any field-confidence < threshold**.
5. **Phase B pilot batch size** — 50 docs (proposed) · enough to surface real failure modes without overwhelming reviewers.
6. **Reviewer training** — does operator want a one-page reviewer guide + short Loom walkthrough as part of Phase B handoff? (Strongly recommended.)
7. **Imported record "Legacy" pill visibility** — always-on (proposed) vs. opt-in per portal? Operator might want full operator-history view to always show source.
8. **Bulk-approve threshold** — is there ever a case for Admin auto-approving high-confidence rows? (Default proposed: NO. Every row gets eyes.)
9. **Retention policy on rejected uploads** — keep R2 blob forever (proposed) or purge after 90 days?
10. **PM-portal intake (Phase G)** — should it be on the roadmap at all, or permanently HR/Safety-only?

---

## 20 · Anti-Patterns This Architecture Explicitly Avoids

Drawn directly from the operator brief — listed here so future agents/iters can reference them:

- ❌ "AI document magic" — silent extraction → silent record creation
- ❌ Separate parallel collections for imported vs. live records
- ❌ Auto-approval of high-confidence extractions
- ❌ Background promotion of any kind
- ❌ Disconnected archive system (a "documents folder" that no operational workflow consults)
- ❌ Generic file uploader without document-type structure
- ❌ Per-doc-type bespoke importer (everything plugs into ONE pipeline)
- ❌ Allowing PM portals to upload directly into operational collections
- ❌ Destructive conversion (always keep the original scan)
- ❌ Indistinguishable imported records (`source` discriminator is required, always)
- ❌ LMS-style learning system (this is NOT a training platform)
- ❌ Speculative "smart system" behavior (every promotion is explicit, audited, human-driven)

---

## 21 · Stabilization-Compatibility Statement

This entire system can be built without disturbing **any** existing iter215/iter236/iter238/iter239/iter242/iter243/iter245/iter246/iter247 invariant. Specifically:

- iter238 email subject system: unchanged (Phase B may add a new event kind like `legacy_import_promoted` with its own `[MASCI · IMPORT]` prefix · slot-into existing prefix registry)
- iter239 branding: unchanged
- iter242 PO authority boundary: unchanged
- iter243 Safety welcome-email parity: unchanged
- iter245 vendor consolidation: unchanged · imported equipment-checkout vendor field could optionally reuse `/api/suppliers`
- iter246 F3 PO digest: unchanged
- iter247 F1 admin login ES + P1-A `dry_run` guard + P1-B AccessDenied ES: unchanged
- Pre-deploy verification gate: all new endpoints automatically picked up by existing anon-RBAC sweep
- Existing equipment-accountability / termination / expiration / compliance code paths: zero changes required (same-collection design)

---

## 22 · Next Step (Operator Decision)

**Before Phase A begins, operator should:**

1. Read this document and mark any disagreements / changes
2. Answer the 10 Open Decisions in §19
3. Confirm phased rollout cadence (one doc type proven before next)
4. Confirm OCR provider choice (Claude Vision recommended)
5. Approve / adjust the operational integration map (§8 + §9 + §10)
6. Confirm the anti-self-approval rule (§14)

**No code work begins until operator explicit go-ahead on Phase A.**

Per stabilization posture: **this is a planning artifact only.** The next iter that implements anything from this document should be small (Phase A scope) and pass through the same pre-deploy gate + operator-acknowledge cycle as iter246 / iter247.

---

*Architecture proposal authored by E1 · iter248 planning phase · 2026-05-19*
*Document is a working draft — expected to evolve as operator surfaces requirements during real-field reviewer trials in Phase B.*
