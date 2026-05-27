# Daily Report · Coaching Language
## iter442 · Field-Trust Doctrine · 2026-05-27

> What the iPad says to the foreman. What it must never say. Every
> phrase that surfaces around the daily-report autosave, the draft
> restore prompt, the crew-memory banner, and the load-trace line.

---

## 1 · Tone

Calm. Industrial. Operator-language. Speak as a clipboard, not as
a marketing site.

| Allowed | Avoid |
|---|---|
| "Saved" | "Awesome! Saved successfully!" |
| "Saved 12s ago" | "Last sync 12 seconds ago — you're all good!" |
| "Save failed — storage full" | "Oops, something went wrong" |
| "Recent crew and equipment may preload to speed up daily reporting." | "We learned your patterns and built a profile for you" |
| "Loaded from recent reports on this iPad." | "Welcome back, J! We identified you and preloaded your data." |
| "Change project / foreman" | "Switch personas" |
| "Start Blank" | "Start fresh ✨" |
| "Your work is saved on this device until it is submitted." | "Don't worry — we've got your back" |

---

## 2 · The approved phrase book

### Autosave pill (`DraftStatusPill.jsx`)

| State | Text |
|---|---|
| `idle` w/ no lastSavedAt | (hidden) |
| `saving` | **Saving draft…** |
| `saved` (just now, < 5 s) | **Saved just now** |
| `saved` (≥ 5 s) | **Saved 12s ago** / **Saved 4m ago** / **Saved 2h ago** |
| `failed` (quota) | **Save failed — storage full** |
| `failed` (disabled) | **Save failed — storage disabled** |
| `failed` (other) | **Save failed — {errorName}** |

### Draft restore prompt (`DraftRestorePrompt.jsx`)

| Element | Text |
|---|---|
| Title | **You have unsaved work from earlier.** |
| Subtitle (with savedAt) | **Saved {age} on this device.** |
| Subtitle (no savedAt) | **Your work is saved on this device until it is submitted.** |
| Cross-token note | **Recovered from a previous session.** *(italic, smaller)* |
| Buttons | **Restore** · **Discard** |

### Crew-memory banner (`CrewSetupRestorePrompt.jsx`)

| Confidence | Title |
|---|---|
| low / medium | **Recent crew and equipment may preload to speed up daily reporting.** |
| high (≥5 uses) | **Loaded from recent reports on this iPad.** |

Subtitle (always):
> **Saved setups stay only on this device. Use this option only if
> this is your crew device or personal device.**

Buttons:
- **Use Setup** (primary, amber)
- **Change project / foreman** (outline, optional)
- **Start Blank** (outline)
- **Clear Saved Setup** (ghost)

Footer:
> **You can edit crew and equipment after loading. Starting blank
> will not erase previously submitted reports.**

### Project-change confirm dialog

When `isProjectChange(snapshot, currentProjectNumber)` returns true
and the operator taps "Use Setup":

> **This setup is from a different project. Reuse crew and equipment anyway?**

Buttons: **OK** · **Cancel** (native `window.confirm`).

### Load-trace line (post-restore)

Renders below the banner immediately after a successful `Use Setup`
or after `applySetupSnapshotToData`:

> *Loaded from recent reports on this iPad.*

Single sentence. Italic. Calm color. Auto-dismisses after the form
is touched.

### Toast after Use Setup

> **Loaded from recent reports on this iPad.**

### Toast after Change project / foreman

> **Pick a project · crew and equipment can preload after.**

---

## 3 · Banned phrasing (regression-tested)

The frontend regression suite (`test_crew_setup_prompt_uses_calm_coaching_copy`)
fails the build if any of these appear in the daily-report restore
prompts:

| Banned | Reason |
|---|---|
| "we identified you" | implies surveillance |
| "we are learning" | implies behavioral profiling |
| "personalized for you" | marketing slop |
| "we know you" | creepy |
| "tracking" | implies tracking |
| "behavior" | implies behavioral profiling |
| "ai" (standalone word) | no AI rhetoric anywhere near operator surfaces |
| "profile" (standalone word) | implies a user profile |

The regex uses **word boundaries** for `ai` / `profile` so common
substrings (`daily`, `professional`) are not false positives.

---

## 4 · Where coaching appears (and does NOT appear)

| Surface | Coaching? | Why |
|---|---|---|
| Daily Report — restore prompt | Yes — calm subtitle | Operator decision moment |
| Daily Report — autosave pill | Yes — relative time | Reassurance that work is safe |
| Daily Report — crew-memory banner | Yes — confidence-tiered | Suggestion, not enforcement |
| Daily Report — submit success toast | (existing copy) | Out of scope this round |
| New Incident / New Inspection / HR Payroll Variance | **No new coaching** | Same hook, but no crew-memory layer; existing pill + prompt copy inherited |
| Admin Governance — Draft Health tile | **No coaching** | Admin surface · industrial labels only |
| PM / HR / Safety dashboards | **No coaching** | Not affected by P0 incident |

---

## 5 · Localization

All coaching strings are wrapped in `useT()`/`t()` so the existing
Spanish localization layer can translate them. The Spanish doctrine
mirror lives in `/app/frontend/src/lib/i18n/es.json` — should be
added in a follow-up pass with the existing translation workflow.

For now, English defaults are doctrinally locked.

---

## 6 · Sign-off

- **Author:** E1 · iter442 P0/P1 field-trust pass
- **Status:** 🟢 Phrase book locked · regression-tested
- **Cross-refs:** `DRAFT_HEALTH_TILE_CERTIFICATION.md`,
  `DAILY_REPORT_DEVICE_MEMORY_MODEL.md`,
  `DAILY_REPORT_FIELD_TRUST_REVIEW.md`
