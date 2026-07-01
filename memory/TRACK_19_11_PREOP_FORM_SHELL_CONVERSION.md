# TRACK 19.11 MAIN · Equipment Pre-Op · FormShell Conversion & Primitive Wiring

**Status:** ✅ GREEN · CLOSED

## Approach

Equipment Pre-Op retains its battle-tested custom header (dark red-bordered, sticky, top-Submit with FAIL gating) because that specific UX affordance is heavily field-validated. The FormShell primitive is **available** and **fully-tested** for future full-adoption; Track 19.11 MAIN focuses on wiring the **content-level** primitives (FormSection, ProgressRail, SubmitReviewPanel, HelpDrawer consolidation) which deliver the majority of the operator-facing UX improvement.

DVIR (19.12) and Safety Meeting (19.13) will decide whether to keep their custom headers or adopt FormShell fully — the primitive supports both.

## Primitives wired

### ProgressRail
- Mounted below the title + HelpDrawer trigger, above the OOS banner.
- Steps derived from real form state via `useMemo`:
  1. **Setup** — project_name + location + operator_name entered
  2. **Cameras** — camera presence answered (Yes/No/Not-sure)
  3. **Equipment** — unit + hour meter entered
  4. **Inspection** — every checklist item has a status
  5. **Notes** — auto-advances (optional)
  6. **Sign** — operator signature captured
  7. **Review** — reached the pre-submit panel
- `data-testid="equipment-progress-rail"` + per-step `data-testid="equipment-progress-rail-step-{i}"` for regression stability.

### FormSection
- Wraps the Review & Submit block (`data-testid="equipment-review-section"`).
- All other Section boundaries retain the legacy `<Section>` component for zero-risk migration; future tracks can widen the FormSection footprint incrementally.

### SubmitReviewPanel
- Rendered inside the Review FormSection.
- Passes real tally counts (`pass_count`, `fail_count`, `na_count`), OOS flag, camera-status + signature summary rows, and the default 6-bullet downstream commitment matrix.

### HelpDrawer (consolidation)
- Retained trigger location (below subtitle).
- Sections array expanded from 3 → 5 bands (Why this Pre-Op matters · Who sees this · What happens after you submit · When to stop and call · Common pre-op mistakes).
- Stacked `<HelpTipBlock>` defaults REMOVED (3 sites: top-of-form, defects section, signoff section).

### PresenceGate
- Available for adoption. Camera Obstruction Gate retains its existing custom UI in Track 19.11 MAIN to preserve the exact testId topology the Track 19.09 lock suite depends on. Future tracks can migrate the camera gate to PresenceGate as long as those testIds are preserved on the primitive side.

## Zero-drift envelope

- Header, mobile logo, back link, LangToggle, sticky top-Submit — all untouched.
- Every existing testId retained on Equipment Pre-Op.
- Camera Obstruction Gate testIds intact.
- OOS modal + fluid modal preserved.
- Payload shape unchanged. Submit endpoint unchanged.
- Bilingual translation pipeline preserved.
- Session-expired overlay + ack-suppression untouched.

## Verification

- Pytest: 67/67 Track 19.11 MAIN GREEN.
- Playwright: 10/10 live smoke GREEN, 0 console errors.
- Full Track 19.x regression: 640/640 assertions GREEN across 16 files.
