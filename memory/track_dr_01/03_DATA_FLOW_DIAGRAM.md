# Data Flow Diagram

Date: 2026-07-14
Track: DR-01

## 1. Current production-like flow map

```mermaid
flowchart TD
    A[/daily/new or /daily/submit/] --> B[DailyReportRouter]
    B -->|flag off| C[NewDailyReport V1]
    B -->|flag on| D[NewDailyReportV3]

    C --> C1[buildDailyReportDefaults]
    C --> C2[useFormDraft]
    C --> C3[crewMemory.js]
    C --> C4[/jobs/{project}/recent-context]
    C --> C5[enqueueUpload / scoped idempotency]
    C --> E[POST /api/daily-reports]

    D --> D1[buildDailyReportDefaults]
    D --> D2[useFormDraft]
    D --> D3[crewMemory.js only]
    D --> D4[unscoped idempotency]
    D --> D5[enqueueUpload formKey=daily-report]
    D --> E[POST /api/daily-reports]

    C2 --> F[draftStore.js / IndexedDB]
    D2 --> F
    C2 --> G[draftTelemetry.js]
    D2 --> G
    G --> H[POST /api/draft-telemetry]
    H --> I[(draft_telemetry)]

    C4 --> J[server.py recent-context]
    J --> K[(daily_reports)]

    E --> K[(daily_reports)]
    E --> L[ODS / photo intelligence / trust spine / email side effects]

    M[Legacy V2 shell not routed] --> N[/api/dr-v2/*]
    N --> O[(dr_v2_* / daily_report_* compat collections)]
```

## 2. Current drift hotspots

### 2.1 Draft identity split
- V1 draft base key: `daily-report-new`
- V3 draft base key: `daily-report`
- V1 scope helper: `project::date::report_number`
- V3 scope helper: `project::date`

Result: the same operator journey can move across different draft keys depending on shell and timing.

### 2.2 Smart Prefill split
- Backend source exists once: `/jobs/{project_number}/recent-context`
- V1 consumes it
- V3 does not
- V1 also duplicates the prefill UI path internally

### 2.3 Legacy V2 persistence split
- V2 draft/AI/PDF subsystem persists outside `daily_reports`
- compatibility layer proves migration is incomplete / dual-path aware

## 3. Canonical data-flow target (planning recommendation)

```mermaid
flowchart TD
    A1[/daily/new or /daily/submit/] --> B1[One canonical Daily Report shell]
    B1 --> C1[buildDailyReportDefaults]
    B1 --> C2[One shared useFormDraft contract]
    B1 --> C3[crewMemory.js explicit local setup only]
    B1 --> C4[/jobs/{project}/recent-context explicit Smart Prefill]
    B1 --> C5[One scoped idempotency + queue contract]
    B1 --> D1[POST /api/daily-reports]
    C2 --> E1[draftStore.js]
    C2 --> E2[draftTelemetry.js]
    E2 --> E3[(draft_telemetry)]
    C4 --> F1[server.py recent-context]
    F1 --> G1[(daily_reports)]
    D1 --> G1[(daily_reports)]
    D1 --> H1[ODS / photo intelligence / trust spine / lifecycle]
    I1[Legacy V2 AI/PDF services] --> J1[explicitly isolated compatibility boundary]
```

## 4. Unknowns

The repo does **not** reveal:
- current production `dr_v3` flag distribution
- actual field device/browser incidence by shell
- whether production users reporting breakage were routed to V1, V3, or both

Those remain UNKNOWN until runtime evidence is gathered.
