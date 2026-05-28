# Timeline Calmness Certification

**Phase V-Prelude · Wave 1.1**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Scope

The Operational Timeline Sidecar — and only the sidecar — is the
subject of this certification. The underlying `/api/timeline`
endpoint inherits the Wave 1 calmness contract documented in
`OPERATIONAL_TIMELINE_CERTIFICATION.md`.

## Doctrine reference
- `/app/memory/OPERATIONAL_TIMELINE_FOUNDATION.md`
- `/app/memory/PHASE_V_PRELUDE_IMPLEMENTATION_PLAN.md`

## Calmness invariants

### Visual chrome (all enforced by Playwright)
- **Single accent.** Slate text body. ONE icon (`Clock3`) in the
  header. No multi-accent palette.
- **No filled badges.** Pytest assertion sweeps the sidecar DOM for
  `bg-amber-50/100`, `bg-emerald-50/100`, `bg-rose-50/100`, and
  `bg-red-50/100` — any presence fails the suite.
- **No charts. No gantt. No swim-lanes.** The sidecar renders an
  `<ol>` of `<li>` rows via the existing `ChronologyPanel`. No `<svg>`,
  no `<canvas>`, no charting library.
- **No engagement metrics.** No "trending", no "fastest growing", no
  "X events in last 7 days" copy.

### Reading rhythm
- **Bounded list.** `max-h-[420px]` with `overflow-auto`. No
  infinite-scroll body trap.
- **30-row floor.** First 30 rows visible. "Show all" affordance
  appears only when there are more. No automatic expansion.
- **Truncation surfacing.** When `truncated=true` from the backend,
  the sidecar appends a single italic slate line — never a "view
  more in another dashboard" CTA.
- **Newest first.** Backend guarantees `at` is monotonically
  non-increasing. Pytest asserts the contract.

### Loading / empty / error states
- Loading copy: `Loading chronology…` — slate-500, no spinner
  iconography.
- Empty copy: `No operational events recorded for this project yet.` —
  italic, slate-500, single sentence.
- Error copy: `rose-700` text, single line, no toast, no modal.

## Acoustic boundary (governance recap)

Calmness in the operational doctrine means **the sidecar must NOT
demand attention**. Every visual layer is intentionally muted because
the field-operational user already lives inside ten other systems
demanding attention. The chronology is reference reading — past tense.

## Probes

### Playwright sweep (`test_v_prelude_wave1_1_sidecar_calmness.py`)
- `test_sidecar_mounts_on_pm_project_detail` × {desktop · iPad ·
  mobile} — sidecar testid present and exactly 1 instance.
- `test_sidecar_calm_chrome_no_loud_badges` × all viewports — DOM
  class sweep rejects loud accents.
- `test_sidecar_refresh_button_is_thumb_safe` × all viewports —
  refresh control bounding box height ≥ 32 px.

### Backend pytest (`test_v_prelude_wave1_1_sidecar.py`)
- `test_sidecar_timeline_orders_newest_first` — ordering contract.
- `test_sidecar_timeline_emits_z_suffixed_iso` — TRUST-TIME-1.
- `test_sidecar_timeline_excludes_voided_links` — calm doctrine §10.

All checks 🟢 green.

---

— certified by E1 · 2026-05-28
