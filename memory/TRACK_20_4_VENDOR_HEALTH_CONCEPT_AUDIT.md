# TRACK 20.4 · Vendor Operational Health Concept Audit

## Language (strict)
**Explanatory only.** No score. No compliance certification. No legal conclusion. Four buckets:
- **Excellent** — no outstanding issues.
- **Good** — 1 low-priority issue (e.g. document renewal within 60 days).
- **Attention Needed** — 2 – 3 issues (e.g. COI expiring soon + PO overdue receipt).
- **Restricted** — do-not-use flag set OR ≥ 4 issues OR expired COI (based on data).

## Signals (all from existing data or thin extension flags)
| Signal                                | Source                                                                       |
|---------------------------------------|------------------------------------------------------------------------------|
| W-9 missing                           | Vendor lane of Historical Records (post-extension)                           |
| COI expired / expiring in 30/60 days  | Vendor-lane document metadata + `document_expirations`                       |
| Contract expired                      | Same                                                                          |
| No approved agreement                 | Vendor lane document count                                                    |
| PO bottleneck (overdue receipts)      | `/api/po-requests/summary` filtered by supplier                              |
| Safety issue linked                    | `incident_cases` cross-links with `involved_party=<supplier>`                |
| Do-not-use flag                       | New boolean on `suppliers` document (extension)                              |
| Inactive status                        | `suppliers.is_active`                                                        |
| Missing contact                       | Contact record extension (optional later)                                    |
| Unresolved invoice issue              | Deferred — no invoice collection today                                        |

## Rendering rules
1. Every bucket must be paired with a plain-English **"Why: …"** narration (same pattern as the other threads).
2. Never display a percentage.
3. Never display a compliance-percent-complete meter.
4. Never make a legal-defensibility claim.
5. **"Restricted" is a hard visual cue** — always warn PM / Safety / Shop before they act on the vendor.

## Zero-drift guarantee
Operational Health for vendors is a **client-side pure function** over 3–4 fields. Zero new score model. Zero new backend engine. Zero new OI product. Identical philosophy to the Track 19.58 "Evidence Readiness" rule.
