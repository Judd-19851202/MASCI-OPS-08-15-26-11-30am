# WP18CY Backup Policy and Freshness Contract

## Contract
1. Latest recoverable point must be **<= 60 minutes old**.
2. Backup alerting must reflect real artifact and restore truth.
3. A backup row is insufficient alone; archive, manifest/checksum, and restore evidence must agree.
4. Preview and production must be judged independently.

## Current Preview Status
| Measure | Observed | Contract | Result |
|---|---:|---:|---|
| Latest backup age | ~797.7 min | <=60 min | FAIL |
| Latest successful complete-r2 age | >4 days | <=60 min | FAIL |
| Latest restore drill outcome | ok | ok | PASS |
| Manifest/checksum sidecars for latest proven complete-r2 archive | present | present | PASS |

## Production Status
- **Unknown / unavailable in this run**.
