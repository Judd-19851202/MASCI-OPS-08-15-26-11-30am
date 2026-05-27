# Operator-Grade Review Synthesis

*Phase IV-BETA.3-P2B · iter437 · 2026-02-27*
*Status: 🟢 Admin / PM / HR reviewed against doctrine + baseline metrics*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Method

Each portal was reviewed against the 10 governance categories below.
The review is grounded in **measured signal** (`HUB_VISUAL_BASELINE.json`)
plus **structural inspection** (sidebar V2 file + hub tile defs +
screenshots).

| Category | What we measured |
|---|---|
| Hierarchy clarity | sidebar domain map · hub tile groups · h1/h2/h3 sequence |
| Navigation speed | sidebar depth · clicks-to-target from hub overview |
| Mobile ergonomics | viewport mobile baseline (390×844) loudness + walked count |
| iPad ergonomics | viewport ipad baseline (1024×1366) loudness + walked count |
| Coaching usefulness | ≤14-word subline compliance · sentence-case · period-terminated |
| Operational calmness | loudness composite + hue family count |
| Cognitive load | emphasis_score + badge_density |
| Badge saturation | badge_density (per-100 elements) |
| Escalation clarity | comm subject/footer doctrine compliance |
| Visual trustworthiness | slate-900 chrome · consistent stripe palette · no marketing flair |

## II. Portal-by-portal synthesis

### II.A · Admin Portal (🟢)

**Strengths**
- Hierarchy: 5-domain V2 sidebar maps cleanly to 4-stripe Hub V2.
- Coaching: every governed subline passes `verify_coaching_sublines.py`.
- Mobile: walked count 160 / loudness 27 — narrowest mobile in the platform.
- Comm doctrine: every system-generated subject + footer compliant.

**Remaining friction**
- Some legacy admin sub-pages (Compliance Export, Email Routing) still
  carry pre-V2 chrome inside the V2 shell. Cosmetic, not functional.
- Per-tile button colours on a few legacy panels are not yet neutralised.

**Preserve at all costs**
- Per-domain stripe colour mapping. Admins recognise domain by stripe.
- Deploy Readiness landing (top of Admin) — single most-clicked surface.

**Safe to simplify later**
- Backup & Recovery's verbose status panel could fold into a 3-card layout.
- Health card area could move to a sticky right rail at desktop only.

### II.B · PM Portal (🟢 best-in-class)

**Strengths**
- **Lowest loudness in the platform** (desktop 26.9 · mobile 15.3).
- 3-hue palette (blue · green · red) — the strictest of any portal.
- PM Hub V2 re-tier (iter437 IV-BETA.2) eliminated tile overload.
- PM auth-routing P0 fix has been live for two iterations with
  zero `/api/admin/*` calls leaking from PM context.

**Remaining friction**
- The legacy V1 SECTIONS sidebar coexists with V2 (`?pmSidebarV2=1`).
  Promotion out of flag is the right next step.
- "Jobs" tab now uses `PmJobsRead` (read-only) which is correct, but
  the table is busy for PMs assigned to 8+ projects. A summary
  "rollup" row would help.

**Preserve at all costs**
- Coaching sublines on PM Hub overview — operator feedback says these
  are the most-quoted operational guidance on the platform.
- Field Leadership document upload UX (untouched by this batch).

**Safe to simplify later**
- "Project Health" card sequencing — currently 6 cards, could be 4.
- Mobile sidebar V2 currently hidden (intentional); revisit if PMs
  start asking for it.

### II.C · HR Portal (🟢 calmer than baseline expected)

**Strengths**
- Calmness tuning (P1B) trimmed sublines 19 → 9 avg words, stripes
  9 → 5, CTA buttons 9 → 1 neutral.
- Cross-portal cohesion with Admin/PM hub now visually evident.
- Sidebar V2 inherits identical chrome rules as PM V2.
- Zero `/api/admin/*` leak risk (audited).

**Remaining friction**
- Baseline loudness 64.7 is the highest of the three (vs PM 26.9 · Admin 36.1).
  Root cause is the rounded-card-with-coloured-background tile design — see
  `VISUAL_DOCTRINE_BASELINE_REPORT.md` §VII on the badge heuristic
  over-counting. Not a UX defect; a measurement quirk.
- Mobile baseline (94 walked elements vs PM mobile 79) suggests HR has
  one more "row" of small-text content that could collapse cleaner on
  mobile.

**Preserve at all costs**
- 5-domain map (matches `HR_INFORMATION_PRIORITY_MAP.json`). Do NOT
  reorder.
- Per-tile stripe palette (green · sky · violet · amber · slate).

**Safe to simplify later**
- "Tasks & Actions" tile is currently a passthrough to `/tasks`;
  consider whether it belongs in HR or in a system-wide tasks shell.

## III. Cross-portal friction points

| Friction | Severity | Portal(s) | Recommended P1 |
|---|---|---|---|
| HR Hub still loudest measured surface | 🟡 measurement quirk | HR | Refine badge heuristic before threshold-setting |
| V1 vs V2 sidebar coexistence | 🟡 dual-mode | PM · HR | Promote V2 out of flag after pilot day |
| Legacy Admin sub-pages keep pre-V2 chrome | 🟡 cosmetic | Admin | Roll into next Admin maintenance pass |
| Mobile sidebar V2 hidden on PM and HR | 🟢 by design | PM · HR | Re-examine only if operator asks |

## IV. Operator trust observations (🟡 ASSUMED until operator review confirms)

- The 3-line operational footer on every transactional email gives
  the receiver instant "what surface produced this" signal — likely
  to reduce inbox confusion when an operator manages multiple
  portals' emails simultaneously.
- Severe-tier subject prefixes (`🚨 PLATFORM OUTAGE`, `⚠ EQUIPMENT FAIL`)
  are visually distinguishable in even a glanced inbox preview;
  routine `[MASCI · TAG]` subjects are calm and skimmable.
- The Cross-Portal Operator Atlas, when handed to a new hire, should
  shorten "where do I go for X?" questions by an order of magnitude.

## V. Pre-Safety readiness signal (🟢)

Based on the cross-portal posture matrix and the doctrine snapshot
trend, **the platform is ready to begin Safety governance work** with
high confidence — see `PRE_SAFETY_CERTIFICATION.md` for the formal
certification.

## VI. Doctrine reaffirmed

- ✅ Preview only
- ✅ Review grounded in measured signal, not impression
- ✅ Every "friction" is classified by severity
- ✅ "Preserve at all costs" surfaces explicitly named per portal
- ✅ Doc readable in a single sitting (operator's lunch break)
