# EXCAVATION OPERATIONS · PROOF CERTIFICATION

**OMEGA Phase FV-6 — Final Verdict**
**Date:** 2026-02-07
**Mode:** Validation-only. No code changes were made.

This certification consolidates the findings of:
- `EXCAVATION_OPERATIONS_FIELD_VALIDATION.md`
- `EXCAVATION_OPERATIONS_CONFUSION_REPORT.md`
- `EXCAVATION_OPERATIONS_CLICK_COUNT_REPORT.md`

---

## VERDICT

**Status:** ⚠ **CONDITIONALLY READY**

The Excavation Operations workflow is **functionally complete** (12 OSHA flags, 14 sections, two-way Daily Report linkage, certified registry integration, Spanish parity, reinspection automation, audit + notification fanout) and is **safe to operate** in a controlled rollout — but it is **not yet PROVEN** by the FORGEDOPS standard.

The four FORGEDOPS attributes:

| Attribute | Verdict | Why |
|-----------|---------|-----|
| **Powerful** | ✅ Yes | Every certified MASCI source (jobs_master, employees, trench_safety_assets, daily_reports) is wired in. Two-way Daily Report linkage. Reinspection queue. Live OSHA engine. |
| **Simple**   | ⚠ Mostly | Phase 10C progressive disclosure hides 5 of 14 sections. Click counts are 12–22 for typical scenarios. **But** competent-person, OSHA terminology, and "lateral travel" wording still need first-time training. |
| **Beautiful**| ✅ Yes | Public form parity with Trench Safety surface. Sticky Live OSHA Status card. Consistent typography + spacing. |
| **Trusted**  | ⚠ Partial | Backend audit + event_fanout fire on every action. **However:** end-to-end email delivery is not certified. Asset-fit (rated_depth, plate size) is not validated. CP certification expiration is not checked. |
| **Proven**   | ❌ Not yet | Zero documented field-user trials. Zero real-device validation (iPhone / Android / iPad). Zero load tests. |

---

## CRITICAL GAPS BLOCKING "PROVEN"

### Safety-impacting (must address before fleet rollout)

1. **Trench-box rated-depth is shown, not enforced.** A 6 ft-rated box linked to a 10 ft excavation passes today. → **Add comparison: if linked box `rated_depth_ft` < excavation `depth_ft`, fire a `TRENCH_BOX_DEPTH_MISMATCH` Action Required flag.**
2. **Road-plate dimensions vs trench opening — no validation.** → **Add a chip "verify plate spans the opening" when plates linked.**
3. **Foreman cannot self-trigger reinspection.** Reinspection trigger is admin-only. A rain event mid-day requires Safety to notice. → **Expose `POST /reinspection-trigger` to the public form for the original foreman of the record (token-by-email or session check).**
4. **Competent Person designation has no certification check.** → **Cross-reference `employees.qualifications` (if data exists). Soft block CP picks with no current trench-safety qualification.**

### Operational visibility gaps

5. **Superintendent cannot answer "who has no CP / no protective system" without opening each record.** → **Add aggregate chips at the top of the Oversight page: "5 with no CP · 3 with no protective system · 12 with action required".**
6. **No fleet view of deployed trench boxes / road plates.** Asset registry knows location; excavation list does not aggregate. → **Add "Deployed Today" tile on Safety dashboard listing every box + plate currently linked to an open excavation.**
7. **No risk aggregation by OSHA flag code.** Reports summary API has the data. UI does not surface it. → **Add chips on Oversight page: "ACCESS_EGRESS: 4 · PROTECTIVE_SYSTEM: 2 · SOIL_UNKNOWN: 7".**

### UX gaps

8. **Photo upload happens "after submission" via the asset photo workflow.** Foremen expect in-form upload. → **Add a single optional photo input on the success card.**
9. **"Create New" from Daily Report opens in a new tab.** Mobile foremen lose context. → **Open in same tab; restore the Daily Report draft on return via session.**
10. **No "Emergency Excavation" designation.** Emergency records look identical to routine ones in the queue. → **Add an "Emergency?" toggle on submit; if Yes, escalate notification kind to `trench_excavation_emergency`.**
11. **No round-trip edit for foremen.** A misclick on depth is permanent. → **Allow the original `submitted_by` email to edit the record within a 2-hour grace window (audit-logged).**

### Proof gaps (not built, not tested)

12. **No documented field-user trial.** Zero foremen have used this in production.
13. **No real-device validation.** iPhone / Android / iPad layouts not tested by a human.
14. **No load test.** 600-asset roster picker performance unknown.
15. **End-to-end email notification delivery is not certified.** `event_fanout` is best-effort `try/except`.
16. **Spanish translation review by a native speaker is not done.** Construction-Spanish dialect may differ from our literal translations.

---

## WHAT IS PROVEN

- 91/91 pytest cases pass (Phase 8/9/10A/10A-B/10C/10D).
- 16/16 Phase 10C compliance engine assertions pass.
- 12 OSHA flags fire deterministically.
- Coaching-language guard: no punitive vocabulary across all 12 flags.
- Two-way Daily Report ↔ Excavation linkage (forward + reverse `$addToSet`).
- Audit + event_fanout reuse certified Phase 7.5C infrastructure.
- JobPicker pulls 28 live MASCI jobs.
- EmployeePicker pulls 330 active employees.
- TrenchAssetPicker pulls live asset registry.
- Public form parity with `/trench-safety` Public surface.

---

## PATH FROM "CONDITIONALLY READY" TO "PROVEN"

A focused FV-7 sprint would do exactly four things:

### 1 · Close the 4 safety gaps (gaps 1–4 above)
- Trench-box rated-depth validation (1 new OSHA flag).
- Road-plate dimension check (1 chip).
- Foreman-driven reinspection trigger (1 endpoint scope change).
- CP certification cross-check (1 employees-roster join).

**Effort:** ~1 sprint. **Risk:** low (additive to existing engine).

### 2 · Surface aggregate visibility on Oversight (gaps 5–7)
- Add 3 aggregate chips at the top of `/safety/trench-safety/excavations`.
- Add a "Deployed Today" tile.
- Add a flag-code histogram chip row.

**Effort:** ~0.5 sprint. **Risk:** low (UI-only).

### 3 · Document and run a real field trial
- 3 foremen, 3 jobs, 3 days. Record click counts, observed confusion, time-to-submit.
- Validate on actual iPhone + Android + iPad with bright sunlight.
- Get one native-Spanish-speaking foreman to review the ES translation.

**Effort:** 1 week of field time + writeup. **Risk:** highest value.

### 4 · End-to-end notification certification
- Verify the certified `event_fanout` actually delivers email/SMS for the `trench_excavation_*` kinds.
- Add a `proof-of-delivery` admin endpoint that lists last 50 fanouts with status.

**Effort:** ~0.5 sprint. **Risk:** low.

---

## FINAL RECOMMENDATION

**CONDITIONALLY READY.**

The Excavation Operations workflow is built, tested at the unit level, and architecturally sound. It is safe to pilot with a controlled set of crews under Safety supervision. **It is not yet PROVEN by the FORGEDOPS standard.**

Recommend a focused FV-7 sprint (4 deliverables above) before fleet-wide rollout.

Do not declare Phase 11 (Trench Safety Final Certification) until the 4 safety gaps are closed and the field trial is documented.

---

*Certified under the OMEGA Field Validation Assault Directive · MASCI Operations Platform.*
