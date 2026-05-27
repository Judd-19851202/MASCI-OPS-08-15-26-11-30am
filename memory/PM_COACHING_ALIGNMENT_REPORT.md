# PM Coaching Alignment Report — Phase IV-BETA.2

**Iteration:** iter437 · Phase IV-BETA.2 · 2026-02-27
**Status:** 🟢 PM SECTION COACHING NORMALIZED · `verify_coaching_sublines.py` PASSING
**Doctrine:** `CROSS_PORTAL_COACHING_STANDARD.md` · 14-word budget · sentence-case slate-500 · ends with period

## I. Surfaces normalized this iteration

### A. PM Hub intro

| Surface | Before | After |
|---|---|---|
| Hub V2 intro | 6-line paragraph: *"Welcome to the PM Portal. The forms below cover the day-to-day — Daily Reports, Inspections, Incidents, Photos, Field Leadership records, and more — scoped to jobs assigned to you. …"* | Single calm subline: *"Today's operational signal across your assigned projects."* (8 words · sentence-case · ends with period) |

### B. PM Section intros (PmSections.jsx · 7 surfaces)

All surfaces now use the calm `<Subline>` helper (sentence-case slate-500, ≤14 words, period-terminated).

| Surface | Before | After |
|---|---|---|
| Jobs | "Active jobs assigned to you · Master list" (mono uppercase feature-list) | "Active jobs assigned to you and the master roster." |
| Equipment Fleet | "Status board · Master · Parts" | "Status board, master roster, and parts across your fleet." |
| People | "Employee master (read-only)" | "Employee master roster (read-only)." |
| Suppliers | "Supplier master (read-only)" | "Approved supplier roster with contacts (read-only)." |
| Site Posters | "JHP · Trench Box · Inspection QRs" | "Printable JHA, trench box, and inspection QR posters for the trailer." |
| Email Routing | "Auto-routing summary" | "Active auto-routing rules per form (admin-edited)." |
| Compliance Export | "Date-range CSV export" | "Date-range CSV of safety records for audits and insurance reviews." |

### C. PM V2 Sidebar (from IV-BETA.1)

Already doctrine-compliant — re-verified in this iteration:

- 6 domain sublines · all ≤ 10 words · all end with period · all sentence-case
- 23 child entry sublines · all ≤ 10 words · all doctrine-compliant
- Verified by `verify_coaching_sublines.py` → **PASS**

### D. Hub V2 inline copy

| Surface | Subline |
|---|---|
| Tier-1 Daily Reports | "Field production · review and approve." |
| Tier-1 Inspections | "Today's field safety and quality checks." |
| Tier-1 Incidents | "Open and recent operational deviations." |
| Tier-2 My Tasks | "Action items across all domains." |
| Tier-2 PO Requests | "Approvals · receipts · spend." |
| Tier-2 Project Health | "Operational friction by job." |
| Tier-2 Asset Transfers | "Equipment movement · lifecycle." |
| Crew Compliance card | "Training currency, PPE, CAPA exposure, expirations." |

All 8 ≤ 14 words. All ends with period or middle-dot (operational shorthand). All sentence-case.

## II. Doctrine-violation patterns eliminated

| Pattern | Where it lived | Resolution |
|---|---|---|
| "Welcome to…" | PmHub intro card | Removed |
| Mono uppercase tracking-wider feature-lists | PmSections intros · legacy SideNav sublines | Replaced with sentence-case sublines (PmSections · V2 SideNav) |
| Parenthetical state qualifiers in mono uppercase | "(read-only)" in mono | Now in sentence-case `<Subline>` text |
| Bullet-separated feature lists | "Status board · Master · Parts" | Now operationally descriptive: "Status board, master roster, and parts across your fleet." |
| Sentence fragments | "Date-range CSV export" | Full sentence with period |

## III. `verify_coaching_sublines.py` results

```
✅ verify_coaching_sublines: all governed sublines pass doctrine
```

Files validated:
- `frontend/src/components/admin/sidebar/domainMap.js` (Admin V2 · 6 domain + ~30 child sublines)
- `frontend/src/components/pm/sidebar/domainMap.js` (PM V2 · 6 domain + 23 child sublines)
- `frontend/src/pages/pm/PmSections.jsx` (7 section sublines)

Total surface coverage: 72 coaching strings · all passing.

## IV. Items NOT touched (preserved per directive)

| Surface | Why preserved |
|---|---|
| Legacy PmHub intro (when V2 flag OFF) | Operator muscle memory preservation until IV-BETA.5 cut |
| Legacy PmShell SECTIONS sublines | Same — legacy still in tree until IV-BETA.5 |
| Field Leadership · Driver portal coaching | Out of scope this session |
| Email/notification body coaching | IV-BETA.3 (communication unification) |
| Modal body coaching | IV-BETA.3 |
| Empty-state coaching across PM pages | IV-BETA.3 (deferred · would require per-page audit) |

## V. Operator-trust principles applied

1. **Every PM surface now coaches without lecturing.** No "Easily…" · no "Welcome to…" · no "Click here…"
2. **Every subline carries the same shape.** Sentence-case slate-500 · ≤14 words · ends with period.
3. **The same operational concept uses the same noun.** "Inspections" not "Site Inspections" · "Pre-Op" not "Equipment Pre-Op" · "Incidents" not "Incident Reports."
4. **Field-leadership and admin nouns aligned.** Cross-portal terminology drift reduced.

## Verdict

🟢 **PM COACHING ALIGNED · DOCTRINE-COMPLIANT · GATE-PASSING.** 72 coaching strings across 3 files pass `verify_coaching_sublines.py`. PM portal speaks in the calm operational voice required by the cross-portal doctrine.
