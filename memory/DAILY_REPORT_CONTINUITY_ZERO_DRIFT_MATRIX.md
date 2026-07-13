# Daily Report Continuity — Zero Drift Matrix

| Concern | Canonical identity used |
|---|---|
| Live draft key | `buildDailyReportScopedFormKey(data)` |
| Draft recovery lookup | `buildDailyReportScopedFormKey(data)` |
| Archive recovery | `buildDailyReportScopedFormKey(data)` |
| Idempotency key | `buildDailyReportScopedFormKey(data)` |
| Upload queue form key | `buildDailyReportScopedFormKey(data)` |
| Prior usage beacon | `buildDailyReportScopedFormKey(data)` |
| Telemetry form key | `buildDailyReportScopedFormKey(data)` |
| Draft owner | `getStableActorIdentity()` |
| Device support ID | `getDeviceId()` |
