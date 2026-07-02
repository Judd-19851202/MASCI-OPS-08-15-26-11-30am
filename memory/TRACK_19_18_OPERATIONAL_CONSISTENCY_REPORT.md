# Track 19.18 · Operational Consistency Report

**Scope:** Compare Incident Report against Daily Report, Equipment Pre-Op, DVIR, and Safety Meeting for spacing, typography, buttons, navigation, review section, terminology, status chips, drawer behavior, progress philosophy, interaction model.

## Result

🟢 **Pass — no drift found.**

All operational workflows share the certified shell:

| Element | Contract |
|---|---|
| Layout shell | `FormShell` (Track 19.15 · locked) |
| Progress indicator | `ProgressRail` |
| Help surface | `HelpDrawer` |
| Review surface | `SubmitReviewPanel` |
| Presence enforcement | `PresenceGate` |
| Header layout | `Header` (Track 19.16 batch 1 · stabilised) |
| Job selector | `JobPicker` (Track 19.16 batch 1) |
| Employee selector | `EmployeePicker` (Track 19.16 batch 2) |
| Vehicle selector | `VehiclePicker` (Track 19.16 batch 2) |
| Equipment selector | `EquipmentPicker` (Track 19.16 batch 2) |
| Photo capture | `PhotoCaptureField` (Track 19.16 batch 2) |
| Weather | `/api/weather` open-meteo (Track 19.16 batch 1) |
| Bilingual toggle | Header `EN / ES` chip (persisted `masci.lang`) |
| Draft persistence | Local-first (`translation-on-submit` doctrine) |
| Submit gate | `SubmitReviewPanel` totalMissing===0 |
| Status chip style | `bg-slate-900 text-white px-2 py-0.5 font-mono` |
| Primary CTA style | `h-10 rounded-md bg-slate-900 text-white font-bold` |
| Danger CTA style | `bg-red-600 text-white` |
| Card style | `rounded-xl border-2 border-slate-300 bg-white p-4` |
| Kicker labels | `font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500` |
| Display headlines | `font-display font-black text-slate-900 tracking-tight` |

**Every screen** in the Safety Case Workspace, the Incident Report picker, the Incident Report flow, and the Incident Report Viewer uses those same tokens.

## Verified against reference workflows

| Workflow | Shell | Progress | Review | Status chip | Verdict |
|---|---|---|---|---|---|
| Daily Report | FormShell | ProgressRail | SubmitReviewPanel | ✓ | consistent |
| Equipment Pre-Op | FormShell | ProgressRail | SubmitReviewPanel | ✓ | consistent |
| DVIR | FormShell | ProgressRail | SubmitReviewPanel | ✓ | consistent |
| Safety Meeting | FormShell | ProgressRail | SubmitReviewPanel | ✓ | consistent |
| **Incident Report** | **FormShell** | **ProgressRail** | **SubmitReviewPanel** | **✓** | **consistent** |
| **Safety Case Workspace** | Case shell (post-submit workspace, not FormShell — appropriate: this is not a form) | tabs | inline actions | ✓ | consistent |

## Terminology parity

Across all workflows and the Incident Engine:

- **Job** (never "Project number" or "Contract" — locked in Track 19.16)
- **Reporter** (never "Submitter", never "Author")
- **Occurred at** (incident time) vs **Reported at** (form submitted)
- **State** (never "Status" for cases)
- **Health** / **Readiness** / **Completeness** (case metrics)
- **Blocker** (never "Warning" for missing prerequisites)
- **Corrective Action** (CAPA) — never "Action Item"
- **Root Cause** — never "Cause" or "Reason"

No drift found.

## Interaction model

Every operational workflow follows the same phased model:

1. **Identity confirm** (never re-type your name)
2. **Job pick** (auto-fills location, superintendent, client, PM)
3. **What happened / observation input**
4. **Evidence capture**
5. **Review**
6. **Submit → server storage, translation, notifications**

No workflow surprises the user by asking for context that another workflow already knows.

## Conclusion

Zero-drift preserved. All operational workflows share the same operational skeleton. The Incident Engine does not feel like a separate application — it feels like an extension of the operational platform.
