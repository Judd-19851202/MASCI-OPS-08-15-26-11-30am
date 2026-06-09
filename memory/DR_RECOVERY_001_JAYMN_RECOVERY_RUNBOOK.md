# DR-RECOVERY-001 · JAYMN DAILY REPORT RECOVERY RUNBOOK

**Priority:** P0
**Target:** Daily Report created by **Jaymn** at ~6:34 PM local on the live platform.
**Filed:** 2026-02-09
**Author:** E1 forensic agent (preview-pod access only)

---

## ⚠️ ACCESS DISCLOSURE — READ FIRST

This agent runs inside the **preview pod** with read access to the preview DB only. To complete the four required phases I need:

| Phase | Resource | Who can execute |
|---|---|---|
| 1 — Verify DB | Live MongoDB credentials (`MONGO_URL`, `DB_NAME` for production) | DevOps / Emergent prod admin |
| 2 — Device recovery | Jaymn's **exact device + browser** used at 6:34 PM (do NOT clear site data) | Jaymn — guided remotely by Safety/IT |
| 3 — Replay | Live admin token + the exported payload from Phase 2 | Anyone with the admin token + Phase 2 export |
| 4 — Evidence | Live record-by-id read | Same as Phase 1 |

**This document is a paste-ready runbook.** Every command below is reviewed against the exact code revision running in production (same git tree). Run them in order; collect the requested evidence after each phase.

---

## PHASE 1 · Verify Database (live ops team)

### 1.1 — Direct project query (broadest)

Jaymn's project number is presumably known to the user filing this directive. If not, use the prepared-by name filter in 1.2.

```bash
LIVE_MONGO_URL="<your live MONGO_URL>"
LIVE_DB="<your live DB_NAME>"

# Window: today 18:00 → 19:30 local. Adjust the TZ offset for your local time.
# Example below assumes US Eastern (UTC-5 standard / UTC-4 DST).
mongosh "$LIVE_MONGO_URL/$LIVE_DB" --quiet --eval '
  const start = new Date(new Date().setHours(18, 0, 0, 0));
  const end   = new Date(new Date().setHours(19, 30, 0, 0));
  printjson(
    db.daily_reports.find(
      {
        $or: [
          { created_at: { $gte: start.toISOString(), $lte: end.toISOString() } },
          { created_at: { $gte: start, $lte: end } }
        ]
      },
      {
        _id: 0, id: 1, doc_id: 1, project_name: 1, project_number: 1,
        prepared_by: 1, prepared_by_bound: 1, prepared_by_identity: 1,
        report_date: 1, created_at: 1, deleted_at: 1
      }
    ).sort({ created_at: -1 }).limit(50).toArray()
  );
'
```

**Expected:** Jaymn's DR will **NOT** be in the results if the DR-BLOCKER-001A diagnosis is correct. If it IS present — recovery is complete; capture the `id` and `doc_id` and skip to Phase 4.

### 1.2 — Filter by prepared_by (when project is unknown)

```bash
mongosh "$LIVE_MONGO_URL/$LIVE_DB" --quiet --eval '
  print("Searches with prepared_by ~= /jaymn/i in the last 24h");
  db.daily_reports.find(
    {
      prepared_by: { $regex: /jaymn/i },
      created_at:  { $gte: new Date(Date.now() - 24*3600*1000).toISOString() }
    },
    {
      _id: 0, id: 1, doc_id: 1, project_name: 1, project_number: 1,
      prepared_by: 1, report_date: 1, created_at: 1, deleted_at: 1
    }
  ).sort({ created_at: -1 }).toArray()
'
```

### 1.3 — Soft-delete + hidden states

```bash
mongosh "$LIVE_MONGO_URL/$LIVE_DB" --quiet --eval '
  db.daily_reports.find(
    {
      prepared_by: { $regex: /jaymn/i },
      $or: [
        { deleted_at: { $exists: true, $ne: null, $ne: "", $ne: false } },
        { archived:   true },
        { hidden:     true }
      ]
    },
    { _id: 0, id: 1, doc_id: 1, prepared_by: 1, created_at: 1, deleted_at: 1, archived: 1 }
  ).toArray()
'
```

### 1.4 — Audit + state-event collections (in case a write started but didn't finalize)

