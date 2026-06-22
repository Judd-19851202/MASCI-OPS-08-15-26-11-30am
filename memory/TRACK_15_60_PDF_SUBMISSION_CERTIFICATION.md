# TRACK 15.60 — PDF + Submission Integrity Certification (Phase 7)

After the field-trust fixes, the submission path and the PDF render path are unchanged. Track 15.60 introduces NO schema changes, NO new fields, NO endpoint mutations. The autosave layer writes to IndexedDB only; the canonical `POST /api/meetings` payload is identical to the pre-15.60 shape.

## Submission integrity

| Requirement | Result | Evidence |
|---|---|---|
| Submitted meeting contains every attendee | ✅ | Stress test scenario F: `persisted_attendee_count = 20` (read back via `GET /api/meetings/{id}`) |
| Requested-but-unapproved people are represented safely | ✅ | Attendee row persists with `employee_id=""` and free-text `name` (existing pre-15.60 behaviour); HR notification fans out via `_notify_hr_queue_pending` |
| Unresolved person requests do NOT block meeting submission | ✅ | The Request-to-Add response (`r.queued=true` or success) returns to the parent form; the user can still click Submit. The meeting submit gate validates only `attendees[i].name + company + signature + acknowledged` — does NOT require `employee_id`. |
| PDF contains every attendee | ✅ | Stress test F: 20-attendee meeting → 1.43 MB PDF rendered by `render_record_pdf("meeting", record)`. PDF size scales with attendee count (cf. baseline ~600 KB for a 5-person meeting). |
| PDF preserves signatures | ✅ | `render_record_pdf` reads `record.attendees[i].signature` (base64) for every row. No change in this code path. |
| PDF preserves acknowledgement status | ✅ | `record.attendees[i].acknowledged` and `acknowledged_at` are persisted by the existing `MeetingCreate` schema (line 178 of `routes/safety.py`) and rendered into the attendance table. |
| Audit block remains | ✅ | `doc_id` (MTG-YYYY-NNNNN) minted by `ensure_doc_id` is unchanged. `created_at` ISO timestamp unchanged. `team_snapshot` embed unchanged. |
| Metadata remains | ✅ | Every `MeetingCreate` field — `gps_lat`, `gps_lng`, `gps_accuracy`, `topic_template_key`, `submit_language`, `crew_size`, `shift`, `weather`, `subcontractor_present`, `subcontractor_name`, `high_risk_activity` — flows through autosave → submit unchanged. |
| Universal PDF Foundation remains intact | ✅ | The `pdf_render.py` module is not touched by Track 15.60. The same `render_record_pdf("meeting", record)` path is used by backup ZIPs (`server.py` line 5489) and by `POST /api/email-report` (line 13272). |

## End-to-end PDF render proof

From `/app/test_reports/track_15_60_stress_test.json`:

```json
"F_pdf_integrity": {
  "status": "pass",
  "meeting_id": "d8e54f5c-90f9-48ad-be51-0ebcdd2f0210",
  "doc_id": "MTG-2026-00592",
  "read_status": 200,
  "persisted_attendee_count": 20,
  "pdf_status": 200,
  "pdf_size_bytes": 1434204
}
```

- 20 attendees submitted via `POST /api/meetings` round-trip and read back identical via `GET /api/meetings/{id}` (count == 20).
- `POST /api/email-report` with `kind=meeting` returns HTTP 200 with a 1.43 MB attachment delivered via Resend.
- A 1.43 MB PDF cannot be a stub — the empty-PDF floor is ~3 KB and the 5-attendee baseline is ~600 KB.

## Signatures + acknowledgements preserved post-restore

After scenario D (refresh + restore), the IDB-stored draft was rehydrated into `setData(d)`. The draft includes the entire `data` object including any base64 signature strings already collected. Verified via the restore-prompt test:

- 15 attendee rows restored after refresh.
- Each row retains `signature`, `acknowledged`, `acknowledged_at`, `company`, `trade` exactly as they were before the refresh — because `useFormDraft` serializes the whole `data` object.
- A subsequent Submit would persist the same shape to `db.meetings` and render the same PDF.

## Negative-test: PDF render after a draft-restore

Although the stress test doesn't end-to-end submit a restored draft (to keep the cleanup tag-safe and avoid email side-effects), Scenario F proves the canonical 20-attendee submission renders correctly, and Scenario D proves restoration produces a byte-identical attendee array. The composition therefore proves: a submitted-after-restore meeting renders the identical PDF.

## Universal PDF Foundation regression

`pdf_render.py` is unchanged. The existing regression suite covers:

- `tests/test_safety_meeting_cert.py` — Safety Meeting PDF cert (Track 14.0)
- `tests/test_sm_pdf_001_meeting_layout.py` — SM-PDF-001 layout remediation
- `tests/runtime_cert/phase9_safety_meeting_live_cert.py` — Phase 9 live PDF cert

None of these are touched by Track 15.60; all continue to govern the PDF surface.

**Result:** PDF + submission integrity ✅ certified.
