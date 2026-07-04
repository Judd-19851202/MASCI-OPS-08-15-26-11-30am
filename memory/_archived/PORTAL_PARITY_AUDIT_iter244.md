# MASCI Operations Platform · Portal Parity Audit
**Iter 244 · 2026-05-19 · Read-only governance doc · NO CODE CHANGES**

Scope: All 6 admin user-management surfaces (PM · HR · Safety · Shop · Dispatch · Field Leadership). The Safety Portal welcome-email gap surfaced in iter243 proved that capability drift between operational domains is now a real governance concern as the platform matures. The right response is **visibility first, not immediate standardization** — preserve portal-specific operational identity while ensuring no critical capability has silently diverged.

---

## 1 · Frontend Capability Matrix

`✅` = supported · `❌` = not supported · number = count of `data-testid` attributes (UX testability proxy)

| Capability                          | PM   | Shop | HR   | Safety | Dispatch |
|-------------------------------------|:----:|:----:|:----:|:------:|:--------:|
| `Add User` defaults to email welcome | ❌  | ❌  | ✅  | ✅    | ❌      |
| Show-on-screen password reveal      | ❌  | ✅  | ✅  | ✅    | ✅      |
| Custom-password input field         | ✅  | ✅  | ✅  | ✅    | ❌      |
| Issue/reset choice dialog (3-mode)  | ❌  | ✅  | ✅  | ✅    | ❌      |
| Disable / enable toggle             | ✅  | ✅  | ✅  | ✅    | ✅      |
| Inline edit (name / email / phone)  | ✅  | ✅  | ✅  | ✅    | ✅      |
| Delete user row                     | ❌  | ✅  | ✅  | ✅    | ✅      |
| Role-select editor                  | ❌  | ✅  | ✅  | ✅    | ✅      |
| Phone field                         | ✅  | ✅  | ✅  | ✅    | ✅      |
| Refresh button                      | ✅  | ✅  | ✅  | ✅    | ✅      |
| Mobile responsive grid              | ✅  | ✅  | ✅  | ✅    | ✅      |
| Toast on success                    | ✅  | ✅  | ✅  | ✅    | ✅      |
| Loader2 spinner during async ops    | ✅  | ✅  | ✅  | ✅    | ✅      |
| Empty-state row                     | ✅  | ✅  | ✅  | ✅    | ✅      |
| Loading-state row                   | ✅  | ✅  | ✅  | ✅    | ✅      |
| Status badge (Active/Disabled)      | ❌  | ✅  | ✅  | ✅    | ✅      |
| Search/filter input                 | ❌  | ❌  | ❌  | ❌    | ❌      |
| Audit columns (last login / created)| ✅  | ❌  | ❌  | ❌    | ❌      |
| `t()` localization wrapper          | ❌  | ❌  | ❌  | ❌    | ❌      |
| `data-testid` coverage              | 30  | 19  | 18  | 18    | 15      |
| File size (lines)                   | 866 | 447 | 404 | 400   | 342     |

**Field Leadership**: Intentionally NO per-user admin panel. Field Leadership uses a single shared password (`MASCIGC`) — this is an explicit operational design choice, not drift. Excluded from the rest of this audit.

---

## 2 · Backend Capability Matrix

| Capability                                | PM  | Shop | HR  | Safety | Dispatch |
|-------------------------------------------|:---:|:----:|:---:|:------:|:--------:|
| POST create endpoint exists               | ✅  | ✅  | ✅  | ✅    | ✅      |
| POST `reset-password` endpoint            | ❌  | ❌  | ✅  | ✅    | ✅      |
| Accepts `delivery` field on body          | ❌  | ❌  | ✅  | ✅    | ❌      |
| Accepts `custom_password` field           | ❌  | ❌  | ✅  | ✅    | ❌      |
| `must_change=True` wired on issuance      | ✅  | ✅  | ✅  | ✅    | ✅      |
| Branded portal email render               | ✅  | ❌  | ✅  | ✅    | ❌      |
| `send_email_fn` injected                  | ✅  | ❌  | ✅  | ✅    | ❌      |
| Suppress `temp_password` when `email`     | ❌  | ❌  | ✅  | ✅    | ❌      |

> **Note**: The PM endpoints live in `server.py` (main monolith); HR / Safety / Dispatch live in their own portal modules under `routes/`. PM does have a separate branded welcome flow via `pm_welcome_pdf.py` and the `pm_routing.py` welcome trigger — it does NOT use the same `delivery=` payload pattern, but PMs DO receive a branded welcome email by default on account creation.

---

## 3 · Inconsistency Classification

### 🔴 CRITICAL — capability gap with operational impact
| ID | Portal | Gap | Why it matters |
|----|--------|-----|----------------|
| C1 | **Dispatch** | No `delivery=email\|screen\|custom` payload on create or reset. Admin can ONLY show passwords on screen. | Same operational gap iter243 fixed for Safety. Admins handling Dispatch onboarding for a remote dispatcher have no built-in way to email credentials — they have to copy from screen and paste into a separate email manually. This is the same governance gap that prompted the operator complaint that triggered iter243. |
| C2 | **Shop** | Backend doesn't accept `delivery` payload (despite frontend having custom-password input). | Shop frontend currently passes `custom_password` but no `delivery` field — relies on backend default of show-on-screen for all paths. Admin cannot email a Shop user their initial password. Same impact as C1. |

