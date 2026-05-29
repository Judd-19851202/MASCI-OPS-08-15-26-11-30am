# PDF Audit Footer Render · Certification

_Phase V.2 · Wave-1C · 2026-05-29 · canonical footer on every page of every DR PDF._

> Daily Report PDFs now carry the same tamper-evident audit footer
> contract that ODR PDFs already do (M0.2 + M0.4). **Invisible to
> field workflow. Visible to FAA · FDOT · CEI · Owner · Legal ·
> Claims.**

---

## 1 · What renders

On every page of every Daily Report PDF (regardless of audience),
the WeasyPrint `@page { @bottom-center }` slot now paints:

```
Official Record · DR-YYYY-NNNNN · sha256=<16 hex> · rendered <UTC>
```

| Element | Source |
|---|---|
| `Official Record` | literal · constant marker |
| `DR-YYYY-NNNNN` | `record["doc_id"]` (stamped at insert by `doc_ids.ensure_doc_id`) |
| `sha256=<16 hex>` | first 16 chars of `_compute_audit_envelope_sha256(record)` |
| `rendered <UTC>` | `datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")` |

## 2 · CSS contract (locked)

```css
@page {
  @bottom-center {
    content: "Official Record · DR-... · sha256=... · rendered <utc>";
    font-family: 'Courier New', monospace;
    font-size: 7pt;
    letter-spacing: 0.12em;
    color: #334155;
    font-weight: normal;
  }
}
```

- **Monospace** — claims-friendly · easy to verify hash characters
- **7pt** — visible but never dominant
- **slate-700 `#334155`** — calm · not red · not alarming
- **`letter-spacing: 0.12em`** — improves hash readability under glare
- **Centered** — symmetric to the existing `@bottom-left` (copyright)
  and `@bottom-right` (page number) slots

## 3 · Audience contract

The footer renders identically on all DR PDFs, regardless of
audience (internal / external / executive). That is **correct**:

| Field in footer | Sensitive? | Render externally? |
|---|---|---|
| `Official Record` | no | ✅ |
| `doc_id` (DR-YYYY-NNNNN) | no — just an identifier | ✅ |
| `sha256` (first 16 hex) | no — purely cryptographic proof | ✅ |
| `rendered <UTC>` | no | ✅ |

No PII. No internal identifiers. No advisory flags. No project
costs. **The footer is the audit-and-integrity contract, not
telemetry.**

## 4 · Failure mode

If any component of the footer compute fails (e.g. the hash helper
import raises), the inner `try/except` swallows the error and the
PDF renders **without** the footer rather than failing. The
operator preference is unanimous on this: a Daily Report PDF
without a footer is operationally fine; a Daily Report PDF that
crashes mid-render is not.

The error is logged via the standard backend log stream so any
silent footer absence is observable in operations.

## 5 · Hash stability invariant

Re-rendering the same record yields the same hash. Verified by:

```python
# tests/odr/test_wave_1bc.py::test_dr_pdf_renders_with_audit_footer
sha1 = _compute_audit_envelope_sha256(record)
sha2 = _compute_audit_envelope_sha256(record)
assert sha1 == sha2
```

Hash drift between renders = content drift = tamper signal.

## 6 · External-party verification flow

> An external auditor downloads `DR-2026-00092.pdf`. They read the
> footer:
>
> `Official Record · DR-2026-00092 · sha256=a3f9c2b14d7e0f81 · rendered 2026-05-29T17:34:18Z`
>
> They call:
>
> `GET /api/daily-reports/<id>/audit-footer`
>
> They compare the `sha256` field's first 16 chars to the footer.
> Match = integrity confirmed. Mismatch = tampering.

The verification flow uses **only the public footer endpoint** —
no proprietary tooling required.

## 7 · Test coverage

| Test | Result |
|---|---|
| `test_dr_pdf_renders_with_audit_footer` (renderer exit path · sha stability) | 🟢 |
| `test_dr_audit_footer_endpoint_still_returns_canonical_payload` | 🟢 |
| `test_audit_envelope_sha256_computed` (Wave-1A) | 🟢 |
| `test_audit_envelope_stable_for_same_content` (Wave-1A) | 🟢 |

## 8 · Doctrine alignment

| Doctrine | Status |
|---|---|
| Doctrine Lock #1 | ✅ no foreman impact · invisible during entry |
| Doctrine Lock #2 | ✅ inherits WeasyPrint stack + footer slot used by other PDF kinds |
| Audience Projection | ✅ footer is universal · no audience-specific stripping needed |
| Operational Calmness | ✅ slate · monospace · 7pt · centered |
| PDF SHA / Audit Footer Doctrine (ODR M0.2/M0.4) | ✅ same contract surface · same hash family |

## 9 · Operator-facing one-liner

> **Every page of every Daily Report PDF now carries `doc_id +
> sha256 + rendered`.** Foremen never see it. Auditors verify it
> in one HTTP call.

---

_End of PDF_AUDIT_FOOTER_RENDER_CERTIFICATION.md._
