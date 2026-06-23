# TRACK 15.69B · EMAIL_ROUTING_V2 Source-of-Truth Audit (READ-ONLY)

_2026-06-23 · Forensic audit · zero mutations_

## TL;DR

**OUTCOME C** — `EMAIL_ROUTING_V2` does NOT exist as an explicit env var anywhere. Production reads `os.environ.get("EMAIL_ROUTING_V2")` → returns `None` → normalized to **`False`** → **legacy routing is universally active in production**.

The previous certifications' claim that "EMAIL_ROUTING_V2 remains FALSE" is **behaviorally correct** but the underlying mechanism is "**unset env defaults to false**", not "env explicitly set to false". Both produce identical behavior because the code reads `(os.environ.get("EMAIL_ROUTING_V2") or "")` then checks against `("1","true","yes","on")`.

## Phase 1 · Global Code Reference Audit

**Single source of truth (verified)**: `backend/email_routing_v2.py:93-98`

```python
def routing_v2_enabled() -> bool:
    """When false, every resolver call short-circuits to its legacy
    provider — exact pre-15.65 behaviour. Production stays OFF until
    operator approval."""
    raw = (os.environ.get("EMAIL_ROUTING_V2") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")
```

**Code call sites that gate on this function** (verified via grep):

| File | Line | Purpose |
|---|---:|---|
| `backend/email_routing_v2.py` | 200 | `resolve()` short-circuits to `legacy_provider()` if `not routing_v2_enabled()` |
| `backend/email_routing_v2.py` | 401 | `resolve_and_audit()` short-circuits if `not routing_v2_enabled()` |

**Modules that import `email_routing_v2`** (and therefore go through the flag check):

| File | Line | Import |
|---|---:|---|
| `backend/health_monitor.py` | 64 | `resolve_and_audit as _v2_resolve` |
| `backend/outage_alerts.py` | 105 | `resolve_and_audit as _v2_resolve` |
| `backend/pm_routing.py` | 368 | `write_audit as _v2_audit` |
| `backend/safety_digest.py` | 86 | `resolve_and_audit as _v2_resolve` |
| `backend/server.py` | 13344, 13367, 13545, 13626 | `invalidate_cache`, `resolve`, `write_audit` |
| `backend/lib/field_submitter_identity.py` | 186 | `resolve_and_audit as _v2_resolve` |
| `backend/lib/operator_digest.py` | 333 | `resolve_and_audit as _v2_resolve` |

**No other source of truth exists.** No `feature_flag` table, no `settings` collection key, no YAML config file, no separate `routing_v2` flag.

## Phase 2 · Environment Audit

| Environment | `EMAIL_ROUTING_V2` present? | Value | Source |
|---|:-:|---|---|
| **Preview pod `.env`** | ❌ **NO** | (unset) | `grep EMAIL_ROUTING /app/backend/.env` → 0 matches |
| **Preview process env** | ❌ **NO** | (unset) | `env \| grep EMAIL_ROUTING` → 0 matches |
| **Production (`mascidocs.com`)** | ❌ **NO** (as reported by operator inspection of Emergent deployment secrets) | (unset) | Operator-confirmed; verified by behavior (next phase) |

**The flag is unset in every environment.** This is by design — the code's default behavior with an absent env var is to return `False` (legacy routing).

## Phase 3 · Database Audit

```
Collections matching settings/feature/flag/config/routing: ['digest_settings', 'email_routes', 'email_routing_audit_v2', 'integration_settings']
```

| Collection | Stores `EMAIL_ROUTING_V2`? |
|---|:-:|
| `settings` | ❌ does not exist |
| `feature_flags` | ❌ does not exist |
| `system_settings` | ❌ does not exist |
| `configuration` | ❌ does not exist |
| `tenant_branding` | ❌ no `EMAIL_ROUTING` key match in any doc |
| `digest_settings` | ❌ unrelated (digest cadence config) |
| `email_routes` | ❌ stores route docs only, not the flag |
| `email_routing_audit_v2` | ❌ stores audit rows only |
| `integration_settings` | ❌ unrelated (third-party integrations) |

**EMAIL_ROUTING_V2 is not stored in Mongo anywhere.** There is no DB-backed override path.

## Phase 4 · Runtime Trace

For every routing call, the execution chain is:

```
Caller (e.g., safety_digest.py:86)
    ↓
email_routing_v2.resolve_and_audit(db, "SAFETY_DIGEST_TO", legacy_provider=...)
    ↓
email_routing_v2.resolve(db, "SAFETY_DIGEST_TO", ...)
    ↓
line 200:  if not routing_v2_enabled():
              return RouteResolution(source="legacy", to=legacy_provider(), ...)
    ↓
legacy email_routing.get_value(db, "safety_forms_to") OR env var read
    ↓
Resend send envelope
```

