# ODR Bilingual Probe Report

_Generated 2026-05-29T13:05:10Z · env=preview · db=masci_safety_preview_

## Catalog snapshot
- Prompt keys: **14**
- EN keys meeting ≥4 floor: **14**
- ES keys meeting ≥4 floor: **14**
- Sections covered: **constraints, delays, equipment, extra_work, manpower, materials, photos, plan_vs_actual, production_segments, project, safety, signature, tomorrow, weather_impact**
- Crews with overlays: **airfield, concrete, electrical, milling, mot, paving, pipe, structures, survey**
- ODRs scanned: **56**

## Checks
- ⚠️ **B1** · ≥1 prompt_key per ODR section
- ✅ **B2** · ≥4 EN + ≥4 ES bullets per prompt_key
- ✅ **B3** · Crew overlay floors ≥4
- ✅ **B4** · No empty / whitespace-only bullets
- ✅ **B5** · Crew universe coverage
- ✅ **B6** · No orphan prompt_keys in live ODR data
- ✅ **B7** · Localized field shape integrity

## Warnings
### B1 · section_coverage_soft
```
{
  "check": "B1",
  "name": "section_coverage_soft",
  "missing": [
    "review",
    "subcontractors"
  ]
}
```
