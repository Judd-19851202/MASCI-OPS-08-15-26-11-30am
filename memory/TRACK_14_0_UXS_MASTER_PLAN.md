# TRACK 14.0-UXS · UNIFIED EXPERIENCE SYSTEM · MASTER EXECUTION CONTRACT

**Status:** UXS-1 CLOSED · UXS-2 through UXS-11 OPEN
**Owner:** Continued sequential closure by next agent fork
**Hard locks (all subtracks):** No deploy · No GitHub · No merge · No backend business-logic change · No map engine change · No Map removal · No Dispatch Map-First weakening · No Repair-Complete ≠ RTS weakening · No new collection/endpoint/schema · No MaintainX/FleetWatcher activation · No accounting/cost/PO/ERP

---

## Execution Contract (NOT a passive plan)

Each subtrack below is a real shippable closure with concrete acceptance criteria. A subtrack is CLOSED only when every criterion in its "Closure Definition" block is verifiably true (grep + lint + screenshot evidence). No subtrack can be sampled or partially-closed.

The five-pillar Beautiful ≥ 9.9 gate applies to **each subtrack individually**, not to the platform overall, until UXS-11 (final route-by-route certification).

Spanish translation (14.0-S1) is **blocked until UXS-1 is closed**. Other UXS subtracks may run in parallel to Spanish if their scope doesn't move translation strings.

---

## Subtrack Sequence + Dependencies

| ID | Title | Depends on | Spanish blocker? | Status |
|---|---|---|---|---|
| **UXS-1** | Inventory + Legacy/rollback purge + visible shell violation list | none | **YES** | ✅ **CLOSED 2026-06-14** — see `TRACK_14_0_UXS1_INVENTORY_LEGACY_PURGE_CLOSURE.md` |
| **UXS-2** | Unified authenticated portal shell (Shop · PM · HR · Safety · Dispatch · Admin · Asset Care · Field Leadership) | UXS-1 | YES | ⚠️ **PARTIAL CLOSURE 2026-06-14** — shared shell primitive locked + 4 PortalShell-consumer hubs (HR/PM/Safety/Dispatch) on unified MASCI chrome with Home + ForgedOps footer + local-time formatting. Admin/Shop/FL deferred to **UXS-2b** with valid structural-refactor reason (each already has MASCI identity in its own shell). See `TRACK_14_0_UXS_2_UNIFIED_AUTHENTICATED_PORTAL_SHELL.md`. |
| **UXS-2b** | Admin / Shop / FL adoption of shared `<PortalShell>` | UXS-2 | YES | OPEN |
| UXS-3 | Public form shell + field tile shell (Daily Report · Pre-Op · DVIR · Incident · Excavation · public submitters) | UXS-1 | YES | OPEN |
| UXS-4 | Color law + severity/status chip law (publish governance doc + apply to status chips across platform) | UXS-1 | no | OPEN |
| UXS-5 | Dashboard / KPI / card / table / queue standardization (36 dashboards) | UXS-2, UXS-4 | no | OPEN |
| UXS-6 | Form / report / page layout standardization (every form surface) | UXS-2, UXS-3 | YES | OPEN |
| UXS-7 | Map shell / control / legend standardization (9 map-using files, no engine change) | UXS-2, UXS-4 | no | OPEN |
| UXS-8 | PDF / report / print lockup standardization (21 PDF generators + frontend print) — picks MASCI primary + ForgedOps/ForgeDocs provider line | UXS-4 | no | OPEN |
| UXS-9 | Training / help / search visual standardization (12 training routes + GlobalSearch + HelpTip parity) | UXS-2, UXS-4 | YES | OPEN |
| UXS-10 | Mobile / iPad visual verification (screenshot evidence at iPad + phone widths for every portal) | UXS-2 through UXS-9 | no | OPEN |
| UXS-11 | Final route-by-route visual certification (339 routes walked with screenshot evidence + Five-Pillar 9.9 gate) | UXS-1 through UXS-10 | no | OPEN |

---

## Closure Definitions

### UXS-1 — Inventory + Legacy/Rollback Purge ✅ CLOSED
- [x] Full route inventory refreshed against current `App.js`.
- [x] Portal shell inventory built for Admin · Shop · PM · HR · Safety · Dispatch · Field Leadership · Asset Care · Public · Training.
- [x] Every operator-visible "Open Classic _ Hub" link removed.
- [x] Every operator-visible "_ Hub V2" portal-role label removed.
- [x] Every operator-visible "Legacy rollback at /_/hub_legacy" preview banner replaced with neutral `"Preview Environment · MASCI Operations Platform"`.
- [x] Every operator-visible "Track 13.6X" recovery-note footer block removed from the four live hubs.
- [x] Grep for `Open Classic` / `Hub V2 ·` / `Legacy rollback at` returns ZERO normal-user-route hits (dev-only `V2Index`, `V2Compare`, `AdminHubV2`, `LeadershipHubV2` excluded — guarded by `RequireDev` per Track 14.0-A1).
- [x] ESLint clean on all touched files.
- [x] Frontend HTTP 200.
- [x] Ledger published: `TRACK_14_0_UXS1_INVENTORY_LEGACY_PURGE_CLOSURE.md`.

