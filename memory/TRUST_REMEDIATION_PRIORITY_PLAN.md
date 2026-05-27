# Trust Remediation Priority Plan
## Phase TRUST-1 · 2026-05-27

> The sequenced surgical-remediation plan. Three small waves, each
> independently shippable, each closing a clear sub-set of findings.
> Phase V (RFI / Schedule / Constraints) is gated on Wave 1 + 2
> landing.

---

## 1 · Wave 1 — "Make invisible failures visible" (4 findings, ~3 hours)

Goal: close the visibility gaps so future field reports are
diagnosable in <1 minute.

| # | Finding | Sev | Effort | Files touched |
|---|---|---|---|---|
| 1.1 | TF-015 — `_id` leak contract test | T2 | 30 min | 1 new test file |
| 1.2 | TF-018 — pre-deploy gate pings `/api/draft-telemetry/health` | T2 | 15 min | `scripts/pre_deploy_check.sh` |
| 1.3 | TF-012 — Draft Health tile "Quiet" verdict for low-volume windows | T2 | 45 min | `DraftHealthTile.jsx` |
| 1.4 | TF-022 — Operator-visible "Show Device ID" affordance | T1 | 1 h | `NewDailyReport.jsx` + tiny popover |

Verification: 1 new test file + 1 backend health-route assertion in
the deploy gate + visual smoke pass on `/admin/governance`.

Doctrine: no schema · no auth · no routing · no shell changes.

---

## 2 · Wave 2 — "Close survivability gaps" (5 findings, ~4 hours)

Goal: harden the data-loss vectors that remain open.

| # | Finding | Sev | Effort | Files touched |
|---|---|---|---|---|
| 2.1 | TF-002 — Sibling forms persist idempotency key | T3 | 1 h | 4 form pages × 8 lines each |
| 2.2 | TF-004 — Quota probe surfaces operator warning at ≥80% | T3 | 1 h | `useFormDraft.js` + `DraftStatusPill.jsx` |
| 2.3 | TF-011 — Submit-time commit() defers discard until 2xx confirmed | T3 | 1 h | `NewDailyReport.jsx` + `draftStore.js` |
| 2.4 | TF-009 — iPad viewport added to draft-loss regression | T2 | 15 min | `test_draft_loss_remediation.py` |
| 2.5 | TF-016 — Recovery affordance for soft-deleted drafts | T2 | 45 min | `NewDailyReport.jsx` + small recovery banner |

Verification: 5 new tests covering each change. Re-run the 35-test
P0+P1 bundle to confirm no regression.

**Phase V gate:** after Wave 2 lands, the four phase-V-blocker
findings (TF-001 plus the three T3s above) are closed except for
TF-001 which is partially mitigated by the visibility work in
Wave 1 (admin can see ITP-empty patterns even without an operator
banner).

---

## 3 · Wave 3 — "Extend doctrine to siblings" (4 findings, ~3 hours)

Goal: apply the iter443 return-path doctrine and iter442 device-
memory doctrine to surfaces beyond the Daily Report.

| # | Finding | Sev | Effort | Files touched |
|---|---|---|---|---|
| 3.1 | TF-003 — ViewCAPA migrates to `useReturnContext()` | T2 | 30 min | `ViewCAPA.jsx` |
| 3.2 | TF-003 — ViewInspection migrates (if exists) | T2 | 30 min | `ViewInspection.jsx` |
| 3.3 | TF-003 — ViewMeeting migrates (if exists) | T2 | 30 min | `ViewMeeting.jsx` |
| 3.4 | TF-017 — PM Project Dashboard incident chip passes state.from | T2 | 30 min | PM Project Dashboard incident chip |

Verification: 4 small Playwright tests cloning the iter443 pattern.

---

## 4 · Backlog (Phase TRUST-2 candidates)

| ID | Sev | Note |
|---|---|---|
| TF-001 | T4 | ITP-purged IDB banner — requires soft prior-usage cookie · paired with operator-facing UI design |
| TF-005 | T2 | Draft Health tile per-device drill-down · requires interaction design |
| TF-006 | T2 | Device-memory telemetry events · enables adoption metrics |
| TF-019 | T1 | Anonymous-only filter on tile |
| TF-020 | T1 | Last-fail-trigger chip on tile |
| TF-021 | T2 | Operator trust-fail playbook (one-page PDF) |
| TF-008 | T2 | RedirectWithId preserves state |
| TF-007 | T1 | Spanish localization of iter442 coaching |
| TF-014 | T1 | Severity badge visual sweep |
| TF-023 | T0 | PRD.md split into PRD/CHANGELOG/ROADMAP |
| TF-010 | T3 | Cross-portal session friction (documented; UX work) |
| TF-013 | T2 | Operator-cleared storage (deferred · user choice) |

---

## 5 · Effort summary

| Wave | Findings | Total effort |
|---|---|---|
| Wave 1 (visibility) | 4 | ~3 hours |
| Wave 2 (survivability) | 5 | ~4 hours |
| Wave 3 (doctrine extension) | 4 | ~3 hours |
| Backlog | 12 | TBD |

Three waves ≈ one full implementation day. Each wave can be
shipped independently with its own regression test set.

---

## 6 · Phase V gate (binding)

Phase V (RFI / Constraints / Schedule / P6 / Operational Records)
MUST NOT begin until:

- ✅ Wave 1 lands (visibility hardened)
- ✅ Wave 2 lands (survivability closed for sibling forms)
- ✅ All T4 findings (TF-001) have at least a documented operator-facing
      response path (banner OR playbook)
- ✅ All T3 findings closed in code or downgraded with rationale

Wave 3 is recommended but not gating.

---

## 7 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 Plan ready · awaiting user direction to start Wave 1
- **Doctrine:** surgical · reversible · no big-bang · highest-risk first
- **Cross-refs:** `OPERATIONAL_TRUST_AUDIT_MASTER.md`, `TRUST_FINDINGS_MATRIX.json`, `TRUST_GOVERNANCE_STANDARD.md`, `TRUST_REGRESSION_GAP_ANALYSIS.md`
