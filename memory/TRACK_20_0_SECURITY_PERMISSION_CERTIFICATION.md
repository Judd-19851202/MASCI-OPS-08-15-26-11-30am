# TRACK 20.0 · Security & Permission Certification

## Auth gates verified
| Portal / route family                    | Gate              | Notes                                            |
|------------------------------------------|-------------------|--------------------------------------------------|
| `/admin/*`                               | Admin token       | Route wrapper `H(...)` / `A(...)` in `App.js`.   |
| `/safety-portal/*`                       | Safety or Admin   | `require_safety_or_admin` on OI preview / dispatch endpoints. |
| `/shop/*`, `/shop/units/:unit/history`   | Shop or Admin     | `RequireShop` wrapper.                           |
| `/hr/*`                                  | HR or Admin       | `H(...)` HR portal wrapper.                      |
| `/pm/*`                                  | PM or Admin       | PM wrapper.                                      |
| `/dispatch-portal/*`                     | Dispatch or Admin | `DP(...)` dispatch portal wrapper.               |
| `/fleet/unit/:unit_number`               | Shop (existing)   | Reuses `S(...)` from Fleet Visibility path — no new gate. |
| `/operational-intelligence/summary`      | Admin token       | `require_admin` dependency in `routes.py`.       |
| `/operational-intelligence/history*`     | Admin token       | Same.                                            |
| `/operational-intelligence/audit*`       | Admin token       | Same.                                            |
| `/operational-intelligence/preview`      | Safety or Admin   | `require_safety_or_admin`.                       |
| `/operational-intelligence/dispatch`     | Safety or Admin + dry-run default | Dispatch requires `dry_run=true` by default. |
| Recipient management                     | Admin token       | Track 19.45A / 19.48 governance intact.          |

## No privilege escalation
- The Guidance Card, Attention Strip, and Thread page are **read-only** consumers of already-gated endpoints.
- `OiAttentionStrip` sends `X-Admin-Token`. Non-admin users receive an honest empty state ("Admin token required to view OI signals · request access from your administrator.") — never fabricated data.
- Fleet Unit Thread reads only the certified Track 13.26 backbone endpoint (already gated) plus the admin-only OI summary — non-admins see the timeline but the OI Section 8 / Section 3 Guidance Card degrade gracefully.

## No information leakage
- Empty states never contain real data leaked from other tenants — they are static strings only.
- Timeline / relationship / audit sections show honest empty states rather than "unknown user" placeholders that could leak IDs.

## No unauthorised writes
Lock tests enforce:
- `test_oi_attention_strip_no_new_backend` — no POST/PUT/PATCH/DELETE in the strip.
- `test_guidance_card_no_writes` — no POST/PUT/PATCH/DELETE in the Guidance Card.
- `test_fleet_pilot_consumes_only_existing_endpoints` — same for the Fleet pilot.
- `test_thread_page_no_fetch` — the shared shell doesn't even talk to the network.
- `test_relationship_graph_read_only` — the graph doesn't fetch.

## Recipient governance intact
- Track 19.45A / 19.48 / 19.49 recipient + group management remains the sole path for wiring who receives OI digests.
- No email sent from any Track 19.51 → 20.0 code path.
- Dispatch endpoint still defaults to `dry_run=true`.

## Verdict
🟢 **Security posture unchanged from Track 19.50 certification.** All
new UI is read-only consumers of already-gated endpoints. Zero drift.
