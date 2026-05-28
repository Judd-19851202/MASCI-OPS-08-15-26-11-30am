# Governance Self-Healing Roadmap

_Phase V-Prelude · Priority #9 · roadmap · 2026-05-28._

## Mission

The platform should increasingly protect itself. Each phase has
added one or more probes that automatically detect doctrine
drift. This roadmap lays out the next 5 probes V-Prelude should
add or extend, ordered by operator-trust value.

## Existing self-protection layer (recap)

| Probe | Phase | Status |
|---|---|---|
| Authority Mismatch Probe | GOVERNANCE-INFRA-1 | 🟢 gated · 58 baselined |
| Self-Protection page (OPS-1) | GOVERNANCE-OPS-1 | 🟢 9 stanzas |
| Trust Surfaces registry | TRUST-1 | 🟢 10 registered |
| Truthful-State matrix | TRUST-1 | 🟢 12 contracts |
| Context Governance matrix | STABILIZATION-FINAL | 🟢 5 governed · 0 TBD |
| Capability primitive parity | STABILIZATION-FINAL | 🟢 4 primitives |
| Field Walk checklists | GOVERNANCE-INFRA-1 | 🟢 5 active |
| Deployment Stanza | CUTOVER-READY | 🟢 history-tracked |
| Timestamp Doctrine Probe | TRUST-TIME-1B | 🟢 81 baselined |

## Proposed V-Prelude additions (5)

### P1 — Terminology Drift Probe (HIGH value · LOW risk)
**Catches:** copy that drifts away from the calm-doctrine
vocabulary (e.g., "AI", "Smart", "Predictive", "Optimize",
"Engagement", "Score" in operator-facing surfaces).
**Implementation:** `scripts/terminology_doctrine_probe.py`
mirrors timestamp probe. Scans `frontend/src/pages` +
`frontend/src/components` for a wordlist. Baseline accepts
legacy lines.
**Effort:** ≤ 200 LOC. Sub-second.

### P2 — Contamination Probe Automation (HIGH value · MEDIUM risk)
**Catches:** preview test fixtures or fake records leaking into
the production DB or vice-versa.
**Implementation:** `scripts/contamination_probe.py` runs a
read-only query against the configured DB for the 7 forbidden
patterns we currently spot-check manually (`Office Jane`,
`TST-`, `PE-`, `test@example`, `fake-`, `demo-`, `Lorem ipsum`).
Adds an OPS-1 stanza.
**Effort:** ≤ 250 LOC. Runs in 1-2 seconds against production.

### P3 — Hierarchy Validation Probe (MEDIUM value · LOW risk)
**Catches:** a project assigned to an employee whose role
doesn't include `pm` / `super`. A PO approved by an actor whose
capability doesn't include `po.approve`.
**Implementation:** `scripts/hierarchy_validation_probe.py`
walks the project / employee / PO collections looking for
authority inversions. Read-only.
**Effort:** ≤ 300 LOC. 2-3 seconds.

### P4 — Token-Scope Leak Probe (HIGH value · MEDIUM risk)
**Catches:** a PM token returning admin-only data due to an
accidental route mounting (the very class of regression
`test_portal_token_routing.py` already covers).
**Implementation:** runs the canonical 27-test PR token routing
sweep on every pre-deploy. Same idea as the Authority probe but
for tokens.
**Effort:** wrapper script · ≤ 100 LOC.

### P5 — OPS-1 Drift Sentinel (LOW value · LOW risk)
**Catches:** a future regression that re-introduces TBD-Wave3
items into the context-governance matrix.
**Implementation:** small CI snapshot comparison of
`SHARED_SURFACE_CONTEXT_MATRIX.json`. If `tbd > 0`, fail the
gate.
**Effort:** ≤ 50 LOC.

## Order of operations

1. **P1 Terminology Drift** — fastest win · zero infrastructure
2. **P5 OPS-1 Drift Sentinel** — almost free · catches V.1 RFI
   surface drift
3. **P4 Token-Scope Leak** — wraps existing tests · zero new logic
4. **P2 Contamination** — needs DB-access plumbing · highest value
5. **P3 Hierarchy Validation** — most complex · needs careful
   baseline

## Doctrine for ALL new probes

- Sub-second target. Hard cap at 3 seconds.
- `--gate` mode exits 1 on new failures.
- `--bless` mode regenerates baseline.
- `--json` mode for machine consumption.
- Allowlist file in `scripts/`.
- Wired into `scripts/pre_deploy_check.sh` as a new `stage_*`
  function.
- OPS-1 stanza shows status if the probe is sufficiently
  operator-relevant (P1 / P2 / P4 yes · P3 / P5 informational).
- Regression test in `tests/pw_suite/test_*_probe.py`.

## Phase-V handoff

V.1 RFI MVP is the FIRST major code drop after this roadmap
ships. Every new probe added in V-Prelude protects V.1.

## Stop condition

Roadmap only. Probes ship one-at-a-time, each independently
reversible. Operator chooses which to ship first.
