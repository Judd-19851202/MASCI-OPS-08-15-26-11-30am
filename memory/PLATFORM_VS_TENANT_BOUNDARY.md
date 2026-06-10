# PLATFORM vs TENANT BOUNDARY
**FORGEDOPS Dispatch Command Center V1 · Architecture Audit · 2026-02-10**
**Status:** Architecture-only · No code · Audit-locked

> **Pillar contract:** Powerful · Simple · Beautiful · Trusted · Proven.
> **Doctrine:** FORGEDOPS is the platform. MASCI is Customer #1. Every
> dispatch/PM/shop/operations decision in this build must be
> platform-first and tenant-configurable. MASCI-specific behavior is
> permitted ONLY where a third-party integration (Motive, MaintainX,
> FleetWatcher) forces it.

---

## §1 · The Boundary Rule (one sentence)

**Platform owns** the contract (data model, lifecycle states, RBAC,
audit, integration framework, UI shells).
**Tenant owns** the configuration (catalog values, thresholds, channels,
which integrations are live, which roles exist, branding).

---

## §2 · Platform-Owned Surfaces (must NEVER be tenant-specific)

| Surface | Why it is platform |
|---|---|
| **Asset Spine doctrine** (`equipment_master` is canonical) | Identity contract — every tenant follows the same model |
| **Dispatch lifecycle state graph** (13 canonical states, forgiving classifier) | Shared cycle vocabulary; tenant cannot rename states |
| **Audit triple** (`admin_audit_log` + `audit_events` + `master_history`) | Trust contract |
| **Auth deps** (`require_admin`, `require_any_portal_token`, `require_dispatch_or_admin`) | Permission contract |
| **Append-only collections** (`dispatch_state_events`, `dispatch_continuity_events`, `haul_cycles`) | Truth provenance |
| **Integration framework** (`integration_settings`, `asset_mappings`, `employee_mappings`, `sync_logs`, `error_logs`, `motive_events`, `integration_health`) | Tenant flips integrations on/off; the wiring is shared |
| **SessionStatusOverlay + errorClassification** | Trust UX is uniform |
| **OfflineQueue + payload repair** | Resiliency contract |
| **Operations Center role-visibility map** (`ROLE_VISIBILITY`) | Cross-portal roll-up grammar |
| **All `/api/*` route paths** | Renaming routes breaks tenant clients |

---

## §3 · Tenant-Owned Configuration (must be configurable per tenant)

| Configuration | Storage today | Tenant access path |
|---|---|---|
| **Tenant ID** | `X-Tenant-Id` header, default `"masci"` (`_resolve_tenant` in `routes/dispatch_lifecycle.py`) | Header carried by every read/write |
| **Material catalog** | `dispatch_assignment_seeds.py` constants (MASCI-hardcoded today) | **Platform debt** — must be promoted to a `tenant_dispatch_catalog` collection |
| **Source / destination locations** | `SEEDED_SOURCES`, `SEEDED_DESTINATIONS`, `SEEDED_PICKUP_LOCATIONS`, `SEEDED_DROPOFF_LOCATIONS` (MASCI-hardcoded) | **Platform debt** — same as above |
| **Haul types** | `HAUL_TYPES` (Material / Equipment Move / Tanker) — generic; safe | None |
| **Truck / trailer categories** | `truck_categories`, `trailer_categories` lists in `dispatch_driver.py` & `fleet_ops.py` (MASCI-hardcoded) | **Platform debt** — must move to `tenant_asset_taxonomy` collection |
| **DVIR checklists** | `checklists_fleet.py` (MASCI-hardcoded) | **Platform debt** — promote to `tenant_checklists` |
| **Integration credentials** | `integration_settings` (per provider, single row today) | **Acceptable for V1**; per-tenant scoping in V2 |
| **SMS templates** | `sms_provider.py` magic-link body (generic) | None |
| **Notification thresholds** | `command_center_thresholds` | Per-tenant in V2 |
| **Branding** | `MasciLogo`, palette names (`paletteFor("dispatch")`) | **Platform debt** — `tenant_brand` registry |
| **OFF_SHIFT / WAITING reasons vocabulary** | Implicit free-text today | **Platform debt** — tenant-configurable enum |

---

## §4 · MASCI-Specific Behavior We Will Tolerate in V1

