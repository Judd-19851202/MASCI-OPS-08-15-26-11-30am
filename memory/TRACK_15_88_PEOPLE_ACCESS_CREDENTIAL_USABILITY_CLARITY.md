# TRACK 15.88 — PEOPLE & ACCESS CREDENTIAL USABILITY CLARITY

**Status: GO — every Admin People & Access row now tells the truth about whether the user can sign in right now (and if not, why not). 26 / 26 static tests · 5 / 5 live API states · browser-verified at 3 breakpoints · 277 / 277 deployment-gate regression suite green.**

## Old behaviour

Before this track, the Access Control Center showed who had portal grants but **not** whether those grants were *usable*. Admins saw "Test — Shop checked" with no signal about whether the user actually had a password issued, whether they owed a password rotation, or whether they were disabled.

When an unusable user couldn't sign in, the operator had to manually reconcile the Admin UI against the per-portal login behaviour to figure out which gating bit was tripping them. That was the source-of-confusion behind the Track 15.87 P0 report ("Test → Shop checked, but cannot log in").

## New behaviour

Every directory row now ships **five canonical fields** in `GET /api/admin/directory` and the mutation responses (`POST` / `PATCH` / reset-password):

```json
{
  "id": "…",
  "email": "user@example.com",
  "portals": ["pm", "shop"],
  …existing fields…,
  "access_state":     "active"   | "inactive",
  "credential_state": "issued"   | "never_issued" | "change_required" | "blocked",
  "portal_count":     2,
  "usable_now":       true,
  "blocked_reason":   null
}
```

The Admin Console People & Access UI renders two compact badges per row:
* **Credential state badge** — issued (green) · never_issued (amber) · change_required (amber) · blocked (slate).
* **Usability badge** — `USABLE NOW` (emerald) when `usable_now=true`, or a blocked-reason chip (dark slate) with one of: "Disabled · cannot sign in", "Credentials not issued", "Password change required", "No portal access granted".

`data-testid` attributes are present on every state element for browser-smoke + the upcoming production smoke check.

## Access state contract

```
access_state ∈ { "active", "inactive" }
  ─ active   ⇔ user_directory.disabled == False
  ─ inactive ⇔ user_directory.disabled == True
```

## Credential state contract

```
credential_state ∈ { "issued", "never_issued", "change_required", "blocked" }
  ─ disabled         → "blocked"
  ─ no password_hash → "never_issued"
  ─ must_change_pw   → "change_required"
  ─ otherwise        → "issued"
```

The helper reads `password_hash` only to compute a boolean (`has_credentials`); the hash itself **never leaves the helper** and is never returned in any response.

## Usability rules (matches Track 15.87 login behaviour 1:1)

```
usable_now == True iff:
  ¬ disabled                  AND
  password_hash present       AND
  ¬ must_change_password      AND
  portal_count >= 1

blocked_reason precedence:
  disabled        →  blocked_reason = "disabled"
  no credentials  →  blocked_reason = "never_issued"
  must_change_pw  →  blocked_reason = "change_required"
  no portals      →  blocked_reason = "no_portal_access"
  otherwise       →  blocked_reason = None  (and usable_now = True)
```

Order matters and mirrors the login endpoint denial order exactly — the Track 15.87 live RBAC matrix proved every `usable_now=True` row would successfully sign in to at least one of its granted portals.

## What was broken

* The Admin Console People & Access UI showed checkbox grants but did NOT show usability. Operators had no way to tell at a glance which users were usable.
* The `GET /api/admin/directory` response carried `disabled`, `must_change_password`, and `portals[]` separately but didn't derive a single canonical "is this user usable right now" envelope. Each consumer of the directory list (UI · cron · debugging) re-derived the rule, risking drift.
* "Never Issued" users were silently checkbox-granted with no clarity that the grant was inert until credentials were issued.

## What was fixed

### 1. Canonical helper · `backend/lib/directory_access_state.py`
* `derive_directory_access_state(row)` returns the canonical 5-field envelope.
* Pure function. No DB hit. No HTTP. No email. No secrets returned.
* Lock-tested for every state including the empty/None row.

### 2. Routes enrich every admin-facing user view
* `routes/auth_directory_routes.py` imports the helper + a tiny `_enrich_with_access_state(view, raw_row)` adapter.
* `GET /api/admin/directory` lists call the enricher per row.
* `POST /api/admin/directory` (create) re-fetches the raw row and enriches.
* `PATCH /api/admin/directory/{id}` (update) re-fetches and enriches.
* `POST /api/admin/directory/{id}/reset-password` (reset) re-fetches and enriches.
* Every consumer of the admin directory API now receives the canonical envelope automatically.

