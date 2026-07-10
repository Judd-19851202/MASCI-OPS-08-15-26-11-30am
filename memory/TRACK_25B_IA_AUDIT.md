# TRACK 25B · Admin OS · Information Architecture Audit

Generated: 2026-07-10
Owner: platform-trust

## Purpose
Complete map of every Admin OS surface with a merge / consolidate /
keep verdict per page. Used to drive Track 25B's navigation reduction
without deleting capability.

## Canonical Admin OS domains (10)
| # | Domain | Canonical route | Cards | Trust gaps | Verdict |
|---|---|---|---|---|---|
| 1 | Platform Overview | `/admin` (landing; details `/admin/executive-overview`) | 10 domain cards | — | canonical · one home |
| 2 | Operations Control Center | `/admin/operations-control` | 12 Trust Layer + 14 maintenance ops | — | canonical · SINGLE action engine |
| 3 | Storage & Recovery | `/admin/storage-recovery` | 7 | 9 | canonical |
| 4 | AI Operations | `/admin/ai-operations` | 4 | 3 | canonical |
| 5 | Communications | `/admin/communications` | 4 | 3 | canonical |
| 6 | Identity & Security | `/admin/identity-security` | 5 | 3 | canonical |
| 7 | Governance & Trust | `/admin/governance-trust` | 7 | 1 | canonical |
| 8 | Platform Configuration | `/admin/platform-configuration` | 6 | 3 | canonical |
| 9 | Diagnostics | `/admin/diagnostics` | 7 | 3 | canonical |
| 10 | Maintenance | `/admin/maintenance` | 9 | 1 | canonical |

## SideNavV3 reduction (Track 25B)
| Old section (top-level) | Action | Reason |
|---|---|---|
| Admin OS (kept · Sprint 7/8) | KEEP | Single-click reachability for all 10 Admin OS domains. |
| Operations Control Center | RENAMED → "Platform Tools" | The duplicate "Operations Console" child link was removed (already reachable via Admin OS → Operations Control). The 3 remaining unique children (Database Capacity · MFA · Self-Protection) are preserved. |
| Home · Executive Home · Command Center · Executive Overview · P&L · My Profile | KEEP (business dashboards, not Admin OS domains) | Non-admin-OS surfaces retained. |
| Jobs & Projects, Fleet & Equipment, Safety & Compliance, People & Access, Training, AI & Intelligence, Communications, Reporting, Audit Log, Legacy Imports | KEEP for now | These are business-domain sections with feature-detail pages. Slated for review in Track 25C (may merge into Admin OS as sub-tabs) but out of scope for 25B. |

## Legacy admin routes
All legacy hub routes (`/admin/hub_v1`, `/admin/hub_v2`, `/admin/platform-overview`) redirect silently to `/admin`. `AdminHub.jsx`, `AdminHubV2.jsx`, `AdminHubSwitcher.jsx`, `AdminHubV3.jsx` are all safe redirects. No operator ever sees V1/V2/V3 labels.

## Breadcrumb certification (Track 25A)
Every Admin OS surface renders `AdminBreadcrumb`:
- AdminOS (/admin) → `Admin OS`
- OCC (/admin/operations-control) → `Admin OS › Operations Control Center`
- 8 DomainLandingShell pages → `Admin OS › <label>`

## One action source (Rule #7)
OCC (`/admin/operations-control`) is the single execution engine for
every mutating maintenance operation. Every other admin page can
SHOW / SUMMARIZE / DEEP-LINK but never DUPLICATE-EXECUTE a maintenance
action. Every domain page's "Maintenance Actions" section uses
`?highlight=<op-id>` deep-links into OCC to preserve this rule.

## Trust gap totals
- Before Sprint 7/8: 30
- After Sprint 7/8: 26 (4 wired via `/api/admin/occ/trust-events`)
- Track 25B: no additional gaps wired (reduction sprint, not feature sprint)
- Remaining 26 gaps require net-new backend probes (Track 27.06 · Track 27.10 · Track 27.11 · Track 27.12+)

## Consistency inventory (Track 25A verified)
- Shell · PortalShell + SideNavV3 · every Admin OS page
- Cards · HealthCard from `TrustPrimitives`
- Status pills · TRUST_STATUS_STYLES palette
- Evidence drawer · EvidenceDrawer from `TrustPrimitives`
- Breadcrumb · `AdminBreadcrumb`
- Time formatting · `platformTime.js` (zero-UTC)
- Trust gaps · same table format across all 8 pages that have gaps

## Not-yet-touched (future tracks)
- SideNavV3 collapse of business-domain sections into Admin OS sub-navigation (Track 25C)
- Feature-flag admin surface (Track 27.12)
- Secret rotation workflow (Track 27.13)
- Latency histograms · Sentry-style error surface (Track 27.12)
- Passkey enrollment stats · RBAC matrix (Track 27.11–12)

---

## PHASE 13 · Platform Evolution Certification (Track 25B addendum)

Audit of every admin route against today's platform architecture
(AI · Trust Spine · OCC · R2 · Executive intelligence · Governance ·
Production Certification · Deploy Readiness · Notification Pipeline).

