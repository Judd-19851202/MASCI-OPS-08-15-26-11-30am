# OMEGA_GAP_REGISTER

**Initiative:** OMEGA · MASCI Operational Perfection Program
**Date:** 2026-05-30 (UTC)
**Method:** Consolidation of `PLATFORM_GAP_LEDGER_FINAL.md` + 5 OMEGA pillar certifications + new findings from prod probes.
**Rule:** Every entry has Memory · Code · Runtime citation. Severity = blast radius × likelihood of harm.

---

## 1 · Master gap register (ranked)

| Rank | Gap ID | Description | Pillar | Risk | Op Impact | Recovery Impact | Effort | Priority | Status |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | **OMEGA-1** | Production photo migration NOT RUN — R2 at 80 GB · archive 464 MB · trajectory documented in Batch G | Recoverability + Platform Clarity | 🟡 Medium (OOM trajectory) | 🟡 Operationally invisible today | 🟡 Restore still works, just at legacy size | **30 min operator command** | **P0** | OPEN |
| 2 | **OMEGA-2** | Batch H write-path defense — likely not deployed to prod (DR-2026-00279 inline base64) | Recoverability | 🟡 New DRs may add bloat | 🟡 Operator-resolvable via fresh deploy | 🟢 unchanged | **15 min deploy** | **P0** | OPEN |
| 3 | **OMEGA-3** / G-P0-01 / ORPHAN-1 | Fleet DVIR — no notification fan-out (orphan workflow) | Ownership | 🔴 Operator never told about defects | 🔴 Real ops gap | 🟢 unchanged | **~30 LOC + 2 h** | **P0 (operator-decision)** | DECISION-READY |
| 4 | **OMEGA-4** | `/api/admin/version` (or equivalent) missing — operator cannot remotely verify which git SHA is deployed | Platform Clarity | 🟡 Hygiene | 🟡 Cannot independently verify deploys | 🟢 unchanged | **30 LOC + 1 h** | **P3 (hygiene)** | OPEN |
| 5 | **OMEGA-5** / G-P1-01 | Field Leadership 10 forms — email-only, no bell/task fan-out | Accountability | 🟡 Forms processed but not visible as queue | 🟡 Soft orphan | 🟢 | ~1 h | **P1** | OPEN |
| 6 | **OMEGA-6** / G-P1-02 | Safety Equipment (3 forms) — email-only, count-only stat | Accountability | 🟡 | 🟡 | 🟢 | ~1 h | **P1** | OPEN |
| 7 | **OMEGA-7** / G-P1-03 | JHA submit — email-only, no task to Safety supervisor | Accountability + Ownership | 🟡 | 🟡 | 🟢 | ~0.5 h | **P1** | OPEN |
| 8 | **OMEGA-8** / G-P1-04 / NEW-GAP-A | Safety Meeting submit — email-only | Accountability + Ownership | 🟡 | 🟡 | 🟢 | ~0.5 h | **P1** | OPEN |
| 9 | **OMEGA-9** / G-P1-05 | Training Record assigned — supervisor of trainee not always notified | Accountability | 🟡 | 🟡 | 🟢 | ~2 h | **P1** | OPEN |
| 10 | **OMEGA-10** / G-P2-04 | Severe Incident — no no-response cadence (single-tier only) | Accountability | 🟡 First-response fires, second tier manual | 🟡 If Safety unavailable, no fallback | 🟢 | ~4 h (framework) | **P2** | OPEN |
| 11 | **OMEGA-11** / G-P2-05 | PO Request — no 60-day escalation tier | Accountability | 🟡 | 🟡 | 🟢 | ~2 h (reuses framework) | **P2** | OPEN |
| 12 | **OMEGA-12** | Watchdog email alarm path untested live | Recoverability | 🟡 Alarm code exists but never fired | 🔴 If real backup fails, alarm path unverified | 🟢 | ~1 h (fire test alarm) | **P2** | OPEN |
| 13 | **OMEGA-13** / G-P2-01 | Payroll Variance manual run — no audit fan-out | Accountability | 🟢 LOW | 🟢 | 🟢 | ~15 min | **P3** | OPEN |
| 14 | **OMEGA-14** / G-P1-06 | Shop Equipment Trash button → 403 (cosmetic) | Platform Clarity | 🟢 LOW | 🟢 Shop user confusion | 🟢 | ~10 min frontend gate | **P3** | OPEN |
| 15 | **OMEGA-15** / G-P1-07, G-P1-08 | `/equipment/:id` and `/inspections/:id` always redirect to admin namespace | User Efficiency | 🟢 LOW | 🟢 minor cross-portal UX | 🟢 | ~30 min | **P3** | OPEN |
| 16 | **OMEGA-16** | Doc-hygiene deltas D2, D3, D4, D7, D8, D13 (endpoint renames, stale assertions) | Platform Clarity | 🟢 LOW | 🟢 documentation only | 🟢 | ~1 h doc cleanup | **P3** | OPEN |
| 17 | **OMEGA-17** / G-P2-02, G-P2-03 | DR Weather=YES / Equipment-Issue=YES — no downstream task | User Efficiency | 🟢 LOW | 🟢 operator stop-list intentional | 🟢 | (intentional) | **P2 future** | INTENTIONAL |
| 18 | **OMEGA-18** | Cross-portal employee accountability timeline NOT BUILT (iter353c proposal exists) | Accountability | 🟡 Deep-audit UX friction | 🟡 Operator must stitch surfaces | 🟢 | ~16 h (per arch doc) | **P2 enhancement** | PHASE 2 |
| 19 | **OMEGA-19** / C1 | DR submission heavy form (22 taps · 4–6 min) | User Efficiency | 🔴 Adoption-blocker | 🔴 reduces data quality | 🟢 | redesign (OUT OF SCOPE) | **P1 redesign (NOT OMEGA)** | DOCUMENTED |
| 20 | **OMEGA-20** / C2 | Incident submission 54 fields (35–40 taps · 5–8 min) | User Efficiency | 🔴 Stress-amplifier | 🔴 hurts OSHA compliance data | 🟢 | redesign (OUT OF SCOPE) | **P1 redesign (NOT OMEGA)** | DOCUMENTED |
| 21 | **OMEGA-21** | H1 QA/QC heavy-form pattern unmeasured | User Efficiency | 🟡 unknown | 🟡 unknown | 🟢 | measurement first | **P2** | OPEN |
| 22 | **OMEGA-22** | H2 Mobile breakpoint inconsistency across admin pages | User Efficiency | 🟡 | 🟡 | 🟢 | (frontend) | **P2** | OPEN |
| 23 | **OMEGA-23** | H4 Notification overload risk per-role daily volume unmeasured | Accountability | 🟡 | 🟡 | 🟢 | instrumentation | **P2** | OPEN |

