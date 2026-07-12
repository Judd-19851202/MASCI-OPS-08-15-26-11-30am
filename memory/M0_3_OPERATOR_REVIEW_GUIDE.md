# M0.3 · Operator Review Guide

_Phase V.1 · 2026-05-29 · final UI checkpoint before pilot._

The directive after M0.2/M0.2A was unambiguous:

> "After M0.3: **STOP.** Do NOT begin M1 migration, dual-write,
> pilot rollout, RFI, Schedule, P6. Await operator review."

This guide is the briefing for that review. Read top-to-bottom in
~5 minutes. Then decide whether to authorize M1.

---

## 1 · What shipped in M0.3

| Surface | Route | Purpose |
|---|---|---|
| Foreman ODR Entry | `/odr/new` | Phone-first, bilingual, 9-step progressive entry · OGC coaching · readiness preview |
| FL ODR Command Center | `/odr/center` | 7 calm tabs · role-aware scope · trust banner |
| PM Consumption Panel | `/pm/odr` | 5-metric "project risk today" lens · read-only · audience-safe |
| Public ODR Viewer | `/odr/public/:doc_id` | DOT/FAA/CEI/Owner-safe view · no-auth · continuity-gated |
| ODR Detail | `/odr/:id` | Substrate read view · 5-audience PDF buttons · amendment chain |
| ODR Done | `/odr/:id/done` | Post-submit confirmation · 24h amend window reminder |
| Trust Banner | embedded | One quiet line · neutral palette · dismissible |
| Adoption Observation | `/api/odr/observation/{event,summary}` | Aggregate-only adoption telemetry |

## 2 · Locked decisions (codified · no further review)

| Decision | Implementation |
|---|---|
| OGC tone: teach, not judge | `guidance_catalog.py` voice is superintendent-mentor; no AI runtime |
| External PDF redaction | `pdf._project_for_audience("external")` strips coaching/readiness/internal data |
| Amendment authority | Foreman 0–24h · Super+ 24h+ · PM 24h+ (project ownership) · Admin always — enforced in `amendments.py::_resolve_role` |
| Public link mint authority | Admin + PM only (Foreman / Crew Lead refused) — enforced in `continuity.py::mint_link` |

## 3 · What this wave does NOT do (per directive)

- ❌ NO M1 migration. NO dual-write.
- ❌ NO pilot rollout.
- ❌ NO RFI. NO Schedule. NO P6.
- ❌ NO production deploy. Preview only.

## 4 · What I would test myself first

1. **Visit `/odr/public/ODR-2026-00003?link=backup-forensics`** — confirm you see ONLY the public-safe envelope (header, crew, production, delays, safety flag, weather, signature, footer). NO coaching, NO readiness, NO telemetry.
2. **Visit `/odr/new`** on a phone-width viewport — toggle EN/ES, step through to the Sign step, attempt submit without ack (expect calm amber hard-stop), check ack and submit (expect navigation to `/odr/{id}/done`).
3. **Visit `/odr/center`** — confirm seven tabs render with calm row layout, no "dashboard sludge."
4. **Visit `/pm/odr`** — confirm 5 metric tiles, list of submitted ODRs, per-row PDF download.
5. **Open any ODR detail** — confirm the 5 audience PDF buttons render, click "External" and read the PDF as a CEI rep would.

## 5 · Telemetry validation

Run as Admin:

```
GET /api/odr/observation/summary?days=1
```

Expect:

- `total_events` > 0
- `by_surface` shows `foreman`, `fl_center`, `pm_panel`
- `average_submit_duration_s` populated after a couple of submits
- **NEVER** any `by_uid` / `actors` / `per_foreman_*` fields

## 6 · Doctrine compliance audit

| Doctrine | Inherited / new | Evidence |
|---|---|---|
| FIELD_LEADERSHIP_VISIBILITY_DOCTRINE | inherited | FL Center header displays `fll`+`verb` from server projector |
| OGC Catalog tone | locked | `guidance_catalog.py` content unchanged from M0.2A — operator-approved |
| External PDF redaction | locked | `pdf._project_for_audience("external")` audit-trail tested |
| Amendment authority | locked | `amendments.py::_resolve_role` + 24h window enforcement |
| Public link mint authority | locked | Admin + PM only path tested in `test_odr_m03.py` |
| Trust banner doctrine | new | `ODR_TRUST_BANNER_DOCTRINE.md` · component renders on every ODR surface |
| Adoption observation plan | new | `ODR_ADOPTION_OBSERVATION_PLAN.md` · aggregate-only API |

## 7 · Test surface

| Suite | Result |
|---|---|
| `tests/odr/test_odr_substrate.py` (M0.1 regression) | 12/12 |
| `tests/odr/test_odr_m02.py` (M0.2 + M0.2A regression) | 24/24 |
| `tests/odr/test_odr_m03.py` (NEW · M0.3) | 9/9 |
| Wave 1 substrate + 1.1 sidecar regression | 27/27 |
| `scripts/odr_public_link_continuity_probe.py --gate` | ✅ 0 failures |
| `scripts/odr_bilingual_probe.py --gate` | ✅ 0 failures |
| `ruff check backend/routes/odr/ scripts/odr_*.py` | ✅ clean |
| `eslint frontend/src/pages/odr/ frontend/src/lib/odrApi.js frontend/src/components/odr/` | ✅ clean |
| Browser smoke (Playwright) | ✅ `/odr/new` renders · `/odr/public/...` renders cleanly |

**Total: 72 tests + 2 probes · 0 failures · 0 regression.**

## 8 · What I want approval on before M1

- [ ] **Foreman entry tone** — Read the EN copy on each step (project / crew / production / delays / safety / tomorrow / sign). Does it feel field-native? Anything that sounds "corporate" should change before pilot.
- [ ] **Public viewer redaction** — Open the public viewer and check: does it look like something you'd hand to FDOT?
- [ ] **PM panel emphasis** — Are the 5 metrics the right 5? Should "Open Constraints" replace one of them?
- [ ] **Trust banner copy** — "Operational Record · Audit history protected · Amendments tracked." — keep as-is, or change.

## 9 · Stop condition acknowledged

🛑 **HALTED at end of M0.3 as directed.**

Awaiting operator instruction before M1 migration / dual-write /
pilot rollout. RFI / Schedule / P6 remain explicitly OUT of scope
until those are independently authorized.

The platform now offers an end-to-end ODR experience for Foremen,
Field Leadership, PMs, and external stakeholders — anchored by
deterministic guidance, continuity-safe public links, audit-true
amendments, and audience-aware PDFs.

Field usability achieved. Operational trust preserved. Doctrine
respected.

_End of M0.3 Operator Review Guide._
