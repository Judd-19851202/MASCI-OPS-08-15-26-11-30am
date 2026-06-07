# OSHA Compliance Certification — MASCI Trench Safety Operations System

**Date:** 2026-02-07
**Standard evaluated:** 29 CFR 1926 Subpart P · §1926.650 / §1926.651 / §1926.652
**Method:** Evidence-based, code-cited audit. No marketing language.

---

## Executive verdict

**🟡 PARTIAL OSHA COMPLIANCE — strong on the asset-level discipline, blind at the excavation-level context.**

MASCI does **not yet qualify** for an unqualified OSHA Subpart P compliance claim. It **does** qualify today for the narrower claim: *"MASCI has a certified, audited, multi-portal asset-management and inspection system for trench-protection equipment, with competent-person attestation, tabulated-data enforcement, hold-engine + repair-engine + 'Repair Complete ≠ Safe To Use' doctrine, and 9-report regulatory reporting suite."*

The gap is the dig itself — Subpart P regulates excavations; MASCI today regulates the tools that protect excavations.

---

## Quantitative coverage

From `OSHA_SUBPART_P_EXISTING_COVERAGE_MATRIX.md`:

| Sub-domain | GREEN | YELLOW | RED | Total | Coverage |
|---|---:|---:|---:|---:|---:|
| §1926.650 (defs) | — | 1 | — | 1 | 50 % |
| §1926.651 (excavation reqs) | 1 | 1 | 17 | 19 | 8 % |
| §1926.652 (protective systems) | 3 | 2 | 7 | 12 | 33 % |
| Road Plate (industry / DOT) | 6 | — | 1 | 7 | 86 % |
| Trench Box (subset of §652) | 4 | 3 | 2 | 9 | 67 % |
| Competent Person (cross-cut) | 3 | 4 | 4 | 11 | 64 % some coverage |

**Overall, by requirement ID: 14 GREEN + 6 YELLOW + 27 RED out of 47 distinct evaluated items.**

- **Strong:** 30 % fully covered
- **Partial:** 13 % partially covered
- **Missing:** 57 % not covered

---

## What MASCI can defensibly claim TODAY

1. **Asset compliance.** Every protective-system asset (trench box, end panel, spreader, hydraulic shore, slide rail, trench jack, ladder, road plate, accessory) is registered, serial-tracked, photo-attached, audit-trailed, and inspectable.
2. **Tabulated data discipline.** §1926.652(g) is enforced at the data layer — a box without tabulated data carries a `Certification Hold` and is DO NOT USE on the public QR landing.
3. **Competent-Person cadence.** Monthly CP + Annual inspections are **server-side rejected** without `competent_person_confirmed=true` (`inspections.py:90-96`).
4. **Inspection → Hold → Repair workflow.** Fail + Major auto-opens Inspection Hold + Maintenance Hold + repair stub; Fail + Critical adds Safety Hold; bell + email + digest via `event_fanout`. (`§1926.652(d) / 651(k)(2)` spirit.)
5. **"Repair Complete ≠ Safe To Use."** Hold-priority resolver guarantees Safety / Certification holds survive every repair endpoint — even a successfully closed repair cannot put a box back into service if a higher-priority hold is active.
6. **Operational visibility.** Pulse + Reports + Subscriptions + Leadership Digest + Road Plate Leadership Package keep leadership informed weekly without manual intervention.
7. **Road Plate program.** 86 % requirement coverage for the plate-as-asset; only RP-5 (cold-mix taper) is a job-site condition that belongs on the future excavation record.

## What MASCI CANNOT defensibly claim today

1. **Excavation registration.** Digs are not modelled. Depth, length, width, soil class, water, spoil, surrounding structures are not captured.
2. **Soil classification.** §1926.652(a) / Appendix A is the heart of Subpart P — and is not in the system.
3. **Protective-system selection rationale.** §1926.652(b) Appendix B/C/D/E/F design path is not captured.
4. **Pre-dig utility locate.** No 811 / Sunshine 811 ticket capture.
5. **Hazardous-atmosphere testing.** §1926.651(g) — no O₂/LEL/CO/H₂S log surface.
6. **Access/egress placement enforcement.** §1926.651(c)(2) — no per-dig ladder/ramp/stairway placement record.
7. **Spoil setback / barricade / walkway-guardrail evidence.** §1926.651(j)(2), (f), (l) — not captured.
8. **Post-rain re-inspection trigger.** §1926.651(k)(1) — CP is on their own.

---

## Regulatory risk assessment

| Risk | Severity | Mitigation status |
|---|---|---|
| OSHA citation for failure to classify soil | High | Not mitigated · requires G-1 + G-5 |
| OSHA citation for failure to inspect after rain | Medium | Not mitigated · weather-event trigger needed |
| OSHA citation for missing tabulated data | Low | **Mitigated** today |
| OSHA citation for damaged shielding in service | Low | **Mitigated** today |
| Strike / damage to underground utility | High | Not mitigated · requires G-2 |
| Fall into trench (egress / barricade) | Medium | Not mitigated · requires G-4 |
| Cave-in fatality with no documented protection rationale | Catastrophic | Not mitigated · requires G-1 + G-5 |
| Road plate failure / vehicle damage | Low | **Mitigated** today |

---

## Verdict

**🟡 PARTIAL PASS — operational excellence, regulatory caveat.**

MASCI may say internally and to clients: *"Trench Safety Operations System is OSHA-aware and OSHA-aligned at the asset level."* MASCI may **not** say: *"MASCI Trench Safety is OSHA Subpart P compliant."* The latter requires shipping Gap G-1 (Excavation Record), G-2 (Utility Locate), G-5 (Soil Classification), at minimum.

---

## Recommended future work (NOT authorised in Phase 9C-A)

Sequential, P0 first:

1. **Phase 10A — Excavation Record (G-1)** — single largest unlock, closes ~10 RED items.
2. **Phase 10B — Soil Classification (G-5)** — depends on G-1; closes §1926.652(a)/(b).
3. **Phase 10C — Pre-Dig Utility Locate (G-2)** — depends on G-1.
4. **Phase 10D — Site Conditions checklist (G-4 + G-6)** — depends on G-1.
5. **Phase 11A — Atmospheric Testing (G-3)** — depends on G-1.
6. **Phase 11B — OSHA Reference Library (G-7)** — independent; ship anytime.
7. **Phase 11C — Training Center** — depends on G-1/G-5 to be meaningful.
8. **Post-Phase-11 yellow-band remediation** — crew-clear ack · rated-depth validation · RPE credential field on repair close · weather-event re-inspection trigger.

All Phase 10/11 work is **architecturally compatible** with the existing certified architecture — every gap can be closed without breaking the asset registry / hold engine / repair engine / notification fanout / Pulse / Reports / Subscription infrastructure. The existing `competent_person_confirmed` primitive is the foundation for every new CP surface.
