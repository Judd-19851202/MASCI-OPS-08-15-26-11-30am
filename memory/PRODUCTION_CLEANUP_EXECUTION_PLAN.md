# Production Cleanup Execution Plan · Critical Fix Sprint 1A · Phase 2

**Batch:** OMEGA Critical Fix Sprint 1A · Phase 2
**Date:** 2026-05-31
**Scope:** Categorized execution plan for production hygiene remediation. Every item carries exact record count · collections affected · rollback strategy · verification strategy. **NOTHING EXECUTED.**

---

## 1 · Categorization

| Category | Items | Records affected | Effort |
|---|---|---|---|
| **P0 · Immediate Cleanup** | 4 | ~13 records | ~30 min DB-only |
| **P1 · Data Integrity** | 3 | ~16 records | ~30 min DB-only |
| **P2 · UX / Messaging** | 1 | 1 frontend page (HR header repro) | 1-2 d (operator screenshot first) |
| **P3 · Documentation** | 2 | 2 markdown docs | 30 min |

---

## 2 · P0 · Immediate Cleanup (4 items · ~13 records)

### 2.1 · P0-1 · Deactivate test FL user

**Records:** 1 (`db.field_leadership_users.d805f3d4`)

**Collections affected:** `field_leadership_users`

**Operation:**
```javascript
db.field_leadership_users.update_one(
  {id: "d805f3d4-76c8-480e-a268-b64b274e059c"},
  {$set: {is_active: false, _deactivated_at: ISODate(), _deactivated_reason: "Sprint 1A · test account hardening"}}
)
```

**Rollback:** `$set: {is_active: true}` on the same record.

**Verification:**
```bash
curl -X POST https://mascidocs.com/api/auth/multi-login \
  -H "Content-Type: application/json" \
  -d '{"email":"fieldleader@mascigc.com","password":"FieldLead2026!"}'
# Expected: 401 / "user inactive" instead of 200 with portal tokens
```

---

### 2.2 · P0-2 · Delete the test incident + dedupe `doc_id='INC-2026-00001'`

**Records:** 1 (`db.incidents.d9626eeb`)

**Collections affected:** `incidents`

**Sprint 1 P0-B correction:** Sprint 1 recommended promoting `d9626eeb` to keep `INC-2026-00001`. **THIS IS WRONG.** Sprint 1A discovered `d9626eeb` carries `reported_by="John Smith"` (canary test marker). **Correct action:** DELETE `d9626eeb` (test data). The duplicate doc_id automatically resolves because the surviving incident `566a38dd` keeps `INC-2026-00001`.

**Operation:**
```javascript
db.incidents.delete_one({id: "d9626eeb-37a8-4e55-a5bb-3ea74f46ccd3"})
// alternatively, move to an archived collection first:
// const doc = db.incidents.findOne({id: "d9626eeb-..."})
// db.incidents_archive_sprint1a.insert_one(doc)
// db.incidents.delete_one({id: "d9626eeb-..."})
```

**Rollback:** Restore from the most recent complete-r2 archive (2026-05-31 16:02Z · 24,002 records · contains this incident).

**Verification:**
```javascript
db.incidents.count_documents({})  // expect: 6 (was 7)
db.incidents.aggregate([
  {$group: {_id: "$doc_id", n: {$sum: 1}}},
  {$match: {n: {$gt: 1}}}
])  // expect: 0 results (no duplicates)

// API verification
curl -H "X-Admin-Token: …" https://mascidocs.com/api/admin/command-center/snapshot
// expect: jobs card item count drops by 1 (incident d9626eeb was in JOBS-ISSUE-NO-PATH)
```

---

### 2.3 · P0-3 · Delete 10 abandoned payroll-variance test batches + 7 decisions

**Records:** Up to 17 (10 batches + 7 decisions)

**Collections affected:** `payroll_variance_batches` · `payroll_variance_decisions`

