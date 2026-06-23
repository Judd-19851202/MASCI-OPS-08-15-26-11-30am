# TRACK 15.70 · Module Certification (Phase 6)

_Generated 2026-06-22_

## The Honest Verdict First

❌ **Runtime module enable/disable is NOT implemented.**

The platform currently ships **all modules enabled** for every
customer. There is no `tenant_branding.modules_enabled` field, no
`MODULES_ENABLED=` env var, no per-route module gate, no frontend
feature-flag layer.

A customer who buys "Safety only" today would still see Field, PM,
Shop, Dispatch, and HR portals in their Hub. The portals would be
functional but unbilled — not technically a defect, but commercially
a real gap if ForgedOps wants to sell modular SKUs.

## What WOULD Be Needed (Track 16.x candidate)

### Backend gate

```python
# In tenant_branding doc
{
  "_id": "customer_2",
  "modules_enabled": ["core", "safety", "pm"]  # subset of {"core","pm","safety","shop","dispatch","hr"}
}

# In each module router init
def require_module(module: str):
    async def _check(branding = Depends(get_branding)):
        if module not in branding.get("modules_enabled", []):
            raise HTTPException(403, f"Module '{module}' not enabled for this tenant")
    return _check

@safety_router.get("/safety/daily-reports", dependencies=[Depends(require_module("safety"))])
...
```

~60 LOC + per-module wiring (~20 LOC per module × 6 modules = ~180 LOC).

### Frontend gate

```jsx
const { modules } = useBranding();
{modules.includes("safety") && <Link to="/safety">Safety</Link>}
{modules.includes("dispatch") && <Link to="/dispatch">Dispatch</Link>}
```

Apply across Hub.jsx, side-nav components, and the role-landing pages.
Estimated ~30 LOC.

### Provisioning

`tenant_branding.modules_enabled` becomes the source of truth. Set at
provision time per the customer's SKU.

## Current Behavior (without module gating)

| Module | Enabled for MASCI? | Enabled for Customer #2? | Configurable? |
|---|:-:|:-:|:-:|
| Core (auth, Hub, branding) | ✅ | ✅ | always-on (correct) |
| PM (project management) | ✅ | ✅ | always-on |
| Safety (daily reports, incidents, inspections) | ✅ | ✅ | always-on |
| Shop (shop ops, equipment care) | ✅ | ✅ | always-on |
| Dispatch (driver assignments, shift QR) | ✅ | ✅ | always-on |
| HR (time off, payroll variance) | ✅ | ✅ | always-on |

## Acceptable for Initial Customer #2 Sale?

**YES, with a sales caveat.**

ForgedOps can sell Customer #2 the entire platform (the "MASCI Suite")
as a single bundle today. The customer gets all six modules. There is
no functional or security blocker — the modules simply aren't gated.

ForgedOps **cannot** offer tiered SKUs ("Safety only" / "Dispatch
only" / "Core + Safety") today. That requires the Track 16.x module
gating work.

## Verdict

| Scenario | Status |
|---|:-:|
| Sell Customer #2 the full bundle | ✅ READY |
| Sell Customer #2 a "Safety-only" tier | ❌ NOT READY (no gating) |
| Sell Customer #5 a "PM + Dispatch" tier | ❌ NOT READY (no gating) |

⚠️ **PARTIAL** — full-bundle sales are READY; tiered SKUs require Track
16.x module gating (~270 LOC across backend + frontend).