### 3. Frontend `AdminAccessControlPanel.jsx`
* New `<UsabilityBadges user={u} />` row helper.
* `CREDENTIAL_BADGE` map (4 keys) + `BLOCKED_REASON_COPY` map (4 keys) — keys come from backend constants and are drift-locked by the static tests.
* Defensive fallback: when an older API response arrives (no `credential_state`), the component derives a best-guess from the existing `disabled` + `must_change_password` + `portals` fields. UI never crashes on partial data.
* `data-testid` on every state element: `acc-row-state-*`, `acc-row-credstate-*`, `acc-row-usable-*`, `acc-row-blocked-*`.

### 4. RBAC + security preservation
* Helper never exposes `password_hash`. Static test asserts no `$2b`-shaped string ever appears in the returned envelope.
* Helper never imports `httpx` / `requests` / `motor` / `smtplib` — it's a pure derivation.
* Routes enricher never reads `row.get("password_hash")` directly — the helper is the only canonical reader.
* Frontend source contains no reference to `password_hash`.

## Files inspected

* `backend/lib/directory_access_state.py` (NEW)
* `backend/lib/directory_portal_login.py` (Track 15.87 — no changes)
* `backend/user_directory.py` (`public_view`, `ALLOWED_PORTALS`)
* `backend/routes/auth_directory_routes.py`
* `backend/server.py` (no changes — directory endpoints live in routes/)
* `frontend/src/components/AdminAccessControlPanel.jsx`
* `frontend/src/pages/admin/AdminPeople.jsx` (uses the panel — no changes)
* `frontend/src/components/iam/IamStandardCells.jsx` (referenced, no changes)

## Files changed

* `backend/lib/directory_access_state.py` (NEW · 138 lines · canonical helper)
* `backend/routes/auth_directory_routes.py` (+18 lines · import + enricher + 4 endpoint sites)
* `frontend/src/components/AdminAccessControlPanel.jsx` (+95 lines · `CREDENTIAL_BADGE` + `BLOCKED_REASON_COPY` + `UsabilityBadges` component + row integration)
* `backend/tests/test_track_15_88_people_access_credential_usability_clarity.py` (NEW · 26 tests)
* `scripts/deployment_gate.py` (Track 15.88 wired as 21st regression file)
* `memory/TRACK_15_88_PEOPLE_ACCESS_CREDENTIAL_USABILITY_CLARITY.md` (this file)
* `memory/PRD.md` (Latest Track updated; 15.85 / 15.86 / 15.87 history preserved)

## Tests added · 26 / 26 GREEN in <0.1 s

State derivation matrix (every input → expected envelope), helper-never-leaks-hash + reads-no-side-effects, route imports + enrichment per endpoint, frontend renders `<UsabilityBadges>` and consumes canonical keys, data-testid coverage, no-password_hash leak in UI source, backend-frontend contract-drift guard, Track 15.85 / 15.86 / 15.87 preservation, deployment-gate wiring.

## Live API state proof · 5 / 5 PASS

Seeded 5 temp directory users covering every credential/usability state. Called `GET /api/admin/directory?q=…` as super-admin. Every row returned the canonical envelope with the expected values and **zero password_hash leak**:

```
[PASS] usable            cred=issued            usable=True   blocked=None
[PASS] never_issued      cred=never_issued      usable=False  blocked=never_issued
[PASS] change_required   cred=change_required   usable=False  blocked=change_required
[PASS] disabled          cred=blocked           usable=False  blocked=disabled
[PASS] no_portals        cred=issued            usable=False  blocked=no_portal_access
```

## Browser verification · 3 / 3 breakpoints PASS

Pulled `/admin/people` on the preview pod at 390×844 / 768×1024 / 1024×768:

| Breakpoint | Body overflow | Hydration warnings | Console errors | `USABLE NOW` badges | Blocked badges |
|---|---|---|---|---|---|
| 390×844 phone | 0 | 0 | 0 | 148 | 14 |
| 768×1024 iPad portrait | 0 | 0 | 0 | 148 | 14 |
| 1024×768 iPad landscape | 0 | 0 | 0 | 148 | 14 |

