# Platform Language Constitution · Applied Registry

> Authoritative mapping of every legacy term to its canonical replacement,
> as actually applied to the codebase by Track 18.04.
>
> The Constitution lives in
> `TRACK_18_03_PLATFORM_LANGUAGE_CONSTITUTION.md`.
> The applied scope and file list lives in
> `TRACK_18_04_PLATFORM_LANGUAGE_MIGRATION.md`.

---

## Workspace identity

| Legacy term | Canonical user-facing term | Status |
|---|---|---|
| Dispatch Portal | **Transportation Operations** | Applied across hub card, login chrome, top bars, branded emails, footer, access-mgmt eyebrow, guidance titles |
| Transportation Portal | **Transportation Operations** | Already eliminated (Track 18 Phase E) |
| Dispatch System | — never adopted — | n/a |
| PM Portal | **Project Management** | Applied |
| PM Hub | **Project Management** (or "PM Home" in breadcrumb back-link) | Applied |
| HR Portal | **Human Resources** | Applied |
| Safety Portal | **Safety Operations** | Applied |
| Shop Portal | **Shop Operations** | Applied |
| Shop Hub | **Shop Operations** | Applied |
| Admin Portal | **Administration** | Applied |
| Admin Console | **Administration** | Applied |
| Office Portals | **Operations** (anonymous Hub section title) | Applied |
| Your Portals | **Your Workspaces** | Applied |
| Other Portals | **Other Workspaces** | Applied |
| Open Portal · Open Console (CTA) | **Open Workspace** | Applied |
| Field Leadership Portal | **Field Leadership** | Applied |

## Operational nouns

| Legacy term | Canonical | Status |
|---|---|---|
| Forbidden · Unauthorized · 403 · Access Denied | **Restricted for your role** | Applied (Track 18.02) |
| TODO · Pending · Outstanding | **Action Required** | Applied (Track 18.02) |
| Active · Green · OK (in readiness) | **Ready** | Applied (Track 18.02) |
| Warning · Caution · Alert · Yellow | **Needs Attention** | Applied (Track 18.02) |
| Audit Log · Activity Log · Event Stream | **Audit Timeline** | Applied (Track 18.02) |
| Sidebar · Side Panel · Right Panel | **Right Rail** | Applied (Track 18.00 Phase D) |
| Universal Search · Global Search · Find · Lookup | **Search** | Applied (Track 18.02) |
| Transportation Dashboard · Operations Home · Hub | **Mission Control** | Applied (Track 18 Phase E) |

## Email + PDF surfaces

| Legacy text | Canonical text | Status |
|---|---|---|
| `[MASCI] Reset your PM Portal password` | `[MASCI] Reset your Project Management password` | Applied |
| `[MASCI] Reset your Shop Portal password` | `[MASCI] Reset your Shop Operations password` | Applied |
| `[MASCI] Reset your HR Portal password` | `[MASCI] Reset your Human Resources password` | Applied |
| `[MASCI] Your Safety Portal account — temporary password inside` | `[MASCI] Your Safety Operations account — temporary password inside` | Applied |
| `[MASCI] Reset your Field Leadership Portal password` | `[MASCI] Reset your Field Leadership password` | Applied |
| Welcome to the MASCI PM Portal | Welcome to MASCI Project Management | Applied |
| Welcome to the MASCI Shop Portal | Welcome to MASCI Shop Operations | Applied |
| `Your MASCI HR Portal account` (headline) | `Your MASCI Human Resources account` | Applied |
| `Your MASCI Safety Portal account` (headline) | `Your MASCI Safety Operations account` | Applied |
| `Your MASCI Field Leadership Portal account` (headline) | `Your MASCI Field Leadership account` | Applied |
| Footer line 2 `automated operational notice · HR Portal` | `automated operational notice · Human Resources` (and all 6 portals) | Applied |
| PDF `<title>Welcome — MASCI PM Portal</title>` | `<title>Welcome — MASCI Project Management</title>` | Applied |
| PDF eyebrow tag `PM Portal · Welcome` | `Project Management · Welcome` | Applied |

## Access-management UI

| Surface | Legacy text | Canonical text | Status |
|---|---|---|---|
| AdminDispatchUsersPanel eyebrow | Dispatch Portal | Transportation Operations | Applied |
| AdminDispatchUsersPanel impersonation prompt | Preview Dispatch Portal as … | Preview Transportation Operations as … | Applied |
| AdminHRUsersPanel eyebrow | HR Portal | Human Resources | Applied |
| AdminSafetyUsersPanel eyebrow | Safety Portal | Safety Operations | Applied |
| AdminFieldLeadershipUsersPanel eyebrow | HR Portal | Human Resources | Applied |

## Preserved (legal / engineering / historical)

| Surface | Term preserved | Reason |
|---|---|---|
| FastAPI route prefixes | `/api/admin/*`, `/api/dispatch-portal/*`, `/api/safety-portal/*`, `/api/hr/*`, `/api/shop/*`, `/api/pm/*`, `/api/field-leadership-portal/*` | URL contracts — locked by 200+ tests + every authenticated client |
| Auth header aliases | `X-Admin-Token`, `X-Dispatch-Token`, `X-Safety-Token`, `X-HR-Token`, `X-Shop-Token`, `X-PM-Token` | Header contracts |
| localStorage keys | `masci.admin.token`, `masci.dispatch.token`, etc. | Auth state contracts |
| MongoDB collections | `transport_persons`, `dispatch_assignments`, `transport_trucks`, `carriers`, etc. | No data migration |
| Test IDs | `admin-side-nav-v2`, `dispatch-hub`, `admin-transportation-page`, `hub-section-dispatch-portal`, etc. | Locked by 18.01 + 18.02 testid contracts |
| Python identifier portal codes | `portal="PM"`, `portal="HR"`, etc. | Constitution carve-out — only user-visible *output* must change |
| Sub-feature names | Dispatch Board · Live Map · Haul Ledger · Pre-Op · JHP · Trench Safety · DVIR | These are feature/product names, not workspace identities |
| Historical track docs | `/app/memory/TRACK_*.md` | Provenance — preserve as the record of what shipped at each phase |
| Operator-review guides referencing legacy names | `/app/memory/*OPERATOR_REVIEW*.md` | Historical record |

---

**Source of truth:**
- Constitution: `TRACK_18_03_PLATFORM_LANGUAGE_CONSTITUTION.md`
- Applied scope + file list: `TRACK_18_04_PLATFORM_LANGUAGE_MIGRATION.md`
- Inventory: `PLATFORM_LANGUAGE_MIGRATION_INVENTORY.md`
- Guidance audit: `OPERATIONAL_GUIDANCE_CENTER_AUDIT.md`
- Regression lock: `backend/tests/test_track_18_04_platform_language_migration.py`