**Operation:**
```javascript
const TEST_BATCH_IDS = [
  "674300c9-0839-408d-a6a8-a06f221c4cc8",
  "48cbc60e-bd33-46ee-99cd-54ba4da65933",
  "6590febb-8fce-469c-a07f-f28b8b26e052",
  "f1371d01-9ecb-4062-bcea-3d318fc5bbcd",
  "76d952ce-7c1b-438b-952c-2d3d9e78efce",
  "f28d4b44-439b-4e63-a1c6-03c3897baac8",
  // + 4 more IDs (ed8ec430, 8b649f92, 2eb4c2d2, d3150925) – full UUIDs to be retrieved at execution time
];
db.payroll_variance_batches.delete_many({id: {$in: TEST_BATCH_IDS}})
db.payroll_variance_decisions.delete_many({batch_id: {$in: TEST_BATCH_IDS}})
```

**Rollback:** Restore from 2026-05-31 16:02Z archive.

**Verification:**
```javascript
db.payroll_variance_batches.count_documents({})  // expect: 0
db.payroll_variance_decisions.count_documents({})  // expect: 0 (if all 7 linked) or remaining un-linked
```

---

### 2.4 · P0-4 · Delete 2 PREVIEW_POSTENV notifications

**Records:** 2

**Collections affected:** `notifications`

**Operation:**
```javascript
db.notifications.delete_many({id: {$in: [
  "64f443d6-350f-4f1f-b057-5a044d8c971b",
  "9ac645f3-1969-42be-b51e-e4fcd3c59fc9"
]}})
```

**Rollback:** Restore from archive.

**Verification:**
```javascript
db.notifications.count_documents({title: {$regex: /PREVIEW_POSTENV/i}})  // expect: 0
```

---

## 3 · P1 · Data Integrity (3 items · ~16 records)

### 3.1 · P1-1 · Rename one of the duplicate `DR-2026-00007`

**Records:** 1

**Collections affected:** `daily_reports`

**Decision required:** Which record keeps the original `doc_id`?

**Operation (operator decides which is the older/canonical):**
```javascript
// Identify older
const records = db.daily_reports.find({doc_id: "DR-2026-00007"}, {id:1, created_at:1}).toArray()
// Promote older; rename newer
db.daily_reports.update_one(
  {id: <newer_id>},
  {$set: {doc_id: "DR-2026-XXXX", _deduped_at: ISODate(), _deduped_from: "DR-2026-00007"}}
)
```

**Rollback:** Reverse the `doc_id` change.

**Verification:** Same aggregation as P0-2.

---

### 3.2 · P1-2 · Backfill 7 incidents to `status="open"`

**Records:** 7

**Collections affected:** `incidents` (or 6 after P0-2)

**Operation:**
```javascript
db.incidents.update_many(
  {status: null},
  {$set: {status: "open", resolution_status: "open", _backfilled_status_at: ISODate()}}
)
// Expected: matched_count=6, modified_count=6 (after P0-2 deletion)
```

**Rollback:** `$set: {status: null, resolution_status: null}` on the same records.

**Verification:**
```javascript
db.incidents.count_documents({status: null})  // expect: 0
```

---

### 3.3 · P1-3 · Backfill 7 `user_directory` rows to `is_active=True`

**Records:** 7

**Collections affected:** `user_directory`

**Operation:**
```javascript
db.user_directory.update_many(
  {is_active: null},
  {$set: {is_active: true, _backfilled_is_active_at: ISODate()}}
)
// Expected: matched_count=7, modified_count=7
```

**Rollback:** `$set: {is_active: null}`.

**Verification:**
```javascript
db.user_directory.count_documents({is_active: null})  // expect: 0
db.user_directory.count_documents({is_active: true})  // expect: 7
```

---

## 4 · P2 · UX / Messaging (1 item)

### 4.1 · P2-1 · HR portal header "empty outlined button" reproduction

**Records:** 0 (no DB write)

**Collections affected:** none

