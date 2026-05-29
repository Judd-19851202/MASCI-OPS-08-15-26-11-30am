# M0.35 · ODR Reality Validation Report

_Phase V.1 · 2026-05-29 · pre-M1 stress test · evidence-based._

## Mission

Force ODR through 4 realistic MASCI workflows and observe what
breaks, what stutters, and what feels right — BEFORE M1 migration
starts.

The harness is `/app/scripts/odr_reality_validation.py`. Raw
results: `/app/memory/M0_35_REALITY_VALIDATION_RAW.json`.

## Scenarios run (4 / 4 submitted clean)

| # | Scenario | doc_id | total ms | submitted? | readiness |
|---|---|---|---|---|---|
| 1 | Airport · Taxiway Closure | ODR-2026-00029 | 5,442 | ✅ | ready |
| 2 | Drainage · Utility Conflict | ODR-2026-00030 | 4,923 | ✅ | ready |
| 3 | Asphalt · Plant Issue + MOT | ODR-2026-00031 | 4,804 | ✅ | ready |
| 4 | Concrete · Structures + Amendment | ODR-2026-00032 | 5,340 | ✅ | ready |

Average end-to-end backend round-trip per ODR (create + 8 patches +
ack + submit + 5 PDFs + audience-profile call + public-link mint +
public resolve): **~5.1 seconds** over the preview HTTPS edge.

## What worked under realistic load

| Capability | Evidence |
|---|---|
| Substrate accepts polymorphic production segments | Pipe runs (RCP), paving lifts, concrete cylinders, airfield paving ALL accepted by `production_segments[]` polymorphic body |
| Materials register accepts mixed kinds (delivered + rejected) | Asphalt scenario captures rejected load 994118 with vendor + ticket |
| Bilingual `LocalizedString` carries free-text from foreman | `delays.entries[].description.text` populated freely |
| Safety event flow refuses submit until notified+complete | Drainage near-miss event explicitly populated `notified_safety=true` + `incident_report_complete=true` (both required for submit) |
| Amendment engine writes `odr_amendments` row | Concrete scenario's QC correction recorded with old/new + reason · `amendment_recorded=true` |
| 24-h amend window stamped on submit | Every scenario's `amend_allowed_until_utc` populated |
| 5-audience PDFs render | All 5 audiences rendered for all 4 scenarios |
| Audience SHA differentiation | Foreman+Super same (intentional); PM, Executive, External all distinct |
| Audience-profile mapping | `audience_profile=external_dot` → `X-ODR-Audience: external` confirmed |
| Public link auto-locks to External | `audience_profile_locked: "external"` on every minted link |
| Public viewer never leaks | `leaks_telemetry / consumer_dispatch / readiness = False` across ALL 4 scenarios |
| Pre-deploy probes still green | Continuity probe + Bilingual probe = ✅ |

## Reality observations · captured then audited

### 1 · Airport · Taxiway Closure (FAA / escorts / FOD / paving)

Foreman entry exercised:
- 4 manpower rows (foreman, paver op, roller op, ground)
- 2 equipment rows with utilization splits
- 1 production segment (paving · 412.5 tons · stations 12+50→18+00)
- 1 delay (FAA escort released runway 25 minutes late · 1.25h)
- 1 constraint (escort window 0300–0800 only)
- Tomorrow plan with required-resources list

What surfaced:
- ✅ Airfield-specific Required topics (escort-requirements,
  fod-control, faa-restrictions, operational-window-adherence) all
  resolve via `crew-readiness/airfield`.
- ⚠️ FOD-walk start/end times have nowhere structured to live —
  currently they go in production segment notes. Documented in
  Reality Gap Audit (G2).
- ⚠️ NOTAM activation/deactivation timestamps similarly informal.

### 2 · Drainage · Utility Conflict (locate delay · safety near-miss)

Foreman entry exercised:
- 3 manpower rows
- 1 production segment with detailed RCP run (size, material, LF,
  from/to structure, backfill, compaction)
- 1 delay (utility · ATT fiber locate variance · 2.0h)
- 1 constraint (utility · field-flagged for design RFI)
- Safety **near-miss** event with `notified_safety=true` and
  `incident_report_complete=true` — submitted clean

What surfaced:
- ✅ Pipe production sub-shape (`PipeRun`) carries from-structure,
  to-structure, backfill, compaction — full evidence chain.
- ✅ Safety hard-stop math is right (`any_event=true` requires every
  event to carry both `notified_safety` AND `incident_report_complete`).
- ⚠️ Locate variance distance ("8 ft south of called location")
  sits in description text — there is no numeric field for "locate
  variance feet". Reality Gap Audit (G3).

### 3 · Asphalt · Plant Issue + MOT (trucking · density · channelizer)

Foreman entry exercised:
- 3 manpower rows + maintenance issue on paver augers
- 2 material events (delivered 540t · rejected 22t with reason)
- 1 production segment (FC-9.5 surface · 518 tons · 3 density cores)
- 2 delays (material 1.0h · MOT 0.5h)

