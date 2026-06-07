# PHASE 9C-A · OSHA SUBPART P COMPLIANCE ASSAULT · CERTIFICATION

**Date:** 2026-02-07
**Sprint:** OMEGA DIRECTIVE — PHASE 9C-A · OSHA Compliance Assault (verification-only)
**Verdict:** 🟡 **PARTIAL PASS · operational excellence, regulatory caveat**

---

## 1 · Executive Summary

Phase 9C-A audited the certified MASCI Trench Safety Operations System against 29 CFR 1926 Subpart P (§1926.650 / .651 / .652) plus utility-construction best-practice for road plates. The system **passes** on asset-level discipline (registration, tabulated data, inspection cadence, hold engine, repair engine, "Repair Complete ≠ Safe To Use", competent-person attestation, public field-safe QR, notification fanout, reporting & distribution). The system **does not yet pass** on excavation-level context (the dig itself: depth, soil class, protective-system selection, utility locate, atmospheric testing, access/egress, spoil setback).

**MASCI must not market the platform as "OSHA Subpart P compliant" today.** MASCI **may** market it as "OSHA-aware and OSHA-aligned at the asset level, with certified competent-person workflows."

---

## 2 · Coverage Percentage

From `OSHA_SUBPART_P_EXISTING_COVERAGE_MATRIX.md`:

| Bucket | Count | % of 47 IDs |
|---|---:|---:|
| 🟢 GREEN — covered | 14 | 30 % |
| 🟡 YELLOW — partial | 6 | 13 % |
| 🔴 RED — missing | 27 | 57 % |

**Headline number: 30 % fully covered + 13 % partially covered = 43 % some coverage.**

The 30 % covered items are not random — they cluster in the asset-management spine that every other Subpart P obligation depends on. Closing the next layer (excavation modelling) is leveraged work: a single new collection + soil-class field unlocks ~10 RED items at once.

---

## 3 · Covered Areas (🟢)

1. R-651.17 · Daily / Monthly CP / Annual inspections by competent person (server-enforced)
2. R-652.6 · Tabulated data presence on protective systems (Certification Hold auto-fires)
3. R-652.10 · Tabulated data on site (public QR + Missing-Data report + Pulse)
4. R-652.11 · Materials defect-free (inspection engine → hold engine → repair engine)
5. RP-1 · Road plate capacity rating
6. RP-2 · Anti-skid surface
7. RP-3 · Proper bearing / overlap
8. RP-4 · Pinning / anchoring
9. RP-6 · Markings / signage
10. RP-7 · Daily inspection cadence
11. CP authorise corrective measures (auto-Hold + repair stub)
12. CP daily-inspection cadence (Daily Posture dashboard)
13. CP tabulated-data verification (Cert Hold + DO NOT USE banner)
14. "Repair Complete ≠ Safe To Use" hold-priority resolver

## 4 · Partial Areas (🟡)

1. R-650 definitions glossary (implicit only)
2. R-651.18 evacuate on cave-in (Safety Hold opened; crew-evac ack field missing)
3. R-652.8 max-rated depth (field exists, unenforced — needs G-1)
4. R-652.12 RPE sign-off (verifier name captured, credential class missing)
5. CP "before each shift" / "as conditions change" / "as needed" inspections (cadence exists, no prompt)

## 5 · Missing Areas (🔴)

**27 items** clustered in 7 functional gaps (G-1 to G-7) — see `OSHA_SUBPART_P_GAP_ANALYSIS.md`.

Highest-leverage gaps:
- **G-1 Excavation Record** — closes ~10 IDs in one architectural addition (P0)
- **G-2 Utility Locate** — closes pre-dig requirements + matches MASCI's #1 incident category (P0)
- **G-5 Soil Classification** — depends on G-1; heart of §1926.652(a)/(b) (P0)
- G-3 Atmospheric Testing · G-4 Site Conditions · G-6 Walkway / Adjacent · G-7 OSHA Reference (P1-P2)

---

## 6 · Road Plate Assessment

**🟢 86 % covered (6 of 7 RP requirements).** See `ROAD_PLATE_COMPLIANCE_ANALYSIS.md`.

The Road Plate program is the **strongest sub-domain in the entire Trench Safety system**. The only open RP item is cold-mix taper around the perimeter — a job-site condition that belongs on the future excavation record (G-1), not on the plate itself.

The Phase 9B Road Plate Leadership Package mails Command + Missing Data + Repairs + Holds weekly to Safety / Shop / Ops leadership; the certified hold engine + repair engine + public QR + Pulse + Reports all treat road plates as first-class. Production-ready.

## 7 · Trench Box Assessment

**🟡 67 % covered (4 GREEN / 3 YELLOW / 2 RED of 9).** See `TRENCH_BOX_COMPLIANCE_ANALYSIS.md`.

