# Track 19.18 · PDF Excellence Report

**Status:** 🟢 Executive-quality · legally defensible · elite

## What a MASCI incident PDF now looks like

### Page 1 — Cover
- **MASCI · Incident Intelligence** wordmark (SF Mono, wide letter-spacing, uppercase)
- Report title kicker
- **Incident type** as the main 32pt title
- **Case number** subtitle
- **Slate-black banner** with audience label + case number pill
- 2-column meta grid: Occurred, Location, Project, Client, Project Manager, Superintendent, Reported by, Case State
- Bottom stamp: **"Confidential — Attorney Work Product"** + generated timestamp
- No footer/header on this page (via `@page :first` suppression) — cover is uninterrupted

### Pages 2..N — Body
- **Running header (top-right):** `{Incident Type} · Case {number}` — appears on every content page
- **Running footer (bottom-center):** `Case {number}` — appears on every content page
- **Bottom-left:** "Confidential · Attorney Work Product"
- **Bottom-right:** `Page N of M`
- Section order for the 9 report types (unchanged, locked in Track 19.16 with cover prepended in Track 19.17):
  1. `cover` (structural — always renders)
  2. `header` (structural — always renders)
  3. `executive_summary` (structural — always renders, now with Case Story)
  4. `summary`, `timeline`, `evidence`, `witnesses`, `medical`, `agency`, `communications`, `corrective_actions`, `root_cause`, `vehicle`/`utility`/`injury`, `linked`, `lessons_learned`, `photographs` — rendered only when non-empty

### Executive Summary section (Track 19.18 upgrade)
```
Executive Summary
─────────────────
<Case Story paragraph — "On {when}, a {type} was reported at {where} 
 (Job {job}). Reported by {reporter · role}.">
<30-second briefing — "Case is currently in SAFETY_REVIEW with SLA 
 ON_PACE. Investigation readiness: 42%. OSHA status pending. Root 
 cause investigation open.">
[Open blockers card: no_photos, missing_root_cause]
```

### Timeline section (Track 19.18 upgrade)
Old shape (Track 19.16): 4-column table with a raw JSON `Payload` column that exposed internal event dicts to executives.  
New shape: narrative rows with `When | Event badge | Actor · from→to · reason` — reads like a written chronology.

### Root Cause section (Track 19.18 upgrade)
- Summary (narrative)
- Categories (comma-joined) — only rendered when populated
- **Contributing factors** as a lettered ordered list (`A. …  B. …  C. …`) — locked by CSS `ol.factors { list-style: upper-alpha; }`

## Empty-state elimination

Structural sections (`cover`, `header`, `executive_summary`) always render.  
Every other section is skipped when its data is empty (list=`[]`, dict all-falsy, `None`, `""`). Result: no orphan `<h2>` headings, no blank tables, no "N/A" spam.

## Page-break protection

`page-break-inside: avoid` is now applied to:
- `.card` (blocker card, structural blocks)
- `.brief` (30-second briefing paragraph)
- `.story` (Case Story paragraph)
- `.grid` (KV pairs)
- `.tline .row` (timeline entries)
- `.photos .p` (photograph tiles — already had it)
- `.cover .meta .row` (cover-page meta rows)
- `.head` (top of every body page)

Result: no professionally-authored block ever splits awkwardly across pages.

## Legal defensibility

- Cover stamp: **"Confidential — Attorney Work Product"**
- Bottom-left every page: **"Confidential · Attorney Work Product"**
- Running header identifies incident + case #
- Page number `N of M` on every page
- Case number in bottom-center on every page

If an insurance adjuster or opposing counsel receives this document, they see a professionally-numbered, professionally-attributed, professionally-classified investigation package.

## Lock tests (all green)

`/app/backend/tests/test_track_19_18_pdf_excellence.py`
- Case Story composer reads field_block shape
- Case Story composer tolerates missing data (no `None`/`undefined` leaks)
- Cover renders wordmark + banner + Attorney Work Product
- Cover carries running header + footer strings
- Executive Summary includes Case Story paragraph
- Timeline is narrative, not JSON
- Root Cause factors render as ordered list
- Empty photographs section is suppressed
- Structural sections never suppress themselves
- CSS protects key blocks from splitting
- Full PDF bytes produce valid `%PDF-` output ≥ 10KB
