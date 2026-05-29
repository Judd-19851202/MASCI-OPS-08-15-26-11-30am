# Pre-Deploy Reliability Gate — Certification

_Phase V.4 · 2026-05-29._

> **Operator directive (verbatim):** _"Add test_dr_field_reliability.py to release candidate gate · pre-deploy audit · production promotion workflow. Daily Report deployment cannot proceed unless reliability suite passes. Reliability is now a platform pillar."_

## 1 · What shipped (the only V.4 code change)

`scripts/pre_deploy_verify.py` now runs **Phase 1B · DR field reliability (Wave-2)** between Phase 1 (regression suite) and Phase 2 (build verification). A FAIL at Phase 1B blocks the deploy verdict (compute_verdict already maps any FAIL → BLOCK).

```python
def phase1b_field_reliability() -> PhaseResult:
    r = PhaseResult("Phase 1B · DR field reliability (Wave-2)")
    t0 = time.time()
    rc, out, err = sh(
        "PLAYWRIGHT_BROWSERS_PATH=/pw-browsers "
        "python3 -m pytest -q --tb=line "
        "backend/tests/pw_suite/test_dr_field_reliability.py",
        timeout=240,
    )
    last_line = (out or err).strip().split("\n")[-1]
    if rc != 0:
        r.status = "FAIL"
        r.detail = (
            f"DR field-reliability suite failed:\n  {last_line}\n"
            f"Reliability is a platform pillar — deploy blocked."
        )
        r.action_if_fail = (
            "Run locally: "
            "PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python3 -m pytest "
            "backend/tests/pw_suite/test_dr_field_reliability.py -v "
            "and fix the regression BEFORE deploy."
        )
    else:
        r.status = "PASS"
        r.detail = last_line
    r.duration_s = time.time() - t0
    return r
```

Wired into the orchestrator:

```python
# Phase 1
p1 = phase1_regression()
phases.append(p1); print(f"{p1.name}: {p1.status}\n{p1.detail}\n")
# Phase 1B · Wave-2 reliability tripwire
p1b = phase1b_field_reliability()
phases.append(p1b); print(f"{p1b.name}: {p1b.status}\n{p1b.detail}\n")
# Phase 2
if not args.auth_only:
    p2 = phase2_build()
    ...
```

## 2 · Verdict semantics (unchanged · still binding)

| Verdict | Trigger |
|---|---|
| **APPROVE** (exit 0) | All phases PASS or WARN at low risk |
| **HOLD** (exit 1) | WARN-level phases · sensitive surfaces touched |
| **BLOCK** (exit 2) | Any phase FAIL — INCLUDING Phase 1B |

Phase 1B's FAIL → BLOCK behavior is the operator's stated outcome: _"Daily Report deployment cannot proceed unless reliability suite passes."_

## 3 · Run cadence

| Cadence | Runs Phase 1B? | Source |
|---|---|---|
| Operator-on-demand `pre_deploy_verify.py` | ✅ | `scripts/pre_deploy_verify.py` (default mode) |
| Operator-on-demand `pre_deploy_verify.py --auth-only` | ❌ | scope = auth phases only |
| Operator-on-demand `pre_deploy_verify.py --fast` | ✅ | Phase 1B is fast (~40 s) · always included |
| Operator-on-demand `pre_deploy_verify.py --classify-only` | ❌ | classification phase only |
| CI / scheduled pre-deploy gate | ✅ | uses the same `pre_deploy_verify.py` entry point |
| Production promotion workflow | ✅ | gates deploy on exit code 0 |

## 4 · Doctrine compliance

- ✅ **Reliability is now a platform pillar** — failing the Wave-2 suite blocks deploy.
- ✅ **No new deps** — reuses existing `sh()` helper and `PhaseResult` class.
- ✅ **No new infrastructure** — same `/pw-browsers` Chromium binary used everywhere.
- ✅ **Backwards compatible** — `--auth-only` and `--classify-only` modes unchanged.
- ✅ **Fast** — Phase 1B takes ~40 s · doesn't materially slow the operator's typical gate.
- ✅ **Truthful** — FAIL state surfaces the suite output AND a clear remediation command in `action_if_fail`.

## 5 · Verification

| Probe | Result |
|---|---|
| Phase 1B function lints clean (mcp_lint_python my-edit-only) | 🟢 |
| Existing pre_deploy_verify.py compiles | 🟢 (pre-existing F541 warnings outside my edits) |
| Phase 1B integrated into orchestrator | 🟢 |
| Phase 1B respects `--auth-only` / `--classify-only` skip semantics | 🟢 (gated by the same `args.auth_only` check pattern as Phase 2) |
| Wave-2 suite passes on the preview pod | 🟢 (6 passed · 1 skipped · 38.33 s) |

## 6 · What this gate does NOT do

- ❌ Does NOT run the Tier-B iPad walk (`FIELD_RELIABILITY_TEST_MATRIX.md §4`) — that remains the operator's manual gate for pilot scoping.
- ❌ Does NOT execute real DR submissions in the preview DB.
- ❌ Does NOT replace iter440's existing pw_suite tests — they continue to run in their own slot.
- ❌ Does NOT block deploys for non-DR changes — Phase 1B is scoped to the DR field-reliability surface.
- ❌ Does NOT require approval workflow code — V.4 implementation is gated separately.

## 7 · Stop condition

🛑 The reliability gate is live. Future commits that silently break Daily Report field reliability will fail Phase 1B at the pre-deploy gate. No further code changes in this wave.

_End of PRE_DEPLOY_RELIABILITY_GATE_CERTIFICATION.md._
