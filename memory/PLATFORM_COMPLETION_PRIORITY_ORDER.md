# PLATFORM COMPLETION · PRIORITY ORDER

**Authority**: FOCP WAR ROOM · Phase 2
**Mode**: READ-ONLY ranking · 6-dimensional scoring on the 4 re-verified ACTIVE findings
**Date**: 2026-06-02T23:15 UTC

---

## Scoring rubric (1 – 10)

* **OR** Operational Risk — likelihood the gap halts work
* **UI** User Impact — count × frequency of pain
* **GR** Governance Risk — audit / compliance / regulatory exposure
* **SR** Safety Risk — physical-safety consequence likelihood
* **DI** Data Integrity Risk — likelihood of producing wrong / lost / duplicate data
* **SS** Self-Sufficiency Impact — multiplier on the 90-day-without-Jaymn question

Composite **PRIORITY** = (OR + UI + GR + SR + DI + SS) / 6.

---

## Per-finding scores

| TR ID | Title | OR | UI | GR | SR | DI | SS | PRIORITY |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| TR-0001 | JHP Acknowledgement Ledger build | 6 | 7 | 9 | 9 | 6 | 8 | **7.5** |
| TR-0002 | Universal undo / status reversal verb | 5 | 9 | 7 | 4 | 8 | 9 | **7.0** |
| TR-0003 | Sub/Vendor archive workflow | 4 | 5 | 6 | 2 | 4 | 4 | **4.2** |
| TR-0005 | Status canonical dictionary (helper + frontend rollout) | 3 | 6 | 4 | 2 | 3 | 5 | **3.8** |

---

## Why each score lands where it does

### TR-0001 · 7.5 — highest priority

* **Safety Risk 9**: Job Hazard Posters are the contract between the worker and the work. Without provable acknowledgement, a serious incident is much harder to defend.
* **Governance Risk 9**: Auditor-facing. OSHA / customer-audit / insurance-audit all expect a per-employee, per-version, per-project acknowledgement record.
* **Self-Sufficiency 8**: Safety persona currently asks Jaymn for the ad-hoc workaround. Without TR-0001 a 90-day Jaymn-free trial generates a weekly call.

### TR-0002 · 7.0 — second highest

* **User Impact 9**: Every persona makes mistakes. Without undo, every mistake becomes a backend ticket.
* **Self-Sufficiency 9**: This is the single biggest driver of "I need to call Jaymn" volume.
* **Data Integrity 8**: A platform without operator-recoverable undo accumulates wrong data; operators eventually learn to be cautious about clicking, slowing throughput.
* **Safety Risk 4**: Lower — undo on a status doesn't directly endanger anyone, but it does correct the audit trail to truth.

### TR-0003 · 4.2 — medium

* **Operational Risk 4**: Real but contained; admins work around it by setting subs to "inactive" via PATCH.
* **User Impact 5**: Admin-only; medium frequency, low headcount.
* **Governance Risk 6**: Audit trail of "who can I do business with?" is incomplete.
* **Self-Sufficiency 4**: Admins ask Jaymn occasionally about this; not the largest call driver.

### TR-0005 · 3.8 — lower priority

* **User Impact 6**: Cross-platform · daily · but each individual incident is small (read a label and move on).
* **Self-Sufficiency 5**: A new user reading `DEFICIENCY_RAISED` will ask Jaymn what it means. The fix removes that question class entirely.
* **Operational Risk 3**: No halt-of-work risk.
* **Safety Risk 2**: None directly.

---

## Final priority order

| Rank | TR ID | Priority Score | Reason in one sentence |
|---:|---|--:|---|
| 1 | TR-0001 | 7.5 | Safety + Governance + Self-Sufficiency · highest composite |
| 2 | TR-0002 | 7.0 | Self-Sufficiency × user-impact · removes the largest support-call class |
| 3 | TR-0003 | 4.2 | Governance closure on procurement |
| 4 | TR-0005 | 3.8 | UX polish · removes a continuous-low-friction tax |

LOW (deferred to post-completion polish window):
* TR-0004 verb harmonization · cosmetic string sweep · ~ 1 day after TR-0005 ships
* TR-0007 Constraint reopen · doctrine-exempt; product call only if Customer #2 demands it

---

## Composite priority insight

If only ONE finding ships before the 90-day trial: **TR-0001**.
If TWO ship: **TR-0001 + TR-0002**.
If THREE: **TR-0001 + TR-0002 + TR-0005** (close the most-frequent ambient friction class, which makes TR-D002 Phase-12 interviews much more meaningful).
If FOUR: all four.

The build order in Phase 4 reflects this scoring directly.

---

End of Phase 2 priority order.
