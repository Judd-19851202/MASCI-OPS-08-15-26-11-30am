# Phase 1C — Multi-Viewport Pre-Deploy Validation Gate

_Status: 📐 **APPROVED BACKLOG · P1 Platform Quality Infrastructure** ·
Authored 2026-02-01 ·
Implement **after** Production Validation + Backup Scheduler Hardening._

> **Mandate**: "Recent production defects passed preview certification
> but were still discovered by operators after deployment. To prevent
> future regressions, all production deployments must pass a
> standardized viewport validation gate before deployment approval."

This document is the **binding spec** for the next agent who picks up
implementation. Do not modify scope without operator sign-off.

---

## 1 · Why

Convert responsive validation from a **manual activity** into a
**permanent deployment gate**. Pre-Phase-1C, Phase V.5 caught the
form-bleed / PM-routing / Shop-pre-op / PO-attachment / delay-enum
defects only because the operator hand-flagged them. Phase 1C makes
that catch automatic for every future redeploy.

### Expected outcome
- Fewer production regressions
- Faster operator confidence
- Repeatable quality checks
- Consistent device experience
- Reduced trust-damaging defects

---

## 2 · What

A new phase (`Phase 1C`) appended to `scripts/pre_deploy_check.sh`
(after the existing Phase 1B reliability gate from V.4). Run a
Playwright-driven multi-viewport sweep over the canonical portals and
emit a binding **viewport validation report**.

### 2a · Viewport classes (10)

| Class | Width × Height | Emulation |
|---|---|---|
| Phone Portrait | 390 × 844 | iPhone 12 / Safari mobile |
| Phone Landscape | 844 × 390 | iPhone 12 / Safari mobile |
| Tablet Portrait | 768 × 1024 | iPad Mini · Safari mobile |
| Tablet Landscape | 1024 × 768 | iPad Mini · Safari mobile |
| iPad Portrait | 820 × 1180 | iPad Air · Safari mobile |
| iPad Landscape | 1180 × 820 | iPad Air · Safari mobile |
| Laptop | 1366 × 768 | Desktop Chromium |
| Desktop | 1440 × 900 | Desktop Chromium |
| Large Desktop | 1920 × 1080 | Desktop Chromium |
| Ultra-Wide | 2560 × 1080 | Desktop Chromium |

### 2b · Core validation targets (11)

Each target must be exercised at every viewport class above.

1. **Daily Reports** — `/daily/new` and `/daily/:id` (existing record).
   FormGrid presence, Project Name/# pair gap ≥ 16 px on ≥ 768 wide,
   Delay enum chips human labels, no center-seam collision.
2. **PM Portal** — `/pm/equipment`, `/pm/equipment/:id` (valid and
   invalid ID). No bounce to `/pm/login` on 404, zero admin widgets,
   zero per-row write buttons.
3. **Shop Portal** — `/shop`, `/shop/equipment`. Pre-Op list loads,
   fail badge visible.
4. **HR Portal** — `/hr`, `/hr/time-verification`,
   `/hr/daily-reports`, `/hr/payroll-variance`. Filter bar
   canonical `gap-x-4` contract.
5. **Safety Portal** — `/safety-portal`, `/safety-portal/forms`.
   Stats strips canonical gap contract.
6. **QA/QC** — `/qaqc/new`, `/qaqc/list`. Form grid canonical
   contract.
7. **PO Requests** — `/po-requests` list, PO drawer open, **attempt
   to open a receipt** (synthetic test PO with `data:` URL inserted
   + cleaned up — see §5).
8. **Attachments** — every surface that streams a file
   (PO receipts, JHA PDFs, Training certs, DR PDFs). Endpoint
   `GET …/receipt|/pdf` returns `application/*` with `inline`
   Content-Disposition.
9. **Routing** — token namespace boundaries: PM token wiped only by
   PM 401, Shop token wiped only by Shop 401, etc.
10. **Responsive layouts** — every `FormGrid` / `gap-x-*` canonical
    class survives every viewport. No element overflow, no
    center-seam < 16 px.
11. **Critical workflows** — DR submit gate (Weather YES requires
    Weather constraint row), PM Pre-Op view, Shop Pre-Op fail badge,
    PO Approve/Reject buttons present, HR Time Verification filter
    cluster.

### 2c · Required outputs (5)

Every Phase 1C run must emit:

1. **Screenshot inventory** — one PNG per (viewport × target). File
   naming: `<target>_<viewport>.png`. Stored under
   `/app/test_reports/predeploy_phase_1c/<run_id>/`.
2. **Pass/Fail matrix** — JSON keyed by `(target, viewport) → status`.
   Includes per-cell metrics (gap measurements, admin widget counts,
   bounce booleans).
3. **Route verification** — for every navigated path, record the
   `page.url` after settle. Bounce to wrong-portal login = FAIL.