### UXS-2 — Unified Authenticated Portal Shell (OPEN)
- [ ] Single `<PortalShell>` (or equivalent) consumed by Shop · PM · HR · Safety · Dispatch · Admin · Asset Care · Field Leadership without portal-specific chrome variants.
- [ ] MASCI lockup present in every header.
- [ ] Home / Back / Search / Portal-Switch / Sign-Out behavior consistent across portals.
- [ ] Notification + status-pill placement consistent.
- [ ] Preview-environment banner standardized.
- [ ] Mobile + iPad header behavior matches across portals.
- [ ] Per-portal coloring limited to a single accent variable that respects UXS-4 color law (when UXS-4 closes).
- [ ] Screenshot evidence per portal at desktop + iPad widths.

### UXS-3 — Public Form Shell + Field Tile Shell (OPEN)
- [ ] Single `<PublicFormShell>` consumed by Daily Report · Pre-Op · DVIR · Incident · Excavation · all public submitters.
- [ ] MASCI lockup + language toggle + thank-you flow standardized.
- [ ] Access-Denied + Thank-You + Submission-Confirmation screens share one visual pattern.

### UXS-4 — Color Law + Status Chip Law (OPEN)
- [ ] Color-law markdown published in `/app/memory/UXS_COLOR_LAW.md`.
- [ ] Status chip primitive consumes the color law (Verified · Pending Verification · Needs Review · Needs Revision · Action Required · Overdue · Expired · Expiring Soon · Open · Closed · Reopened · Out of Service · Maintenance Hold · Available · Assigned · In Transit · Pending Transfer · Repair Complete · Return to Service · Offline Feed · Awaiting Integration).
- [ ] Every visible status chip across the platform sourced from the shared primitive.

### UXS-5 — Dashboard/KPI/Card/Table/Queue (OPEN)
- [ ] One canonical `<KPITile>` primitive consumed by all 36 dashboards.
- [ ] One canonical `<QueueCard>` for queue lists.
- [ ] One canonical `<DataTable>` row-action pattern.
- [ ] Empty-state pattern standardized.

### UXS-6 — Form / Report / Page Layout (OPEN)
- [ ] `<Section>` adoption verified across every form surface.
- [ ] Required-marker / helper / validation tone consistent.
- [ ] Submit/Cancel placement consistent.

### UXS-7 — Map Shell / Control / Legend (OPEN)
- [ ] Single `<MapShell>` wraps MapLibre across all 9 map files.
- [ ] Map legend / control / status-chip colors align with UXS-4 color law.
- [ ] Map engine + Dispatch Map-First doctrine untouched.

### UXS-8 — PDF / Report / Print Lockup (OPEN)
- [ ] MASCI primary lockup + "Powered by ForgedOps" (or ForgeDocs — final naming decision documented in this subtrack from existing memory) applied to all 21 backend PDF generators.
- [ ] Document title + ID + generated timestamp + page number + footer pattern standardized.
- [ ] No Emergent branding anywhere.

### UXS-9 — Training / Help / Search Visual (OPEN)
- [ ] All 12 training routes use portal shell.
- [ ] GlobalSearch placement consistent.
- [ ] HelpTip / HelpTipBlock / LifecycleGuide visual parity audited.

### UXS-10 — Mobile / iPad Visual (OPEN)
- [ ] Screenshot evidence at iPad + phone widths for every portal + every public form.
- [ ] Zero horizontal overflow.
- [ ] Submit/primary actions reachable on every form.

### UXS-11 — Final Route-by-Route Visual Certification (OPEN)
- [ ] All 339 routes walked with screenshot evidence.
- [ ] Five-Pillar Beautiful ≥ 9.9 gate met platform-wide.
- [ ] RC-1 certification artifact `MASCI_RC1_FIVE_PILLAR_CERTIFICATION.md` published.

---

## Hard Rule (applies to every subtrack)

> If you touch a file and see safe visual drift, fix it. Do not walk past it.

No "outside this subtrack" excuses. The user has stated this rule plainly.

---

**End MASTER EXECUTION CONTRACT. UXS-1 CLOSED. UXS-2 next.**