What surfaced:
- ✅ Material `kind=rejected` + `issue=reject` cleanly captures
  vendor-side waste.
- ✅ Equipment `maintenance_issue` block populated with severity.
- ⚠️ Density core test results ("pulled at sta 312+85, 313+25, 313+60")
  are descriptive rather than structured — no `TestRecord` array on
  the paving production sub-shape (only on `PipeRun.testing[]`).
  Reality Gap Audit (G4).

### 4 · Concrete · Structures + Amendment

Foreman entry exercised:
- 3 manpower rows (foreman, finisher, pump op)
- 1 production segment (Class IV deck panel pour · 92 cy)
- Weather impact toggle **TRUE** with hours_lost + description
- Tomorrow plan + concerns
- ✅ Submit + 1 amendment recorded inside the 24-h window:
  - `field_path`: `production_segments[0].body.concrete.notes`
  - `reason`: "QC log review · cylinder source truck mis-recorded"
  - `amendment_count` incremented · `amend_allowed_until_utc` preserved

What surfaced:
- ✅ Amendment audit-trail integrity intact (`old_value_sha256` ≠
  `new_value_sha256` on the row).
- ✅ Weather impact block calmly carries non-blocking impact data.
- ⚠️ Cylinder cast schedule (truck-numbers + 7-day/28-day/56-day
  set) is free-text — no structured cylinder log. Reality Gap
  Audit (G5).

## Validation question answers (per directive)

### Foreman · Could this be completed from a truck/phone, under time pressure, in poor signal?

Backend round-trip per scenario: ~5 seconds for the full create-to-
submit sequence. UI step-through tested at phone breakpoint
(`max-w-md`, 44pt tap targets) in M0.3.

| Question | Reality | Verdict |
|---|---|---|
| From a truck? | Yes — single-column phone layout, thumb-friendly | ✅ |
| From a phone? | Yes — tested at 414×800 viewport | ✅ |
| Under time pressure? | 5s end-to-end backend + ~30-90s UI typing per section | ✅ |
| In poor signal? | Best-effort PATCH; coaching falls back to base bullets if `/api/odr/guidance/resolve` errors out (silently caught) — **but no offline queue yet** (see Offline Queue Readiness Assessment) | 🟡 partial |

### Superintendent · Does the ODR actually tell what / why / what blocked?

Reading scenarios 1–4 fresh:

- **Airport scenario** — story reads: paving 412.5t E to W, lost 1.25h to ATC release lag, escort window narrow, plant 3 had no issue. ✅ Clear what / why / blocker.
- **Drainage scenario** — story reads: 87 LF of 36" RCP installed, ATT fiber blocked locate, field RFI flagged, near-miss reported clean. ✅ Clear.
- **Asphalt scenario** — story reads: 518 tons placed, plant 3 burner trip cost 1h, channelizer hit cost 0.5h, augers chattering on paver. ✅ Clear.
- **Concrete scenario** — story reads: 92 cy Class IV placed, brief shower, cylinders cast, QC correction issued. ✅ Clear.

### PM · Can project health / risk be understood quickly?

The PM panel (`/pm/odr`) summarized 4 submitted ODRs with:
- Open Delays = 3 (scenarios 1, 2, 3)
- Hours Lost = 4.75
- Safety Events = 1 (scenario 2 near-miss)
- Extra Work = 0

Reading time: ~10 seconds. ✅ Within the directive target.

### Public Viewer · Would DOT / FAA / CEI / Owner accept the resulting PDF package?

External PDFs rendered for all 4 scenarios at sizes 2.7–3.1 KB.
Public envelope endpoint returned ZERO leaks of internal fields:

```
leaks_telemetry: False   (4/4 scenarios)
leaks_consumer_dispatch: False   (4/4 scenarios)
leaks_readiness: False   (4/4 scenarios)
```

Doctrine: ✅ acceptable.

## Performance characteristics observed

| Metric | Observed |
|---|---|
| Backend create-to-submit per ODR | 5.0–5.5 seconds (8 patches + submit) |
| PDF render per audience | 80–200 ms |
| Public link mint | 30–80 ms |
| Public resolve | 50–120 ms |
| Amendment write | 50–100 ms |

These are preview-environment numbers including the HTTPS edge.
No performance regression vs. M0.3.

## Reliability characteristics observed

- 0 unhandled exceptions across the 4 scenarios.
- 0 schema violations on any submit.
- 0 readiness false-blocks (every scenario submitted with
  readiness=ready).
- 0 audit-log gaps (every PDF render audited; every public link
  audience-locked).

## Verdict

🟢 **REALITY VALIDATION PASS.** ODR holds under realistic
multi-discipline workloads. Surface gaps captured in
`ODR_REALITY_GAP_AUDIT.md`. Performance acceptable. No new
architecture required.

_End of ODR_REALITY_VALIDATION_REPORT.md._
