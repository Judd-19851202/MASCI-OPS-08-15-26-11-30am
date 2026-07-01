# TRACK 19.08 · Complete Data Flow Trace

Byte-by-byte trace from operator tap → historical record.

---

## 1 · Full pipeline (DVIR as canonical example)

```
[1] OPERATOR TAP
    Component: <YesNo> pill on section item "Brakes"
    Handler: setDefectItem(sectionId, itemId, "fail")

[2] REACT STATE
    File: NewFleetDVIR.jsx
    Reducer: setState((p) => ({ ...p, sections: p.sections.map(...) }))
    Side effect: useEffect recomputes overall_status client-side

[3] AUTOSAVE
    Hook: useFormDraft(formKey="dvir-new", stateRef, actor)
    Storage: IndexedDB (via idb) at db="masci-drafts", store="drafts"
    Key: `${formKey}::${deviceId}::${actorAuthKey}` (Track 19.04 actor-scope)
    Debounce: 400ms
    Contract: contract_version="19.04"

[4] SUBMIT INTENT
    Component: <SubmitButton>
    Handler: submit()
    Steps:
      a. validate() — client-side field presence + business rules
      b. Language check → translateUserInput if ES via OpenAI
      c. mintIdempotencyKey() + persist to IndexedDB
      d. Sanitize payload (Track 19.06 amend: strip `_prefilled`)
      e. Set headers (X-FL-Token if field-leadership context)

[5] NETWORK — CLIENT
    enqueueUpload({method:"POST", url:"/fleet/inspections", body:payload, idempotencyKey, formKey})
    Offline: enqueued in IndexedDB queue; retried × 5 exponential backoff
    Online: fetch → REACT_APP_BACKEND_URL/api/fleet/inspections
    Timeout: 60s

[6] KUBERNETES INGRESS
    Rewrite: /api/* → backend service :8001
    Preserves headers; adds X-Real-IP, X-Forwarded-For

[7] FASTAPI ENTRY
    File: server.py — api_router mounted at /api
    Middleware chain:
      - CORS
      - Sentry request context
      - rate_limit_public_post (this route is public)
      - Idempotency: with_idempotency(db, key, actor_context, do_action)

[8] ROUTE HANDLER
    File: routes/fleet_ops.py — POST /fleet/inspections
    Steps:
      a. Pydantic model validation (FleetInspectionCreate)
      b. Enrich payload with computed fields (overall_status server-side re-derive)
      c. datetime.now(timezone.utc) for submitted_at
      d. Insert into db.fleet_audit
      e. For each item in defects[]:
         - lookup severity in db.fleet_defect_severity
         - insert into db.fleet_defects (state=open)
         - if critical/high → upsert db.fleet_status.oos
      f. Emit audit_events (workflow="dvir-submit", correlation_id=idempotencyKey)
      g. Schedule PDF render (async task via BackgroundTasks)
      h. schedule_auto_email("dvir", doc) — enqueues to email_routes
      i. schedule_auto_email("fleet-defect", each) — per defect
      j. If integration_settings.motive/samsara enabled → sync payload
      k. Return DailyInspection response body

[9] MONGODB WRITES (motor async)
    Collections touched:
      db.fleet_audit — new DVIR doc
      db.fleet_defects — 1 per failed item
      db.fleet_status — upsert on OOS
      db.dispatch_state_events — unit_oos event
      db.audit_events — N events (submit + defect + OOS)
      db.email_routing_audit_v — per email dispatched
      db.notifications — in-app notifications for shop portal

[10] EMAIL DISPATCH
    schedule_auto_email resolves recipients from db.email_routes
    Rate-limit awareness: batches per template
    Delivery: SES / SMTP (config-dependent)
    Bounce handling: dead-letter to ADMIN_DEAD_LETTER_EMAIL

[11] PDF RENDER
    pdf_render.py builds HTML with WeasyPrint
    Fonts: embedded (no remote fetch)
    Assets: R2 keys converted to data URIs at render time
    Output: bytes → uploaded to R2 → key stored on doc

[12] CLIENT RECEIVES 200
    Commit draft (clear IndexedDB row)
    Clear idempotency key from IndexedDB
    Save crew setup (device-local memory)
    Remember last project
    Toast "Submitted"
    Navigate to /fleet/dvir/submitted/{id}

[13] DOWNSTREAM CONSUMERS (async, cadence-driven)
    Job Photos indexer mirrors any defect photos into db.job_photos
    Trust Spine correlation-id joins all touched surfaces
    Weekly safety-digest cron scans events since last run
    Compliance export snapshots the record into the CSV/XLSX bundle

[14] HISTORICAL RECORD
    fleet_audit doc: immutable (soft-delete only via audited admin action)
    fleet_defects docs: mutable via state machine only
    audit_events: append-only
    Historical DELETE on /fleet/inspections/{id}: NOT SUPPORTED — no route registered
```

---

## 2 · What is EPHEMERAL (does not survive)

| Data | Where it dies |
| --- | --- |
| Signature stroke coordinates | data-URL is persisted, stroke path is not |
| GPS accuracy value | Persisted, but not used downstream |
| Client-side computed `overall_status` | Server re-derives; client value is not authoritative |
| Idempotency key | Cleared client-side on 2xx; audit_events retains it as correlation_id |
| Draft IndexedDB row | Cleared on commit; kept on queued-then-give-up (manual retry) |

---

## 3 · What is IMMUTABLE (survives forever, cannot be edited)

| Collection | Immutability rule |
| --- | --- |
| `daily_reports` | HTTP DELETE returns 410 (Track 19.05 lock). Content-mutations blocked by route absence. |
| `fleet_audit` | No PATCH route; soft-delete via admin only. |
| `incidents` | Content immutable post-submit; lifecycle state advances via typed transitions only. |
| `meetings` | Content immutable post-submit. |
| `jhas` | Amendments create a new revision; original revision immutable. |
| `audit_events` | Append-only; no delete route anywhere. |
| `email_routing_audit_v` | Append-only. |

---

## 4 · What is MUTABLE (has PATCH / PUT surfaces)

| Collection | Mutability path |
| --- | --- |
| `fleet_defects` | Shop state machine only. |
| `fleet_status` | Dispatch/shop actions only. |
| `corrective_actions` | Safety/HR edit workflow. |
| `equipment_issuances` | Issue → Return workflow. |
| `jha_acknowledgements` | Append-only per-employee-per-revision. |
| `email_routes` (config) | Admin only. |

---

## 5 · Where the data is HIDDEN from the operator

* Server-derived fields (`overall_status`, `defect_ticket_ids[]`) are NOT surfaced in the submit confirmation.
* Downstream commitments (which shop foreman got notified, which PDF ID was created) are NOT surfaced.
* Trust-Spine correlation id is NOT surfaced to the operator (visible only under Admin console).

**Consequence**: Operators cannot see what their submit produced. See `13_INDUSTRY_COMPARISON.md` — closing this gap is the P0 trust improvement.

---

## 6 · Bytes vs. semantic size

Typical DVIR submit payload (10-section, 3-defect, 3-photo): ~1.8 MB (photos dominate).
After Track 19.04's unified attachment envelope: no material size change.
Photos go via chunked upload; DVIR body itself is <30 KB.
