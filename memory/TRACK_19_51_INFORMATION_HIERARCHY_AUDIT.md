# TRACK 19.51 · Information Hierarchy Audit

For each portal home: top-3 signals the user actually needs vs top-3 signals currently shown above the fold.

| Portal | User needs (top 3) | Currently shows (top 3) | Mismatch |
|---|---|---|:-:|
| OI Cockpit | Corporate score · worst product · failures | Corporate score · worst product · failures | ✅ zero |
| OI Recipients | Total · active · groups | Total · active · inactive | ✅ ok |
| Admin v1 | System health · pending actions · integration failures | Tile grid (34 tiles) | ❌ major |
| Admin v2 | System health · pending actions · integration failures | Section sidebar | ⚠️ partial |
| Safety | Overdue CAPAs · new incidents · attention cases | Nav tiles | ❌ major |
| HR | Expiring certs · onboarding · terminations | Employee search · nav tiles | ❌ major |
| PM Hub | Missing daily reports · project attention · constraints | Nav tiles | ❌ major |
| PM Command Center | Missing daily reports · project attention · constraints | ~matches | ✅ ok |
| Shop | Safety holds · aging critical defects · OOS units | Nav tiles + counts | ❌ major |
| Dispatch V2 | Today's schedule conflicts · driver quals · vehicle OOS | ~matches | ✅ ok |
| Fleet | Active holds · critical defects · availability | Data table | ⚠️ partial |
| Field | Today's assignments · safety cards due · trench inspections due | Tile launcher | ⚠️ partial |
| Guidance | My-role workflow (contextual) | Feature list | ❌ major |

## Fix pattern
Every ❌ major maps to a P1 in the Remediation Roadmap. The pattern is the same everywhere: **add an Attention Strip driven by the relevant Operational Intelligence product's summary**. Zero new backend. Zero new score models. Reuse the OI engine.
