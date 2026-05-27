# Cross-Portal Validation Synthesis — Phase IV-BETA.5A-P1C

*iter437 · 2026-02-27*
*Status: 🟢 OPERATOR-GRADE REVIEW COMPLETE*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Conduct an operator-grade review **across the four governed portals**
(Admin · PM · HR · Safety) focused on cross-portal coherence — not
per-portal polish. The unit under review is **operator continuity** as
they move between portals during a working day.

## II. Strongest governance surfaces (🟢)

| Surface | Why it is strong |
|---|---|
| Portal Sidebars V2 | Same idiom across PM / HR / Safety: dark slate-900 chrome · domain stripes · sentence-case sublines ≤14 words · domain stripe colour mirrors the priority map JSON. **Single visual vocabulary across three portals.** |
| Hub Tile Pattern | Identical structure on each Hub: left-edge stripe + white card + slate-200 border + h3 + ≤14-word coaching subline + single neutral slate-800 CTA. Operator brain stops "switching contexts" between portals. |
| Severity Discipline | SEV_PILL data-bound to severity; severe-tier banners record-level only; severe-incident email prefix `🚨 SEVERE INCIDENT · …` consistent across PM auto-email + Safety review. **True urgency reads the same regardless of which portal an operator is in.** |
| Communication Footers | Standardised via `operational_footer.py` + `branded_portal_emails.py` (iter437 IV-BETA.3 + P1C). Operator sees the same identifying line on every system email. |
| Auth Routing | Zero `/api/admin/*` leakage across PM / HR / Safety contexts. `EnforcePortalScope` clears tokens on URL exit. **One unbreakable auth contract across portals.** |
| Governance Health Chip (new) | Same chip on every Hub V2 (Admin / PM / HR / Safety). Operator can spot doctrine drift in one glance regardless of which portal they happen to be on. |

## III. Remaining fragmentation (🟡 to be addressed in later phases)

| Surface | Fragmentation |
|---|---|
| Admin Hub palette | Admin uses 5 hue families on the Hub today (per baseline). PM/HR/Safety collapsed to 2–3. Admin V2 calmness pass is **not yet scoped** — Admin remains the implicit "command center" portal with a richer palette. Acceptable; flagging for future review. |
| Hub kicker label | PM uses `PM PORTAL`, HR uses `HR PORTAL`, Safety uses `SAFETY PORTAL`. Admin uses prose. Consider unifying to mono kicker on Admin as well in a future polish pass — non-blocking. |
| Sub-page chrome | PM has rich `PmShell` with hamburger + portal switcher. HR has lean `HrPageShell`. Safety has lean `SafetyShell`. None of these are bugs, but the **density of chrome differs** between portals on sub-pages. Document, do not unify yet. |
| Hub-level "intro" sentence | PM no intro · HR has a 14-word read-only intro · Safety has only kicker. Acceptable variance per portal personality, but worth noting. |
| Tasks / Actions surface | "Tasks & Actions" tile appears on PM and Safety with slightly different sublines. Both pass the 14-word budget, but the wording (`Cross-portal accountability engine` vs `Cross-portal accountability`) differs. Easy unify in a future polish pass. |

## IV. Wording inconsistencies (🟡 small set)

| Surface | Today | Recommended |
|---|---|---|
| Hub kicker · Admin | (none) | `ADMIN CONSOLE` to match the other portals' mono kicker pattern |
| Safety incidents page kicker | `Safety Portal · Incidents` | Consider trimming to `Safety · Incidents` for parity with PM/HR sub-page kickers |
| `OPEN` CTA label | Used on all Hub tiles — consistent | 🟢 no change needed |
| `View as …` (impersonation) | Admin-only · used in Dispatch + Shop panels — consistent within Admin | 🟢 no change needed |

All recommended wording changes are **deferred** to a later polish
pass. No fragmentation currently blocks operator scan speed.

## V. Navigation friction (🟢 LOW)

