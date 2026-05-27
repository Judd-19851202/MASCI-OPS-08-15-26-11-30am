# Pre-Safety Certification

*Phase IV-BETA.3-P2D · iter437 · 2026-02-27*
*Status: 🟢 PLATFORM CERTIFIED STABLE FOR SAFETY GOVERNANCE START*
*Awaiting operator authorisation to begin Safety portal alignment.*

> **Verification legend:**
> 🟢 stable · 🟡 caution · 🔴 blocker

---

## I. Mandate

Before Safety governance begins, verify the platform is stable enough
to safely absorb the Safety portal's V2 alignment work. This cert
scores 8 categories and produces a single go/hold signal.

## II. Certification matrix

| Category | Score | Evidence |
|---|---|---|
| **Cross-portal consistency** | 🟢 | Admin V2 + PM V2 + HR V2 all share the same doctrine: slate-900 chrome, domain-grouped sidebar, ≤14-word coaching sublines, neutral-CTA hub tiles, severe-tier email prefixes. Visual baseline confirms cohesion (`HUB_VISUAL_BASELINE.json`). |
| **Auth boundary stability** | 🟢 | iter437 P0 fix held for 4 iterations. PM auth-routing suite **27/27 green**, zero `/api/admin/*` leak across 7 PM routes × 3 viewports. HR audited clean. Doctrine snapshot baseline includes admin-leak guard. |
| **Mobile governance stability** | 🟢 | All 3 hubs render cleanly at 390×844 (mobile baseline). PM mobile sidebar V2 explicitly hidden by design; HR Sidebar V2 hidden `<lg` (intentional). iPad walked counts match desktop for every hub (no hidden-content delta). |
| **Communication doctrine stability** | 🟢 | 6/6 subject-line drift sites remediated and locked. 3-line operational footer cascades to 5 portal email types (PM/Shop/HR/Safety/Dispatch + Admin alerts). 89/89 unit tests green incl. iter238 PM gold-standard intact at 44/44. |
| **Regression maturity** | 🟢 | **138/138 cells green across 9 test files** (24 + 15 + 44 + 4 + 15 + 9 + 27 + governance scripts + lint). Every new feature in iter437 has a dedicated regression file. |
| **Governance instrumentation maturity** | 🟢 | Three warning-only stages in `pre_deploy_check.sh` (coaching · admin copy · visual loudness) + new DOM-style doctrine baseline. P0-class gates (admin leaks · contamination · env mismatch · auth routing) remain deploy-blocking. |
| **Deploy governance maturity** | 🟢 | `pre_deploy_check.sh` syntax-clean. New "Portal auth-routing" stage runs the leak guard before every deploy. Visual loudness sweep extended to include `/hr` routes. Coaching subline gate hardened with 6 escalation-wording bans. |
| **Operational trust maturity** | 🟢 | Operator can hand a new hire the Cross-Portal Operator Atlas + the doctrine baseline JSON and have a single page of measurable platform truth. Every email now carries the calm "MASCI · automated operational notice · {Portal} Portal · do-not-reply" footer. |

## III. Verdict

**🟢 PLATFORM CERTIFIED STABLE.** Safety governance is safe to begin
on operator authorisation. No blockers detected.

## IV. Conditions / cautions for the Safety pass

| Condition | Why it matters | Owner |
|---|---|---|
| Promote `?hrSidebarV2=1` and `?pmSidebarV2=1` out of flag **before** introducing `?safetySidebarV2=1` | Avoids tri-mode UX state | Operator decision |
| Baseline Safety hub on day 1 of its V2 work | Establishes pre-Safety-Hub vs post-Safety-Hub trend | Implementation iteration |
| Re-run `test_visual_doctrine_baseline.py` after each Safety hub commit | Detects unintended drift on the existing 3 portals | CI / pre-deploy gate |
| Keep using the doctrine snapshot, not pixel-diff | Avoids false-positive screenshot noise | This iteration's instrument |
| Safety V2 must NOT touch `/api/admin/*` from Safety token | iter180 boundary doctrine | `test_portal_token_routing.py`-style test for Safety |

## V. Recommended order for Safety governance (when authorised)

1. **Safety inventory audit** (mirrors `HR_PORTAL_CURRENT_STATE_AUDIT.md` discipline)
2. **Safety V2 information priority map** (mirrors `HR_INFORMATION_PRIORITY_MAP.json`)
3. **Safety Sidebar V2 behind `?safetySidebarV2=1`**
4. **Safety doctrine snapshot** (extends `HUB_VISUAL_BASELINE.json`)
5. **Safety Playwright regression suite** (mirrors `test_hr_sidebar_v2.py`)
6. **Safety calmness tuning** (if/when baseline shows it's needed)
7. **Safety governance docs** (mirror the 8-doc HR set)

## VI. Items deferred from this iteration

| Item | Defer to |
|---|---|
| Promote `?hrSidebarV2=1` out of flag | Operator pilot day |
| Promote any baseline metric to deploy-blocking | After 2 more iterations of trend data |
| Refine the "badge" heuristic to reduce HR Hub false-positives | Same |
| Add Safety / Dispatch / FL cells to the baseline test | When those portals' V2 ships |
| Field Leadership surface A vs B unification decision | Operator call |

## VII. Doctrine reaffirmed (final)

- ✅ Preview only · `APP_ENV=preview` · `DB_NAME=masci_safety_preview`
- ✅ NO production deploy
- ✅ NO destructive data action
- ✅ NO backend rewrites · NO notification engine fork · NO permission changes
- ✅ NO weakening of `/api/admin/*` boundary
- ✅ All artifacts distinguish 🟢 / 🟡 / ⚪
- ✅ Every change regression-locked BEFORE certification
- ✅ Doctrine-snapshot baseline captured (9 cells)

# 🟢 PRE-SAFETY CERTIFICATION CLOSED · platform ready · STOP for operator review
