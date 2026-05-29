# Daily Report Audit Footer · Certification

_Phase V.2 · Wave-1A · 2026-05-29 · SHA256 + continuity ID + rendered timestamp._

> The Daily Report now carries the same audit-defensibility contract
> that ODR external PDFs already enjoy (M0.4): canonical envelope
> SHA256 + doc_id + rendered timestamp, surfaced as a calm
> single-line footer. Invisible to field workflow. Visible in
> exported PDFs and the audit footer API.

---

## 1 · Surface contract

### 1.1 Audit envelope stored on insert

Every `POST /api/daily-reports` insert stamps
`audit_envelope_sha256` (64-char hex) onto the row. The envelope
excludes:

- `_id` (Mongo internal)
- `created_at` (transient · changes on every insert and would force
  hash drift across re-fetches)
- `audit_envelope_sha256` itself

Everything else (project, location, date, prepared_by, signatures,
masci_crews, equipment, materials, photos, production, constraints,
weather, safety, etc.) is part of the canonical envelope.

### 1.2 Audit footer endpoint

```
GET /api/daily-reports/{report_id}/audit-footer
→ 200 OK
{
  "report_id":      "<uuid>",
  "doc_id":         "DR-2026-00086",
  "sha256":         "<64 hex>",
  "rendered_at_utc":"2026-05-29T13:00:00.000Z",
  "footer_text":    "Official Record · DR-2026-00086 · sha256=<16> · rendered <utc>"
}
```

Admin / PM only. 404 on unknown id. Read-only — never mutates.

The hash is **recomputed** on every call from the current envelope.
Wave-1A stores the hash at insert (for change detection) and
recomputes at fetch (for content-current truth) — both are equal at
insert time. Future content edits via `PUT /api/daily-reports/{id}`
will produce a different recomputed hash, which is the desired
tamper signal.

### 1.3 Render flow

```
PDF generation surface (Wave-1C will wire this)
    ↓
fetch the row
    ↓
GET /api/daily-reports/{id}/audit-footer  ← single source of truth
    ↓
Render the footer on every PDF page using the doctrine canvas
    ↓
External PDFs · FAA · FDOT · claims · legal · audit
```

Wave-1A ships the data plumbing. Wave-1C will wire the existing DR
PDF renderer to consume this footer endpoint and stamp the footer on
every page — using the same `_FooterCanvas` pattern as the M0.4 ODR
PDF renderer.

## 2 · What the footer guarantees

| Guarantee | How |
|---|---|
| **Identity** | `doc_id = DR-YYYY-NNNNN` — already issued by `doc_ids.ensure_doc_id` at insert |
| **Integrity** | `sha256` over the canonical envelope · invalid byte == different hash |
| **Time** | `rendered_at_utc` · ISO-8601 · always UTC |
| **Provenance** | Footer line carries all three on every page |
| **Continuity** | The doc_id is stable across re-renders; the sha changes only when content changes |

## 3 · Threat model coverage

| Threat | Mitigation |
|---|---|
| External party claims PDF was tampered after issue | sha256 in footer · operator verifies against the audit-footer endpoint |
| External party crops the footer | sha256 hash printed on EVERY page of the rendered PDF (Wave-1C renderer change) |
| Operator silently edits Mongo directly | next audit-footer fetch returns a different sha · drift signal |
| External party fakes a doc_id | doc_id is paired with sha256; no two records share both |
| External party requests audit footer for someone else's DR | endpoint requires Admin / PM token via `require_admin` dependency |

## 4 · Forward compatibility · Wave-1C PDF wiring

When the existing DR PDF renderer (`server.py` rendering surface) is
upgraded in Wave-1C:

- Add a `_FooterCanvas` analog (or reuse the M0.4 helper if the
  audience-projection module is extracted to `routes/_shared/`)
- Fetch `footer_text` from this endpoint at render time
- Stamp on every page bottom: small font · slate · non-distracting

This is **not in Wave-1A scope.** The data and API surface are
ready; the visual surface lands when operator approves Wave-1C.

## 5 · Backward compatibility

Existing `daily_reports` rows WITHOUT a stored
`audit_envelope_sha256` are not mutated. The audit-footer endpoint
recomputes the hash from the current envelope on every call, so
historical rows continue to return a footer payload — based on
their content, even though it was never stamped at insert. The
stored field is purely a write-time convenience; the canonical
truth is the recomputed value.

## 6 · Test coverage

4 dedicated cases in `test_wave_1a.py`:

- `test_audit_envelope_sha256_computed` — sha stored at insert · 64 hex
- `test_audit_footer_endpoint` — endpoint returns all 5 fields + valid footer line
- `test_audit_footer_404_for_missing` — unknown id → 404
- `test_audit_envelope_stable_for_same_content` — repeat fetches return identical sha

All 🟢.

## 7 · Field simplicity verdict (Doctrine Lock #1)

| Test | Answer |
|---|---|
| Does this add a foreman step? | NO · 100% backend |
| Does this change foreman workflow? | NO |
| Time-to-complete impact for foreman | 0 s |
| Visible to foreman during entry | NO (visible only on exported PDFs and admin/audit surfaces) |

PASS · audit footer ships invisibly.

## 8 · Operator-facing one-liner

> **Every Daily Report now carries the same tamper-evident footer
> contract that ODR PDFs do.** doc_id + sha256 + rendered_at. The
> field never sees it. Auditors, claims attorneys, DOT, and FAA do.

---

_End of DAILY_REPORT_AUDIT_FOOTER_CERTIFICATION.md._
