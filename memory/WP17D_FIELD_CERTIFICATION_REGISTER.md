# WP-17D Field Certification Register

Last updated: 2026-08-01

## Scope Rule
- This register tracks **rendered Field-family surfaces only**.
- Pure redirects and aliases that do not render their own UI are excluded from the denominator.
- A route is only marked **COMPLETE** when it passes all gates: Visual, Functional, English, Spanish, Responsive, Console/Network, Constitution Guard, Anti-Drift, and associated workflow coverage.
- A workflow is only marked **COMPLETE** when its operator journey is exercised end-to-end in English and Spanish.

## Current Denominator
- Total audited Field-family rendered routes: **36**
- Total audited Field-family workflows: **16**
- Fully certified routes: **0**
- Fully certified workflows: **0**
- Reopened under Executive Amendments #5–#9: **36 routes / 16 workflows**
- Remaining uncertified routes: **36**
- Remaining uncertified workflows: **16**

## Gate Legend
- Route Status: per-surface certification state
- Workflow Status: end-to-end journey state
- Visual: layout, governed primitives, no drift
- Functional: interactive controls and state changes exercised
- EN: English content check
- ES: Spanish content check
- Responsive: 390 / 430 / 768 / 1024 / 1440
- Workflow Complete: `Yes` only when the full operator journey passes
- Blocking Defects: currently open workflow or route blockers
- Executive Notes: evidence, caveats, and next certification gap

Status values: `REOPENED`, `IN_PROGRESS`, `COMPLETE`, `BLOCKED`

## Route Register

