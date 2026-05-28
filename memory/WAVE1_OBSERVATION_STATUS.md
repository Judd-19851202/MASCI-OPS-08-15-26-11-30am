# Wave 1 — Observation Status

**Phase V-Prelude · Wave 1 Observation Window**
**Status:** 🟡 **WINDOW OPEN · observation posture active**
**Date opened:** 2026-05-28
**Posture:** discipline-first · no feature work · no Wave 2.

---

## Window context

This is the formal observation window that follows the four
implementation passes:

| Pass | Scope | Status |
|---|---|---|
| Wave 1 | Operational substrate (constraints · links · timeline · photo gov.) | 🟢 complete |
| Wave 1.1 | Timeline sidecar on PM Project Detail | 🟢 complete |
| Wave 1.1A | Passive calmness telemetry · institutional memory begins | 🟢 complete |
| Wave 1.1B | Governance memory self-protection · 18 freeze triggers | 🟢 complete |

The window exists to:
- Validate operational trust under real usage.
- Observe chronology usefulness.
- Confirm calmness preservation.
- Catch slow-burn drift before it compounds.
- Earn the right to advance to Wave 2 by NOT advancing prematurely.

---

## Entry-of-window stability sweep (2026-05-28)

### Doctrine probes — all 5 green

```
authority_mismatch_probe         · 0 new violations · 89 ms
timestamp_doctrine_probe         · 0 new violations · 119 ms
operational_links_doctrine_probe · 0 violations     · 714 ms · 0 rows
trendline_integrity_probe        · 0 violations     · <100 ms · 2 trendlines
timeline_calmness_probe          · score 0.0        · 0 breaches · 3 viewports
```

### Regression suite — 50/50 green

```
test_v_prelude_wave1_substrate.py        · 19 passed
test_v_prelude_wave1_1_sidecar.py        ·  8 passed
test_timeline_calmness_probe.py          ·  3 passed
test_chronology_density_heuristics.py    ·  4 passed
test_trendline_integrity_probe.py        · 16 passed
                                          ─────────
                                            50 passed
```

### Mongo footprint (substrate)

```
constraints_total:     0
constraints_open:      0
constraints_resolved:  0
links_total:           0
links_active:          0
links_archived:        0
links_voided:          0
links_superseded:      0
links_audit_only:      0
```

The substrate has been swept to zero before observation begins. Two
smoke-test artifacts (`project_id="TEST"`, `title="x"`) from the
initial Wave 1 curl probes were removed under the observation
discipline — see `Cleanup Receipts` section below.

### Trendline state

```
TIMELINE_LOUDNESS_TRENDLINE: live=4 entries · snapshot=3 entries
                              · newest 2026-05-28T19:28:22Z
                              · append-only behavior verified
LOUDNESS_TRENDLINE:          live=1 entry · snapshot=1 entry
                              · newest 2026-05-27T19:13:55Z
                              · TRUST-TIME-1 conformant
```

### Operator-facing UI surface

```
PM Project Detail (/pm/projects/:projectNumber)  · 🟢 live
  └─ OperationalTimelineSidecar                  · 🟢 live (read-only)
Constraints page (/constraints)                   · 🟢 live
New constraint (/constraints/new)                 · 🟢 live
Constraint detail (/constraints/:id)              · 🟢 live
```

---

## 18 freeze triggers — current state

All 18 freeze triggers documented in
`OBSERVATION_FREEZE_HARDENING_REPORT.md` are **INACTIVE** as of
window open:

### Substrate triggers
| # | Trigger | State |
|---|---|---|
| 1 | `operational_links` doctrine violation | 🟢 inactive (probe green) |
| 2 | Mongo `_id` leak in API | 🟢 inactive (Pydantic models) |
| 3 | Audit-only link surfaces to non-admin | 🟢 inactive (PM-probe green) |
| 4 | Hard DELETE endpoint on links | 🟢 inactive (never existed) |
| 5 | Notification fan-out on link write | 🟢 inactive (no fan-out paths) |

### Sidecar triggers
| # | Trigger | State |
|---|---|---|
| 6 | Sidecar Playwright sweep regresses | 🟢 inactive (10/10 green) |
| 7 | Mobile body horizontal overflow | 🟢 inactive (PW asserts ≤390 + 4 px) |
| 8 | Loud-badge accent in sidecar chrome | 🟢 inactive (DOM sweep clean) |

### Telemetry triggers
| # | Trigger | State |
|---|---|---|
| 9 | Calmness score above 1.0 (2 consecutive) | 🟢 inactive (last 2 scores = 0.0) |
| 10 | `gate_breaches` non-empty | 🟢 inactive |
| 11 | Chronology dup-ratio > 0.20 sustained | 🟢 inactive |

### Memory triggers (Wave 1.1B)
| # | Trigger | State |
|---|---|---|
| 12 | Trendline shape regression | 🟢 inactive (both list-shaped) |
| 13 | Silent overwrite | 🟢 inactive (snapshot count matches) |
| 14 | Historical mutation | 🟢 inactive (checksums match) |
| 15 | Non-Z timestamp | 🟢 inactive (regex passes) |
| 16 | Chronology-order violation | 🟢 inactive (monotonic) |
| 17 | Duplicate (iteration, timestamp) | 🟢 inactive |
| 18 | Snapshot tampering | 🟢 inactive (both readable) |

**0/18 fired.** Window remains open.

---

## Cleanup receipts (observation hygiene)

| Artifact | Action | Justification |
|---|---|---|
| 2× constraints `project_id="TEST"` title="x" | DELETE_MANY | smoke-test residue from initial Wave 1 build curls; never owned by a test fixture |

No operational data was touched. Both rows were structurally
identical placeholder probes with no chronology, no links, no
photos. Receipt timestamp: 2026-05-28.

---

## Observation cadence

| Cadence | Action |
|---|---|
| Every deploy | All 8 governance probe stages run via `pre_deploy_check.sh`. |
| Daily during window | Manual heartbeat — see `WAVE1_OBSERVATION_GUIDE.md`. |
| Weekly | Routine `timeline_calmness_probe.py --iteration weekly-check` baseline. |
| On any trigger | STOP. Triage. Document. |

---

## Wave 2 readiness gate (current)

```
[x] Wave 1 substrate live
[x] Wave 1.1 sidecar live
[x] Wave 1.1A telemetry live + baselined
[x] Wave 1.1B memory self-protection live + sealed
[x] All 5 doctrine probes green
[x] 50/50 regression suite green
[ ] No freeze trigger fires during the observation window
[ ] Operator explicitly issues "start V-Prelude Wave 2"
```

Two checkboxes remain. Both belong to the operator + the calendar,
not to the agent.

---

— issued by E1 · V-Prelude Wave 1 observation posture · 2026-05-28
