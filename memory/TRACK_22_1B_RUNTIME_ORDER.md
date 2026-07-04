# TRACK 22.1B · Runtime Order Report

## Module import order (safety-critical)

```
process boot
    ↓
python -m uvicorn server:app --host 0.0.0.0 --port 8001
    ↓
import server
    ├── L1-27      stdlib + third-party imports (fastapi, motor, dotenv, pydantic, ...)
    ├── L44-71     env sanity check, MongoDB client
    ├── L73        app = FastAPI(title="MASCI Job Site Safety Inspection API")
    ├── L105-142   ┌─ EMAIL SAFETY BLOCK ────────────────────────────────────┐
    │              │ _EMAIL_SAFETY_MODE = os.environ["EMAIL_SAFETY_MODE"]...  │
    │              │ if strict/silent/test:                                   │
    │              │     import resend as _resend_boot                        │
    │              │     _resend_boot.Emails.send = _blocked_send             │
    │              │     _resend_boot.send = _blocked_send                    │
    │              │     logger.warning "Resend SDK patched"                  │
    │              └──────────────────────────────────────────────────────────┘
    │              **KEEPS ITS POSITION** — Track 22.1B did not touch this block.
    ├── L~150      app.state.ready = False (readiness gate)
    ├── L~154      from lib.health_probes import attach_health_probes; attach_health_probes(app)
    │              (Track 22.1 — no resend import)
    ├── L~180-210  Sentry init, singleton_scheduler, session_timeout, admin_hardening
    │              (all pre-existing imports, no resend)
    ├── L~230-245  from lib.rate_limiting import (...)
    │              (Track 22.1 — no resend import)
    │
    ├── L~13560    from pm_routing import (auto_email_enabled, recipients_for_record_async, ...)
    │              (pre-existing — no resend import at module scope in pm_routing)
    ├── L~13580    _KIND_TO_COLLECTION = {...}
    ├── L~13591    ┌─ from lib.email_dispatch import ... ─────────────────────┐
    │              │ (Track 22.1B — NEW)                                        │
    │              │ imports: _filename_for, _is_severe_incident,               │
    │              │          _AUTO_EMAIL_DISPATCH_TASKS, schedule_auto_email,  │
    │              │          register_dispatcher as _register_email_dispatcher │
    │              │ lib/email_dispatch.py imports only asyncio + typing        │
    │              │ **NO RESEND IMPORT AT MODULE SCOPE**                       │
    │              └─────────────────────────────────────────────────────────────┘
    ├── L~13622    async def _dispatch_auto_email(kind, record):
    │              (body unchanged; imports resend INSIDE the function)
    │
    ├── L~14099    _register_email_dispatcher(_dispatch_auto_email)
    │              (Track 22.1B — NEW: wires the dispatcher into the lib scheduler)
    │
    ├── L~15234    /api/auto-email-preview endpoint uses _KIND_TO_COLLECTION
    │
    └── L~16000    @app.on_event("startup") handlers (51)
                   readiness flip flips app.state.ready = True (last handler)
```

## Invariants preserved by Track 22.1B

1. **SDK patch fires before any router or helper obtains `resend.Emails.send`.**
   - Track 21.2E installed the patch at L109-133. Track 22.1B did not touch L1-13590 except for the health-probes/rate-limiting imports at L~154/230 (Track 22.1) — none of which import resend.
   - The new `from lib.email_dispatch import ...` at L~13591 does not import resend either.
   - The dispatcher's `import resend` at L~13897 runs only at call time.

2. **Startup handler count and order unchanged.**
   - 51 handlers pre → 51 handlers post, byte-identical qualname list (verified by JSON snapshot).
   - Readiness-flip remains the last handler.

3. **Scheduler timing unchanged.**
   - `SCHEDULER_ENABLED=false` in preview: 0 background jobs fire. Verified via boot log ("scheduler disabled on this worker (preview / non-prod)").
   - `SCHEDULER_ENABLED=true` in production: 39 `asyncio.create_task` chains still fire from their original startup handlers.

4. **Middleware chain unchanged.**
   - 7 middleware, same classes, same option keys, same order (verified by JSON snapshot).

## Startup timing (informational)

- Wall-clock boot ~5s (unchanged relative to Track 22.1).
- Additional import cost of `lib/email_dispatch.py`: ~50µs (Python module load + parse).
- No observable startup regression.

## Verdict

🟢 **RUNTIME ORDER CERTIFIED.** SDK patch installs first, extracted lib imports do not touch Resend at module scope, dispatcher's own `import resend` remains inside the function body and returns the already-patched module.
