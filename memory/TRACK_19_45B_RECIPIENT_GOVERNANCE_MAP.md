# TRACK 19.45B · Recipient Governance Map

Track 19.45A shipped the universal recipient engine. Track 19.45B
declares recipient group mapping for the two new products without
introducing new infrastructure.

## Shop Intelligence · recipient groups
| Group | Purpose |
|---|---|
| `shop` | Shop manager · mechanics · parts coordinator |
| `fleet` | Fleet ops · asset admins |
| `operations` | Field ops leadership |
| `safety` | Safety team (safety hold visibility) |
| `executive_leadership` | Executive rollup context |
| `custom` | Ad-hoc recipient list |

## Corporate Intelligence · recipient groups
| Group | Purpose |
|---|---|
| `executive_leadership` | C-suite · principals |
| `operations` | VP Ops · Directors |
| `corporate` | Corporate services team |
| `admin` | Platform admins (audit / verification) |
| `custom` | Ad-hoc recipient list |

## Governance rules
- **No hardcoded individuals** — every recipient is stored in the
  `morning_digest_recipients` collection (per-row `digest_type`) or the
  `operational_recipient_groups` collection.
- **All recipient CRUD flows through Track 19.45A** admin-only endpoints
  (`/api/operational-intelligence/recipients*` and `/groups*`).
- **Soft delete only** — deactivation preferred over hard delete for
  regulatory replay.
- **Audit trail** — every recipient mutation lands in
  `operational_intelligence_audit`.

## Zero drift
No new recipient collections. No new admin panel. No new recipient
management endpoints. Track 19.45B adds only the group taxonomy
documented above.
