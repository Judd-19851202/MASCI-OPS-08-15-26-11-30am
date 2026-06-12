# MASCI Target State Architecture

**Track 13.5C · Platform-Wide Target State Specification**
**Mode:** Architecture-only · no code, no migration, no design generation.
**Generated:** 2026-06-12 (UTC)

> Source of truth for every future implementation decision in MASCI Operations Platform. Every future track must be measurable against this document. Discovery is closed; this is the **finish line**.

---

## 1. What "10/10" means on each pillar (measurable definitions)

These are the only acceptable 10/10 definitions. Future tracks must score against these — not against aspirational statements.

### 1.1 Powerful = 10/10

Measurable:
- **No operator workflow requires leaving the operator's own portal** to complete the core daily task.
- **Every visible KPI is backed by a real, source-of-truth API.** Zero derivations from screen state. Zero re-entry of the same field across forms.
- **Every persistent operator question has exactly one answer surface.** ("Where are my crews?" / "What needs me today?" / "Is this safe to proceed?")
- **Cross-portal moves are first-class.** A safety hold raised in Safety surfaces automatically in PM and Dispatch within ≤ 60 s.
- **The platform answers "what changed in the last 24 h?" on every portal** with a single auditable feed.

### 1.2 Simple = 10/10

Measurable:
- **One vocabulary across the platform.** 18 canonical status keys (Phase B1 registry) are the **only** statuses anywhere. Forbidden labels (Rejected · Denied · Failed) are absent.
- **One header strategy, one navigation strategy, one shell, one card, one chip, one table, one empty state.** Zero ad-hoc variants survive.
- **One naming taxonomy for landings.** "Command Center" means *one thing*: the primary role landing for a portal — and nothing else.
- **A first-time operator needs zero training** to complete their first-task-in-5-minutes (see `MASCI_HUMAN_USABILITY_TARGET.md`).
- **Maximum two action verbs above the fold per portal.** Excess buttons are demoted into context menus or removed.
- **No tribal knowledge in any UI string.** All labels read at a 12th-grade level or below.

### 1.3 Beautiful = 10/10

Measurable:
- **100% of operator surfaces consume `tokens.css`** — zero hardcoded brand hex outside the token file.
- **Header chrome is identical across portals** in structure (only role color, role name, and a single 32-px logo vary).
- **Typography is exactly two faces:** display (titles) + body (Inter or Inter-equivalent). No third font enters by accident.
- **Status colors are derived from severity** (good · attention · urgent · halt · info · neutral), not from arbitrary brand-tinted choices.
- **Whitespace honors `--pad-section` (32 px) / `--pad-card` (16 px) / `--pad-tight` (8 px)** with no override. Cards are not jammed against each other.
- **Heavy-civil appropriate:** no SaaS gradients, no purple/violet, no glassmorphism on dashboards. Calm, operator-readable in sunlight on iPad.
- **No emoji icons anywhere.** Lucide-React or FontAwesome only.

### 1.4 Trusted = 10/10

Measurable:
- **Every visible number cites its source.** Hover-tooltip shows the API endpoint + last refresh timestamp + sample size.
- **No stale data is presented as live.** If a feed exceeds its SLA (Motive ≤ 5 min, ops-summary ≤ 60 s), the chip changes to `stale_position` / `offline_feed`.
- **No duplicate notification of the same event.** One source-of-truth per event (digest XOR per-action, not both).
- **All bilingual operator-facing strings round-trip ES⇄EN at 100%.** Zero EN-only safety strings.
- **Backend documents (PDFs, emails, Excel exports) honor operator locale** — no EN-only PDFs to ES operators.
- **All status writes are auditable** (state-event log present and reachable from the chip).
- **No "Rejected / Denied / Failed" in any operator-facing surface.**

### 1.5 Proven = 10/10

Measurable:
- **Every portal has at least one Playwright visual guardrail** that runs on each commit and asserts the canvas/DOM renders real content (e.g., the Track 13.4A Dispatch map guardrail: `mean ≥ 15`, `variance ≥ 5`, `unique ≥ 8`).
- **Every API endpoint has a contract test** (status code + shape + at least one role-scoped happy path + one rejection path).
- **Every portal has an operator-screenshot evidence baseline** for desktop / iPad landscape / iPad portrait, refreshed on every release.
- **Production verification checklist is current** — Motive webhook arrival rate, GPS coverage %, feed_status=live, geofence render count, operational_summary independent rederivation. Updated ≤ 30 days.
- **Five-pillar scorecard is regenerated each release** with cited evidence.
- **No "it works on my machine"** — `/api/health` + `/api/admin/deploy-readiness` are green before any deploy.

---

## 2. Platform-wide architecture (current vs target, per dimension)

### 2.1 Global Visual Identity