---

## 2 · By pillar

| Pillar | Open items | P0 | P1 | P2 | P3 |
|---|---:|---:|---:|---:|---:|
| Recoverability | 3 | 2 | 0 | 1 | 0 |
| Ownership | 2 (with overlap) | 1 | 1 | 0 | 0 |
| Accountability | 8 (with overlap) | 0 | 5 | 2 | 1 |
| Platform Clarity | 3 | 0 | 0 | 0 | 2 (D's are clarity) |
| User Efficiency | 5 (incl. 2 redesign items NOT OMEGA-scope) | 0 | 2 (out-of-scope) | 3 | 0 |

---

## 3 · "What is already elite" / "acceptable" / "unacceptable" / "must be fixed immediately"

### 3.1 · Already ELITE 🟢

- Production backup scheduler (PASS · CERTIFIED HEALTHY · live tick 43 sec ago · email path proven)
- Disaster recovery (FULLY RECOVERABLE · all 4 scenarios proven · RTO < 30 min)
- Audit trails (16 audit collections operationally populated · zero silent completions)
- Portal isolation (zero cross-portal data leakage observed)
- Idempotent incident submission (LTE-resilient)
- Backend fail-closed gates (anon → 401, wrong portal → 401)
- Fleet defect lifecycle handlers (ack → repair → clear chain works · audit-logged)
- Pre-Op FAIL fan-out (Shop + Dispatch · Critical priority on ≥3 fails)
- Safety incident first-response fan-out (Safety + PM · severity-driven priority)

### 3.2 · ACCEPTABLE 🟡

- Cross-portal employee timeline not yet implemented (architectural plan exists · UX friction during deep audits)
- Severe Incident no-response cadence absent (first-response works · manual oversight backup)
- 6 doc-hygiene deltas (endpoint naming · validation wording)
- Heavy field forms documented but unaddressed (out of OMEGA scope)
- Notification overload per-role volume uninstrumented
- 80 GB R2 usage (alert firing as designed · not a failure)

### 3.3 · UNACCEPTABLE 🔴 — must be fixed

- **OMEGA-3 / Fleet DVIR orphan** — vehicle defects can be submitted with no operator notified. Real ops gap.

### 3.4 · MUST BE FIXED IMMEDIATELY (P0 — operator action)

- **OMEGA-1**: run `migrate_dr_photos.py` on prod (~30 min · drops R2 80→20 GB · drops archive 464→115 MB)
- **OMEGA-2**: redeploy preview→prod so Batch H write-path defense is active
- **OMEGA-3**: operator sign-off on Fleet DVIR decision package · then ~2 h implementation in a future authorized batch

### 3.5 · CAN WAIT (P1/P2/P3)

- All notification visibility gaps (OMEGA-5 through OMEGA-9 · workflows function · just dashboard-surface improvements)
- Escalation cadence framework (OMEGA-10, OMEGA-11 · first-response works)
- Doc-hygiene cleanup (OMEGA-16)
- Cosmetic redirects (OMEGA-14, OMEGA-15)
- Heavy-form redesign (OMEGA-19, OMEGA-20 · out of OMEGA scope; future batch if authorized)

---

## 4 · Top-3 risk-weighted priorities

1. **OMEGA-3 / Fleet DVIR** — defects can hit prod with no one notified. Operator decision pending. (Severity × Likelihood = highest.)
2. **OMEGA-1 / Photo migration** — does not break recovery today, but the OOM trajectory documented in Batch G is real. (Severity × Likelihood = medium-high.)
3. **OMEGA-2 / Batch H deploy** — every new DR submitted without the write-path defense compounds OMEGA-1. (Severity × Likelihood = medium.)

---

## 5 · Stop-condition compliance

- ✅ Every entry has Memory + Code + Runtime traceability
- ✅ No remediation proposed in this register (closure paths described in `OMEGA_IMPLEMENTATION_PLAN.md`)
- ✅ No new features
- ✅ No redesign

---

_End of OMEGA_GAP_REGISTER.md._