Screenshot confirms the People & Access UI rendering cleanly with the new badges integrated under each user row (panel header text "Access Control Center" + 162 total users · 161 grants · 0 disabled visible in the Quick Stats tile).

## Security

* Helper never returns `password_hash`. Static test `test_helper_never_leaks_password_hash` asserts no `$2b…` substring ever appears in the helper's return value.
* Helper has no DB / HTTP / email side effects — pure function (`test_helper_only_reads_safe_fields`).
* Route enricher reads the hash via the helper only, never directly (`test_enrich_helper_strips_no_hash_from_view`).
* Frontend source contains no reference to `password_hash` (`test_panel_does_not_render_password_hash`).
* No new endpoints added. No new auth surface. Track 15.32 retired-admin-stub lock untouched.

## Track 15.87 preservation

* Access contract preserved verbatim. The 7 canonical portal keys still write through `PATCH /api/admin/directory/{id}` with `{ portals: [...] }` (test `test_canonical_portal_grant_keys_remain_seven` from Track 15.87 still green).
* The directory portal-login helper at `lib/directory_portal_login.py` is unchanged (test `test_track_15_87_helper_still_present`).
* The 33 Track 15.87 static tests + the live 32 / 32 RBAC matrix still pass.
* The Track 15.86 browser smoke gate still passes 9 / 9 (route × viewport).
* The Track 15.85 13-portal certification ledger is untouched.

## Deployment gate

* Now **21 regression files** · **277 backend tests · exit 0** (was 251 · +26 from Track 15.88) · 70 seconds via canonical `-q --timeout 30` harness.
* `python scripts/deployment_gate.py --no-runtime` → DECISION: PASS.
* Track 15.85 (26) + 15.86 (19) + 15.87 (33) + 15.88 (26) all green.

## Production smoke checklist

After deploying, operator must verify on the live platform:

1. Open Admin → People & Access on the live pod.
2. Confirm every row still shows the canonical portal checkboxes (Admin · PM · Shop · HR · Safety · Dispatch · Field Leadership).
3. Confirm users with credentials show the green `CREDENTIALS ISSUED` badge.
4. Confirm any "Never Issued" users show the amber `NEVER ISSUED` badge + `CREDENTIALS NOT ISSUED` blocked chip.
5. Confirm any `must_change_password=true` users show the amber `PASSWORD CHANGE REQUIRED` chip.
6. Confirm any disabled users show the slate `CREDENTIALS BLOCKED` + `DISABLED · CANNOT SIGN IN` chip.
7. Confirm usable users show the emerald `USABLE NOW` chip.
8. Confirm DOM inspector shows NO `password_hash` field on any user object.
9. Toggle a portal checkbox — verify the grant persists and the badges still render correctly after refresh.
10. Run `python scripts/deployment_gate.py --no-runtime` — must PASS.
11. Run `MASCI_SMOKE_BROWSER=1 pytest backend/tests/test_track_15_86_browser_smoke_runtime.py -v` — must PASS.
12. Sign in as a `USABLE NOW` user → confirm portal login still works (Track 15.87 contract).
13. Sign in as a `NEVER ISSUED` user → confirm 401 with clear copy.
14. Sign in as a `PASSWORD CHANGE REQUIRED` user → confirm rotation flow fires.

## Remaining advisories

* **UI polish (P2):** The "Issue Credentials" action could become more prominent on rows where `credential_state="never_issued"` — currently the existing `KeyRound` reset-password button serves both first-issue and rotation. A future track could split into two distinct affordances.
* **Audit (P3):** When a row transitions from `never_issued` → `issued` (admin issues a temp password) the audit row already exists. Adding the `credential_state` *transition* as an explicit audit diff would give the audit-log timeline an even cleaner story.
* **Bulk view (P3):** A "Filter: only show blocked" toggle on the panel would let admins zero-in on users who need attention faster than scrolling through 162 rows.

## Final call

GO. The Admin Console People & Access UI now tells the operational truth on every row. Granted ≠ usable, and operators can now tell the difference at a glance. Backend derives the truth from the same fields the login endpoints check, so UI ↔ login behaviour is 1:1 — no drift possible. No password material ever leaves the backend. No RBAC weakening. No new auth surface. The Track 15.87 multi-portal access authority contract is preserved, the Track 15.86 browser smoke gate still passes, and the Track 15.85 13-portal certification ledger is unchanged. Deployment gate green at 277 / 277. Elite AF.
