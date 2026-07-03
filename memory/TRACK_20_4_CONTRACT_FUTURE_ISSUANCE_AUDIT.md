# TRACK 20.4 · Contract Future Issuance Audit

## Current state
- No dedicated contract collection.
- No contract templates.
- No contract PDF renderer.
- No signature workflow.
- No draft / review / send / execute pipeline.
- No renewal tracking.
- Contract-adjacent artefacts today: PO Requests (`po_requests`), carrier hauling agreements (`transport_docs.hauling_agreement`), employee-onboarding docs (`employee_documents`).

## Future-state need (per mandate)
The Vendor Thread must eventually support:
1. Contract draft
2. Review
3. Approval
4. Send to vendor
5. Signature capture
6. Executed upload
7. Renewal tracking
8. Project linkage
9. PO linkage
10. Audit

## Reuse audit
| Future capability          | Can reuse                                                                 | Must build later                                    |
|----------------------------|---------------------------------------------------------------------------|-----------------------------------------------------|
| Contract draft             | ❌ No draft engine today                                                  | ✅ Small template/draft engine (later)              |
| Review workflow            | ✅ Reuse Historical Records approval queue pattern (entity_kind="vendor") | Adapter only                                        |
| Approval                   | ✅ Reuse HR/Admin approval envelope                                       | Adapter only                                        |
| Send                       | ❌ Not today                                                              | Later — reuse existing email routing envelope        |
| Signature                  | ❌ Not today                                                              | Later — integrate a signing provider                |
| Executed PDF upload        | ✅ Reuse Historical Records upload                                        | Adapter only                                        |
| Renewal tracking           | ✅ Reuse `document_expirations` generic tracker                            | Adapter only                                        |
| Project linkage            | ✅ Reuse `po_requests.project_number` pattern                              | Adapter only                                        |
| PO linkage                 | ✅ Reuse existing PO record                                                | Adapter only                                        |
| Audit                      | ✅ Reuse `historical_records_audit`                                       | Adapter only                                        |

## Verdict
🟢 **Do not build contract issuance now.** In Track 19.60, contracts are treated as **stored documents in the vendor lane of Historical Records Intake** — a fully certified path that answers the mandate's near-term need ("W-9 · COI · contracts · insurance · business license · quotes · proposals · invoices · correspondence · safety docs · compliance docs · material certifications · historical paper files"). Full signing/renewal automation is deferred to a dedicated later track (proposed Track 19.7x) when the underlying signing integration is chosen.
