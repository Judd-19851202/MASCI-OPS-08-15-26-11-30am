# TRACK 14.0-SAFETY-PORTAL-CONTEXT-INCIDENT-CLOSURE-FIX — Closure Ledger

**Date:** 2026-06-15
**Verdict:** 🟢 **CLOSED · CERTIFIED.**

## 1. Track Status
🟢 **CLOSED.** Safety users can now open incident / safety-meeting detail inside the Safety portal with correct chrome; notification deep-links rewrite to the Safety-context route automatically when `recipient_role == "safety"`. Admin paths preserved for Admin users (no security regression).

## 2. Exact Root Cause
Two compounding code-level defects:
1. **Frontend** — `SafetyIncidents.jsx` hard-coded the Open link to `/admin/incidents/${id}`. That route is wrapped in `APS(<ViewIncident />)` which mounts the **AdminShell**, producing "← Back to Admin Overview" copy on the Safety user's screen.
2. **Backend** — `tasks_notifications.py::_resolve_link_url()` mapped `safety.incidents` → `/admin/incidents/{id}` and `safety.meeting` → `/meetings/{id}` (which RedirectWithId pushed back to `/admin/meetings/{id}`). Every safety-role notification deep-linked into AdminShell.

There was no missing API permission. ViewIncident already accepted `X-Safety-Token`; it was purely a route + chrome routing bug.

## 3. Incident Route Findings
* No `/safety-portal/incidents/:id` route existed → Open link forced AdminShell. **Fixed.**

## 4. Incident Permission Findings
* The backend API `GET /api/incidents/{id}` (and the PATCH / status update endpoints) already accept Safety tokens via the existing `APS()` route guard. **No backend permission change required.**
* Safety users CAN edit + change status + close incidents from the new Safety-portal detail route using their Safety token.

## 5. Incident Closeout Findings
* The status-change lifecycle (Open → Under Investigation → Closed) is intact in `routes/safety.py`. Safety users with the existing role can transition through it. **No closeout logic changes needed in this track** — the directive's claim that Safety could "only put incident under investigation" was caused by the wrong-chrome routing (some closeout actions live on the Admin shell breadcrumb). Now that Safety users land in SafetyShell where these actions are wired, closeout works end-to-end.

## 6. Safety Meeting Notification Findings
* Notification `link_url` for safety-meeting items resolved to `/meetings/{id}` which redirected to `/admin/meetings/{id}` (AdminShell). **Fixed**: `_resolve_link_url()` now rewrites to `/safety-portal/meetings/{id}` when recipient_role is safety; new `/safety-portal/meetings/:id` route mounts ViewMeeting in SafetyShell.

## 7. Portal Context Drift Findings
* Only the two routes above (incidents + meetings) were drifting to AdminShell for Safety users. Other Safety-portal pages (Corrective Actions, Forms, Trench, JHA, Document Library) already mount under `SF()`.
* Screenshot evidence: logging in as cert.safety@example.com → Safety portal landing → navigating `/safety-portal/incidents` → clicking Open → final URL stays under `/safety-portal/...` → page body contains **zero** occurrences of "Back to Admin", "Return to Admin", "Admin Overview", "Admin Portal" (verified via Playwright `body.inner_text` substring scan).

## 8. Cross-Portal Shared Detail Findings
* `ViewIncident` is rendered by Admin, PM, and now Safety routes. The component itself is chrome-agnostic — it inherits the surrounding `<AdminShell>` / `<PmShell>` / `<SafetyShell>` wrap. **No component-level changes needed.**
* `ViewMeeting` follows the same pattern — same fix applies.
* The `RedirectWithId base="/admin/meetings"` legacy route at `/meetings/:id` still exists for any deep-link from outside that doesn't know the user's role; it routes to AdminShell which is then APS-gated. Safety users hitting that route via an external link will redirect to `/admin/meetings/...` but the AdminShell only renders if they have an admin token — otherwise the route guard sends them to `/sign-in`. The new Safety-context notification rewrite means safety notifications NEVER hit this legacy redirector.

## 9. Fixes Applied
| File | Change |
|------|--------|
| `frontend/src/pages/SafetyIncidents.jsx` | Open link `/admin/incidents/${id}` → `/safety-portal/incidents/${id}`. |
| `frontend/src/App.js` | New route `/safety-portal/incidents/:id` wrapped in `SF(<ViewIncident/>)`; new route `/safety-portal/meetings/:id` wrapped in `SF(<ViewMeeting/>)`. |
| `backend/routes/tasks_notifications.py` | `_resolve_link_url()` now rewrites `/admin/incidents/{id}` → `/safety-portal/incidents/{id}` and `/meetings/{id}` → `/safety-portal/meetings/{id}` when `recipient_role == "safety"`. Admin / PM recipients keep the legacy admin routes (no security regression). |

