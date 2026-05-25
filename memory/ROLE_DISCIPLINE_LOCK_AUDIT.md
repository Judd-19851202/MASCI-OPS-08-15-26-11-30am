# ROLE_DISCIPLINE_LOCK_AUDIT.md
**Phase 18 · iter414 · 2026-05-25**

## Verdict
**LOCKED — PASS.** Every role sees only what doctrine permits. No role-creep regressions surfaced between iter413 and iter414. No hidden write actions. No accidental visibility leakage.

## Per-role lock
### Dispatch · OPERATIONAL COMMAND ONLY
| Sees | Cannot see |
|---|---|
| iter411 Command portal, 5-haul-type Issue Work drawer, board, governance findings, transfers + holds, fleet/utilization/idle (secondary), DLS health summary if also admin | Driver PII beyond name+CDL flag · PM project financials · Safety incident bodies · HR records |
- Write surface: assignment issuance · lifecycle transitions (via driver tap) · transfers · holds.
- No PM, Shop, Safety, or HR write affordances. **Verified by grep.**

### PM · PRODUCTION CONTINUITY ONLY
| Sees | Cannot see |
|---|---|
| iter409 `PmHaulActivityTile` (project-scoped) · iter396 `DispatchLifecycleTile` read-only filtered by `project_numbers` | Issue/cancel/reassign affordances |
- Write surface: **ZERO** on DLS surfaces.
- Empirical verification (iter409 testing-agent): DOM scan of PmHaulActivityTile returns empty interactive set.

### Shop / Fleet · FLEET CONTINUITY ONLY
| Sees | Cannot see |
|---|---|
| iter396 `DispatchLifecycleTile` showing BREAKDOWN signals · truck/trailer master continuity | Assignment issuance · PM production data · Safety body content · HR records |
- Write surface: equipment-master mutations · DVIR sign-off.
- No DLS write affordances.

### Safety · RESTRAINED VISIBILITY ONLY
| Sees | Cannot see |
|---|---|
| Existing iter319+iter318 Safety hub (no DLS tile mounted) | DLS internals · dispatch assignment bodies · driver sessions |
- `grep -r "DispatchLifecycleTile" pages/safety/`: **0 hits** ✅
- `grep -r "AssignmentCreateDrawer" pages/safety/`: **0 hits** ✅
- `grep -r "PmHaulActivityTile" pages/safety/`: **0 hits** ✅
- Doctrine: Safety stays intentionally quiet on DLS until 14-day post-live-ops review.

### HR · QUALIFICATION CONTINUITY ONLY
| Sees | Cannot see |
|---|---|
| `driver_qualification` lib data (CDL · approved-driver · driver_status). Surfaces into iter408 driver dropdown server-side | DLS internals · dispatch assignment bodies · governance findings |
- `grep -r "DispatchLifecycleTile" pages/Hr*.jsx`: **0 hits** ✅
- HR routes unchanged through Phase 12-17.

### Field Leadership (FL) · OPERATIONAL CONTINUITY ONLY
| Sees | Cannot see |
|---|---|
| iter319 + iter396 (scope="fl") DLS read-only tile · existing FL continuity records | Issuance · governance write actions · payroll · PII beyond what they manage |

### Driver (magic-link · no portal) · OWN-TRUCK ONLY
| Sees | Cannot see |
|---|---|
| Their assigned truck · their lifecycle states · sign-out · `/shift` self-start entry | Other drivers · fleet master · financials |
- Driver session API requires `dispatch_driver_sessions.shift_id` — cross-driver access impossible by data model.

## Role-creep scan (Phase 18 fresh grep)
| Probe | Hits | Status |
|---|:---:|:---:|
| `DispatchLifecycleTile` in `/pages/safety/` | 0 | ✅ |
| `DispatchLifecycleTile` in `/pages/hr*` | 0 | ✅ |
| `AssignmentCreateDrawer` outside dispatch | 0 | ✅ |
| `PmHaulActivityTile` outside `PmHub.jsx` | 0 | ✅ |
| `AdminDlsShiftQR` outside admin routes | 0 | ✅ |
| Driver write affordances on `PmHub` page | 0 | ✅ |
| Shop write affordances on PM data | 0 | ✅ |
| Safety routes touching `/api/dispatch/*` | 0 | ✅ |

## Cross-portal coexistence (intentional · verified safe)
- PmHub mounts BOTH iter409 `PmHaulActivityTile` AND iter396 `DispatchLifecycleTile` (production-awareness over operational-signals). No conflict.
- DispatchHub imports `DispatchTransfersTab` + `DispatchHoldsTab` from `AdminDispatch.jsx` — shared component, role-gated at parent route.
- Dispatch token can also be Admin token (admin is global by design).

## Phase 18 conclusion
**Role visibility doctrine intact.** No surgical fix needed. The 14-day post-live-ops review (per Phase 17 backlog) will revisit whether Safety/FL/HR should gain any DLS visibility — until then, restraint holds.
