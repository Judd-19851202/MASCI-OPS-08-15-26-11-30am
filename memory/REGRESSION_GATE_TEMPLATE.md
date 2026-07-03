# REGRESSION GATE TEMPLATE

**Doctrine:** Every future track must run the applicable subset of these regression categories before it can claim GO.
**Established:** Track 19.30 · 2026-07-03
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

---

## Regression categories

### 1 · Backend unit tests
- **What:** Per-module Python tests for individual functions, services, and helpers.
- **Where:** `/app/backend/tests/`
- **Run:** `pytest tests/<file>.py -v` (isolated per-file execution to avoid known asyncio cross-suite bleed).
- **Required for:** Any track that changes backend code.

### 2 · Backend route contract tests
- **What:** Verify each `/api/*` endpoint's contract — method, auth gate, request payload shape, response schema, error paths.
- **Where:** `/app/backend/tests/test_track_<NN>_*.py` (per-track lock tests).
- **Required for:** Any track that adds, modifies, or retires a backend route.

### 3 · Frontend build
- **What:** `yarn build` completes without errors.
- **Run:** `cd /app/frontend && yarn build` (only if track intends production build validation; supervisor hot-reload otherwise covers dev-mode).
- **Required for:** Any track that changes frontend code with risk to build (JSX errors · import cycles · missing exports).

### 4 · Frontend lint
- **What:** ESLint clean on all touched files.
- **Run:** `mcp_lint_javascript` tool on each modified file.
- **Required for:** Any track that changes frontend code.

### 5 · Playwright smoke
- **What:** Real-browser automation walking the track's main flow(s).
- **Where:** Executed via `testing_agent_v3_fork` for medium+ features.
- **Run:** Testing agent invocation with feature list.
- **Required for:** Any track with UX flows > 2 steps or > 3 endpoints.

### 6 · Role permission smoke
- **What:** Verify each role sees only what it should. Set expected localStorage tokens or use real login for each role. Confirm restricted routes redirect or show neutral gate UI.
- **Where:** Playwright smoke or backend contract tests.
- **Required for:** Any track that touches permissions, guards, or role-scoped surfaces.

### 7 · Bilingual smoke
- **What:** Toggle to Spanish via `LangToggle`, verify every user-facing string is translated. Toggle back to English, verify no ES leakage.
- **Where:** Playwright smoke (`page.click('[data-testid="lang-toggle-es"]')`).
- **Required for:** Any track that adds new user-facing strings.

### 8 · PDF smoke
- **What:** Trigger a real PDF generation, verify HTTP 200 · content-type `application/pdf` · non-zero size · opens in a viewer without corruption.
- **Where:** Backend curl or Playwright download.
- **Required for:** Any track that adds or modifies a PDF endpoint.

### 9 · Email dry-run smoke
- **What:** Trigger a real email dispatch in `dry_run=true` mode, verify `email_routing_audit_v2` records the dispatch with correct recipients/reason.
- **Where:** Backend curl or manual admin trigger via `/admin/digest-config`.
- **Required for:** Any track that adds or modifies an email trigger.

### 10 · Notification dry-run smoke
- **What:** Verify in-platform notification digest at `/notifications` renders the new event correctly for the intended role(s).
- **Where:** Playwright smoke.
- **Required for:** Any track that adds a new notification-emitting workflow.

### 11 · Mobile viewport smoke
- **What:** Playwright at `page.set_viewport_size({"width": 390, "height": 844})` (iPhone 14 Pro dimensions). Verify layout, touch targets ≥ 44 pt, no horizontal scroll, sticky headers not overlapping keyboard.
- **Required for:** Any track with a field-facing surface.

### 12 · iPad viewport smoke
- **What:** Playwright at `page.set_viewport_size({"width": 810, "height": 1080})` (iPad portrait) and `1080 × 810` (landscape).
- **Required for:** Any track with a supervisor-facing or PM-facing surface used on-site.

### 13 · Desktop smoke
- **What:** Playwright at `1920 × 1080`. Verify sidebar V2 domain accordion, drawer/dropdown behavior, and no wasted whitespace.
- **Required for:** Any track with an office-user surface.

### 14 · Historical record smoke
- **What:** Verify that any state-mutating action produces an entry in the correct append-only audit collection (`employee_record_audit` · `email_routing_audit_v2` · `incident_case_audit` · etc.).
- **Required for:** Any track that mutates a record with historical significance.

### 15 · Audit event smoke
- **What:** Verify every mutation is captured in `/admin/audit-log` timeline.
- **Required for:** Any track with cross-portal or governance-sensitive changes.

### 16 · Trust Spine smoke
- **What:** Verify cross-portal reads (Employee 360 · Case Workspace · Ops Attention) see the new data correctly.
- **Required for:** Any track that adds a new cross-portal data source.

### 17 · Rollback sanity check
- **What:** Verify the documented rollback path actually works — canonical route toggle · `_legacy` URL · feature flag reverse · migration reverse.
- **Required for:** Every track that canonicalizes a route or promotes a V2 surface.

---

## Applicability matrix (heuristic)

| Track type | Categories required |
|---|---|
| Pure documentation / audit | 3 · 4 (if any code touched) + lock test |
| Bugfix (frontend-only) | 3 · 4 · 5 |
| Bugfix (backend-only) | 1 · 2 |
| Frontend feature | 3 · 4 · 5 · 6 · 7 · 11 · 12 · 13 + applicable subset |
| Backend feature | 1 · 2 + applicable subset |
| Cross-portal feature | Nearly all categories |
| Cleanup / retirement | 4 · 5 · 17 |

## Enforcement

- Each track's closeout document (per `FUTURE_TRACK_CLOSEOUT_TEMPLATE.md`) must list which categories were run and their results.
- Missing a required category = incomplete gate = NO-GO.

## Known test-infra debt

- Pytest asyncio cross-suite bleed on combined-suite runs. Isolated per-file execution GREEN. Any track running the full `pytest tests/` suite must expect ~109 asyncio-related failures unrelated to the track. Not blocking. Owned by a future test-infra track.
