# DR-UNIFY-003 · Route Alias Matrix

## Doctrine

- **Canonical** = the name we want everyone to use going forward.
- **Deprecated alias** = the name we still serve for backward
  compatibility during the migration window.

Both are served today. Neither may be removed until DR-UNIFY-004
certifies deletion.

## Matrix

| Purpose                                          | Canonical (preferred)                            | Deprecated alias (still served)                  | Auth               |
| ------------------------------------------------ | ------------------------------------------------ | ------------------------------------------------ | ------------------ |
| Approved reports list                            | `GET /api/daily-reports/approved`                | `GET /api/dr-v2/reports/approved`                | Public read        |
| PDF download                                     | `GET /api/daily-reports/{report_id}/pdf`         | `GET /api/dr-v2/reports/{report_id}/pdf`         | Admin / PM / HR    |
| Draft summary                                    | `POST /api/daily-reports/summary/draft`          | (none — canonical only)                          | Public rate-limit  |
| Accept summary                                   | `POST /api/daily-reports/{report_id}/summary/accept` | (none)                                       | Public rate-limit  |
| Submit new daily report                          | `POST /api/daily-reports`                        | (none — never had a V2 alias)                    | Public rate-limit  |
| Fetch single daily report                        | `GET /api/daily-reports/{id}`                    | (none)                                           | Admin / PM / HR    |
| Legacy dr-v2 dev endpoints (synthesise/etc.)     | (n/a — no user-facing canonical yet)             | `POST /api/dr-v2/synthesize` (internal only)     | Flag-gated         |

## Enforcement

- Backend router `routes/dr_v2_pdf.py` explicitly declares both routes
  side-by-side in `register_dr_v2_pdf_routes`.
- Lock test `test_dr_v2_pdf_router_serves_both_canonical_and_alias`
  verifies both strings appear in the source.
- Lock test `test_no_new_route_deletes_a_legacy_alias` counts each
  string at least once — refactors that accidentally drop either
  variant fail CI.

## Payload equivalence

Both approved-list variants delegate to the same handler. Both PDF
variants stream the same bytes. Any drift is a bug. This is asserted
manually today; DR-UNIFY-004 will add a byte-comparison test.

## Retirement window

- **Now → DR-UNIFY-004:** both variants live and are equivalent.
- **DR-UNIFY-004:** production certification pass. If prod logs show
  zero calls to the `/dr-v2/*` aliases for 30 days, DR-UNIFY-004
  removes the alias routes. Otherwise, retention window is extended.
- **Client migration guide:** internal callers (tests, scripts,
  admin UI) should already prefer canonical. External callers must
  audit before the alias is removed.

## No user-facing exposure

- No user-facing nav, link, or button references the `/dr-v2/*`
  prefix. The alias exists only to preserve any external integrations
  or bookmarks that predate DR-UNIFY-002.
- The frontend Admin UI already reads from the canonical variants.
