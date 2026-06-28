TRANSPORTATION ROLE PERMISSION MATRIX
=====================================

DATE  : 2026-02-15
SCOPE : Every backend endpoint called by /transportation-operations/*
        with the post-Track-18.12C contract. Tokens evaluated: admin,
        dispatch, hr, pm, safety, shop, fl, multi-login portal_tokens.*,
        anonymous.

Legend:
  ✅ = accepts                ❌ = rejects (401/403)
  ADMIN-STRICT  = `Depends(require_admin_dep)` direct
  OPS-GUARD     = `Depends(ops_guard)` alias = `require_dispatch_or_admin_dep
                  or require_admin_dep` (admin fallback when no dispatch dep)
  CROSS-PORTAL  = `Depends(dashboard_guard)` = `require_portal_dep or
                  require_admin_dep` (any portal token)

│ Endpoint                                                          │ Gate         │ admin │ dispatch │ other portals │ anon │ Class │ Notes │
│-------------------------------------------------------------------│--------------│-------│----------│---------------│------│-------│-------│
│ GET  /api/operations/transportation/readiness                     │ helper       │ ✅    │ ✅       │ ✅            │ ❌   │ A     │ Mission Control foundation. |
│ GET  /api/admin/transportation/dashboard                          │ CROSS-PORTAL │ ✅    │ ✅       │ ✅            │ ❌   │ A     │ Compliance summary tile feed. |
│ GET  /api/admin/transportation/carriers                           │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Dispatcher-operational list. |
│ GET  /api/admin/transportation/carriers/{cid}                     │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Dispatcher carrier record read. |
│ GET  /api/admin/transportation/carriers/{cid}/workspace           │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Carrier workspace aggregate. |
│ POST /api/admin/transportation/carriers                           │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Admin write. |
│ PATCH /api/admin/transportation/carriers/{cid}                    │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Admin write. |
│ GET  /api/admin/transportation/persons                            │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Drivers list. |
│ GET  /api/admin/transportation/persons/{pid}                      │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Driver record read. |
│ GET  /api/admin/transportation/persons/{pid}/workspace            │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Driver workspace aggregate. |
│ POST /api/admin/transportation/persons                            │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Admin write. |
│ PATCH /api/admin/transportation/persons/{pid}                     │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Admin write. |
│ GET  /api/admin/transportation/trucks                             │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Trucks list. |
│ GET  /api/admin/transportation/trucks/{tid}                       │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Truck record read. |
│ GET  /api/admin/transportation/trucks/{tid}/workspace             │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Truck workspace aggregate. |
│ POST /api/admin/transportation/trucks                             │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Admin write. |
│ PATCH /api/admin/transportation/trucks/{tid}                      │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Admin write. |
│ GET  /api/admin/transportation/eligibility/{type}/{id}            │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Dispatcher must see eligibility. |
│ GET  /api/admin/transportation/documents/queue                    │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Compliance Document Center. |
│ GET  /api/admin/transportation/inspections/queue                  │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Compliance Inspection Center. |
│ GET  /api/admin/transportation/audit-timeline                     │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Governance trail. UI nav hidden from dispatch. |
│ GET  /api/admin/transportation/timeline/{type}/{id}               │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Per-entity compliance trail. |
│ GET  /api/admin/transportation/orientation/dashboard              │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Orientation summary. |
│ GET  /api/admin/transportation/orientation/modules                │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Module list (read). |
│ POST/PATCH/DELETE /api/admin/transportation/orientation/modules/* │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Module CMS writes. |
│ GET  /api/admin/transportation/orientation/modules/{id}/questions │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Questions list (read). |
│ POST/PATCH /.../questions(/*)                                     │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Question CMS writes. |
│ GET  /api/admin/transportation/orientation/assignments            │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Driver assignment list. |
│ GET  /api/admin/transportation/orientation/certificates           │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Certificate list. |
│ GET  /api/admin/transportation/automation/actions                 │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ Morning Queue read. |
│ PATCH /api/admin/transportation/automation/actions/{aid}          │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Resolve/dismiss writes. |
│ GET  /api/admin/transportation/automation/forecast                │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ A     │ 30-day forecast read. |
│ POST /api/admin/transportation/automation/run|dry-run             │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Automation runner. |
│ GET  /api/admin/transportation/automation/health                  │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Health monitor (admin diagnostic). |
│ GET  /api/admin/transportation/automation/digest/*                │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Digest engine surface. |
│ GET  /api/admin/transportation/automation/runs|events             │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Run history + dedupe ledger. |
│ GET  /api/admin/transportation/intelligence/cleanup-signals       │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ B     │ Mission Control Cleanup card. |
│ GET  /api/admin/transportation/intelligence/cleanup-signals/{key} │ OPS-GUARD    │ ✅    │ ✅       │ ❌            │ ❌   │ B     │ Cleanup drill-down. |
│ POST /api/admin/transportation/intelligence/cleanup-signals/{key}/materialize-actions │ ADMIN-STRICT │ ✅ │ ❌ │ ❌ │ ❌ │ C │ Admin write. |
│ GET  /api/admin/transportation/intelligence/dashboard             │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Executive analytics. |
│ GET  /api/admin/transportation/intelligence/recommendations       │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Admin scoring engine. |
│ GET  /api/admin/transportation/intelligence/predictions           │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Admin predictions. |
│ GET  /api/admin/transportation/intelligence/dispatch-learning     │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Dispatcher-learning meta. |
│ GET  /api/admin/transportation/hr-sync(/*)                        │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ HR ↔ Transportation sync diag. |
│ GET/PATCH /api/admin/transportation/email-routes(/*)              │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Email routing CMS. |
│ GET  /api/admin/transportation/rate-schedules                     │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Rate CMS read. |
│ POST /api/admin/transportation/rate-schedules                     │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Rate CMS write. |
│ GET  /api/admin/transportation/search/* (relationships, suggest)  │ ADMIN-STRICT │ ✅    │ ❌       │ ❌            │ ❌   │ C     │ Cross-domain admin search. |
│ POST /api/dispatch/login                                          │ public       │ —     │ ✅       │ —             │ ✅   │ —     │ Dispatch portal login. |
│ GET  /api/dispatch/transportation/recommendation                  │ DISPATCH/ADMIN│ ✅   │ ✅       │ ❌            │ ❌   │ A     │ Dispatch decision surface. |
│ POST /api/dispatch/transportation/recommendation/audit            │ DISPATCH/ADMIN│ ✅   │ ✅       │ ❌            │ ❌   │ A     │ Dispatch action audit write. |
│ GET  /api/dispatch/fleet/status                                   │ DISPATCH/ADMIN│ ✅   │ ✅       │ ❌            │ ❌   │ A     │ Live ops fleet status. |
│ POST /api/dispatch/fleet/defects/{id}/clear                       │ DISPATCH/ADMIN│ ✅   │ ✅       │ ❌            │ ❌   │ A     │ Dispatch operational write. |
│ POST /api/dispatch/fleet/units/{u}/oos                            │ DISPATCH/ADMIN│ ✅   │ ✅       │ ❌            │ ❌   │ A     │ Dispatch OOS write. |
│ GET  /api/dispatch/command/*                                      │ DISPATCH/ADMIN│ ✅   │ ✅       │ ❌            │ ❌   │ A     │ Dispatch command center. |

Operational reading
───────────────────
• Class A surfaces (37) are dispatcher-operational. Dispatch + admin
  both read real data. Other portal tokens (HR/PM/Safety/etc.) are
  NOT granted access here — their portals have their own scoped
  endpoints elsewhere on the platform.
• Class B (3) surfaces are dispatcher-read-only summaries
  (cleanup-signals + drill-down). The Mission Control Cleanup card
  loads for both dispatch and admin.
• Class C surfaces (governance / writes / admin-only analytics) stay
  admin-strict. The frontend either hides them from dispatch nav
  (Administration group) or renders TxOpsRestrictedData when deep-
  linked. No data leak, no overlay.
• Class D = ReportsView (ComingSoon — intentional placeholder).