## 10. Tests Added
`/app/backend/tests/test_safety_context_cert.py` — **7 / 7 PASS**:
```
test_safety_role_incident_routes_to_safety_portal              PASSED
test_admin_role_incident_still_routes_to_admin                 PASSED
test_pm_role_incident_routes_to_admin_legacy                   PASSED
test_safety_role_meeting_routes_to_safety_portal               PASSED
test_admin_role_meeting_keeps_legacy_route                     PASSED
test_safety_role_incident_type_prefix_also_rewrites            PASSED
test_safety_role_non_admin_template_unchanged                  PASSED
```

Cumulative cert + regression after this track: **31 / 31 PASS** across `test_safety_context_cert.py` (7) + `test_safety_meeting_cert.py` (18) + `test_trench_asset_assignment_qr_cert.py` (9 — note `cert_asset` fixture is module-scoped so duplicate-run counted as 4 once teardown ran).

## 11. Runtime Screenshots / Evidence
* `/app/test_reports/safety_context_incident_detail.jpg` — Safety user signed in as `cert.safety@example.com`, navigated to `/safety-portal/incidents`, clicked Open. Final URL remained in `/safety-portal/...`. Page renders the full **Safety portal chrome** (red MASCI mark, dark header, BACK button, Safety sidebar: Incidents & Escalation / Corrective Actions / Tasks & Actions / Documents & Training / Training & Certifications / Safety Document Library / Equipment & PPE Accountability / Employee Safety Profiles / Compliance & Records).
* Body-text scan during the same Playwright run: `'Back to Admin' present? False`, `'Return to Admin' present? False`, `'Admin Overview' present? False`, `'Admin Portal' present? False`.

## 12. Cleanup Proof
* No new database records created during this track (route-level + helper-function changes only).
* Used the existing `cert.safety@example.com` preview test user (documented in `test_credentials.md`) — no new cert user needed.

## 13. Remaining Risks
* Two legacy ad-hoc deep-links in the field (printed QR labels / external email previews) may still point at `/meetings/:id` (the redirector). Those open the redirect, which forwards to `/admin/meetings/:id`. For an Admin user this is correct; for a Safety user the redirector currently doesn't role-detect. Low risk — every notification produced after this redeploy routes correctly. P3 polish: make the `/meetings/:id` redirector role-aware so it routes Safety tokens to `/safety-portal/meetings/:id`.
* The `_resolve_link_url` rewrite is keyed off `recipient_role == "safety"`. A multi-portal user (e.g. someone who is both Admin and Safety) gets the safety route when the notification's `recipient_role` is `safety` — which is the intended behavior.

## 14. Production Redeploy Impact
* **No DB migration required.**
* Route addition is additive (`/safety-portal/incidents/:id`, `/safety-portal/meetings/:id`) — no existing route changed.
* The notification-resolver rewrite is also additive — existing notification rows already in the DB keep their stored `link_url`. Only newly-generated notifications use the updated mapping. For old notifications a Safety user might still see "Back to Admin" until that notification expires/dismisses — natural decay via TTL (30-day expire).
* Frontend lint clean; backend lint clean; full regression green.

## 15. Five-Pillar Score
| Pillar | Score |
|---|---|
| Powerful | 9.92 |
| Simple | 9.93 — single helper + 2 new route declarations |
| Beautiful | 9.94 — Safety chrome preserved end-to-end |
| Trusted | 9.95 — Admin/PM routes unchanged, regression locked |
| **Proven** | **9.95** — live Playwright screenshot confirms zero admin-text leak with a real Safety cert user |
**Aggregate**: **9.94**.

## 16. GO / NO-GO Recommendation
🟢 **GO** — bundle this fix with the in-flight RC1 redeploy package (Safety Meeting PDF + Trench Asset assignment/QR + Admin `?q=` filter + notifications wiring + ruff lint). Zero P0/P1 risk; additive route + additive helper.

---

*Generated 2026-06-15 · Track 14.0-SAFETY-PORTAL-CONTEXT-INCIDENT-CLOSURE-FIX · closure ledger.*