These are tenant-injected behaviors that V1 **may** ship as MASCI defaults
because the platform refactor for them is bigger than Dispatch Command
Center. They MUST carry a `# TENANT: masci` comment and be loaded by a
tenant resolver so they can be replaced later without rewriting Dispatch.

| Behavior | Reason | V2 promotion path |
|---|---|---|
| MASCI truck/trailer categories list | Categories are tenant-defined fleet taxonomy | Move to `tenant_asset_taxonomy.categories[]` |
| MASCI haul source / destination seed lists | Field operators expect specific plant/yard names | Move to `tenant_dispatch_catalog.sources[]` / `.destinations[]` |
| MASCI material catalog (`flat_material_options`) | Material names are operationally specific | Move to `tenant_dispatch_catalog.materials[]` |
| Default tenant_id = "masci" | Single-tenant launch | Resolve from sub-domain / auth claim in V2 |
| MASCI branding (logo, color palette) | Customer #1 visual identity | `tenant_brand` registry |

**Forbidden in V1:** hardcoding any new MASCI-specific logic into
Dispatch Command Center code paths beyond what is listed above.

---

## §5 · Tenant Header Discipline (mandatory)

Every Dispatch Command Center read **must** accept `X-Tenant-Id`:

```
GET  /api/dispatch/assignments/board   ← already supports X-Tenant-Id ✅
GET  /api/asset-spine/assets           ← does NOT yet support X-Tenant-Id ⚠ (V1 build will add)
GET  /api/operations-center            ← does NOT yet support X-Tenant-Id ⚠ (V1 build will add)
GET  /api/dispatch/haul-activity       ← already supports X-Tenant-Id ✅
GET  /api/shop/fleet/defects           ← does NOT yet support X-Tenant-Id ⚠ (V1 build will add)
```

**Default tenant resolution** stays `"masci"` until the multi-tenant
auth claim path lands. Every query against the four collections that
already have a `tenant_id` field (`dispatch_assignments`,
`dispatch_state_events`, `haul_cycles`, `dispatch_continuity_events`)
must filter by tenant.

`equipment_master`, `equipment_inspections`, `fleet_defects`,
`fleet_status`, `asset_mappings`, `motive_events`, `daily_reports`,
`employees`, `projects` do **not** yet carry `tenant_id`. **V1 will
NOT migrate these**; instead it will resolve the tenant from the
operator's portal token and gate reads at the API layer until the
backfill sprint lands.

---

## §6 · Decision Matrix — Where to Put Each New Capability

| New capability we are about to build | Lives where |
|---|---|
| Live Fleet Board endpoint | Platform · `routes/dispatch_command_center.py` (new) |
| Live Driver Board endpoint | Platform · same router |
| Live Job Board endpoint | Platform · same router |
| Live Haul Board endpoint | Platform · same router (composes `dispatch_assignments` + `haul_cycles`) |
| Driver Comms broadcast SMS | Platform · reuses `services/sms_provider.py` |
| Shop Command Feed | Platform · joins `fleet_defects` + `dispatch_continuity_events` |
| PM Visibility tile (cross-Dispatch) | Platform · composes `/api/dispatch/haul-activity` + Asset Spine assignment join |
| Cross-job Operations Center board | Platform · extends existing `/api/operations-center` |
| Tenant material / source / destination catalog | Tenant configurable (V2 backlog; V1 reads from `dispatch_assignment_seeds.py` MASCI defaults) |

---

## §7 · STOP Condition

Anything that requires hardcoding the literal string `"MASCI"` or a
MASCI plant/yard/material name inside V1 Dispatch Command Center
**business logic** is forbidden. Tenant-specific defaults are loaded
from `dispatch_assignment_seeds.py` (existing) at request time only —
the seed list itself is technical debt to be removed when the
`tenant_dispatch_catalog` collection lands.

---

## §8 · Acceptance Criteria for V1

1. Every new Dispatch Command Center endpoint accepts `X-Tenant-Id` and
   resolves via `_resolve_tenant(...)`.
2. Every aggregation query filters by `tenant_id` on collections that
   carry it.
3. No new MASCI-string literal exists in any route file beyond the
   `DEFAULT_TENANT_ID = "masci"` constant already present.
4. Every new component (Live Fleet / Driver / Job / Haul board) is
   stateless re: tenant — it reads the tenant header and renders.
5. Every new collection writes a `tenant_id` field.

---

**Verdict:** Boundary is clear, defensible, and already partially
enforced by the dispatch_lifecycle module. The build proceeds.