| | Current | Target | Why this supports the Pillars |
| --- | --- | --- | --- |
| Tokens | `tokens.css` wired (Phase A); only `/_internal/*` consumes it | **100% of operator surfaces consume tokens.css; zero hardcoded brand hex outside `/styles/tokens.css`** | Beautiful 10, Simple 10 |
| Color | Per-portal brand reds vary (V-03 FL red-700 vs Admin red-600); amber/orange drift (V-01, V-02) | **One brand red (`--brand-primary`), per-role color reserved for role-name strip only**, status colors derived from severity | Beautiful 10 |
| Typography | Mixed Inter/system/display | **Display (Source Serif Pro or equivalent) on titles + Inter on body. Two faces, no third** | Beautiful 10, Simple 10 |
| Iconography | Mixed FA/Lucide + occasional emoji | **Lucide-React only** (single library, single line-weight) | Beautiful 10, Simple 10 |

### 2.2 Header Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Strategies | ≥ 4 different header patterns (V-06) | **One `PortalShell` header pattern** (Phase B1). Identical structure; only role color, role name, and 32-px logo vary | Beautiful 10, Simple 10 |
| Content | Mixed kicker / title / subtitle / amber preview-banner stacking | **Fixed order:** environment banner (preview-only) → role-color strip → kicker → page title → subtitle → primary actions (max 2) → last-activity slot | Simple 10, Trusted 10 |

### 2.3 Navigation Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Pattern | Portal-specific nav strategies; some hubs use tile grids, some use rails | **Two-layer:** (a) **portal switcher** (super-admin only) and (b) **portal-local rail** (consistent shape across all portals, max 7 destinations) | Simple 10 |
| Deep links | Sometimes work, sometimes 404 | **Every operator route is deep-linkable, bookmarkable, and survives a hard reload** | Trusted 10 |
| Mobile | Inconsistent | **Bottom-bar on phone for the 3 most-used destinations**; same rail collapses to it on < 768 px | Simple 10, Beautiful 10 |

### 2.4 Portal Shell Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Wrapper | ≥ 4 ad-hoc shells across portals | **`<PortalShell>`** is the only wrapper for authenticated operator surfaces. **`<PublicShell>`** is the only wrapper for public QR / form / landing surfaces | Simple 10, Beautiful 10 |
| Slots | Inconsistent | **Exactly 5:** environment banner, role strip, page header (kicker + title + subtitle), primary actions, last-activity | Simple 10 |

### 2.5 Public Surface Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Chrome | 22 first-class public surfaces; each carries its own header (V-14) | **One `<PublicShell>`** wraps every public surface. No exception | Beautiful 10 |
| Branding | MASCI brand visible in 497 source files (W-03 / W-04) | **Brand resolves from `--brand-primary` + `--logo-asset` per tenant** (white-label-ready; preserved for MASCI today) | Beautiful 10, Productization |
| QR landing voice | Calm on Trench Safety; inconsistent elsewhere | **Trench Safety voice is the platform-wide reference** for all public surfaces | Simple 10, Beautiful 10 |

### 2.6 KPI Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| KPI cards | Ad-hoc per portal | **`<Card>` primitive only; one of 4 variants** (default / warning / danger / success). Metric · description · status chip · last refresh | Simple 10, Beautiful 10 |
| Provenance | None | **Every metric carries a hover-tooltip naming the API endpoint, last refresh ISO timestamp, and sample size** | Trusted 10 |
| Density | Mixed | **Three named densities** (compact / regular / spacious). Each surface uses one, consistently | Beautiful 10, Simple 10 |
| Stale handling | Silent stale | **Chip flips to `stale_position` / `offline_feed` when the source has not refreshed within its SLA** | Trusted 10 |

### 2.7 Card Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Renderers | ≥ 7 ad-hoc card renderers in PM alone | **One `<Card>` primitive; 4 variants × 3 densities = 12 legitimate shapes. Nothing else exists** | Beautiful 10, Simple 10 |
| Click affordance | Implicit | **A Card is clickable iff it has a `to=` destination; non-clickable Cards must not visually mimic clickable Cards** | Simple 10, Trusted 10 |

### 2.8 Status Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Vocabulary | 15 chip components, case drift, three meanings of `offline` (V-10/V-11) | **18 canonical keys from `statusRegistry` are the only statuses anywhere.** Engine literals wrap through `t()` to localize | Simple 10, Trusted 10 |
| Forbidden labels | Possible | **"Rejected · Denied · Failed" must not appear in any operator surface.** The strongest negative is "Needs Revision" | Trusted 10 |
| Severity mapping | Per-component | **Severity is the only color authority** (good · attention · urgent · halt · info · neutral) | Beautiful 10, Simple 10 |

