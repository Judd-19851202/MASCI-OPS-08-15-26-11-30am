# MOBILE_FIRST_LOCK_REPORT.md
**Phase 18 · iter414 · 2026-05-25**

## Verdict
**PASS — mobile-first doctrine locked at 390px across all Phase 12-17 surfaces.**

The touch-target audit returns clean. No undersized interactive elements. No stacked chaos. No horizontal overflow. The platform is genuinely field-first.

## Audit guardrail evidence
| Tool | Result |
|---|---|
| `/app/scripts/touch_target_audit.py` | **Clean** — no undersized interactive candidates ✅ |
| ESLint | Clean ✅ |
| Mobile validation iter399 | PASS ✅ |
| Mobile validation iter404 | PASS ✅ |
| Mobile validation iter409 | PASS ✅ |
| Mobile validation iter410 | PASS ✅ |
| Mobile validation iter411 | PASS ✅ |

## Per-surface 390px verification (re-walked)
| Surface | Verified | Status |
|---|---|:---:|
| `/field` Field Tile (4 lanes) | iter404 testing-agent | ✅ Sections stack cleanly · all 7 tiles tap-friendly |
| `/shift` driver self-start | iter401 testing-agent · iter402 SearchableSelect | ✅ 56px inputs · 64px primary button · WCAG-AAA tap targets |
| QR sticker card (iter406) | iter406 print-CSS sweep | ✅ Card prints at 340px · 220px QR readable |
| `/dispatch-portal` (iter411) | iter411 testing-agent | ✅ 7 sections stack single-column · Issue Work reflows to `grid-cols-2 lg:grid-cols-4` |
| `/dispatch-portal/board` | iter408 testing-agent | ✅ Drawer slides over · 56px+ tap targets · combobox fits |
| Assignment Create Drawer (iter408/410) | iter410 testing-agent | ✅ Drawer occupies full viewport on 390px · 9 fields scroll cleanly |
| Tanker conditional fields | iter410 | ✅ 3 conditional fields stack vertically · catalog dropdown searchable |
| `/pm` PM Hub + PmHaulActivityTile (iter409) | iter409 testing-agent | ✅ Stats reflow to 2 columns · empty state visible |
| `/shop` Shop Hub + BREAKDOWN tile (iter396) | testing-agent | ✅ Tile stacks · BREAKDOWN row tap-friendly |
| `/field-leadership` | iter319 + iter396 mobile sweep | ✅ |
| `/admin/dls/shift-qr` (iter406) | iter406 mobile print-CSS | ✅ Inputs scale · QR remains scannable |
| `/admin/dls/health-summary` JSON endpoint | n/a (API) | n/a |

## Mobile drift patterns NOT found
- ❌ No stacked chaos (sections cleanly flow top → bottom on 390px)
- ❌ No cramped forms (`min-h-[48px]` inputs throughout iter402+)
- ❌ No buried actions (primary CTAs are always above-the-fold or floating)
- ❌ No broken dropdowns (SearchableSelect pattern handles 390px)
- ❌ No impossible taps (touch-target audit clean)
- ❌ No horizontal overflow (no `whitespace-nowrap` on critical paths)
- ❌ No operational overload (calm spacing preserved · 7-section cap on portals)

## Mobile drift patterns PRESENT (legacy · non-blocking)
- ⚠️ Legacy table dashboards (HrTimeVerification · HrTrainingRecords · MeetingsDashboard) use `<table>` chrome that doesn't reflow as well on 390px. **Acceptable**: these are HR/Safety leadership surfaces accessed primarily from desktop. Day-1 debrief Question 3 will surface if field users actually hit them on phones.
- ⚠️ Some legacy form pages (Daily Report · Inspections) use 1-column layouts that work but lack the iter408-era spacious 56px+ tap rhythm.

## Field-first doctrine reinforced
| Principle | Status |
|---|:---:|
| Drivers operate the platform on phones only | ✅ |
| Dispatchers operate primarily on desktop, but mobile-functional | ✅ |
| PM/Shop monitor primarily on desktop | ✅ |
| Public field forms must work on 390px without zoom | ✅ |
| Tap targets ≥ 44px on all interactive paths | ✅ |

## Phase 18 conclusion
**Mobile-first lock holds.** No regressions surfaced. Legacy table chrome on HR surfaces deferred until Day-1 names them as a problem on phones.
