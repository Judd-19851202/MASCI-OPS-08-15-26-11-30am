# Track 21.2 · Platform Reconciliation Matrix

_Generated 2026-07-04T13:15:19.536568Z_

| Category | Count | Status | Evidence |
|---|---|---|---|
| repository | 6969 | VERIFIED | git ls-files -> 6969 entries... |
| backend_endpoints | 1331 | VERIFIED | AST scan of every FunctionDef with a *.get|post|put|delete|patch decorator. 934/1331 sites have per-arg or router-level Depends() or live under an explicit public prefix (auth/heal... |
| frontend_routes | 385 | VERIFIED | 385 <Route ... path=...> declarations in App.js... |
| frontend_lazy_imports | 180 | VERIFIED | Alias-aware resolver (`@/` -> src/) walked 180 lazy() targets. 180 resolved to a real file. 0 broken.... |
| frontend/pages | 309 | VERIFIED | jsx/js scan |
| frontend/components | 355 | VERIFIED | jsx/js scan |
| frontend/dialogs | 98 | VERIFIED | jsx/js scan |
| frontend/forms | 67 | VERIFIED | jsx/js scan |
| frontend/buttons | 1687 | VERIFIED | jsx/js scan |
| frontend/inputs | 1198 | VERIFIED | jsx/js scan |
| frontend/tables | 198 | VERIFIED | jsx/js scan |
| backend_email_dispatch_sites | 29 | VERIFIED | Every direct-SDK reference to `resend.Emails.send` / `_resend.Emails.send` is downstream of the Track 21.2E SDK-level kill switch. Preview env sets EMAIL_SAFETY_MODE=strict -> the ... |
| backend_upload_endpoints | 23 | VERIFIED | 20/23 upload endpoints have per-arg or router-level Depends() gates. Remaining sites are the certified public-submit uploads for Daily Reports attachments and Job Photos.... |
| backend_pdf_modules | 24 | VERIFIED | 24 modules importing reportlab / weasyprint / SimpleDocTemplate identified. All are wrapped by their respective route handlers that carry a Depends() gate.... |
| backend_scheduler_task_scheduling | 31 | VERIFIED | asyncio.create_task() invocations enumerated. Track 15.79C strong-reference set retains them so GC cannot free them. Every schedulable dispatch flows through _dispatch_auto_email, ... |
| mongo_collections | 328 unique | VERIFIED | 328 distinct collection names discovered via `db[<name>]` / `db.<name>` scan (method-noise filtered). |
| tech_debt_markers | TODO=13 FIXME=3 XXX=16 HACK=1 | DEFERRED | 33 tech-debt markers logged. Each represents a specific engineering intent left by a prior track. Zero-Drift mandate: cataloging only, no changes in this track. |