Box-as-asset coverage is mature: tabulated data discipline, inspection cadence, hold + repair engines, hold-priority resolver, public QR. Box-as-deployment coverage is blind: max-rated-depth-at-dig validation, 18-inch extension verification, no-personnel-during-shield-motion ack are all blocked on G-1.

## 8 · Competent Person Assessment

**🟡 27 % strong + 36 % partial coverage (3 GREEN / 4 YELLOW / 4 RED of 11).** See `COMPETENT_PERSON_COMPLIANCE_ANALYSIS.md`.

The platform has a robust **`competent_person_confirmed` primitive** at the data layer — Monthly CP + Annual inspections are server-rejected without it. This primitive is the right foundation for every future CP workflow (soil class attestation · atmospheric authorisation · evac acknowledgement · post-rain re-inspection). CP gaps cluster around (a) absent soil-class capture, (b) absent dig context, (c) no rain-event trigger, (d) no atmospheric reading record.

---

## 9 · Regulatory Risk Assessment

| Risk | Severity | Mitigation today |
|---|---|---|
| OSHA citation — failure to classify soil | High | ❌ none |
| OSHA citation — failure to re-inspect after rain | Medium | ❌ none |
| OSHA citation — missing tabulated data | Low | ✅ mitigated |
| OSHA citation — damaged shielding in service | Low | ✅ mitigated |
| Strike of underground utility | High | ❌ none |
| Fall into trench (egress / barricade) | Medium | ❌ none |
| Cave-in with no documented protection rationale | Catastrophic | ❌ none |
| Road plate failure / vehicle damage | Low | ✅ mitigated |

Three of four highest-severity risks are unmitigated and all three depend on the same architectural move: **modelling the excavation**.

---

## 10 · Recommended Future Work (NOT authorised here)

| Phase | Scope | Closes |
|---|---|---|
| Phase 10A | Excavation Record (G-1) | ~10 RED items |
| Phase 10B | Soil Classification (G-5) | §1926.652(a)/(b) |
| Phase 10C | Pre-Dig Utility Locate (G-2) | §1926.651(b) |
| Phase 10D | Site Conditions checklist (G-4 + G-6) | §1926.651 multiple |
| Phase 11A | Atmospheric Testing (G-3) | §1926.651(g)/(h) |
| Phase 11B | OSHA Reference Library (G-7) | operational readiness |
| Phase 11C | Training Center | depends on Phase 10 |
| Phase 11-D | Yellow-band remediation | crew-clear ack · rated-depth validation · RPE credential field · weather-event trigger |

Each future phase is **architecturally compatible** with the existing certified architecture — the asset registry / hold engine / repair engine / notification fanout / Pulse / Reports / Subscription infrastructure stays intact. Every new compliance surface attaches to the existing `competent_person_confirmed` + `event_fanout` + `audit_events` primitives.

---

## 11 · Deliverables produced in this sprint

| Document | Status |
|---|---|
| `/app/memory/OSHA_SUBPART_P_REQUIREMENTS_MATRIX.md` | ✅ |
| `/app/memory/OSHA_SUBPART_P_EXISTING_COVERAGE_MATRIX.md` | ✅ |
| `/app/memory/OSHA_SUBPART_P_GAP_ANALYSIS.md` | ✅ |
| `/app/memory/ROAD_PLATE_COMPLIANCE_ANALYSIS.md` | ✅ |
| `/app/memory/TRENCH_BOX_COMPLIANCE_ANALYSIS.md` | ✅ |
| `/app/memory/COMPETENT_PERSON_COMPLIANCE_ANALYSIS.md` | ✅ |
| `/app/memory/OSHA_COMPLIANCE_CERTIFICATION.md` | ✅ |
| `/app/memory/PHASE9CA_OSHA_COMPLIANCE_ASSAULT_CERTIFICATION.md` | ✅ (this file) |

**Code changes:** ✅ ZERO — this was a verification-only sprint as directed.

---

## 12 · PASS / FAIL Recommendation

**🟡 PARTIAL PASS — Verification objective met; OSHA compliance objective NOT met.**

The audit is complete, evidence-based, and code-cited. MASCI leadership now knows **exactly where coverage exists, exactly where gaps exist, and exactly what must be built next** to claim full OSHA Subpart P compliance. The Road Plate program is OSHA-ready. The Trench Box program is asset-level ready, deployment-level blind. The Competent Person workflow is the strongest data-layer enforcement primitive in the platform — the foundation for every future compliance surface.

---

### STOP CONDITIONS HONORED
- ✅ Assessment complete
- ✅ Documentation complete (8 markdown deliverables)
- ✅ Certification complete
- ✅ PASS / FAIL recommendation issued (🟡 PARTIAL PASS)
- ✅ Zero code changes

No Training Center · OSHA Library · Search · OCR · Vision · Phase 10 · Phase 11 started.

— END OF CERTIFICATION —
