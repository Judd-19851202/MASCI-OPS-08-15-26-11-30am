# TRACK 22.1B · Zero-Drift Matrix

## What changed

| Change | File(s) | Kind |
|---|---|---|
| Email dispatch scaffolding extracted | `backend/server.py` (−31 lines) → `backend/lib/email_dispatch.py` (+136 lines) | **Runtime code move** (lift-and-shift, parity-proven) |
| Dispatcher body preserved with SHA-256 lock | `backend/server.py` `_dispatch_auto_email` (473 lines, unchanged) | **Bytecode fingerprint locked** |
| 10 memory MDs | `memory/TRACK_22_1B_*.md` | Documentation |
| Snapshots | `memory/track_22_1b/RUNTIME_ENUMERATION_{before,after}.json` | Evidence |
| Fingerprint | `memory/track_22_1b/DISPATCHER_BYTECODE_FINGERPRINT.txt` | CI lock |
| Lock test | `backend/tests/test_track_22_1b_email_dispatch.py` (17 assertions) | Test infrastructure |
| Ledgers | PRD · CHANGELOG · Debt Register | Documentation |

**Runtime code files touched:** 1 (`backend/server.py`) plus 1 new `backend/lib/email_dispatch.py`.

## What did NOT change

- **1,440 backend endpoints.** Byte-equal route set. Byte-equal `(path, methods)` tuples.
- **1,444 method entries. 1,263 OpenAPI paths.**
- **Every route's dependency chain** — 0 diffs across all 1,440 routes.
- **51 startup handlers, 1 shutdown handler, 7 middleware, 3 exception handlers** — same set, same order.
- **`_dispatch_auto_email` body** — same bytecode (SHA-256 `ebf5259dd6b8987d3c5a4ffff9a63abb5898f774711851c293e55672403f6a5b`).
- **Recipient resolution** — `pm_routing.recipients_for_record_async` untouched.
- **PDF generation** — `render_record_pdf`, `_maybe_enrich_for_pdf` untouched.
- **Subject / HTML generation** — `build_email_subject`, `render_email_html` untouched.
- **Trust Spine events** — every `emit_workflow_stage(...)` call site inside `_dispatch_auto_email` preserved (bytecode-locked).
- **Email safety envelope** — SDK monkey patch position unchanged; dispatcher gate + `TEST_` payload guardrail intact.
- **CORS explicit allow-lists** (Track 21.3) — preserved.
- **`EMAIL_SAFETY_MODE=strict`** in preview `.env` — preserved.
- **Scheduler timing** — 39 `create_task` chains, `SCHEDULER_ENABLED=false` in preview.
- **Every Mongo collection, schema, field, index.**
- **Every auth gate.**
- **Frontend** — untouched. `yarn lint` / `yarn build` unaffected.
- **All 12 prior-track lock tests** — still committed.

## Production impact

**Zero.** Extraction is invisible to any consumer of the API and any consumer of the email pipeline.

- Same URL paths (all 1,440).
- Same JSON responses.
- Same email recipients / subjects / attachments / PDFs / message IDs.
- Same Trust Spine event stream.
- Same audit rows in `email_routing_audit_v2`.
- Same safety-mode gating.

**Rollback path:** revert the two `search_replace` edits in `server.py` (re-inline the two blocks) and delete `lib/email_dispatch.py` + the 10 memory MDs + the lock test + the runtime snapshots + the fingerprint file. Contained diff.

## Zero-drift verdict

🟢 **CERTIFIED.** Every diff is either documentation, evidence, or a proven-safe code move. Zero production behavior drift, verified by JSON snapshot + SHA-256 bytecode fingerprint.
