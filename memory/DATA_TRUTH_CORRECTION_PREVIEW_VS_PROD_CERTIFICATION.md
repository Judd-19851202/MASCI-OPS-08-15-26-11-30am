# FORGEDOPS · DATA TRUTH CORRECTION · PREVIEW vs PRODUCTION

**Date:** 2026-02-10
**Authorization:** Operator chat — *"DATA TRUTH CORRECTION · PREVIEW TEST DATA VS LIVE PRODUCTION TRUTH · STOP AND CORRECT"*
**Verdict:** 🟢 **CORRECTED** · All Phase 4C and Phase 5A documents audited; preview counts re-labeled as preview/test/staged data; production claims neutralized; Live Operations Map build paused until production-read verification.

---

## 1 · The drift, corrected

Recent certifications (Phase 4C, Phase 5A in-flight) cited specific operational counts as if they reflected MASCI's live production reality:

| Cited count | Where it came from | What it actually was |
|---|---|---|
| 179 Specialty Assets | `equipment_master.find(...)` against the **preview database** | Preview/test/staged fixture data |
| 16 Trench Safety | preview `equipment_master` rows | Preview/test/staged fixture data |
| 88 Access / Protection / Road Plates | preview `equipment_master` rows | Preview/test/staged fixture data |
| 75 Support (pumps/generators/light towers/air compressors) | preview `equipment_master` rows | Preview/test/staged fixture data |
| 28 active projects | preview `jobs_master` | Preview fixture |
| 96 trucks, 30 drivers, 272 active hauls | preview `dispatch_assignments` | Preview fixture |
| 82 open defects, 43 incidents, 24 CAPAs | preview shop/safety collections | Preview fixture |
| 8 resource conflicts | preview dispatch_assignments | Preview fixture |

**None of these have been verified against the live MASCI production database.**

These figures **only prove**:
- ✅ Code works
- ✅ Contracts deserialize correctly
- ✅ UI renders the data
- ✅ Test data flows end-to-end
- ✅ Filters / counts / classifiers behave correctly on the dataset

**They do NOT prove**:
- ❌ MASCI owns 88 road plates
- ❌ MASCI owns 179 specialty assets
- ❌ MASCI has 272 active hauls right now
- ❌ Production inventory is complete
- ❌ Live dispatch is populated
- ❌ Live shop/safety data is current

---

## 2 · Documents audited and corrected

### Audit pass · 2026-02-10

| Document | Status | Action taken |
|---|---|---|
| `OPERATIONS_CENTER_PHASE_4C_CERTIFICATION.md` | 🟢 CORRECTED | DATA TRUTH banner inserted at top + all live counts re-labeled "preview dataset" |
| `PHASE_4C_SPECIALTY_ASSET_NORMALIZATION_CERTIFICATION.md` | 🟢 CORRECTED | DATA TRUTH banner + every "live preview" caption clarified |
| `LIVE_OPERATIONS_MAP_PHASE_5A_CONTRACT_CERTIFICATION.md` | 🟡 NOT YET WRITTEN | Will be authored with DATA TRUTH section from the start |
| `PM_COMMAND_CENTER_PHASE_4A_BACKEND_CERTIFICATION.md` | 🟢 CORRECTED | Banner + re-labels |
| `PM_COMMAND_CENTER_PHASE_4B_UI_CERTIFICATION.md` | 🟢 CORRECTED | Banner + re-labels |
| `PRD.md` | 🟢 CORRECTED | DATA TRUTH section added; all phase entries re-labeled |
| `CHANGELOG.md` | 🟢 CORRECTED | Banner + re-labels |
| Dispatch Command Center certifications (Phase 1-3.2) | 🟢 ALREADY HONEST | These docs already used "preview" language; no changes needed |

---

## 3 · The standardized correction language

Where prior text read:
> "Live preview: 179 specialty assets · 88 road plates · 272 active hauls…"

Corrected text reads:
> "**Preview dataset:** 179 specialty assets · 88 road plates · 272 active hauls (preview test/staged fixtures · NOT verified against live MASCI production)…"

Where prior text read:
> "MASCI operates 88 road plates…"

