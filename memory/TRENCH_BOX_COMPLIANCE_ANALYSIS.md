# Trench Box Compliance Analysis

**Scope:** Compare the certified Trench Box program against §1926.652(c)/(d)/(g) (shielding requirements + tabulated data) and the related §651(k) inspection cadence.

**Conclusion ahead of detail:** 🟡 **Trench Box compliance is partially covered.** The platform tracks the *asset* well; it does **not** track the *deployment context* that §1926.652(a)/(b) require.

---

## Per-requirement assessment

| ID | Requirement | Color | Evidence |
|----|-------------|-------|----------|
| R-652.6 | Shielding conforms to manufacturer tabulated data OR RPE design | 🟢 | Every box carries `tabulated_data_filename` + `tabulated_data_missing` flag. Missing data fires Certification Hold via `_helpers.open_hold` (`_models.py::HOLD_PRIORITY` Certification Hold = 90). Surfaces in Reports Missing Data + Pulse + Dashboard. |
| R-652.7 | Shield top extends ≥ 18 in above lowest vertical wall it protects | 🔴 | Not captured. Lives on the deployment record (Gap G-1). |
| R-652.8 | Max-rated depth respected | 🟡 | `rated_depth_ft` field exists on the model; not enforced at dig assignment because the dig itself isn't modelled. |
| R-652.9 | No employees in shield during install / removal / move | 🔴 | Not captured. Procedural; could be enforced via a "lift hazard acknowledged" checkbox on the Dispatch workflow (future). |
| R-652.10 | Tabulated data on site, in writing | 🟢 | `tabulated_data_missing=True` auto-flags assets; reportable + sorted in Missing-Data report and Pulse. PDF/email distribution via Phase 9B. Public QR landing tells a field crew if tabulated data is missing. |
| R-652.11 | Materials defect-free | 🟢 | Daily Visual / Monthly CP / Annual inspection engine; Fail + Major auto-opens Inspection Hold + Maintenance Hold + repair stub. Critical adds Safety Hold (`_helpers.open_hold`). |
| R-652.12 | Damaged materials repaired only by RPE | 🟡 | Repair status tracks "Completed → Closed After Verification"; "Repair Complete ≠ Safe To Use" doctrine preserved (Safety / Cert holds survive repair). RPE credential field does **not** exist on repair close. |
| R-651.17 | Daily / shift / post-rain inspections by CP | 🟢 | `INSPECTION_TYPES = ("Daily Visual", "Monthly Competent Person", "Annual Review")`; CP confirmation enforced server-side on Monthly + Annual (`inspections.py:90-96`). Email + bell + digest via `event_fanout`. |
| R-651.18 | Evacuate when cave-in evidence | 🟡 | Critical inspection auto-opens **Safety Hold** + repair stub + bell + email. Workflow ends "stop work on this asset"; it does **not** explicitly capture a crew-evacuated acknowledgement. |

**Score: 4 GREEN / 3 YELLOW / 2 RED out of 9 → 67 % covered (44 % strong + 33 % partial).**

---

## What works extremely well

1. **Tabulated data discipline.** A trench box that arrives without manufacturer tabulated data automatically lands in the Missing-Data report, the Pulse, the public QR landing's DO NOT USE banner, and the weekly Road Plate Leadership Package (when filtered to boxes). MASCI cannot accidentally deploy a box without paperwork.

2. **Hold priority resolver.** `HOLD_PRIORITY = {Safety:100, Certification:90, Maintenance:80, Inspection:70}` means a Safety Hold survives every repair endpoint — the "Repair Complete ≠ Safe To Use" rule is enforced at the data layer, not in UI copy.

3. **Inspection cadence + competent-person enforcement.** Server-side rejection of Monthly CP / Annual inspections without `competent_person_confirmed=true`.

4. **Daily Posture dashboard.** Surfaces every active hold + every Daily Visual completed / pending in one glance — passes the 5:30 AM Superintendent Test.

---

## What is missing

1. **Box-deployment record.** No collection links a specific box (e.g., TB-04) to a specific excavation on a specific date at a specific depth. Without this link, R-652.7 (extension), R-652.8 (max rated depth at *this* dig), and R-652.9 (no personnel during shield motion) cannot be evidenced.

2. **RPE credential capture on damaged-material repair close.** Today's repair close stores a verifier name; it does not store the verifier's credential class. R-652.12 explicitly requires RPE sign-off when structural elements of a manufactured shield are repaired.

3. **18-inch extension check.** Belongs on the future deployment record.

4. **Crew-clear acknowledgement.** Procedural — single Boolean field on Critical inspections.

---

## Verdict

🟡 **Trench Box compliance is operationally mature at the asset level but blind at the deployment level.** Closing G-1 (Excavation Record) in a future phase converts every yellow + red on this matrix to green, because the box-to-dig link is the missing piece.

In its current state, MASCI can claim:
- Full daily / monthly / annual CP inspection coverage for trench boxes
- Full tabulated-data discipline
- Full repair-engine + hold-engine + "Repair Complete ≠ Safe To Use" enforcement

MASCI cannot yet claim:
- Per-dig depth enforcement against `rated_depth_ft`
- Per-dig extension verification
- RPE-credentialed damaged-material repair sign-off

These are the well-defined Phase-10/11 work items that the OSHA Compliance Certification will reference.