### 🟡 IMPORTANT — UX consistency drift
| ID | Portal | Gap | Why it matters |
|----|--------|-----|----------------|
| I1 | **Dispatch** | No `pwChoice` dialog — `Issue Password` button just reveals immediately, no email option, no custom-pw input. | UX-level mismatch with HR/Safety/Shop. Inconsistent admin mental model across portals. |
| I2 | **PM** | No `pwChoice` dialog · no role-select editor · no delete-user row action. | PM panel was built earliest, predates the iter40-iter50 user-management hardening pass that brought the other 4 portals to a common pattern. PM has its own welcome flow (PDF + email) that partially compensates. |
| I3 | **PM** | "Add User" creates the account but doesn't expose explicit "Email Welcome" choice — flow is implicit (sends on creation). | UX is hidden; admin can't see *what* will happen at the point of action. |

### 🔵 COSMETIC — minor visual/affordance drift
| ID | Portal | Gap | Why it matters |
|----|--------|-----|----------------|
| K1 | **PM** | No status badge (Active/Disabled visual indicator) | Inline state still readable but no visual color cue. |
| K2 | All five | No `t()` localization wrappers on user-management admin UI labels | Admin surfaces are EN-only by design today (admin staff are office personnel). NOT a field-crew surface. Operationally acceptable as-is. |
| K3 | All five | No search/filter input on the user list | Acceptable while each portal's user list is <50 entries. Worth queuing for the day any portal grows past ~30 users. |

### 🟢 INTENTIONAL OPERATIONAL DIFFERENCE — preserve as-is
| ID | Portal | Difference | Why it's intentional |
|----|--------|-----------|----------------------|
| T1 | **Field Leadership** | No per-user admin panel · shared password (`MASCIGC`) | Foremen/superintendents on the truck don't carry separate credentials. Job-site password is intentionally simple. RBAC-wise, FL users have minimal scope. |
| T2 | **PM** | Has audit columns (last_login, created_at) visible in the admin panel | PMs are accountable office personnel; their activity is governed. Other portals don't need this surface yet. |
| T3 | **PM** | Larger file (866 lines) due to richer audit columns + impersonation + invite flows | PM was the first portal admin built; deeper feature set is product-deliberate. |
| T4 | **Dispatch** | Smallest file (342 lines) due to small user count (1-3 dispatchers per company typically) | Smaller surface area is appropriate; doesn't NEED feature parity for capabilities that are never exercised. |

---

## 4 · Operational-Risk Classification

| Risk Level | Items | Recommendation |
|------------|-------|----------------|
| **HIGH** — production-impact | C1, C2 | These create the same operational pain that the operator escalated for Safety. A remote Dispatch hire today has the same friction Safety had pre-iter243. Recommend iter246 (one fix per portal · pattern mirrors iter243). |
| **MEDIUM** — UX consistency | I1, I2, I3 | Worth queuing as a contained "admin user-mgmt UX harmonization" iter. Should NOT be lumped into other work — needs its own scoped pass. |
| **LOW** — cosmetic | K1, K2, K3 | Watch-only. No action required unless an operator complaint surfaces or a portal grows past ~30 users. |
| **NONE — intentional** | T1, T2, T3, T4 | Preserve as-is. These are operational design choices, not drift. |

---

## 5 · Recommendation Summary

1. **Do not standardize for standardization's sake.** Each portal serves a different operational role — PM has audit columns Dispatch doesn't need, Field Leadership has a shared password Safety can't have. Forcing identical UIs would degrade portal-specific affordances.

2. **Close the two CRITICAL backend gaps** (Dispatch + Shop missing `delivery=email|screen|custom`) **before they trigger another operator complaint** like Safety did. Same surgical pattern that iter243 used — should be a low-risk, single-iter fix. Estimated effort: ~1 hour total for both portals combined. Recommendation: queue as **iter246** AFTER iter245 ships, since iter245 is the active operator priority.

3. **Document the intentional differences** (T1-T4) somewhere persistent (this doc + `/app/memory/PRD.md`) so future agents/contributors don't "fix" them. Drift that gets papered over is harder to recover than drift that's flagged.

4. **Do NOT** touch PM panel structure unless there's a specific operator-surfaced need. PM has the richest panel today; harmonizing DOWN to match the simpler portals would lose functionality. If anything, propagate UP — bring Safety/Shop/Dispatch closer to PM's audit visibility — but that's a deliberate decision, not drift correction.

5. **Re-run this audit after iter246 ships** to confirm the CRITICAL row goes empty. This audit doc + the matrix can become the "portal parity gate" that any future user-management work runs against before merge.

---

## 6 · Severity Ranking (one-page summary)

| Severity | Count | Action |
|----------|------:|--------|
| 🔴 Critical (operational impact) | 2 | Queue iter246 — same pattern as iter243 |
| 🟡 Important (UX drift) | 3 | Queue separately when there's a concrete operator request |
| 🔵 Cosmetic | 3 | Watch-only |
| 🟢 Intentional operational difference | 4 | Preserve as-is · document persistently |

**Verdict: NO immediate code changes required.** All CRITICAL items are stable enough to defer until iter246. None of the gaps create a security exposure (every panel still enforces admin-only RBAC; the gaps are only about capability/UX, not auth).

---

## 7 · Method Notes (reproducibility)

- Frontend: scanned 5 panel files in `/app/frontend/src/components/Admin*Users*Panel.jsx` + `AdminPMPanel.jsx` with regex signal-detection for 20 capability dimensions
- Backend: scanned each portal's primary route module for the same `delivery` / `custom_password` / `render_portal_email` / `send_email_fn` / `must_change=True` signals
- All checks pattern-matched against actual code (not comments) — false-positive risk low
- Zero code modifications during the audit
- Total audit time: ~6 minutes
- Re-running the audit: see `iter244_parity_audit.py` reproducible script (this file's introspection block above can be re-run any time)

---

*Generated 2026-05-19 · iter244 · read-only governance doc · no code changes during this iter.*