**Operation:**
- Operator visits `https://mascidocs.com/hr/hub` with viewport widths { 360px, 768px, 1024px, 1440px } and captures screenshot of any visibly-empty button.
- Operator reports back with the captured viewport + element data-testid.
- Engineering reproduces + surgical fix.

**Rollback:** n/a

**Verification:** screenshot diff after fix.

---

## 5 · P3 · Documentation (2 items)

### 5.1 · P3-1 · Update `/app/memory/test_credentials.md` to remove `fieldleader@mascigc.com`

After P0-1 ships, edit the file to either delete the FL test-user line OR mark it deactivated.

### 5.2 · P3-2 · Document the doc_id-counter race finding

Add a note to `/app/memory/PRD.md` and create `DOC_ID_COUNTER_DEFECT.md` capturing:
- The two duplicate-doc_id incidents observed (`incidents.INC-2026-00001`, `daily_reports.DR-2026-00007`)
- Suspected root cause (non-atomic `find_one` + `update_one`)
- Recommended fix: use `find_one_and_update(..., {$inc: {seq: 1}}, return_document="after", upsert=True)`

---

## 6 · Combined execution sequence

🟢 **Recommended order:**

1. **DB-only sweep (~60 minutes)** — all P0 + P1 items in a single authorized DB session:
   - P0-1 (FL test user deactivate)
   - P0-2 (delete test incident `d9626eeb`)
   - P0-3 (delete 10 payroll batches + decisions)
   - P0-4 (delete 2 PREVIEW_POSTENV notifications)
   - P1-1 (rename one duplicate DR)
   - P1-2 (backfill 6 incidents status)
   - P1-3 (backfill 7 user_directory `is_active`)

2. **Operator-side actions (parallel)**:
   - P2-1 (HR header screenshot capture)
   - Default-password audit on 5 `user_directory` rows (operator-side; not in scope of this DB sweep)
   - Legacy owner consult (4 `users.role=owner` idle 33+ days)

3. **Documentation (~30 min)**:
   - P3-1 (test_credentials.md update)
   - P3-2 (doc_id counter defect doc)

4. **Verification gates after sweep**:
   - Pillar 1 `/api/admin/accountability/sources` returns 6 sources
   - Pillar 2 `/api/admin/command-center/snapshot` returns 5 cards; pulse reconciles
   - Backup scheduler `alive=true · ticking`
   - `escalation_level=0` across all sampled projections (Pillar 1 invariant)
   - `db.incidents.count_documents({status:null})` = 0
   - `db.user_directory.count_documents({is_active:null})` = 0
   - All duplicate-doc_id aggregations return empty

---

## 7 · Total record impact

| Operation | Records |
|---|---|
| Hard-delete | ~30 (1 incident + 10 batches + 7 decisions + 2 notifications + optional 68 session_activity + optional 24 idempotency) |
| Update | ~14 (1 FL deactivate + 7 incident backfill + 7 user_directory backfill + 1 DR rename + ?owner consult) |
| **Total touched** | **~44 mandatory + ~92 optional retention** |

---

## 8 · Effort estimate

| Phase | Effort |
|---|---|
| Authorize + run DB sweep (P0 + P1) | ~60 min total · DB-only · reversible |
| Operator screenshot for P2-1 | ~15 min |
| Documentation (P3) | ~30 min |
| Optional retention sweeps (session_activity · idempotency · audit_events) | +30 min (operator-decided) |
| **Sprint 1A complete** | **~2-2.5 hr** |

---

## 9 · OMEGA discipline

| Discipline rule | Status |
|---|---|
| Zero code changes | 🟢 |
| Zero DB writes | 🟢 (this is planning only) |
| Zero deployments | 🟢 |
| Zero feature work | 🟢 |
| Read-only certification only | 🟢 |
| Operator-authorization gate before any cleanup | 🟢 |

---

## 10 · Closeout

🟡 Plan ready. **Awaiting explicit operator authorization to execute the DB sweep.** Sprint 1A execution will be DB-only · reversible via the 2026-05-31 16:02Z archive · ~1 hour total with full verification gates.

🛑 STOP.
