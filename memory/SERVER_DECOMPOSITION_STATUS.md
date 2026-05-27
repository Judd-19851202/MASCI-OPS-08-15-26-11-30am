# Server Decomposition Status — Phase IV-BETA.5A-P4B

*iter437 · 2026-02-27*
*Status: 🟢 ONE EXTRACTION COMPLETE · catalog updated*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. server.py size & route distribution

| Metric | Value |
|---|---|
| Line count | 11,315 (−84 since pre-P4B) |
| `@api_router.get / post / etc` in-file | ~335 |
| `app.include_router(...)` calls | 26+ |

## II. Decomposition roster

### 🟢 EXTRACTED SAFELY (this iter + prior)

| Router | File | Extracted in | Tests |
|---|---|---|---|
| Guidance content (5 endpoints) | `routes/guidance_routes.py` | **iter437 IV-BETA.5A-P4B (this phase)** | 9/9 green |
| Training center | `routes/training_center.py` | (prior iter) | covered |
| PM | `routes/pm_routes.py` | iter437 (P0 fix iter) | multi-suite |
| Shop parts | `routes/shop_parts.py` | (prior iter) | shop suite |
| Dispatch lifecycle (iter392) | `routes/dispatch_*.py` | iter392 | dispatch suite |
| Governance (admin-strict) | `routes/governance.py` | prior | covered |
| Governance health | `routes/governance_health.py` | iter437 IV-BETA.5A-P1A | 21/21 green |
| Admin digest config / K4 / etc. | `routes/admin_*.py` | various | covered |

### 🟡 NEXT EXTRACTION CANDIDATES — ranked low → medium risk

| Order | Group | server.py lines | Risk | Estimated effort |
|---|---|---|---|---|
| 1 | Health / version (`/health`, `/healthz`, `/health/full`, `/version`) | 501 – 901 | 🟢 low | 1 hour |
| 2 | Dev / ops-manual snapshots | 951 – 1265 | 🟢 low (dev-token gated · already isolated) | 2 hours |
| 3 | Admin export endpoints (CSV streams) | 1377 – 1488 | 🟡 medium (admin-strict; many model imports) | 3–4 hours |
| 4 | Admin guidance-coverage endpoints | ~547 – 600 | 🟡 medium (depends on `require_admin_strict`) | 1 hour |

### 🔴 HIGH-RISK / DEFERRED · DO NOT EXTRACT YET

| Group | Reason |
|---|---|
| Auth (login / refresh / multi-login / cookie set-up) | Core platform safety — auth playbook requires manual coordination |
| Safety escalation endpoints | Compliance-critical |
| Notification engine endpoints | Per directive: "NO notification engine rewrites" |
| Session reset / portal scope enforcement | Cross-cutting · touches every portal |
| Startup `app.include_router(...)` block · scheduler arming · index ensures | Could destabilise boot |
| `_guidance_caller_scopes` helper | Depends on internal token validators · best left injected, not moved |

## III. Cumulative extractions (last 3 iterations)

| Iteration | New extractions | server.py LOC delta |
|---|---|---|
| IV-BETA.5A-P3 | 0 (catalog only) | 0 |
| IV-BETA.5A-P4B (this iter) | 5 endpoints (guidance) | **−84** |

The decomposition cadence is intentionally slow — **stability > speed**.

## IV. Per-iteration extraction rule

Operator-blessed extractions follow this rule:

1. Pick **one** group from the LOW-risk band.
2. Mirror an existing extraction pattern (`build_<name>_router(db, deps)`).
3. Run all regressions before and after.
4. Add a small extraction-specific test asserting JSON shape parity.
5. Declare a checkpoint if the operator wants to lock the post-extraction state.

## V. Doctrine reaffirmed

- ✅ One extraction this iter · cleanly reversible
- ✅ Catalog ranked for future operator authorisation
- ✅ 🔴 HIGH-RISK groups documented as off-limits
- ✅ No startup-order or middleware changes
- ✅ Preview only · NO production deploy
