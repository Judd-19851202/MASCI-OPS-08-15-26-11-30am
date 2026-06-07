# Trench Safety — Reference Split Report
**Sprint:** Public Trench Safety UX Correction
**Date:** 2026-02-07

---

## 1. Problem
On the pre-correction dashboard, the **Tabulated Data** tile and the **Safety References** tile both pointed at `/trench-boxes`. Crew members tapping either tile landed on identical content — the engineered tabulated-data PDF library. There was no surface dedicated to OSHA general guidance, competent-person rules, stop-work coaching, or unsafe-condition examples.

This violated the directive "split into two clearly different experiences" and risked normalising the duplication for printed materials and posters.

---

## 2. Resolution — distinct surfaces

### 2.1 `/trench-safety/tabulated-data` — Tabulated Data Library
Holds engineered, manufacturer-specific data:
- TabulatedDataPrimer (existing, unchanged) — OSHA's definition, why it matters, how to read a sheet.
- TrenchBoxTabulatedLibrary (existing, unchanged) — per-box folders, search, download.
- Manufacturer / box-specific PDFs.
- Soil-type ratings, spreader configurations, depth limits.
- Coaching: *Match the box to the right sheet.*

### 2.2 `/trench-safety/references` — Safety References
Holds general OSHA-aligned trench safety guidance:
- **Stop-Work Authority** banner.
- **Competent Person Required** (every trench ≥ 5 ft).
- **Inspect Daily — and After Every Change** (rain, soil change).
- **Unsafe Condition Examples** (cracked panels, bent spreaders, standing water, spoil-pile-edge, cracked walls, undermined utilities, improper sloping).
- **Missing Pins** — do not use, tag, stage another box.
- **Missing or Illegible Labels** — without labels there is no tabulated-data match, the box is not OSHA-compliant.
- **Safe-Use Reminders** — ladder/ramp every 25 ft, swing-radius rules, never lift the box with crew inside, verify spreaders before stacking.
- **Tabulated Data Match** — what to confirm before use.
- **When in Doubt — Don't** — culture line, safety beats schedule.

---

## 3. Cross-linking (not duplication)
- Tabulated Data surface → "Looking for OSHA general guidance, competent-person reminders, or what to do if pins/labels are missing? **Open Safety References →**".
- Safety References surface → "Tabulated data is specific to manufacturer, model, soil type, and spreader configuration. **Open Tabulated Data →**".

Crews can step from one to the other without bouncing through the dashboard.

---

## 4. Component reuse vs. duplication
| Component | Used by Tabulated Data | Used by Safety References |
|---|---|---|
| `TabulatedDataPrimer` | ✅ | ❌ |
| `TrenchBoxTabulatedLibrary` | ✅ | ❌ |
| Reference cards (new in this file) | ❌ | ✅ |

No file holds both — the surfaces are physically separate at the route level and at the component composition level.

---

## 5. Verdict
🟢 **Tabulated Data and Safety References are now two distinct experiences with deliberate cross-links. No duplicate content.**
