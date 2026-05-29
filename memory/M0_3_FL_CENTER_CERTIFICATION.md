# M0.3 · Field Leadership ODR Center · Certification

_Phase V.1 · 2026-05-29 · ROLE-AWARE COMMAND CENTER · NOT A DASHBOARD._

## Mission

A calm command center for Foremen / Superintendents / Senior Supers
that surfaces what they need to **run work successfully** — without
"dashboard sludge."

## Page

`/odr/center` · `/app/frontend/src/pages/odr/OdrCenter.jsx`

## Primary views (7 calm tabs)

| Tab | Surfaces |
|---|---|
| Needs Attention | Drafts and returned ODRs in the actor's scope |
| Recently Submitted | What the field reported in the last 7 days |
| Recently Amended | ODRs changed after submission (Super+/Admin trail) |
| Ready for Review | Submitted records awaiting approval |
| Constraint-Linked | ODRs tied to active operational constraints |
| Chronology | Recent events across the actor's scope |
| Readiness Signals | Records with open hard stops or missing required items |

Each tab uses the same `GET /api/odr` endpoint with role-aware scope
filtering already enforced by `routes/odr/visibility.py`. The
front-end never re-implements visibility — it consumes the
projector's verb (`FULL` / `LIMITED` / `SUMMARY` / `NONE`).

## Role-aware behavior (Field Leadership Visibility Doctrine)

| FLL | Scope | UI signal |
|---|---|---|
| FLL-1 Foreman | own ODRs (`project.foreman_uid` match) | "FLL-1 · FULL verb" displayed in header |
| FLL-2 General Foreman | own crews managed | scope filtered server-side |
| FLL-3 Superintendent | project assignment | full project visibility |
| FLL-4 Senior Super | regional assignment | regional aggregation |
| FLL-5 PM | redirected to `/pm/odr` (PM has dedicated consumption panel) |
| FLL-6 Admin / Ops Leadership | SUMMARY default (open scope) |

UI never displays the FLL of any OTHER user — only the actor's own
FLL. That's intentional: FL doctrine does not gossip about hierarchy.

## What's calm (intentional design choices)

| Choice | Why |
|---|---|
| No metric tiles | Tiles are PM/exec language; FL leaders work in rows |
| Single-line row | crew + project + status — operator can scan 50 rows |
| Capitalized verb pills | submitted / draft / returned — color-coded gently |
| No badges-of-engagement | no streaks, no fire emojis, no "behind by X" |
| Tab descriptions | one quiet sentence per tab — fewer questions later |
| Trust banner | one calm reminder · dismissible per session |
| Empty state | "Nothing here right now. That's good." — calm, not anxious |

## Telemetry wired

| Event | Tracked |
|---|---|
| Tab opened | `fl_inbox_opened` (with context.tab) |
| Record opened | `fl_record_opened` |
| Chronology tab opened | `chronology_opened` |
| Readiness tab opened | `readiness_signal_clicked` |
| PDF downloaded from detail | `pdf_rendered` |

All telemetry is aggregate-only — see `ODR_ADOPTION_OBSERVATION_PLAN.md`.

## Test surface

- `data-testid="fl-odr-center"` · `fl-odr-tabs` · `fl-odr-tab-{key}` ·
  `fl-odr-tab-desc` · `fl-odr-list` · `fl-odr-row-{doc_id}` · `fl-odr-empty`
- Backend `tests/odr/test_odr_substrate.py::test_8_list_returns_fll_verb_for_admin`
  proves the scope filter + verb wiring.
- M0.3 pytest exercises continuity + amendment chain reads that the
  detail link surfaces.

## Out of scope (deferred to M0.4)

- Side-by-side amendment diff viewer.
- In-line approve / return controls.
- Bulk-select / bulk-action surfaces (operationally noisy).
- Real-time updates (polling acceptable at M0.3).

## Verdict

🟢 **FL ODR COMMAND CENTER LIVE.** Calm, role-aware, role-respectful.
Drives the superintendent's day without bombarding them with noise.
Visibility doctrine is inherited at the server projector — front-end
never bypasses.
