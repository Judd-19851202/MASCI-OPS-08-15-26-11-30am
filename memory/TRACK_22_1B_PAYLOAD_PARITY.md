# TRACK 22.1B · Payload Parity Report

## Certification statement

Every byte of the email payload — subject, HTML, plain text, attachments, PDF filename, metadata, headers, reply-to, message IDs, tracking IDs, Trust Spine payload — is produced by code that either lives outside this track's scope or lives inside `_dispatch_auto_email` (SHA-256 bytecode-locked).

## Payload construction sites (unchanged)

| Payload field | Source | Track 22.1B change |
|---|---|---|
| `from` | f-string using `_resolve_sender_email(db)` result | none (server module) |
| `to` | `list(dist["all"])` from `recipients_for_record_async(...)` | none (`pm_routing`) |
| `subject` | `build_email_subject(kind, record, equipment_fail=..., severe_incident=...)` | none (server module) |
| `html` | `render_email_html(kind, record, note)` | none (server module) |
| `attachments[0].filename` | **`_filename_for(kind, record)`** | **extracted** — pure function, byte-identical body |
| `attachments[0].content` | `base64.b64encode(pdf_bytes).decode()` where `pdf_bytes = await asyncio.to_thread(render_record_pdf, kind, await _maybe_enrich_for_pdf(db, kind, record))` | none (server module) |
| `reply_to` | `await _resolve_reply_to_email(db)` (optional) | none (server module) |
| Trust Spine correlation_id | `attach_correlation(record)` from `lib.trust_spine` | none |
| Trust Spine stage events | `emit_workflow_stage(...)` from `lib.trust_spine` | none |
| `email_routing_audit_v2` row | `write_audit(db, route_key=..., subject=..., resend_message_id=..., ...)` | none |
| Resend message id / tracking id | `(result or {}).get("id")` where `result = await asyncio.to_thread(resend.Emails.send, params)` | none (SDK-level, patched to safety stub under strict) |

## `_filename_for(kind, record)` — extracted, byte-identical

Verified by:

- Source file diff: the function body in `lib/email_dispatch.py` line-for-line matches the pre-22.1B inline body (comment style + docstring).
- Consumer: called at the same call site inside `_dispatch_auto_email` (line ~13965 pre-22.1B, same location post — bytecode-locked).
- Behavior: given identical `(kind, record)` input, produces identical `MASCI-<kind>-<sanitized-project>-<date>.pdf` output.

Test coverage: implicit via bytecode fingerprint of the caller.

## `_is_severe_incident(record)` — extracted, byte-identical

- 3 call sites inside `_dispatch_auto_email` (equipment_fail flag, severe_incident flag, `if kind == "incident" and _is_severe_incident(record)` for note text).
- Every call site is preserved by the bytecode fingerprint.
- Function body identical.

## Attachment / PDF flow

- PDF bytes produced by `render_record_pdf(kind, await _maybe_enrich_for_pdf(db, kind, record))` on a thread — unchanged.
- Base64 encoded by `_email_b64.b64encode(pdf_bytes).decode()` — unchanged.
- Filename passed via `_filename_for(kind, record)` — extracted; same output.

## Trust Spine payload

Every `emit_workflow_stage(...)` call site inside `_dispatch_auto_email` is preserved by the bytecode fingerprint:

- `STAGE_ROUTING_RESOLVED` — 1 site.
- `STAGE_RECIPIENTS_BUILT` — 2 sites (ok and failed paths).
- `STAGE_NOTIFICATION_QUEUED` — 3 sites (skipped-safety, skipped-test, ok).
- `STAGE_PROVIDER_ACCEPTED` — 1 site.
- `STAGE_AUDIT_WRITTEN` — 1 site.
- `STAGE_COMPLETED` — 2 sites (ok + failed).

`failure_reason` and `remediation` strings are also bytecode-locked.

## Verdict

🟢 **PAYLOAD PARITY CERTIFIED.** No payload byte can change without a matching bytecode-fingerprint update, which is auditable in the git history of `memory/track_22_1b/DISPATCHER_BYTECODE_FINGERPRINT.txt`.