| Vector | Risk | Status |
|---|---|---|
| Sidebar V2 mounting only at lg+ | Mobile / iPad portrait users see Hub tiles, not the sidebar | 🟢 by design — Hub tiles are the mobile-first navigation idiom |
| Cross-portal switcher placement | Admin has it in header, PM has it in header, HR/Safety do not (intentional — those portals are scoped) | 🟢 intentional · matches portal-isolation doctrine |
| Token isolation on URL exit | `EnforcePortalScope` clears tokens when URL leaves portal | 🟢 verified by `test_portal_token_routing.py` |
| Back-link consistency | Every sub-page has a `← {Portal} Hub` link via the shell | 🟢 consistent across HR + Safety + PM + Admin |

## VI. Mobile edge cases (🟢 checked)

| Case | Behaviour |
|---|---|
| Sidebar V2 + mobile | Sidebar hidden via `hidden lg:block`; Hub tile grid renders single-column |
| iPad portrait (768 px) | Sidebar hidden (below `lg`); operator uses Hub tiles |
| iPad landscape (1024 px) | Sidebar V2 mounts; full 4-domain map visible |
| Severity pills on mobile | Preserved size + weight at all viewports per doctrine §IV |
| File upload (Safety / PM) | Native `<input type="file">` preserved · iOS camera capture sheet works |
| Severe-incident email subject on iOS Mail preview | `🚨 SEVERE INCIDENT · …` readable in the 375 px preview line |

## VII. Hierarchy confusion (🟢 NONE detected)

| Test | Result |
|---|---|
| Each portal has 1 hierarchy hash across desktop / iPad / mobile | 🟢 PASS (per `diff_doctrine_baseline.py --summary`) |
| No portal has overlapping h1/h2 hierarchy | 🟢 PASS |
| KPI strip is visually subordinate to the Hub h1 | 🟢 PASS |
| Tile h3 < section h2 < page h1 | 🟢 PASS |

## VIII. Operator trust signals (🟢)

The platform now exposes **3 quiet trust signals** the operator can
read at a glance, all installed in the iter437 IV-BETA series:

1. **Governance health chip** — `governance stable · 27/100` on every Hub V2.
2. **Communication footer** — consistent identifying footer on every system email.
3. **Severe-tier email subject prefix** — `🚨 SEVERE INCIDENT · …` reserved for true escalation.

Combined, these tell the operator: "the system is calm; this email is
serious; this dashboard reflects yesterday's state, not noise." Three
small but reinforcing signals.

## IX. Cognitive load (🟢 reduced)

Per `HUB_VISUAL_BASELINE.json` aggregates:

| Portal | Hue families | Loudness | Calmness rank |
|---|---|---|---|
| PM | 3 | 26.86 | 🥇 calmest |
| Admin | 5 | 36.15 | 🥈 |
| HR | 2 | 64.71 | 🥉 (low hues; loudness driven by data-bound badges) |
| Safety | 2 | 66.78 | 🥉 (same profile as HR) |

Compared to the **iter437 IV-BETA.4 audit baseline**:

- Safety: 9 → 2 hue families (78% reduction)
- HR: 9 → 2 hue families (achieved in P1B)
- PM: held at 3 hue families (best-in-class · no change needed)
- Admin: 5 hue families (intentional richer palette · future review)

## X. Recommended next-cycle work (advisory · not authorised)

| Priority | Item |
|---|---|
| P1 | Admin Hub calmness review (if operator wants Admin to match PM's 3-hue discipline) |
| P2 | Wording unify pass (Hub kicker · Tasks subline parity) |
| P2 | Document the cross-portal IA decisions in a single `OPERATOR_VOCABULARY_GLOSSARY.md` |
| P3 | Consider extending Governance Health Chip to email subjects (chip rendered into the digest email header) — only if operator authorises |

## XI. Doctrine reaffirmed

- ✅ Cross-portal IDIOMS now consistent (Sidebar V2, Hub tiles, severity pills, footers)
- ✅ Auth boundaries verified across PM / HR / Safety
- ✅ No mechanical blockers to V2 default flip
- ✅ Mobile / iPad parity preserved
- ✅ Operator scan time reduced via palette collapse
- ✅ Preview only · no production deploy from this synthesis
