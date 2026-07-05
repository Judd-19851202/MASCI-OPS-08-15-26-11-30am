# DR-ROI-001F · Platform UI Consistency Audit

## Reference — Platform design language
Anchor file: `frontend/src/pages/NewDailyReport.jsx` (V1 Daily Report).
Other references: safety forms, QA/QC forms, HR forms, PM/Admin views.

### Platform visual grammar (locked in)
- **Canvas:** `bg-slate-50` (page), `bg-white` (cards).
- **Borders:** `border-slate-200` (subtle) / `border-slate-300` (input).
- **Radius:** `rounded-2xl` (cards), `rounded-md` (inputs, buttons), `rounded-full` (chips).
- **Typography:** `text-slate-900` (body), `text-slate-600` (secondary),
  `text-slate-500` (tertiary), `font-mono text-[10px] uppercase
  tracking-[0.2em] text-red-700 font-bold` (micro-labels), `text-red-700`
  (primary accent).
- **Inputs:** `h-12 text-base border-2 border-slate-300
  focus-visible:ring-red-600 focus-visible:ring-2`.
- **Primary CTA:** `bg-red-700 hover:bg-red-600 text-white h-11
  px-4 rounded-md font-semibold`.
- **Secondary CTA:** `border-2 border-slate-300 bg-white
  hover:bg-slate-100 text-slate-800 h-11 px-4 rounded-md font-semibold`.
- **Empty state:** `rounded-xl border border-dashed border-slate-300
  bg-slate-50 px-4 py-6 text-sm text-slate-600`.
- **Chips:** tone-scoped colored border + light bg (green/amber/red/blue/slate).
- **Focus ring:** red-600 with offset — accessibility-first.

## V2 audit findings (Session A)

### Shell
| Attribute            | Before                                 | After (platform)                   |
|----------------------|----------------------------------------|-------------------------------------|
| Page background      | `bg-neutral-950`                       | `bg-slate-50`                       |
| Body text            | `text-neutral-100`                     | `text-slate-900`                    |
| Header               | `border-neutral-800`                   | `border-slate-200`                  |
| Save bar             | Inline text opacity                    | Sticky top bar, `bg-white/95`       |
| PDF buttons          | Absent                                 | Preview / Download in save bar      |
| Sidebar              | Dominating 360px rail on right         | Inline panels · single-column       |
| PM panel             | Inline inside field form               | Removed · lives at `/pm/*`          |

### SectionCard
| Attribute       | Before                              | After                             |
|-----------------|-------------------------------------|-----------------------------------|
| Border          | `border-neutral-800`                | `border-slate-200`                |
| Fill            | `bg-neutral-900/60`                 | `bg-white`                        |
| Title color     | Default (light on dark)             | `text-slate-900`                  |
| Description     | Absent (subtitle only)              | Optional `description` prop       |
| Action slot     | Absent                              | Optional `action` prop            |
| Badge           | `border-neutral-700 opacity-70`     | `border-slate-300 bg-slate-50`    |

### Inputs
| Attribute       | Before                                       | After (platform)                            |
|-----------------|----------------------------------------------|---------------------------------------------|
| Height          | `py-1` (~24px)                               | `h-12` (48px · thumb-friendly)              |
| Border          | `border-neutral-700`                         | `border-2 border-slate-300`                 |
| Focus           | No visible ring                              | `focus-visible:ring-2 focus-visible:ring-red-600` |
| Fill            | `bg-neutral-900`                             | `bg-white`                                  |
| Placeholder     | Default                                      | `placeholder:text-slate-400`                |

### Language
| Before                            | After (platform / invisible-intel) |
|-----------------------------------|-------------------------------------|
| "Live Operational Summary"        | "Daily Operational Summary"         |
| "Confidence & Validation"         | "Summary readiness"                 |
| "Uncertainties"                   | "Items to verify"                   |
| "Regenerate all"                  | "Regenerate"                        |
| "Accept full synthesis"           | "Accept full summary"               |
| Reference to "agent"              | "source"                            |

## Accessibility & Device
- Red-600 focus ring on every input / button — visible and consistent.
- All inputs `h-12` — hit-target ≥44px for ToughBook glove use.
- Chips are ≥28px vertical — tap-friendly on iPad.
- No horizontal scroll on mobile (sticky bar wraps).
- `whitespace-nowrap` avoided on data columns — tables scroll on narrow
  viewports instead of clipping.

## CI-Locked Guardrails
- `test_no_ai_branding_in_field_form` — scans all V2 files for AI vendor
  strings.
- `test_no_dark_theme_classes_in_field_form` — rejects `bg-neutral-9*`,
  `text-neutral-100`, and other dark drift classes.
- `test_shell_uses_platform_light_theme` — asserts `bg-slate-50` +
  `text-slate-900` + Preview/Download PDF testids.
- `test_pm_intelligence_panel_removed_from_field_form` — physical file
  absence + import absence in shell.
- `test_ui_primitives_export_platform_grammar` — exports contract.
- `test_v1_daily_report_untouched_reference_lines` — V1 anchor imports
  still present.
- `test_dr_v2_flag_still_gates_the_shell` — feature-flag preservation.
