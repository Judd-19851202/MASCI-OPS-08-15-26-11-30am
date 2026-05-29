# Section 03 Cleanup — Certification

_Phase V.2 · Daily Report Field-Logic · 2026-05-29 · supplemental._

## Issue
When `schedule_delays === "Yes"` was selected in Section 03, the legacy free-text **"Detail any 'Yes' answers"** amber box still rendered alongside the new structured Delays / Extra Work card. This forced foremen to enter the same delay information twice — once in narrative and once in structured rows.

## Fix
Trigger condition for the legacy detail box in `NewDailyReport.jsx` Section 03:

```diff
- {(data.schedule_delays === "Yes" ||
-   data.weather_impact === "Yes" ||
-   data.safety_incidents_today === "Yes" ||
-   data.injuries_reported === "Yes") && (
+ {(data.weather_impact === "Yes" ||
+   data.safety_incidents_today === "Yes" ||
+   data.injuries_reported === "Yes") && (
```

Placeholder copy updated:
- _"Describe delays, weather impact, accidents, injuries..."_ → _"Describe weather impact, accidents, injuries…"_

## Behavior matrix
| Section 03 flags | Legacy "Detail any 'Yes' answers" box | Delays card amber-required pill | Submit gate |
|---|---|---|---|
| Delays YES · all others NO | ❌ hidden | 🟡 amber | blocks until ≥1 delay row |
| Weather YES · others NO | ✅ shown | slate | unchanged |
| Accident YES · others NO | ✅ shown | slate | unchanged |
| Injury YES · others NO | ✅ shown | slate | unchanged |
| Delays YES + Weather YES | ✅ shown (because of weather) | 🟡 amber | blocks until ≥1 delay row |

## Backend compatibility
- `incident_notes` field stays on the schema — old reports rendering the legacy box continue to display their stored text.
- No migration. No data deletion. No schema change.
- General Notes textarea (Section 03 bottom) remains unchanged for general comments.

## Verification
| Probe | Result |
|---|---|
| Delays YES only → legacy detail box hidden | 🟢 |
| Weather YES → legacy detail box appears | 🟢 |
| Both YES → legacy detail box appears (one-time, not duplicated) | 🟢 |
| Delay rows still required when Delays YES | 🟢 |
| 89/89 ODR tests | 🟢 |

🛑 Stop after this cleanup as directed.

_End of SECTION_03_CLEANUP_CERTIFICATION.md._