### Legacy admin pages · modernization verdicts
Pages reachable via deep-links from Sprint 4/5/6 domain landings.
"Modern shell" = PortalShell + SideNavV3 + AdminBreadcrumb + TrustPrimitives.

| Route | Current shell | Verdict | Reason / Track |
|---|---|---|---|
| `/admin/executive-overview` | Legacy | **Modernize (25C)** — should render the same Executive Verdict pattern as Sprint 4-6 domains. |
| `/admin/email` | Legacy | **Consolidate (25C)** — surface its unique panels (route-template editor · V2 audit tail) as an EmailRouting *detail* page inside `/admin/communications`, or wrap it in the modern shell + AdminBreadcrumb. Do not delete panels. |
| `/admin/ai-configuration` | Legacy | **Consolidate (25C)** — the AI provider config editor should sit under `/admin/ai-operations` as a `/admin/ai-operations/configuration` detail route with the same shell. |
| `/admin/sessions` | Legacy | **Modernize (25C)** — wrap in modern shell + breadcrumb `Admin OS › Identity & Security › Sessions`. |
| `/admin/mfa` | Legacy | **Modernize (25C)** — same as sessions, under Identity & Security. |
| `/admin/people` | Legacy | **Modernize (25C)** — same shell wrapping. |
| `/admin/audit-log` | Legacy | **Modernize (25C)** — wrap in modern shell + breadcrumb `Admin OS › Governance & Trust › Audit Log`. |
| `/admin/governance` | Legacy | **Modernize (25C)** — becomes `Admin OS › Governance & Trust › Rules` detail page. |
| `/admin/integrations` | Legacy | **Modernize (25C)** — becomes `Admin OS › Platform Configuration › Integrations` detail. |
| `/admin/system-health` | Legacy | **Modernize (25C)** — becomes `Admin OS › Diagnostics › System Health Detail`. |
| `/admin/scheduler-runs` | Legacy | **Modernize (25C)** — becomes `Admin OS › Diagnostics › Scheduler Runs`. |
| `/admin/database` | Legacy | **Modernize (25C)** — becomes `Admin OS › Diagnostics › Database Capacity`. |
| `/admin/recovery` | Legacy (retained for bookmarks) | **Retire (25C)** — modern replacement is `/admin/storage-recovery`. Legacy route stays as silent redirect after unique panels are surfaced there. |
| `/admin/legacy-imports` | Legacy | **Modernize (25C)** — becomes `Admin OS › Maintenance › Legacy Imports`. |
| `/admin/analytics` | Legacy | **Modernize (25C)** — becomes `Admin OS › Diagnostics › Analytics` OR moves under Platform Overview per usage frequency. |
| `/admin/digest-config` | Legacy | **Consolidate (25C)** — Communications sub-page. |
| `/admin/branding` | Legacy | **Consolidate (25C)** — Platform Configuration sub-page. |
| `/admin/deploy-recovery` | Legacy | **Consolidate (25C)** — Governance & Trust sub-page. |
| `/admin/governance/self-protection` | Legacy | **Modernize (25C)** — moves under Identity & Security as detail. |
| `/admin/operational-language` | Legacy | **Modernize or Retire (25C)** — evaluate usage frequency. |

### Aggregate finding
- **20 legacy admin pages** still render in the pre-Track-25 shell.
- **All** are reachable from modernized Sprint 3-6 domain landings — no bookmark or capability loss risk.
- **Zero** legacy pages present operator-facing V1/V2/V3 language (verified · Sprint 25A).
- **Every legacy page must be** either wrapped in the modern shell + AdminBreadcrumb + rebranded to match Admin OS domain vocabulary, OR retired if its capability is fully absorbed by a modernized replacement.
- **Estimated effort** for full Phase 13 modernization: **~3-4 additional sprints** (Track 25C P0-P3), one Admin OS domain at a time (Identity + Comms + Governance + Config + Diagnostics + Maintenance sub-pages).

### No historical bias verdict
Every legacy page fails the Phase 13 test:
- Same shell as Sprint 3-6? **NO**
- Same breadcrumb pattern? **NO**
- Same evidence-first card language? **NO** (mostly form-oriented legacy UI)
- Same status pill / TrustPrimitives palette? **NO**
- Surfaces today's OCC / Trust Events / Production Cert / R2 evidence? **PARTIAL**

**Definition-of-done for Phase 13 is NOT achieved by Track 25B alone.**
Track 25B has certified:
- Every Admin OS **domain landing** matches (Sprints 3–6 · 8 pages)
- Universal **breadcrumb** across all Admin OS surfaces (Sprint 25A)
- OCC now uses the **same shell** as domain landings (Sprint 25A)
- SideNavV3 first-level **duplicate removed** (Sprint 25B — Operations Console top-level entry consolidated into Admin OS section)

Track 25C is the follow-on to modernize the 20 legacy admin sub-pages into the same shell + breadcrumb + card language, one Admin OS domain per sprint slice, preserving all bookmarks via silent redirects for retired routes and preserving 100% of capability by absorbing each legacy panel into its canonical domain landing as a detail route.

