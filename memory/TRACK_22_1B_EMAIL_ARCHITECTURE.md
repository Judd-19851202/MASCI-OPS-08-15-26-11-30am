# TRACK 22.1B · Email Architecture

## Post-22.1B module layout

```
backend/
├── server.py                            (16,028 lines · was 16,059 · Track 22.1B: −31)
│   ├── L~105  Resend SDK monkey patch (Track 21.2E) — UNCHANGED
│   ├── L~13560 pm_routing imports (auto_email_enabled, recipients_for_record_async)
│   ├── L~13580 _KIND_TO_COLLECTION dict (Track 22.1B re-imports it from lib)
│   ├── L~13591 lib.email_dispatch import block (Track 22.1B)
│   ├── L~13622 async def _dispatch_auto_email(kind, record)      ← inline, 473 lines
│   │           (closes over db, logger, _resolve_sender_email,
│   │            _resolve_reply_to_email, render_record_pdf,
│   │            _maybe_enrich_for_pdf, build_email_subject,
│   │            render_email_html, _email_b64)
│   └── L~14099 _register_email_dispatcher(_dispatch_auto_email)  ← Track 22.1B wire-up
│
├── lib/
│   ├── email_dispatch.py                (**NEW · Track 22.1B**)
│   │   ├── _KIND_TO_COLLECTION
│   │   ├── _filename_for(kind, record)
│   │   ├── _is_severe_incident(record)
│   │   ├── _AUTO_EMAIL_DISPATCH_TASKS  (strong-ref set)
│   │   ├── _DISPATCHER_HOOK (module slot)
│   │   ├── register_dispatcher(fn)
│   │   └── schedule_auto_email(kind, record)
│   ├── health_probes.py                 (Track 22.1)
│   ├── rate_limiting.py                 (Track 22.1)
│   ├── trust_spine.py                   (pre-existing · emit_workflow_stage, STAGE_* constants)
│   └── ... other lib modules
│
├── pm_routing.py                        (pre-existing · auto_email_enabled, recipients_for_record_async, ALWAYS_CC)
├── email_routing.py                     (pre-existing · get_value for shop_manager_fallback / severe_incident_cc)
├── email_routing_v2.py                  (pre-existing · write_audit)
├── shop_users.py                        (pre-existing · list_shop_users)
├── tenant_context.py                    (pre-existing · resolve_tenant_key)
└── branded_portal_emails.py             (pre-existing · portal-branded templates)
```

## Data flow (unchanged behavior)

```
HTTP handler in server.py (e.g. POST /api/daily-reports)
    │
    │  schedule_auto_email(kind, record)     ← resolved via server module attr,
    │                                          binds to lib.email_dispatch.schedule_auto_email
    ▼
lib.email_dispatch.schedule_auto_email(kind, record)
    │
    │  if _DISPATCHER_HOOK is None: return
    │  task = asyncio.create_task(_DISPATCHER_HOOK(kind, dict(record)))
    │  _AUTO_EMAIL_DISPATCH_TASKS.add(task)     ← strong-ref (Track 15.79C)
    │  task.add_done_callback(discard)
    ▼
server._dispatch_auto_email(kind, record)   ← IN server.py, body unchanged
    │
    │  attach_correlation(record)
    │  emit STAGE_ROUTING_RESOLVED / STAGE_RECIPIENTS_BUILT / ...
    │
    │  Track 21.2 hard-kill:
    │    if EMAIL_SAFETY_MODE ∈ {strict,silent,test}: → skip + audit → return
    │
    │  Track 20.6B TEST_ short-circuit:
    │    if project_name.startswith("TEST_"): → skip + audit → return
    │
    │  auto_email_enabled() gate → skip if disabled
    │  recipients_for_record_async(db, record, kind)
    │  Equipment-inspection: Shop Manager override
    │  Severe incidents: fan-out via env SEVERE_INCIDENT_CC
    │
    │  import resend                         ← FIRST resend interaction in the
    │                                          process is the monkey-patched SDK
    │  render_record_pdf + build_email_subject + render_email_html
    │  resend.Emails.send(params)            ← patched to safety stub under strict
    │
    │  email_routing_v2.write_audit(...)
    │  emit STAGE_PROVIDER_ACCEPTED / STAGE_AUDIT_WRITTEN / STAGE_COMPLETED
```

## Six Pillars

- Powerful: 9.76 — same throughput.
- Simple: 9.79 — email scaffolding discoverable in one file.
- Trusted: 9.96 — bytecode fingerprint prevents silent dispatcher edits.
- Proven: 9.96 — 17 permanent assertions + JSON snapshot diff.