```bash
mongosh "$LIVE_MONGO_URL/$LIVE_DB" --quiet --eval '
  print("--- workflow_state_events for daily_reports in window ---");
  const start = new Date(new Date().setHours(18,0,0,0));
  db.workflow_state_events.find(
    { record_kind: "daily-report", created_at: { $gte: start.toISOString() } },
    { _id: 0, record_id: 1, from_state: 1, to_state: 1, actor: 1, created_at: 1 }
  ).sort({ created_at: -1 }).limit(20).toArray();

  print("--- audit_events for daily_reports in window ---");
  db.audit_events.find(
    { kind: "daily-report", created_at: { $gte: start.toISOString() } },
    { _id: 0, record_id: 1, event: 1, actor: 1, created_at: 1 }
  ).sort({ created_at: -1 }).limit(20).toArray();
'
```

**Phase 1 evidence to capture:**
- Output of 1.1 (full list of DRs in window) — expected empty for Jaymn
- Output of 1.2 (any DR by Jaymn in 24h) — expected: prior reports only, none at 6:34 PM
- Output of 1.3 (soft-delete check) — confirms not hidden
- Output of 1.4 (state events) — confirms no in-flight write started

If all four queries return **no record matching Jaymn at ~18:34**, proceed to Phase 2. If any query returns the DR — recovery is complete; report and stop.

---

## PHASE 2 · Device Recovery (Jaymn's exact device/browser)

**Critical:** Jaymn must use **the same device + same browser profile + same domain** as the 6:34 PM submit. Do NOT clear cookies, site data, or IndexedDB before running these steps. iOS Safari users: do NOT use private browsing.

### 2.1 — Locate the queued payload

Have Jaymn open the production app URL, then open DevTools (Safari: Develop → Show Web Inspector; Chrome/Edge: F12; iOS Safari requires a Mac with the device tethered for remote inspection).

Paste this into the **Console** tab and press Enter:

```js
// DR-RECOVERY-001 · Phase 2 · Inspect queue + draft for Daily Report
(async () => {
  const idb = await import("https://esm.sh/idb-keyval@6");
  const QUEUE_KEY = "masci.resiliency.queue.v1";

  const queue = (await idb.get(QUEUE_KEY)) || [];
  console.log("==== RESILIENCY QUEUE (count: " + queue.length + ") ====");
  console.table(queue.map(q => ({
    id: q.id,
    url: q.url,
    formKey: q.formKey,
    idempotencyKey: q.idempotencyKey,
    tries: q.tries,
    status: q.status,
    enqueuedAt: q.enqueuedAt,
    lastError: q.lastError && q.lastError.slice(0, 80)
  })));

  // Pull the Daily Report queue entries
  const drQueue = queue.filter(q =>
    (q.url || "").endsWith("/daily-reports") &&
    (q.formKey === "daily-report-new" || (q.body && q.body.project_name))
  );
  console.log("\n==== DR QUEUE ENTRIES ====");
  console.log(JSON.stringify(drQueue, null, 2));

  // Also fetch all keys (the draft for the DR may be under a separate key)
  const allKeys = await idb.keys();
  const drDraftKeys = allKeys.filter(k =>
    typeof k === "string" && (k.startsWith("masci.draft.") || k.startsWith("masci.draft-archive.") || k.startsWith("masci.draft-idempotency."))
    && k.includes("daily-report-new")
  );
  console.log("\n==== DR DRAFT KEYS ====", drDraftKeys);
  for (const k of drDraftKeys) {
    console.log(`-- ${k} --`);
    console.log(JSON.stringify(await idb.get(k), null, 2));
  }

  // Export EVERYTHING relevant as a single JSON blob (downloadable)
  const exportPayload = {
    capturedAt: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: location.href,
    queue: drQueue,
    drafts: Object.fromEntries(
      await Promise.all(drDraftKeys.map(async k => [k, await idb.get(k)]))
    )
  };
  const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "jaymn-dr-recovery-" + Date.now() + ".json";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(a.href); }, 100);
  console.log("\n✅ Export downloaded.");
})();
```

This script does five things:
1. Dumps the resiliency queue as a console table
2. Pretty-prints any Daily Report queue rows
3. Lists draft keys related to `daily-report-new`
4. Dumps draft contents
5. **Downloads a `jaymn-dr-recovery-<timestamp>.json` file** containing the full payload + drafts

### 2.2 — What we expect to see

Per the DR-BLOCKER-001A forensic analysis, the queue row should look like:

```json
{
  "id": "<random>",
  "url": "/daily-reports",
  "method": "POST",
  "headers": { "Content-Type": "application/json", ... },
  "body": { "project_name": "...", "project_number": "...", "prepared_by": "Jaymn ...", ... },
  "idempotencyKey": "<uuid>",
  "formKey": "daily-report-new",
  "enqueuedAt": "2026-02-09T22:36:xx.xxxZ",
  "tries": 1 .. 5,
  "status": "pending" | "failed",
  "lastError": "timeout of 60000ms exceeded" or similar
}
```