| Route | Surface Family | Route Status | Workflow Status | Visual | Functional | EN | ES | Responsive | Workflow Complete | Blocking Defects | Executive Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/field` | Field landing | IN_PROGRESS | Supports `field-launchpad` | Pass (smoke) | Partial | Pass | Pass | Pass | No | Remaining card/button exercise | ES toggle locator repaired; 390/430/768/1024/1440 checks now pass. |
| `/field/calculators` | Calculators landing | IN_PROGRESS | Supports `material-calculators` | Pass (smoke) | Partial | Pass | Pass | Pass | No | Calculator-by-calculator exercise pending | Shared shell padding + calculator mobile overflow repaired. |
| `/daily/submit` | Daily Report create | IN_PROGRESS | `daily-report` | Pass | Pass | Pass | Pass | Pass (390/1024) | Partial | Detail/review/edit/return surfaces still pending | Draft restore prompt, GPS-denied branch, crew/equipment/production, photo uploads, attachment upload, manual summary, signature, EN submit, and ES submit are now proven. |
| `/thank-you` | Shared field success state | IN_PROGRESS | Supports `daily-report`, `equipment-preop` | Pass | Pass | Pass | Pass | Pass (390/1024) | Partial | Queued and failed states still pending | Hidden shared success surface discovered in HUNT MODE. Spanish mixed-language survivor was fixed; Daily and Equipment success states now pass here. |
| `/equipment/new` | Equipment Pre-Op create | IN_PROGRESS | `equipment-preop` | Pass | Pass | Pass | Pass | Pass (390) | Partial | Dedicated review/detail route still pending | Validation, full all-pass submission, signature capture, and bilingual success-state proof now pass; unauthenticated roster/taxonomy console noise was removed. |
| `/equipment/submit` | REOPENED | `equipment-preop-public` | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | No | Route + workflow untouched under Amendment #6 | Same workflow family as `/equipment/new`, but must be independently certified. |
| `/fleet/dvir/new` | DVIR create | IN_PROGRESS | `dvir` | Pass | Pass | Pass | Pass | Pass (390) | Partial | Draft/resume support not yet found; return/wider-breakpoint pass still pending | Camera obstruction block, no-defect submit, signature, photo-backed defect submit, and ES localization all now have direct evidence. |
| `/fleet/dvir/submit` | IN_PROGRESS | `dvir-public` | Pass (smoke) | Partial | Pass | Pass | Pass (390) | Partial | Full public submit under the alias still pending | Public alias route reopened and verified in Spanish; no inherited certification from `/fleet/dvir/new`. |
| `/fleet/weekly-lead/new` | Weekly lead inspection | REOPENED | `weekly-lead-inspection` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Full route + workflow certification pending | Needs full route certification. |
| `/fleet/weekly-emergency/new` | Weekly emergency inspection | REOPENED | `weekly-emergency-inspection` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Full route + workflow certification pending | Needs full route certification. |
| `/fleet/dvir/submitted/:id` | DVIR confirmation | IN_PROGRESS | `dvir` | Pass | Pass | Pass | Pass | Pass (390) | Partial | Return CTA / wider breakpoints still pending | Both live confirmation branches and orphan deep-link confirmation were reopened and inspected. |
| `/shift` | Driver shift start | REOPENED | `shift-start-driver` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Start-to-active-driver flow not yet exercised | Field-family operator start surface. |
| `/driver` | Driver active shift | REOPENED | `shift-start-driver` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Live control interaction checks pending | Must pass live control interaction checks. |
| `/d/:token` | Driver magic-link landing | REOPENED | `driver-magic-link` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Token fixture + full public journey pending | Independent route certification required. |
| `/leadership/login` | Field Leadership login | IN_PROGRESS | `field-leadership-record` | Pass | Pass | Pass | Pass | Pass (390) | Partial | Wider breakpoint rerun still pending | Login → route launch → bilingual record submission has now been exercised successfully. |
| `/leadership` | Field Leadership landing | IN_PROGRESS | Supports `field-leadership-record` | Pass | Pass | Pass | Pass | Pass (390) | Partial | Wider breakpoint rerun still pending | Tile launcher + bilingual submit path now proven through `/leadership/verbal_coaching/new`. |
| `/leadership/hub_v2` | Field Leadership companion | REOPENED | Supports `field-leadership-record` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Route untouched | Route exists and must be individually certified. |
| `/leadership/records` | Field Leadership list | IN_PROGRESS | `field-leadership-record` | Pass | Pass | Pass | Pass | Pass (390) | Partial | Print/export/list filtering still pending | Records subtitle translated, mobile overflow removed, and return navigation from submitted records is now proven. |
| `/leadership/records/:id` | Field Leadership detail | IN_PROGRESS | `field-leadership-record` | Pass | Pass | Pass | Pass | Pass (390) | Partial | Print/export/back across breakpoints still pending | Detail view now renders Spanish original text via bilingual sidecar, shows original-language badge, and passes 390px without overflow. |
| `/leadership/:kind/new` | Field Leadership create | IN_PROGRESS | `field-leadership-record` | Pass | Pass | Pass | Pass | Pass (390) | Partial | Additional kinds still pending | Draft restore, signature capture, English submit, Spanish submit, and detail landing are now proven for `verbal_coaching`. |
| `/field-leadership/portal/login` | Field Leadership portal login | IN_PROGRESS | `field-leadership-portal` | Pass (smoke) | Partial | Pass | Pass | Pass (390) | No | Portal-to-record journey pending | Independently verified route path now lands on the governed dashboard after FL login. |
| `/field-leadership/portal/change-password` | Field Leadership auth maintenance | REOPENED | `field-leadership-portal` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Separate auth maintenance route untouched | Included in Field-family auth scope. |
| `/field-leadership/portal/dashboard` | Field Leadership portal dashboard | IN_PROGRESS | `field-leadership-portal` | Pass (smoke) | Partial | Pass | Pass | Pass (390) | No | Full dashboard-to-record completion pending | ES dashboard copy repaired, mobile overflow removed, and workflow launchers 0-4 now route correctly. |
| `/field-leadership/portal` | Field Leadership portal root | REOPENED | `field-leadership-portal` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Root route needs direct evidence | Separate route path; no inherited pass-through allowed. |
| `/field-leadership/portal/driver-qualification` | Field Leadership driver qualification | IN_PROGRESS | `driver-qualification` | Pass (smoke) | Partial | Pass | Pass | Pass (390) | No | Full list/filter/return coverage pending | ES subtitle/portal chrome repaired and 390px mobile layout passes without overflow. |
| `/admin/daily` | Admin daily list | REOPENED | `daily-report-review` | Prior evidence | Reopened | Prior evidence | Reopened | Prior evidence | No | Admin review path not yet exercised | Field workflow review surface. |
| `/daily-reports` | Daily report review alias | REOPENED | `daily-report-review` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Hidden field review list discovered in HUNT MODE | Canonical list route separate from `/admin/daily` and must be certified independently. |
| `/admin/daily/:id` | Admin daily detail | REOPENED | `daily-report-review` | Prior evidence | Reopened | Prior evidence | Reopened | Prior evidence | No | Detail review/print/return path pending | Field workflow detail surface. |
| `/pm/daily` | PM daily list | REOPENED | `daily-report-review` | Reopened | Reopened | Reopened | Reopened | Reopened | No | PM review path pending | Needs full certification. |
| `/pm/daily/:id` | PM daily detail | REOPENED | `daily-report-review` | Prior evidence | Reopened | Prior evidence | Reopened | Prior evidence | No | Detail review/return path pending | Field workflow detail surface. |
| `/admin/equipment-inspections` | Admin equipment list | REOPENED | `equipment-review` | Prior evidence | Reopened | Prior evidence | Reopened | Prior evidence | No | Admin equipment review path pending | Field workflow review surface. |
| `/admin/equipment/:id` | Admin equipment detail | REOPENED | `equipment-review` | Prior evidence | Reopened | Prior evidence | Reopened | Prior evidence | No | Detail review path pending | Field workflow detail surface. |
| `/admin/leadership/records` | Admin field leadership list | REOPENED | `field-leadership-record` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Hidden admin review path discovered in HUNT MODE | Separate admin route path; no inherited certification from `/leadership/records`. |
| `/admin/leadership/records/:id` | Admin field leadership detail | REOPENED | `field-leadership-record` | Reopened | Reopened | Reopened | Reopened | Reopened | No | Hidden admin detail path discovered in HUNT MODE | Separate admin route path; must be certified independently. |
| `/pm/equipment` | PM equipment list | REOPENED | `equipment-review` | Reopened | Reopened | Reopened | Reopened | Reopened | No | PM equipment review path pending | Needs full certification. |
| `/pm/equipment/:id` | PM equipment detail | REOPENED | `equipment-review` | Reopened | Reopened | Reopened | Reopened | Reopened | No | PM detail review path pending | Needs full certification. |

## Workflow Register

| Workflow | Operator Journey | Route Scope | EN | ES | Responsive | Workflow Complete | Blocking Defects | Executive Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `field-launchpad` | Open `/field` → launch cards → return | `/field` | Partial | Partial | Pass (smoke) | No | Full card/button exercise pending | Launcher smoke only so far. |
| `material-calculators` | Open `/field/calculators` → choose calculators → calculate/reset/save | `/field/calculators` | Partial | Partial | Pass (smoke) | No | Calculator-by-calculator journey pending | Landing + ES layout repaired; tool journeys remain. |
| `daily-report` | Entry → new report → draft → restore → GPS branch → crew/equipment/production → photos → attachment → manual summary → signature → submit → success | `/daily/submit`, `/thank-you` | Pass | Pass | Pass (390/1024) | Partial | Detail/review/edit/return branches still pending | EN and ES submit paths now reach `/thank-you`; shared success copy was recertified after a Spanish mixed-language survivor fix. |
| `equipment-preop` | Open route → fill unit + checklist + camera gate + signature → submit → success/review | `/equipment/new` | Pass | Pass | Pass (390) | Partial | Dedicated review/detail route still pending | EN + ES operator journeys now reach the governed `/thank-you` success state with all-pass checklist completion and signature capture. |
| `equipment-preop-public` | Public entry → fill checklist → submit → success/detail | `/equipment/submit` | Reopened | Reopened | Reopened | No | Untested | Public variant must be certified independently. |
| `dvir` | Open route → fill truck + defects + camera gate → signature → submit → confirmation | `/fleet/dvir/new`, `/fleet/dvir/submitted/:id` | Pass | Pass | Pass (390) | Partial | Explicit draft/resume branch still not found; return/wider-breakpoint pass pending | No-defect, defect-with-photo, and obstruction-block branches are all now proven. |
| `dvir-public` | Public DVIR → entry → localization → submit → confirmation | `/fleet/dvir/submit`, `/fleet/dvir/submitted/:id` | Partial | Partial | Pass (390) | No | Needs full public submit proof | Public alias reopened in HUNT MODE; still needs full public-path submission evidence. |
| `weekly-lead-inspection` | Lead inspection → answer sections → submit → success | `/fleet/weekly-lead/new` | Reopened | Reopened | Reopened | No | Untested | Workflow untouched. |
| `weekly-emergency-inspection` | Emergency inspection → answer sections → submit → success | `/fleet/weekly-emergency/new` | Reopened | Reopened | Reopened | No | Untested | Workflow untouched. |
| `field-leadership-record` | Login → landing → new record → save draft → restore draft → signature → submit → detail → records | `/leadership/login`, `/leadership`, `/leadership/records`, `/leadership/:kind/new`, `/leadership/records/:id` | Pass | Pass | Pass (390) | Partial | Export/print + additional record kinds still pending | Proven with `verbal_coaching`: EN submit succeeded, ES submit succeeded after translation/meta + auth fixes, draft restore worked, detail now shows Spanish originals through bilingual sidecar. |
| `field-leadership-portal` | Portal login → dashboard → launch workflow → return | `/field-leadership/portal/login`, `/field-leadership/portal/dashboard`, `/field-leadership/portal` | Partial | Partial | Pass (smoke) | No | Dashboard launcher smoke only | Portal chrome stabilized. |
| `driver-qualification` | Open qualification view → inspect readiness states → navigate back | `/field-leadership/portal/driver-qualification` | Partial | Partial | Pass (smoke) | No | Wider breakpoint + full control checks pending | Read-only but still workflow-scoped. |
| `shift-start-driver` | `/shift` start → `/driver` active journey → acknowledge/transition/upload/return | `/shift`, `/driver` | Reopened | Reopened | Reopened | No | Entire journey untested | Core driver operator flow. |
| `driver-magic-link` | `/d/:token` → acknowledge/start → active driver flow | `/d/:token`, `/driver` | Reopened | Reopened | Reopened | No | Token fixture + live journey pending | Public token-based flow. |
| `daily-report-review` | Submit report → admin/PM list → detail/review/return/print | `/admin/daily`, `/admin/daily/:id`, `/pm/daily`, `/pm/daily/:id` | Reopened | Reopened | Reopened | No | Reviewer credentials + fixture journey pending | Cross-role completion workflow. |
| `equipment-review` | Submit inspection → admin/PM list → detail/review/return | `/admin/equipment-inspections`, `/admin/equipment/:id`, `/pm/equipment`, `/pm/equipment/:id` | Reopened | Reopened | Reopened | No | Reviewer credentials + fixture journey pending | Cross-role completion workflow. |

## Current Blockers
- Daily Report still lacks verified detail/review/edit/return certification after public submit, and its custom-job draft restore branch needs a cleaner end-to-end replay proof.
- DVIR still needs confirmed draft/resume parity (if the branch exists), plus public alias submit proof and full return/wider-breakpoint confirmation coverage.
- Shared success route `/thank-you` still needs queued and failed-state certification, not just delivered/archive states.

## Immediate Execution Focus
1. Close the remaining Daily Report survivors: detail/review/edit/return surfaces, cleaner custom-job draft restore proof, and queued/failed `/thank-you` states.
2. Finish DVIR with public alias submit proof, return-path certification, and explicit confirmation on whether draft/resume is missing or just undiscovered.
3. Finish the remaining Field Leadership gaps: export/print, wider breakpoint reruns, and additional record kinds beyond `verbal_coaching`.
4. Certify the remaining crew-facing Field workflows (`/equipment/submit`, weekly inspections, `/shift`, `/driver`, `/d/:token`) with full journey coverage.
5. Reopen Field review/detail surfaces (`/admin/daily`, `/admin/daily/:id`, `/pm/daily`, `/pm/daily/:id`, `/admin/equipment-inspections`, `/admin/equipment/:id`, `/pm/equipment`, `/pm/equipment/:id`) and attach them to submit-review workflows.
6. Continue until both the route denominator and workflow denominator reach zero uncertified items.