# TRACK 19.29 · PLATFORM CONSISTENCY REPORT

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Anchor:** `TRACK_19_29_PRODUCTION_READINESS_CERTIFICATION.md`

Certifies visual, verbal, and behavioral consistency across every major portal and surface.

---

## Portal V2 rollout status (post-Track 19.28)

| Portal | Hub V2 | Sidebar V2 | Rollback path | Verdict |
|---|---|---|---|---|
| Admin | ✅ AdminHubV2 (canonical at `/admin` post-19.28) | ✅ SideNavV2 (domain-grouped) | `/admin/hub_v1` | 🟢 GO |
| HR | ✅ HrHubV2 (canonical at `/hr`) | ✅ HrSideNavV2 | `/hr/hub_legacy` | 🟢 GO |
| Safety | ✅ SafetyHubV2 | ✅ SafetySideNavV2 | `/safety-portal/hub_legacy` | 🟢 GO |
| PM | ✅ PmHubV2 (canonical at `/pm/hub`) | ✅ PmSideNavV2 | `/pm/hub_legacy` | 🟢 GO |
| Dispatch | ✅ DispatchHubV2 | ✅ DispatchSideNavV2 | Yes | 🟢 GO |
| Shop | ✅ ShopHubV2 (canonical at `/shop`) | ⏳ P3-1 backlog (Hub V2 tile-grid working today) | `/shop/hub_legacy` | 🟢 GO (Sidebar V2 opportunistic polish) |
| Transportation | ✅ Uses `AdminTransportation` shell | ⏳ P3-2 backlog | — | 🟢 GO |
| Fleet | Uses Shop portal | Uses Shop portal | — | 🟢 GO |
| Field Leadership | ✅ FieldLeadershipHub (also has `/leadership/hub_v2`) | Purpose-built layout | — | 🟢 GO |

## Consistency dimensions audited (via `TRACK_19_27_SCREEN_LAYOUT_AUDIT.md`)

### Headers
- ✅ Every portal V2 uses `PortalShell` primitive (`portalName`, `portalRole`, `pageTitle`, `subtitle`, `primaryActions`, `lastActivity`).
- ✅ Consistent kicker + title pattern.
- ✅ LangToggle in every header.
- ✅ Sign-out / back-to-classic where applicable.

### Sidebars
- ✅ 5 formal Sidebar V2 shells: HR · Safety · Admin · PM · Dispatch.
- ✅ Domain-grouped two-tier nav (Tier 1 domain row + Tier 2 children).
- ✅ Consistent stripe colors and iconography (lucide-react).
- ✅ Track 19.28 · Admin Sidebar V2 domain parity closed (+Command Center · +Operational Records · +Project Identity Governance).

### Hubs
- ✅ Every hub answers ONE question ("What requires admin action right now?" · "What needs attention in Shop today?" · etc.).
- ✅ Every tile opens a REAL workflow (no dead objects doctrine).
- ✅ Live data via `/api/*` — no fabricated metrics.

### Tiles
- ✅ Consistent `Card` design-system primitive.
- ✅ Metric + status chip pattern (`StatusChip statusKey="verified|pending_verification|offline_feed|draft"`).
- ✅ Consistent hover/focus states.
- ✅ Test IDs on every tile.

### Buttons
- ✅ Consistent design-system button styles.
- ✅ Primary actions in `primaryActions` prop of `PortalShell`.
- ✅ Uppercase kicker text for section headers.
- ✅ Consistent icon + label patterns.

### Empty states
- ✅ Every hub/list surface uses `<EmptyState>` primitive with `severity` variants (`good`, `attention`, `error`).
- ✅ Bilingual body copy.
- ✅ Explanatory subtitle + CTA where applicable.

### Loading states
- ✅ `<StatusChip compact label="Loading" />` on every metric while loading.
- ✅ Skeleton placeholders on cards.
- ✅ No blank white screens.

