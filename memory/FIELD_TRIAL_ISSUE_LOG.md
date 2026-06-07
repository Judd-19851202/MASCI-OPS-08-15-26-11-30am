# FIELD TRIAL · ISSUE LOG

**Trial**: OMEGA Automated Proxy · 3 simulated foremen × 3 days
**Generated**: 2026-02-11

---

## OPEN ISSUES

### FT-D1-001 · Mobile viewport horizontal-overflow metric
* **Severity**: Medium (needs human verification — may be false alarm).
* **Workflow**: All workflows render on mobile profiles (393×852 iPhone, 412×915 Pixel, 820×1180 iPad).
* **Symptom**: Headless `document.body.scrollWidth` reports **1920** on all three viewport sizes.
* **Interpretation**: Could be (a) the layout actually overflows on physical devices, or (b) the headless rendering pipeline is reporting the desktop intrinsic width instead of the responsive layout width. The screenshot returned at the 393 px viewport renders correctly mobile-styled — suggesting it may be a measurement artifact, not a real overflow.
* **Resolution path**: Reproduce on a physical iPhone and physical Android during the real human trial. If real overflow → file a UI fix sprint (FV-7.1B). If not → close as headless-artifact.
* **Status**: OPEN · pending human-device verification.

### FT-D1-002 · Emergency Excavation block not translated to Spanish
* **Severity**: Low.
* **Workflow**: Public Excavation Form Section 1.
* **Symptom**: When user clicks ES toggle, the "Emergency Excavation?" heading and the helper paragraph ("Unscheduled, life-safety, utility-strike, water-main break, or after-hours excavation. Yes routes this to the Superintendent's Emergency chip immediately.") remain in English. Surrounding form text translates correctly.
* **Root cause (hypothesis)**: The Emergency block was added under FV-7.5; the i18n bundle was not updated with ES strings for this block.
* **Resolution path**: Add ES translations for: "Emergency Excavation?", and the helper text. Both keys exist in `PublicExcavationForm.jsx` Section 1 wrapped in `t(...)` calls — adding the ES bundle entries is a 2-line change.
* **Status**: OPEN · low-priority post-trial polish.

---

## NON-ISSUES NOTED FOR CLARITY (do not require fix)

* **FT-INFO-001** · `chip=` filter with unknown chip key falls through to base list (no 500). This is intentional defensive behaviour — confirmed safe.
* **FT-INFO-002** · `flag_no_cp` count combines `COMPETENT_PERSON` + `COMPETENT_PERSON_QUALIFIED` flag codes — intentional, both represent "no qualified CP" from the Safety lens.
* **FT-INFO-003** · `notification` fanout to Safety + Superintendent uses best-effort try/except — if the bell/email channel fails, the audit record + reinspection_required flag still persist. This is correct degradation under failure.

---

## SUMMARY

| Severity | Count |
|---|---|
| P0 (blocker) | **0** |
| P1 (critical) | 0 |
| P2 (medium) | 1 (FT-D1-001 mobile overflow — needs human verification) |
| P3 (low) | 1 (FT-D1-002 ES translation gap) |
| INFO | 3 |

**P0 bug count**: 0.
The proxy trial revealed **no production-blocking bugs**. Per OMEGA STOP CONDITION, no code changes were authorized or made during the trial.