4. **Attachment verification** — per attachment endpoint:
   `{http, content_type, content_disposition, first_bytes}` log.
5. **Responsive verification** — per FormGrid / filter-bar surface:
   measured horizontal gap between paired inputs at each viewport.

---

## 3 · Deployment policy (binding)

> **No production deployment may be recommended `SAFE TO DEPLOY`
> without a completed viewport validation report from this gate.**

`pre_deploy_check.sh` must:
- Run Phase 1C **after** Phase 1B reliability suite (i.e., once Wave-2
  field-reliability has passed).
- Fail the entire pre-deploy check if any Phase 1C cell is FAIL.
- Treat WARN cells as informational only (do not block deploy).
- Print the path to the run's report directory so the operator can
  inspect screenshots before approving.

The Emergent deploy dashboard cannot enforce this directly, so the
gate produces a `PHASE_1C_VIEWPORT_VALIDATION_REPORT.md` file with a
top-line **🟢 SAFE TO REDEPLOY** or **🔴 HOLD REDEPLOY** verdict that
the operator references before clicking redeploy.

---

## 4 · Implementation plan

### 4a · New files

| Path | Purpose |
|---|---|
| `backend/tests/pw_suite/test_phase_1c_viewport_gate.py` | Parametrized pytest suite — 10 viewports × 11 targets · emits screenshots + JSON receipts |
| `scripts/phase_1c_viewport_validation.py` | Orchestrator wrapping the pytest run · writes `PHASE_1C_VIEWPORT_VALIDATION_REPORT.md` with verdict |
| `backend/tests/pw_suite/conftest_phase_1c.py` | Adds 10-viewport `viewport_class` fixture (parametrized) extending existing 3-viewport fixture |

### 4b · Modifications

| Path | Change |
|---|---|
| `scripts/pre_deploy_check.sh` | Add Phase 1C step after Phase 1B; FAIL surfaces if any cell is FAIL |
| `memory/_INDEX.md` | Add this spec doc + report doc + script paths to Section 1 |
| `memory/PRD.md` | Reference Phase 1C closure when implemented |

### 4c · Reuse — Phase V.5 validation harness

The Phase V.5 pre-deploy validation matrix (the work shipped
2026-02-01) is the **prototype** for Phase 1C. Reuse:
- `/tmp/gate/predeploy/run_validation.py` — 5-viewport · 6-defect
  proof of pattern.
- `/tmp/gate/predeploy/check_delay_enum.py` — CollapseCard expansion
  + chip / select assertion pattern.
- Multi-login fan-out via `POST /api/auth/multi-login`.
- PM / Shop token minting via portal `/login` endpoints.

Promote both scripts into `/app/backend/tests/pw_suite/` with
parametrized viewport fixtures.

### 4d · Test-PO cleanup contract

Phase 1C inserts a synthetic PO with a `data:application/pdf` receipt
URL to exercise the streaming endpoint, then **must** delete it in a
`finally` block. Preview DB must return to baseline. Suggested ID
pattern: `PHASE_1C_<run_id>_RECEIPT`.

### 4e · Estimated effort

- Suite scaffolding: ~2 hours
- 11 target probes × parametrized viewport: ~3 hours
- Orchestrator + report writer: ~1 hour
- `pre_deploy_check.sh` wiring + dry run: ~30 min
- Operator review + first authoritative run: ~30 min

**Total: ~7 dev-hours · 1 working day.**

---

## 5 · Stop conditions (binding)

- ❌ Do NOT begin implementation until Production Validation of the
  current Phase V.5 fixes lands clean (operator verifies live on
  `mascidocs.com`).
- ❌ Do NOT begin implementation until Backup Scheduler Hardening
  (P0 GAP-7) is complete.
- ❌ Phase 1C must be **read-only** against production. Preview-only
  DB safety gate from existing conftest must be inherited.
- ❌ Do NOT touch the 1B reliability suite or any V.4 governance
  artifact.

---

## 6 · Acceptance criteria

Phase 1C ships when:

1. `bash scripts/pre_deploy_check.sh` completes including Phase 1C.
2. A run of Phase 1C against preview emits all 5 required outputs.
3. The orchestrator produces a `PHASE_1C_VIEWPORT_VALIDATION_REPORT.md`
   with a top-line verdict the operator can read in < 30 seconds.
4. A deliberate regression (e.g., re-introducing
   `grid grid-cols-1 sm:grid-cols-2 gap-3` on a known surface)
   triggers a FAIL cell + blocks `pre_deploy_check.sh`.
5. The full 10-viewport × 11-target sweep completes in < 5 minutes
   wall-clock on the preview pod.

---

_End of PHASE_1C_VIEWPORT_VALIDATION_GATE_SPEC.md._
