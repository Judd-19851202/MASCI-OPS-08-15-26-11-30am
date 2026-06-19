# TRACK 15.41 · Field Preservation Matrix

**Date:** 2026-06-19
**Track:** 15.41 · Phase 1 · Field Preservation Audit (CRITICAL DIRECTIVE #1)
**Status:** 🟢 PASS — every operational field preserved across all 6 PDFs

> Rule (operator-set, non-negotiable):
> **AFTER PDF TEXT MUST BE A SUPERSET OF BEFORE PDF TEXT.**
>
> Verified by `scripts/track_15_41_pdf_compare.py` (extracts text via
> pdfminer.six, hashes each non-empty stripped line into a fingerprint
> set, asserts `before ⊆ after`).

---

## 1 · Final verdict

| # | PDF type | BEFORE lines | AFTER lines | Missing | Verdict |
|---|---|---:|---:|---:|---|
| 1 | Safety Meeting           | 66 | 83 | **0** | 🟢 PASS |
| 2 | Daily Report             | 56 | 74 | **0** | 🟢 PASS |
| 3 | JHA                      | 40 | 57 | **0** | 🟢 PASS |
| 4 | Equipment Issuance       | 54 | 69 | **0** | 🟢 PASS |
| 5 | Equipment Return         | 39 | 55 | **0** | 🟢 PASS |
| 6 | Training Acknowledgement | 42 | 57 | **0** | 🟢 PASS |

**Total:** 297 operational lines BEFORE · 395 lines AFTER · **0 missing**.

The 98-line growth is entirely the **additive** foundation chrome:
metadata block (~5 lines per PDF) + audit block (~12 lines per PDF) +
optional fields the audit block surfaces.

---

## 2 · CRITICAL DIRECTIVE #6 — Safety Meeting & Daily Report deep audit

These two PDFs previously suffered field-loss risk and were therefore
audited line-by-line.

### 2.1 · Safety Meeting (`pdf_render._render_meeting`)

| Field group | BEFORE coverage | AFTER coverage | Notes |
|---|---|---|---|
| Topic + topic category   | ✓ | ✓ | Render path unchanged. |
| Meeting date + time      | ✓ | ✓ | `_fmt_date`, `_fmt_time_12h` unchanged. |
| Project name + number    | ✓ | ✓ | Top meta-line + NEW metadata block both surface project#. |
| Conducted by             | ✓ | ✓ | |
| Conductor signature      | ✓ | ✓ | `_signature(...)` flow unchanged. |
| Discussion notes         | ✓ | ✓ | Rich text passes through `_render_meeting`. |
| Hazards reviewed         | ✓ | ✓ | |
| References cited         | ✓ | ✓ | |
| Action items             | ✓ | ✓ | |
| Attendees (every row)    | ✓ | ✓ | `_render_meeting_attendee_rows`. |
| Attendee signatures      | ✓ | ✓ | Embedded data URIs intact. |
| Photos                   | ✓ | ✓ | `_photos_block` + `_resolve_photo_ref` unchanged. |
| GPS lat/lng + accuracy   | ✓ | ✓ | Surfaces if present. |
| Submit language          | ✓ | ✓ | |
| Doc ID + canonical ref   | ✓ | ✓ | Plus NEW audit block restates it. |
| Last-page legal          | ✓ | ✓ | Bottom-of-body unchanged. |
| @bottom-left tagline     | ✓ | ✓ | Existing @page CSS untouched. |
| @bottom-right Page X of Y | ✓ | ✓ | Existing @page CSS untouched. |
| **NEW** Audit block      | — | ✓ | Foundation v15.41.1. |
| **NEW** Metadata block   | — | ✓ | DocType · DocID · Project# · Generated · Env. |

### 2.2 · Daily Report (`pdf_render._render_daily`)

| Field group | BEFORE coverage | AFTER coverage | Notes |
|---|---|---|---|
| Weather                  | ✓ | ✓ | |
| Workforce                | ✓ | ✓ | Crew rows with start/stop/lunch math. |
| Equipment                | ✓ | ✓ | Excavation surface + asset usage. |
| Visitors                 | ✓ | ✓ | |
| Delays                   | ✓ | ✓ | |
| Quantities               | ✓ | ✓ | |
| Notes                    | ✓ | ✓ | |
| Photos                   | ✓ | ✓ | |
| Approvals + signatures   | ✓ | ✓ | |
| Project name + number    | ✓ | ✓ | |
| Report date              | ✓ | ✓ | |
| Doc ID + canonical ref   | ✓ | ✓ | |
| Executive summary card   | ✓ | ✓ | `_render_exec_summary_card`. |
| Wave-1C audit envelope footer (`Official Record · DR-... · sha256=... · rendered <utc>`) | ✓ | ✓ | Bottom-center @page CSS unchanged. |
| Last-page legal          | ✓ | ✓ | |
| @bottom-left tagline     | ✓ | ✓ | |
| @bottom-right Page X of Y | ✓ | ✓ | |
| **NEW** Audit block      | — | ✓ | Layered above last-page legal. |
| **NEW** Metadata block   | — | ✓ | |

Note: The Daily Report's existing **Wave-1C audit envelope footer**
(SHA-256 of canonical record JSON, rendered in @bottom-center @page
CSS) is preserved exactly. The Track 15.41 audit block is an
additional layer that captures FOUNDATION-level metadata (version,
environment, source module) without disturbing the legal-grade
content-hash footer.

### 2.3 · JHA, Issuance, Return, Training

Same additive pattern. Verified by superset comparison; 0 missing
fingerprints across all four. Detailed line-by-line breakdown is
captured in `/tmp/track_15_41/before/*.txt` vs
`/tmp/track_15_41/after/*.txt` (raw artifacts retained on the cert
container for re-verification at any time).

---

## 3 · Comparison script (`scripts/track_15_41_pdf_compare.py`)

```python
def _fingerprints(text: str) -> set[str]:
    """Stripped, non-empty lines, with moving-target artifacts
    filtered (ISO timestamps, sha256= rows, "Page N of M",
    "Generated 20...") so the comparison is content-level only."""
```

Filters applied (legitimate moving values, NOT operational data):
* Pagination artifacts (`Page N of M`)
* Generation timestamp lines (`Generated 20...`)
* Standalone ISO timestamps (`2026-06-19T14:12:09Z`) — used by DR
  audit footer (`rendered <utc>` slot)
* Standalone sha256 fragments — used by DR audit footer

Operational content is NOT filtered. Every field name, every value,
every signature label, every attendee line, every photo URL, every
section heading is required to appear verbatim in the AFTER text.

---

## 4 · Re-verification (any time)

```bash
cd /app/backend
python3 scripts/track_15_41_pdf_baseline.py before   # snapshot pre-state
# … make code changes …
python3 scripts/track_15_41_pdf_baseline.py after
python3 scripts/track_15_41_pdf_compare.py           # 🟢 PASS or 🔴 FAIL exit code
```

🟢 **Phase 1 field preservation complete. Zero field loss.**
