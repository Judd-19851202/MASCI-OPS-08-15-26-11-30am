# TRACK 19.47 · Zero-Drift Matrix

## Schemas
| Change | Type | Zero-drift impact |
|---|---|---|
| No new MongoDB collections | — | ✅ |
| No new indexes | — | ✅ |
| No new fields on existing collections | — | ✅ |

## Routes
| Change | Type | Zero-drift impact |
|---|---|---|
| **NEW read-only backend:** `GET /api/operational-intelligence/summary` | additive · GET only · admin_only | ✅ |
| **NEW frontend route:** `/admin/operational-intelligence` (lazy) | additive · admin-gated | ✅ |
| No POST/PATCH/DELETE added anywhere | — | ✅ |

## Emails
| Change | Type | Zero-drift impact |
|---|---|---|
| Cockpit dry-run button uses shared `POST /{id}/dispatch?dry_run=true` — no new email path | — | ✅ |
| Cockpit does not surface a live-send button | grep-locked | ✅ |

## Scheduler
| Change | Type | Zero-drift impact |
|---|---|---|
| No new scheduler | — | ✅ |
| No new cron job | — | ✅ |

## Recipients
| Change | Type | Zero-drift impact |
|---|---|---|
| Cockpit links to existing Track 19.45A recipient/group JSON endpoints | additive doc entry | ✅ |
| No new recipient collection | — | ✅ |
| No new recipient CRUD UI in this track (deferred to future track) | — | ✅ |

## Audit / history / dedupe
| Change | Type | Zero-drift impact |
|---|---|---|
| Cockpit consumes existing `/history` + `/audit` endpoints | — | ✅ |
| Audit rows still stripped of `token`/`secret`/`password`/`api_key` at the API layer | — | ✅ |
| Cockpit adds a second defence-in-depth layer by rendering only a small allow-list of columns | additive safety | ✅ |

## Score / trend
| Change | Type | Zero-drift impact |
|---|---|---|
| Cockpit renders backend-supplied score fields only — no local computation | — | ✅ |
| No new score model | — | ✅ |
| No new trend engine | — | ✅ |

## Rollback
Revert `routes.py` (remove `/summary` endpoint block) · revert
`App.js` (remove lazy import + route) · revert `AdminShell.jsx`
(remove nav entry) · delete `AdminOperationalIntelligence.jsx` ·
delete `test_track_19_47_cockpit_and_summary.py` · delete 9
Track 19.47 docs. Rollback risk: **HIGH** (clean · no schema touched ·
no user-visible dependencies from other pages).
