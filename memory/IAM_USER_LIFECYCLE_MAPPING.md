# FORGEDOPS IAM SPRINT · 3 · USER LIFECYCLE MAPPING
## OMEGA P0 · Canonical 8-state lifecycle mapped to existing fields

**Date**: 2026-06-03

---

## 1 · Canonical 8-state lifecycle (per directive)

```
1 · User Created
2 · Welcome Sent
3 · Temporary Password Issued
4 · First Login
5 · Password Set
6 · Active
7 · Disabled
8 · Reactivated
```

---

## 2 · State map vs existing fields

For each lifecycle state we identify: the existing fields that prove that state, how the state is surfaced in the canonical row, and whether any new persistence is required.

### State 1 · User Created

| Existing fields | Surfacing | New persistence? |
|---|---|:-:|
| `id`, `email`, `name`, `created_at` (where stored), or default to "—" | Row appears in panel; **Access Status = `PENDING_ACTIVATION`** if no `last_login_at` and `must_change_password = true`; otherwise `ACTIVE` | NO |

### State 2 · Welcome Sent

| Existing fields | Surfacing | New persistence? |
|---|---|:-:|
| `welcome_sent_at` (FL portal only — exists on `field_leadership_users`); not present on HR/Safety/Dispatch/Shop today | Row shows "Welcome sent: 2h ago" when field present; "—" otherwise | NO (additive UI; field already exists on FL; other portals will simply render "—") |

### State 3 · Temporary Password Issued

| Existing fields | Surfacing | New persistence? |
|---|---|:-:|
| `must_change_password === true` (canonical across all 6 collections); some portals also store `temp_password_issued_at` (e.g., `field_leadership_users`) | **Password Status badge = `TEMP_PASSWORD_ACTIVE`**. If `temp_password_issued_at` exists, render "Issued: 2h ago" | NO |

### State 4 · First Login

| Existing fields | Surfacing | New persistence? |
|---|---|:-:|
| `last_login_at` becomes non-null **AND** `must_change_password` becomes false (or `password_set_at` becomes set) | Row transitions from `PENDING_ACTIVATION` → `ACTIVE`; Password Status badge transitions to `PASSWORD_SET` | NO |

### State 5 · Password Set

| Existing fields | Surfacing | New persistence? |
|---|---|:-:|
| `must_change_password === false` (and `last_login_at` is set) | **Password Status badge = `PASSWORD_SET`** | NO |

### State 6 · Active

| Existing fields | Surfacing | New persistence? |
|---|---|:-:|
| `disabled === false` (HR/Safety/Dispatch/FL) **OR** `is_active === true` (Shop, Admin core) | **Access Status badge = `ACTIVE`** (green) | NO |

### State 7 · Disabled

| Existing fields | Surfacing | New persistence? |
|---|---|:-:|
| `disabled === true` (HR/Safety/Dispatch/FL) **OR** `is_active === false` (Shop, Admin core) | **Access Status badge = `DISABLED`** (rose); row dimmed; only "Re-enable" + "View Audit" actions available | NO |

### State 8 · Reactivated

| Existing fields | Surfacing | New persistence? |
|---|---|:-:|
| Transition from State 7 back to State 6 (toggle `disabled` from `true` → `false` or `is_active` from `false` → `true`) | Reactivation audit entry is already written by the existing PATCH/POST `/disable` handler. No new persistence needed in this sprint. | NO |

---

## 3 · Field provenance matrix (read-only audit)

| Field | HR | Safety | Dispatch | Shop | FL | Admin core |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `id` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `email` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `name` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `phone` | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| `role` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `employee_id` | — (optional add-on) | — | — | — | — | — |
| `created_at` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `created_by` | — | — | — | ✅ | ✅ | — |
| `disabled` | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| `is_active` | — | — | — | ✅ | — | ✅ |
| `must_change_password` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `last_login_at` | ✅ (where indexed) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `welcome_sent_at` | — | — | — | ✅ | ✅ | — |
| `password_set_at` | — | — | — | — | — | — |
| `temp_password_issued_at` | — | — | — | — | ✅ | — |
| `temp_password_issued_by` | — | — | — | — | — | — |
| `disabled_at` / `disabled_by` | — | — | — | ✅ | ✅ | — |

Legend: ✅ = field stored today (per inspection of route handlers and DB samples); — = field absent.

---

## 4 · What this sprint **CAN** standardize (presentation-only)

| Lifecycle state | Surfacable today with existing fields? |
|---|:-:|
| 1 — User Created | ✅ via `created_at` |
| 2 — Welcome Sent | 🟡 only on Shop + FL; others render "—" |
| 3 — Temp Password Issued | ✅ via `must_change_password === true` |
| 4 — First Login | ✅ via `last_login_at` non-null |
| 5 — Password Set | ✅ via `must_change_password === false` AND `last_login_at` non-null |
| 6 — Active | ✅ via `disabled` / `is_active` reducer |
| 7 — Disabled | ✅ via same reducer |
| 8 — Reactivated | ✅ as a transition between 7 → 6 (no new state badge needed) |

**6 of 8 states are fully surfacable today**; 2 (Welcome Sent across all portals, full Reactivated history) require either future persistence or a UI render of "—" on portals lacking the field.

---

## 5 · What this sprint **WILL NOT** standardize (out of scope per directive)

| Item | Why excluded |
|---|---|
| Backend `last_password_issued_by` tracking | Requires DB write hooks; directive forbids data migrations / schema changes |
| Backend password expiration policy | Requires new business rule; directive forbids new business logic |
| HR/Safety/Dispatch welcome-email endpoints | Requires new APIs; directive forbids new APIs |
| Audit history view enrichment | Existing audit view stays; only adds a row-level link to it |
| Cross-portal SSO / unified login | Requires major architecture work; not in scope |

---

## 6 · Stop-rule compliance

| Rule | Status |
|---|:-:|
| No user creation | 🟢 |
| No user deletion | 🟢 |
| No password reset | 🟢 |
| No DB write | 🟢 |
| No login history modification | 🟢 |
| No audit history modification | 🟢 |
| No data migration | 🟢 |
| No schema change | 🟢 |
| Lifecycle is **mapping only**, not modification | 🟢 |