### 2.9 Table Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Renderers | ≥ 3 table renderers in PM alone | **One `<DataTable>` primitive; controlled sort; explicit loading + empty rows; status chips render inline** | Simple 10, Beautiful 10 |
| Mutation | Tables sometimes mutate data | **`<DataTable>` is presentation-only;** parent owns rows + sort state | Trusted 10, Proven 10 |
| Mobile | Horizontal-scroll on phone | **`<DataTable density="compact">` plus a "Cards" mobile variant** for narrow viewports | Simple 10, Beautiful 10 |

### 2.10 Empty-State Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Voice | 9 different empty-state copies in PM, some punitive | **One `<EmptyState>` primitive; three severities** (good · neutral · attention). **"No data" is never an error voice.** | Trusted 10, Beautiful 10 |
| Copy | Per-page, ad-hoc | **Operator-edited canonical empty messages library**, with the Trench Safety voice as reference | Simple 10, Trusted 10 |

### 2.11 Notification Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Channels | Bell · digest · per-action email · in-portal banner — no single owner (R-07) | **One event → one channel rule.** Operator chooses per category. No event is delivered twice | Trusted 10, Simple 10 |
| Surface | Surface chrome varies | **A bell in `PortalShell` is the single in-app surface.** Banners are reserved for environment-level concerns | Simple 10 |
| Acknowledgment | Inconsistent | **Every notification is dismissable and audited** | Trusted 10 |

### 2.12 Coaching Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Coaching surfaces | `OperationalGuidanceCenter` exists; `guidance_search_misses` invisible to operators (R-15) | **Coaching is a slot on `PortalShell`** — operator can collapse it. Search misses surface back to authors via a "request guidance" affordance. Coaching content is registry-backed | Simple 10, Powerful 10 |
| Tone | Mixed | **Non-punitive · operator-as-peer voice. No "you should have…" phrasing** | Trusted 10 |

### 2.13 Command Center Architecture

See `MASCI_COMMAND_CENTER_TARGET_STATE.md`. Summary here:

| | Current | Target | Why |
| --- | --- | --- | --- |
| Number of "Centers" | 8 (+1) named `*Center` | **5 role-landing Centers** (Admin · Dispatch · PM · Safety · Field-Leadership) **+ one cross-portal `OperationsCenter` for super-admin**. ODR / Trench / Guidance / Training / Integration are renamed away from "Center" | Simple 10 |
| Behavior | Mixed | **A Command Center is a portal's first-screen aggregator** answering "What needs me today?" — it is **not** an authoring tool, a settings page, or a domain ops view | Simple 10, Powerful 10 |

### 2.14 Mobile (phone) Architecture

| | Current | Target | Why |
| --- | --- | --- | --- |
| Coverage | Field captures partial (V-13) | **Driver + Field Leadership + Safety Forms run at parity on phone**; other portals degrade gracefully | Powerful 10, Adoption |
| Pattern | Mixed | **Bottom-bar nav · 1-column scroll · Cards collapse from `regular` to `compact` density · DataTables switch to Cards mobile variant** | Beautiful 10, Simple 10 |
| Offline | None | **Field-Leadership Daily Report + Equipment Issuance offline-capable** with queued sync; ≤ 30 s background reconciliation | Powerful 10, Trusted 10 |

### 2.15 iPad Architecture (PM + Dispatcher + Safety primary)

| | Current | Target | Why |
| --- | --- | --- | --- |
| Layouts | Inconsistent at 820×1180 portrait | **Layouts validated at three viewports: 1920×1080 desktop · 1180×820 iPad landscape · 820×1180 iPad portrait.** Required for every operator surface | Beautiful 10, Proven 10 |
| Input | Touch | **44×44 px minimum tap target** across all controls. Forms remain keyboard-navigable | Simple 10, Trusted 10 |
| Map | Map dominance verified on Dispatch (13.4A) | **Map surfaces target ≥ 60% viewport height on iPad landscape** | Powerful 10, Trusted 10 |

---

## 3. The drift-elimination contract

This document **is** the contract. Going forward:

1. Any PR that adds a non-token color must reference a tracked exception in this file.
2. Any PR that adds a new status string must add it to `statusRegistry.js` first.
3. Any PR that adds a new "Center" surface must declare which of the 5 role-landings it is.
4. Any new card / table / chip / empty-state must use the primitives. New ad-hoc implementations require explicit operator authorization.
5. Any new operator route must be deep-linkable and screenshot-baselined at three viewports.
6. Any new notification channel must declare its event-owner.

Future audits **measure** against these clauses. They do not re-discover them.

---

## 4. What this document is NOT

- Not a design system spec (that is `MASCI_DESIGN_SYSTEM_V1.md`).
- Not a recovery plan (that is the priority list).
- Not a coding instruction (Tracks 13.5+ phases authorize that, one at a time).
- Not an aspirational manifesto. Every clause is measurable.

Standing rules: No deploy. No GitHub save. No merge.