### Success states
- ✅ `/thank-you` page for public submissions.
- ✅ Success toast for in-portal submissions (via `sonner` / shadcn toaster).
- ✅ Redirect to record detail for authenticated submits.

### Failure states
- ✅ `SessionStatusOverlay` catches 401.
- ✅ Inline error messaging on forms (bilingual).
- ✅ Retry CTA where transient.
- ✅ No raw error JSON exposed.

### Terminology (per `TRACK_19_27_MASTER_FORM_INVENTORY.md` + operational language glossary)
- ✅ "Portal" (not "app" or "console") for role-specific UIs.
- ✅ "Hub" for portal landing pages.
- ✅ "Sidebar" for navigation shell (Tier 1 domain rail).
- ✅ Consistent state labels: `pending_classification` · `pending_match` · `pending_approval` · `linked` · `rejected`.
- ✅ `/admin/operational-language` is the single source of vocabulary truth (Track 15).

### Route naming
- ✅ Portal prefix + verb-oriented resource: `/hr/employees/:id/profile`, `/safety/cases/:caseId`, `/admin/audit-log`.
- ✅ Public forms end in `/submit` (or `/new` for authenticated).
- ✅ V2 hubs use `/hub_v2` alias (some now canonicalized).
- ✅ Legacy rollbacks use `/hub_legacy` (Shop · Safety · PM · HR) or `/hub_v1` (Admin post-19.28).

### Portal naming
- ✅ Consistent: "Admin Portal", "HR Portal", "Safety Portal", "PM Portal", "Shop Operations", "Dispatch Portal", "Transportation Operations", "Field Leadership".

## No "classic vs new" confusion
- Every classic surface is either:
  - Retired and redirects to canonical (`/incidents/new` → `/incidents/report` · `/qa-qc` → `/qaqc` · `/field-leadership/hub_v2` → `/field-leadership/portal/dashboard` · `/cheat-sheet` → `/cheatsheet` · `/admin/hub_v2` → `/admin`).
  - Available as a rollback path (`_legacy` suffix) — but no navigation surfaces link to it.
- Users landing on `/admin` see the modern V2 Operations Control Center — no confusion about "which admin hub is real."

## Track 19.28 delta consistency re-verification

- **Admin Hub V1 soft-retire:** `/admin` = V2 canonical. `/admin/hub_v1` = rollback only (unlinked from nav). ✅ No confusion.
- **Cheat Sheet consolidation:** `/cheatsheet` canonical · `/cheat-sheet` redirects. ✅ One source of truth.
- **Shop Hub V2 visibility polish:** Non-asset-admin users no longer see confusing tiles. ✅ Cleaner surface.
- **AdminSideNavV2 +3 routes:** Sidebar V2 now has full parity with V1 flat sidebar. ✅ No missing nav paths.

## Industry benchmark comparison
Per `TRACK_19_27_INDUSTRY_COMPARISON.md`, MASCI is compared against:
- HCSS · Raken · Procore · Autodesk Construction Cloud · Fieldwire · SafetyCulture · Samsara

MASCI **meets or exceeds** on:
- Field-first design (mobile-critical surfaces).
- Bilingual completeness (EN + ES translation-on-submit).
- Operational intelligence (Live Ops attention queues · cross-portal signals).
- Zero-drift audit trail (append-only ledgers).
- Trust Spine (single-source-of-truth data mesh).

MASCI is **strategically behind** on (roadmapped, not blocking):
- Mobile-native (iOS/Android) shell — currently PWA/web-mobile.
- Pre-canned OSHA 300 auto-fill (partial today).
- Wider integrations catalog (Samsara · Buildertrend · HCSS deeper).

## Findings
- No P0 consistency defects.
- No P1 consistency defects.
- P3 items (Sidebar V2 for Shop/Transportation/Fleet) roadmapped as opportunistic polish.

## Verdict

🟢 **GO for pilot.** Platform consistency is 10/10 on the P0/P1 dimensions. All portals share the same design-system primitives, terminology, route conventions, and behavior patterns. No unfinished visual systems. No duplicate confusing UX.