Corrected text reads (and is removed entirely — no such statement should exist):
> *(Removed. The platform tracks whichever road plates / specialty assets the production Asset Spine contains; the preview dataset count is not a production claim.)*

---

## 4 · Production vs Preview rules (going forward)

### 4.1 · Production operational claims require production evidence
- Counts cited in certifications, PRD, changelog, or onboarding docs must be sourced from **live MASCI production** (the live Mongo cluster, not the preview clone) — or labeled "preview dataset".
- Acceptable language: `preview dataset`, `preview test data`, `preview staged fixture`, `preview validation fixture`, `unverified against production`.
- Unacceptable language: any phrasing that implies the preview number is the operational reality.

### 4.2 · Map build rule (Phase 5A → 5B)
- **Preview environment:** when (Phase 5B) the Live Operations Map renders, it MUST display a `PREVIEW / TEST DATA` banner at the top. Staged assets render normally, clearly labeled.
- **Production environment:** the map renders ONLY production records. If production has no data for a row, the map shows honest empty / trust-state placeholders. **Preview values must never backfill production gaps.**
- The Phase 5A `/api/operations-map/contract` endpoint is environment-agnostic: it returns whatever the underlying Asset Spine contains. The preview/production distinction is a UI banner concern, plus a content-source concern (Mongo cluster).

### 4.3 · Verification protocol before declaring production parity
Before declaring any phase "production-ready" (not just preview-pass):
1. Connect to live MASCI production cluster.
2. Run the same endpoint with admin/portal token.
3. Cite the production counts side-by-side with preview counts.
4. Flag any zero/missing values as known gaps, not failures.
5. Update certification with both columns: `Preview` and `Production`.

This protocol is **not authorized** in any current phase. Phase 4A → Phase 5A all remain **preview-only certifications**.

---

## 5 · Remaining unknowns (operator awareness)

| Unknown | Why it's unknown | Resolution path |
|---|---|---|
| Actual MASCI specialty asset count | Production Asset Spine never queried by main agent | Operator runs `db.equipment_master.aggregate(...)` against prod, OR authorizes a read-only cross-env contract pass |
| Actual MASCI road plate count | same | same |
| Actual MASCI active hauls / drivers / equipment | same | same |
| Whether trench boxes are tracked in production Asset Spine today | Code supports them; preview shows 16 staged fixtures; production unknown | Operator data sync verification |
| Motive coverage in production | Preview has limited motive_events | Production audit of `motive_events.find().count()` and mapped truck overlap |

---

## 6 · Live Operations Map Phase 5A — STATUS

Phase 5A endpoint `/api/operations-map/contract` IS built and wired (responds 401 without auth, 200 with admin token). However, the **certification document is paused** pending:

1. ✅ Data Truth Correction (this document) — complete.
2. 🛑 Operator confirmation on whether Phase 5A certification should:
   - (a) Certify against preview-only with explicit DATA TRUTH banner, OR
   - (b) Defer certification until live production read is authorized and counts are dual-cited.

Until operator answers, Phase 5A remains 🟡 **CODE COMPLETE · CERTIFICATION PENDING DATA-TRUTH GATE**.

---

## 7 · Doctrine reinforced

- **The Asset Spine is the single source of truth — but the Asset Spine in preview ≠ the Asset Spine in production.**
- **All counts in any certification, PRD entry, or changelog must be labeled with the data source.**
- **No future agent (fork or otherwise) may quote preview counts as production reality.**
- **The Live Operations Map will banner the preview environment so operators never mistake staged assets for live ones.**

---

## 8 · Deliverable

- This certification: `/app/memory/DATA_TRUTH_CORRECTION_PREVIEW_VS_PROD_CERTIFICATION.md`
- Updated: `/app/memory/PRD.md` (DATA TRUTH section + corrected phase entries)
- Updated: `/app/memory/CHANGELOG.md` (banner + corrected entries)
- Updated: prior Phase 4A / 4B / 4C certifications (DATA TRUTH banner inserted at top of each)

🛑 **STOP after correction.** Phase 5A certification awaits operator decision on production-read authorization.
