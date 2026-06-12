# MASCI Platform — Standardization List (Track 13.4C · Deliverable #6)

**Mode:** documentation only. NOT a standardisation pass — catalogue of things that should eventually be standardised.

---

## S-1 · Status Chips

| What | Current state | Target standard |
|---|---|---|
| Status chip components | 15 distinct components, 2 share `StatusBadge.jsx` filename (V-07) | one `<StatusChip status={…} verb={…} t={…}>` primitive consumed everywhere |
| Visual treatment | varies per consumer | one chip family (color / size / icon) sourced from tokens |
| Status verb translation | 0 % (verbs not wrapped in `t()`) (T-12) | every chip wraps its verb through `t()` |

## S-2 · Colors

| What | Current state | Target standard |
|---|---|---|
| Token layer | `tokens.css` "PROPOSAL — NOT YET WIRED" (V-04) | wired and consumed by every Tailwind color reference |
| Portal palette | hardcoded literals in `portalPalette.js` (W-07) | derived from token references |
| Per-portal accents | mixed case (Shop amber vs orange, PM amber vs indigo per V-01/V-02) | reconciled to canonical accent per portal |
| Brand red overlap | FL red-700 overlaps Admin (V-03) | distinct accent per portal OR explicit policy "two portals share brand red because they're both leadership-tier" |

## S-3 · Terminology

| What | Current state | Target standard |
|---|---|---|
| Status verbs | 23 distinct verbs, mixed case (V-10/V-11) | canonical lowercase verb per workflow, with explicit synonym map |
| Closure verbs | 7+ different closure verbs (V-12) | one closure verb per workflow type, documented in a registry |
| Role nouns | "Project Manager", "Foreman", etc. hardcoded throughout source (W-13) | role tokens defined once, used everywhere via translation |
| Workflow nouns | "Daily Report", "JHA", "Site Inspection" hardcoded | same pattern — one source of truth |

## S-4 · Notifications

| What | Current state | Target standard |
|---|---|---|
| Notification kinds | per-route email sends mixed with bell writes mixed with digest aggregation | single registry: `kind → {audience, channels, dedup rule, template}` |
| Recipient lists | hardcoded with platform-level env override (W-08) | per-tenant config when tenant model lands; for MASCI today, single env-config map |
| Digest cadence | partial — `digest_settings` admin-editable (W-18) | full — all digests editable via this collection |
| Template body | Python-coded (W-20) | template-style with variable interpolation |

## S-5 · Coaching Patterns

| What | Current state | Target standard |
|---|---|---|
| Hub banners | rotating, admin-curated | continues — but with a documented "coaching banner" schema |
| Per-portal coaching | mixed — some inline, some via Operational Guidance Center | every portal links to `OperationalGuidanceCenter?from={portal}` |
| `guidance_search_misses` collection | invisible (R-15) | exposed as a coaching-gap report on the Admin Guidance Coverage page |

## S-6 · Table Patterns

| What | Current state | Target standard |
|---|---|---|
| Table component | no central `<Table>` primitive — mix of `data-table` and `<table>` HTML across modules | one table component family with shared column-defs, paging, mobile-collapse rules |
| Empty state | inlined per consumer | one `<EmptyState>` primitive with title / icon / CTA slots |

## S-7 · Form Patterns

| What | Current state | Target standard |
|---|---|---|
| Form skeleton | each form authored bespoke | shared "field group" primitive used by Daily / Inspection / Incident / Equipment (collapses R-02 overlap) |
| Form validation messages | mixed — client wraps in `t()`, server returns English `HTTPException.detail` (T-11) | every validation message translatable |
| Photo upload | rebuilt iter274 / iter261 — works | continues — but should be a shared sub-form so Trench / Site Inspection / Incident / Daily / Equipment all use the same upload primitive |

## S-8 · Empty States

| What | Current state | Target standard |
|---|---|---|
| Component | none shared | one `<EmptyState>` primitive |
| Verbiage | each consumer authors its own copy | one canonical operator-native sentence pattern |

## S-9 · Headers (Page chrome)

| What | Current state | Target standard |
|---|---|---|
| Portal header | ≥ 4 different strategies (V-06) | one `<PortalShell>` mounting header + kicker + nav |
| Public surface header | drifts per surface (V-14) | one `<PublicShell>` |
| Hub header | varies by hub-file complexity (V-05) | shell carries chrome; hubs only own their tile/KPI body |

## S-10 · Navigation Structures

| What | Current state | Target standard |
|---|---|---|
| `*CommandCenter` naming | 8 pages share the noun (V-09) | naming taxonomy that reserves "Command Center" for true role landings |
| Auth flow | 8 variations doing the same job (R-01) | one auth flow with portal-aware redirect |
| Cross-portal switcher | `<PortalSwitcher>` exists; mounted in some hubs, not all | mounted by `<PortalShell>` always |

---

## Standardisation discipline

Each row above represents *eventual* convergence. None of this work
should begin until:
1. Operator authorisation for the corresponding implementation track.
2. A cross-check against the Preserve List.
3. A migration plan that does not lose existing functionality.
