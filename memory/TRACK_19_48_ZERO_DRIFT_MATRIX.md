# TRACK 19.48 · Zero-Drift Matrix

## Schemas
| Change | Type | Zero-drift |
|---|---|---|
| No new MongoDB collections | — | ✅ |
| No new indexes | — | ✅ |
| No new fields on existing collections | — | ✅ |

## Routes
| Change | Type | Zero-drift |
|---|---|---|
| **NEW frontend route:** `/admin/operational-intelligence/recipients` (lazy, admin-gated) | additive | ✅ |
| No new backend routes — reuses Track 19.45A endpoints | — | ✅ |
| No POST/PATCH/DELETE added to the backend | — | ✅ |

## Emails
| Change | Type | Zero-drift |
|---|---|---|
| Zero email code paths introduced | — | ✅ |
| Recipient page cannot trigger a live send (grep-locked) | additive safety | ✅ |
| `fsi_send_email` untouched | — | ✅ |

## Scheduler
| Change | Type | Zero-drift |
|---|---|---|
| No scheduler changes | — | ✅ |
| No new cron | — | ✅ |

## Recipients
| Change | Type | Zero-drift |
|---|---|---|
| UI consumes existing Track 19.45A recipient CRUD endpoints | additive UI | ✅ |
| No second recipient system — lock test asserts exactly one `recipients*.py` module in the engine | grep-locked | ✅ |

## Audit
| Change | Type | Zero-drift |
|---|---|---|
| Every mutation continues to write to `operational_intelligence_audit` via existing engine | — | ✅ |
| No new audit collection | — | ✅ |

## Rollback
Revert `App.js` (route + lazy import) · delete
`AdminOperationalIntelligenceRecipients.jsx` · revert Cockpit
"Manage Recipients →" link (search-replace the entry block back to the
"deferred" copy) · delete lock test · delete 5 Track 19.48 docs. **No
backend revert required.** No schema migration. Rollback risk: HIGH.
