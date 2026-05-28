# Operational Timeline — Stability Report

**Phase V-Prelude · Wave 1.1A**
**Date:** 2026-05-28
**Observation window:** OPEN (24 hr from Wave 1.1 + extended through
Wave 1.1A).

---

## Stability picture (end of Wave 1.1A)

### Backend substrate (Wave 1)
- `/api/timeline` — 200 OK · sort-newest-first contract · TRUST-TIME-1
  Z-suffixed `at` on every row · ≤ 200 items per call · project-scope
  strict.
- `/api/operational-links` — full §1–§11 doctrine enforced; the static
  + Mongo sweep probe scans 0 violations · 0 rows currently in
  preview Mongo.
- `/api/constraints` — full CRUD + chronology + resolve · 19/19
  regression green.
- Mongo footprint: tiny. `operational_constraints` collection has the
  test-cleanup baseline (0 production rows). `operational_links`
  collection unchanged.

### Frontend surface (Wave 1.1)
- `/pm/projects/:projectNumber` — calm shell + sidecar.
- `OperationalTimelineSidecar.jsx` — passive · bounded
  (max-h-420 px · 30-row floor) · role-aware · mobile-safe.
- 10/10 Playwright tests pass across desktop / iPad / mobile.

### Governance intelligence (Wave 1.1A)
- `timeline_calmness_probe.py` — score **0.0** · 0 gate breaches ·
  baseline persisted to `TIMELINE_LOUDNESS_TRENDLINE.json`.
- `pre_deploy_check.sh` — new warning-first stage wired.
- 7/7 telemetry + density regression tests pass.

---

## Per-dimension reading (baseline)

```
accent_class_ratio       0.0000  (target ≤ 0.1800)  · slate-only palette
badge_density_per_1k_px2 0.0000  (target ≤ 1e-4)    · zero filled badges
red_usage                0       (target ≤ 2)        · zero red hits
hierarchy_compression    4       (target ≤ 5)        · 1 H2 + body type
vertical_density         0       (target ≤ 12 rows)  · empty state
chronology_dup_ratio     0.00    (target ≤ 0.20)     · no dup signatures
```

Every dimension is at ZERO except `hierarchy_compression`, which is
4 of 5 allowed (one count under target). This is the cleanest opening
baseline the trendline will ever have. Drift FROM this point is
exactly what the probe will catch.

---

## What "stable" means right now

| Stability axis | State |
|---|---|
| API contract | 🟢 stable · 27/27 substrate + sidecar tests green |
| Visual chrome | 🟢 calm · 10/10 Playwright tests green |
| Calmness telemetry | 🟢 baseline 0.0 · 0 breaches |
| Doctrine probes | 🟢 4/4 green (authority · timestamp · links · calmness) |
| Mongo health | 🟢 tiny · zero index pressure |
| Role visibility | 🟢 audit-only links blocked for non-admin (PM probe green) |
| Mobile rendering | 🟢 single-column at 390 px · zero body overflow |
| Mutation surface | 🟢 ZERO · sidecar remains passive |
| Notification fan-out | 🟢 zero (Wave 1.1 + 1.1A rule #9 honoured) |
| Reversibility | 🟢 every change is a file delete / line revert away |

---

## Freeze triggers (active)

The observation window remains armed. ANY of the following blocks
Wave 2 authorization:

1. `operational_links` doctrine probe reports a new violation.
2. Calmness score rises above 1.0 across two consecutive trendline
   entries.
3. `gate_breaches` becomes non-empty on any deploy.
4. Audit-only link surfaces in any non-admin actor's timeline.
5. Mongo `_id` leaks into any response.
6. Notification fan-out triggered by a link write.
7. Mobile body overflow at iPhone 13 (Playwright sweep catches).
8. Red / loud-badge accent introduced in the sidecar chrome.

Each trigger has a corresponding pytest + probe. **Do not advance to
Wave 2 with any open freeze trigger.**

---

## Wave 2 readiness gate (re-stated)

Wave 2 (Operational Search + Field Memory) is LOCKED until ALL of the
following hold:
- [x] Wave 1.1A passive telemetry shipped + green.
- [x] No new doctrine probe violations.
- [x] Sidecar Playwright sweep stays green.
- [ ] No freeze trigger fired during the observation window.
- [ ] Operator explicitly issues "start V-Prelude Wave 2".

---

## Next observation cadence

| Cadence | Action |
|---|---|
| Every deploy | `pre_deploy_check.sh` runs all 5 governance probes including the new calmness telemetry stage. |
| Daily during window | Manual heartbeat curl + Mongo health snapshot (see `WAVE1_OBSERVATION_GUIDE.md`). |
| Weekly post-window | Run `timeline_calmness_probe.py --iteration weekly-check` to add a routine trendline entry. |
| On any 🚨 | Stop. Triage. Document in this file before resuming. |

---

— issued by E1 · V-Prelude Wave 1.1A · 2026-05-28
