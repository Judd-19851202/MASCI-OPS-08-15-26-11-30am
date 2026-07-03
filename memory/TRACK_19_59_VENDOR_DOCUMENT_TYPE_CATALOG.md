# TRACK 19.59 · Vendor Document Type Catalog

15 human-readable slugs. No legal conclusions. No compliance-ready wording. No OSHA-ready wording. No "approved to use" phrasing.

| Slug                        | Human label                       | Notes                                          |
|-----------------------------|-----------------------------------|------------------------------------------------|
| `w9`                        | W-9                               | US tax reporting form                          |
| `certificate_of_insurance`  | Certificate of Insurance / COI    | Insurance evidence                             |
| `contract_agreement`        | Contract / Agreement              | Master vendor agreement                        |
| `subcontract`               | Subcontract                        | Project-specific subcontract agreement         |
| `rental_agreement`          | Rental Agreement                   | Equipment / space rental                       |
| `service_agreement`         | Service Agreement                  | Service / maintenance agreement                |
| `business_license`          | Business License                   | State / municipal license                      |
| `prequalification`          | Prequalification                   | Prequalification packet                        |
| `vendor_packet`             | Vendor Packet                      | Onboarding packet                              |
| `quote_proposal`            | Quote / Proposal                   | Bid / quote / proposal                         |
| `pricing_sheet`             | Pricing Sheet                      | Rate card / pricing schedule                   |
| `safety_document`           | Safety Document                    | Safety-adjacent document                       |
| `material_certification`    | Material Certification             | Vendor-specific mill / lab certification        |
| `correspondence`            | Correspondence                     | Letters / notes                                |
| `other_vendor_document`     | Other Vendor Document              | Catch-all — never left as the only tag         |

## Additive by design
`LANE_RECORD_TYPES["vendor"]` may be safely appended in future tracks. Removing or reordering slugs would break existing records — do not do so without a migration.

## Explicit prohibitions
- No `approved_to_use` — approval status is a separate field.
- No `osha_ready` — the platform never certifies OSHA readiness.
- No `compliance_ready` — no compliance certification.
- No `legally_defensible` — no legal conclusion.
- No `court_ready` — no litigation claim.