Because `routing_v2_enabled()` returns `False` (env unset → empty string → not in the truthy set), every call returns at line 202-214 with `source="legacy"`. The DB read at line 217 (`_get_route_doc(...)`) is **never reached** in production.

**Single source of truth (proven)**: `os.environ.get("EMAIL_ROUTING_V2")` — present → V2 / absent → legacy.

## Phase 5 · Certification Validation

| Previous claim | Truth status |
|---|:-:|
| "EMAIL_ROUTING_V2 remains FALSE" (15.69 deliverables) | ✅ behaviorally correct |
| "Flag is set to `false` in production env" | ❌ the flag is **UNSET**, not explicitly `false` |
| "Production reads the flag" | ✅ yes — every routing call invokes `routing_v2_enabled()` |
| "Legacy routing is active" | ✅ proven by code path: line 200 short-circuit |
| "V2 routing is NOT active" | ✅ proven by code path: DB read at line 217 unreachable |

**The certifications were based on actual evidence (the code path), but the language conflated "unset" with "explicitly false". The behavior is identical, but the operator-facing operation is different:**
- Cutover = **ADD** `EMAIL_ROUTING_V2=true` to production env (not "change false to true")
- Rollback = **REMOVE** the env var OR set it to `false` (either works because the code treats both as false)

## Phase 6 · Executive Answers

```
1. Does EMAIL_ROUTING_V2 exist?
   ✅ YES, as a code-level concept (backend/email_routing_v2.py:97).
   ❌ NO, as a deployed env var in any environment (preview or production).

2. Where does it exist?
   - As a Python env-var lookup: backend/email_routing_v2.py:97
   - As 2 gate checks: backend/email_routing_v2.py:200, 401
   - Referenced (docs) in: health_monitor.py:61, outage_alerts.py:102,
     lib/field_submitter_identity.py:184/279, server.py:13371
   - NOT in: .env files, Emergent deployment secrets, Mongo collections,
     YAML configs.

3. What is its current value?
   At runtime: os.environ.get("EMAIL_ROUTING_V2") → None
   After normalization: "" → not in ("1","true","yes","on") → False

4. Does production read it?
   YES — every routing call invokes routing_v2_enabled() which reads
   os.environ at every call (no caching).

5. If not, what does production read?
   N/A — production DOES read it. It reads None (unset), which
   normalizes to False.

6. Is legacy routing active?
   ✅ YES. Every routing call returns source="legacy" at line 202
   because the flag normalizes to False.

7. Is V2 routing active?
   ❌ NO. The DB read at line 217 is unreachable while the flag is unset.

8. Is cutover still required?
   ✅ YES, if the operator wants V2's DB-driven routing in production.
   The cutover step is: ADD `EMAIL_ROUTING_V2=true` to the production
   environment (Emergent deployment secrets) and restart the backend.

9. What exact action must operator perform?
   In Emergent deployment secrets:
     - Add NEW env var: KEY = EMAIL_ROUTING_V2 · VALUE = true
     - Save and trigger backend restart.
   Rollback: delete the env var OR set value=false; restart.

10. GO or NO-GO?
    🟢 GO — for understanding and certification correction. The
    audit confirms the certification's behavioral claim (legacy active)
    is correct, even though the wording about "flag set to false"
    should be amended to "flag unset / effectively false".

    🟢 GO — for Track 15.69 cutover, when authorized. The operator
    knows the exact action: add the env var in Emergent secrets.
```

## Net Findings

| Question | Answer |
|---|:-:|
| Was production routing already V2? | ❌ NO — legacy is active |
| Did certifications mislead? | ⚠️ PARTIAL — behaviorally correct, but language imprecise |
| Is any code change required? | ❌ NO — code is correct |
| Is any DB change required? | ❌ NO — DB is correct |
| Is any cutover action different from previous runbooks? | ⚠️ MINOR — the runbook should say "ADD env var" not "FLIP env var" |

## Recommended Correction to Track 15.69 Runbook

Replace the phrase "Set `EMAIL_ROUTING_V2=true`" with the more precise:

> **Add a new environment variable** `EMAIL_ROUTING_V2 = true` to the production deploy's secrets (it does not currently exist). Save, then trigger backend restart.

And replace rollback phrase "Set `EMAIL_ROUTING_V2=false`" with:

> **Either delete the env var** `EMAIL_ROUTING_V2` from production secrets, **or set its value to `false`**. Both result in legacy routing being restored.

This is a documentation-only correction — no code change, no behavior change.

## Verdict

✅ **Forensic audit complete. No production action taken. No code modified. No env modified. No DB modified.**

🟢 **Track 15.69 cutover remains GO with the documentation correction above. The operator's next step is to ADD `EMAIL_ROUTING_V2=true` to production deploy secrets when authorized.**