### 2.3 — Phase 2 evidence to capture

- The downloaded `jaymn-dr-recovery-<timestamp>.json`
- Screenshot of the Console output showing the queue row + draft keys
- The value of `idempotencyKey` (write it down — required for Phase 3)
- The value of `status` — `pending` means auto-drain will keep retrying; `failed` means MAX_TRIES exhausted and manual replay is needed
- The exact `body` — this IS the original Daily Report payload, untouched

If the queue is empty AND no `masci.draft.*.daily-report-new` key exists → the device data has been cleared / wasn't where the submit happened / browser profile is different. Stop Phase 2 and triage with Jaymn before proceeding.

---

## PHASE 3 · Replay through Live API

Use the exported `body` from Phase 2 to POST a fresh Daily Report. The `Idempotency-Key` header reuses Jaymn's original key, so if for any reason the original DID reach the backend (race conditions), the live server will return the existing record instead of creating a duplicate.

### 3.1 — Replay command

Save the exported file from Phase 2 to a host that has the live admin token (or Jaymn's PM/portal token if preferred):

```bash
# Variables you provide
EXPORT_JSON="./jaymn-dr-recovery-1739xxxxxx.json"        # from Phase 2
LIVE_API="<https://your-live-domain>/api"
ADMIN_TOKEN="<live admin token>"

# Extract first DR queue row's body and idempotency key
BODY=$(jq '.queue[0].body' "$EXPORT_JSON")
IDEMPOTENCY=$(jq -r '.queue[0].idempotencyKey' "$EXPORT_JSON")

echo "Replaying DR with Idempotency-Key=$IDEMPOTENCY"
echo "Project: $(echo $BODY | jq -r '.project_name')  ·  $(echo $BODY | jq -r '.project_number')"
echo "Prepared by: $(echo $BODY | jq -r '.prepared_by')"
echo "Report date: $(echo $BODY | jq -r '.report_date')"

curl -i -X POST "$LIVE_API/daily-reports" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Idempotency-Key: $IDEMPOTENCY" \
  --data "$BODY"
```

**Expected response:** HTTP 200 with body `{"id": "<uuid>", "doc_id": "DR-2026-NNNNN", "project_number": "...", ...}`. Record the `id` and `doc_id`.

### 3.2 — If replay fails

| Failure | Likely cause | Action |
|---|---|---|
| 401 Unauthorized | Wrong admin token | Use a fresh token from the production admin login |
| 422 Validation Error | Payload schema drift | Diff the body against `routes/daily_reports.py::DailyReportCreate`; remove unknown fields if any |
| 524 / timeout again | Same network issue at the replay host | Run the curl from a stable network (server console) |
| 200 with same `id` returned twice | Idempotency cache hit (good — already there) | Confirm in Phase 4 |

### 3.3 — Verify Mongo write

```bash
mongosh "$LIVE_MONGO_URL/$LIVE_DB" --quiet --eval '
  db.daily_reports.findOne(
    { id: "<id-from-curl-response>" },
    { _id: 0, id: 1, doc_id: 1, project_number: 1, prepared_by: 1,
      report_date: 1, created_at: 1, audit_envelope_sha256: 1,
      prepared_by_bound: 1 }
  )
'
```

Expected: a document with `audit_envelope_sha256` populated (proves the audit envelope path ran). `prepared_by_bound` will be `true` if the replay used a directory-bound token (admin token resolves to `{"directory":"admin", "user_id":"admin", "role":"Admin"}` per DR-FIX-3 / R9). Note that the audit will record the replay actor, not the original Jaymn session — this is acceptable for recovery but worth disclosing in the audit trail.

### 3.4 — Verify PDF render

```bash
# In-process render via Python (preserve from breaking the live server)
ssh <prod-host>  # or run this on the production backend
python3 -c "
import sys; sys.path.insert(0, '/app/backend')
import pdf_render
from pymongo import MongoClient
import os, json
mc = MongoClient(os.environ['MONGO_URL'])
db = mc[os.environ['DB_NAME']]
doc = db.daily_reports.find_one({'id': '<id-from-curl-response>'})
del doc['_id']
b = pdf_render.render_record_pdf('daily-report', doc)
open('/tmp/jaymn_recovered.pdf', 'wb').write(b)
print(f'PDF: {len(b)} bytes; magic: {b[:5]}')
"
```

Expected: `b[:5] == b"%PDF-"`. Copy `/tmp/jaymn_recovered.pdf` off the host for visual confirmation.

### 3.5 — Verify visibility in the app

Open the live admin UI: `https://<live>/admin/daily/<id-from-curl-response>` — should render the read view with Executive Summary card + all sections + Section 09D · MATERIAL MOVEMENT TODAY (if Jaymn captured any outbound material per MM-ENTRY-002).

### 3.6 — Once replay is verified, clean the device queue

Have Jaymn paste this in the Console to remove the now-delivered queue entry:

```js
(async () => {
  const idb = await import("https://esm.sh/idb-keyval@6");
  const QUEUE_KEY = "masci.resiliency.queue.v1";
  const queue = (await idb.get(QUEUE_KEY)) || [];
  const before = queue.length;
  const cleaned = queue.filter(q =>
    !((q.url || "").endsWith("/daily-reports") && q.formKey === "daily-report-new")
  );
  await idb.set(QUEUE_KEY, cleaned);
  console.log(`Queue: ${before} → ${cleaned.length}`);
})();
```

This removes the DR queue entry. The draft is auto-cleared by `useFormDraft.commit()` after a successful 2xx from the live drain; if you ran the replay from a server console instead, also clean the draft:

```js
(async () => {
  const idb = await import("https://esm.sh/idb-keyval@6");
  const keys = (await idb.keys()).filter(k =>
    typeof k === "string" &&
    (k.startsWith("masci.draft.") || k.startsWith("masci.draft-archive.") || k.startsWith("masci.draft-idempotency."))
    && k.includes("daily-report-new")
  );
  for (const k of keys) await idb.del(k);
  console.log("Cleared draft keys:", keys);
})();
```

---

## PHASE 4 · Evidence Template

Fill this in after Phase 1–3 are complete and return as the certification:

```
DR-RECOVERY-001 · OUTCOME
-------------------------
Was report recovered?     YES / NO
Source of recovery:       Phase 1 / Phase 2 IDB / not recoverable
Record ID (id):           <uuid>
Doc ID (doc_id):          DR-2026-NNNNN
Project name:             <from body.project_name>
Project number:           <from body.project_number>
Original submit time:     2026-02-09 ~18:34 local (from queue.enqueuedAt)
Replay submit time:       <Phase 3 timestamp>
Replay HTTP status:       200
Replay command actor:     X-Admin-Token (replay) — note for audit trail
Mongo write verified:     YES (audit_envelope_sha256 populated)
PDF render verified:      YES (magic bytes %PDF-)
Audit envelope SHA256:    <16-char prefix>
Visibility verified:      YES (visible at /admin/daily/<id>)
Device queue cleaned:     YES / NO / N/A
```

---

## SUCCESS CONDITION CHECK

> *The original Daily Report is recovered and exists as a normal live Daily Report record without requiring the operator to recreate it manually.*

Pass requires:
- ✅ Original `body` recovered from Jaymn's device IDB **without re-entry**
- ✅ Replay POST returned 200 with a real `id` and `doc_id`
- ✅ Live MongoDB now contains the document
- ✅ PDF renders cleanly
- ✅ Document visible in the live app
- ✅ Audit envelope SHA256 populated (proves the standard create path ran)

The recovered DR will carry **the original payload data (project, date, crews, materials, outbound, photos, signatures)** but with `created_at` = the replay timestamp and `prepared_by_identity` populated by the replay actor's token. Both are documented in this runbook for the audit trail.

---

## FALLBACK — If Phase 2 returns nothing

If Jaymn's device IDB is empty:
1. Confirm with Jaymn: same device · same browser profile · same domain · no incognito · site data NOT cleared
2. If iOS, check that Safari's Intelligent Tracking Prevention hasn't evicted the data (>7 days inactive site data is auto-purged on iOS 14+)
3. If the data is truly gone, re-entry is the only path. The runbook stops here, and the success condition cannot be met.

The DR-BLOCKER-001B fix shipped earlier today **prevents this scenario from recurring** — Jaymn (or any future foreman) hitting a slow upload will now see the explicit amber "Saved Locally — Not Yet Delivered" screen with the warning *"Do not clear browser data until delivery is confirmed."*

---

## STOP

This runbook is the complete deliverable for DR-RECOVERY-001 from the preview-pod side. No code changes were made. Execution requires live access (Phase 1 + 3 + 4) and Jaymn's device (Phase 2). Return the filled Phase 4 Evidence Template once execution is complete.

**RECOVERY RUNBOOK COMPLETE · AWAITING EXECUTION ON LIVE + JAYMN'S DEVICE**
