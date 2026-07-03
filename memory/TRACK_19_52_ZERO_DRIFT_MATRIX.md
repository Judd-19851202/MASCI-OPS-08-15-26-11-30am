# TRACK 19.52 · Zero Drift Matrix

Every category audited against the Track 19.52 absolute rules.

| Category                                          | Rule                       | Verified? | Evidence                                                                                       |
|---------------------------------------------------|----------------------------|:---------:|------------------------------------------------------------------------------------------------|
| New command center framework                       | FORBIDDEN                  | ✅        | Zero new frameworks · single shared consumer component only.                                   |
| New dashboard engine                               | FORBIDDEN                  | ✅        | No engine added; consumes existing OI engine.                                                  |
| New Operational Intelligence engine                | FORBIDDEN                  | ✅        | `backend/operational_intelligence/` inventory unchanged from Track 19.50.                      |
| New score model                                    | FORBIDDEN                  | ✅        | No scoring logic in `OiAttentionStrip.jsx`; pure consumer of summary payload.                  |
| New email system                                   | FORBIDDEN                  | ✅        | No email code touched.                                                                         |
| New scheduler                                      | FORBIDDEN                  | ✅        | `scheduler.py` unchanged.                                                                      |
| New recipient system                               | FORBIDDEN                  | ✅        | `recipients.py` unchanged.                                                                     |
| New report/export primitive                        | FORBIDDEN                  | ✅        | No PDF/export module created.                                                                  |
| Command Center Snapshot export                     | FORBIDDEN                  | ✅        | Deliberately not built.                                                                        |
| New PDF/email snapshot feature                     | FORBIDDEN                  | ✅        | None created.                                                                                  |
| New portal shell                                   | FORBIDDEN                  | ✅        | Continues to use existing `@/design-system/PortalShell`.                                       |
| Use existing portal components                     | REQUIRED                   | ✅        | Strip mounted inside the existing `PortalShell` on each hub.                                   |
| Use existing routes                                | REQUIRED                   | ✅        | No new routes added; `App.js` route table untouched.                                           |
| Use existing sidebars                              | REQUIRED                   | ✅        | Sidebars unchanged.                                                                            |
| Use existing OI outputs                            | REQUIRED                   | ✅        | Consumes `GET /api/operational-intelligence/summary` (Track 19.46).                            |
| Use existing permission gates                      | REQUIRED                   | ✅        | Endpoint requires admin token · consumer degrades gracefully otherwise.                        |
| Preserve all payloads                              | REQUIRED                   | ✅        | Consumer only reads `products[]`; payload contract unchanged.                                  |
| Preserve OI contracts                              | REQUIRED                   | ✅        | No mutation, no bypass.                                                                        |
| Preserve email governance                          | REQUIRED                   | ✅        | No email path touched.                                                                         |
| Preserve recipient governance                      | REQUIRED                   | ✅        | No recipient path touched.                                                                     |
| Preserve certified workflows                       | REQUIRED                   | ✅        | Every prior link and section on each hub preserved.                                            |

## Backend module inventory (frozen)
```
backend/operational_intelligence/
├── __init__.py
├── engine.py
├── product_layout.py
├── products.py
├── recipients.py
├── registry.py
├── routes.py
├── scheduler.py       ← pre-existing (Track 19.50 baseline)
└── score_model.py
```
No file added. No file removed. No file renamed.

## Front-end footprint
- 1 new file (`OiAttentionStrip.jsx`) — pure UI consumer.
- 5 files modified — each with a small mount block (≤ 8 LOC).

## Total scope
- Frontend: 1 new component + 5 surgical mount points.
- Backend: 0 changes.
- Tests: 1 new lock test file.
- Docs: 7 new files + PRD + CHANGELOG updates.
