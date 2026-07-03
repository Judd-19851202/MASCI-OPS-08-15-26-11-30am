# TRACK 20.4 · Safety · Compliance Relationship Audit

## Existing safety-adjacent vendor signals
| Signal                             | Source                                                                | Notes                                                    |
|------------------------------------|-----------------------------------------------------------------------|----------------------------------------------------------|
| Vendor incident linkage            | `incident_cases.involved_parties` + `cross_links`                     | Weak — populated only when investigators mark it         |
| Carrier compliance (subset)        | `transport_docs.insurance_certificate` + `w9` + `hauling_agreement`   | Carrier-only; NOT general vendor                         |
| Prequalification                    | *(not stored today)*                                                  | Gap                                                      |
| Approved-vendor flag                | `suppliers.is_active` (weak proxy)                                    | Partial                                                  |
| Do-not-use flag                    | *(not stored today)*                                                  | Gap                                                      |
| Jobsite access                      | *(implied via approval; not stored)*                                 | Gap                                                      |
| Safety meeting attendance by vendor | `safety_meetings` free-text attendees                                 | Weak — no FK                                             |
| JHA / toolbox / OSHA docs by vendor | Historical Records (once vendor lane exists)                          | Future state                                             |

## What Safety needs to see on the Vendor Thread
- COI status + expiration (from a new supplier field OR from vendor-lane document metadata)
- Prequalification status (future field)
- Incidents cross-linked to this vendor (via `incident_cases` cross-link query)
- Any Safety notes uploaded to the vendor lane of Historical Records

## What Safety must NOT see
- Contract value.
- Payment terms.
- Tax ID.
- Attorney work product.

## What Safety must NOT do (through the thread)
- Approve or reject the vendor master status. Safety can only **flag** an issue — HR/Admin actions the flag.

## Compliance guardrails
- **No OSHA compliance conclusions rendered.**
- **No legal-defensibility claim rendered.**
- **No automated blocking of vendor usage** — Safety flags do not automatically restrict PO creation. That remains a manual HR/Admin decision.

## Verdict
Enough existing safety signal exists to render an honest Attention slot for vendors. Missing prequalification / do-not-use flags should be added by Track 19.60 as **small additions to the `suppliers` document** (boolean flags · nullable string with reason). No new safety collection is required.
