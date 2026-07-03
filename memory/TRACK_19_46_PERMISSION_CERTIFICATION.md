# TRACK 19.46 · Permission Certification

## Weekly Operations Digest
- **Registered role:** `admin_only`
- **Rationale:** Weekly Operations exposes cross-domain WoW deltas
  across safety / HR / projects / procurement — only admin sees the
  full company view.
- **Preview:** `GET /api/operational-intelligence/weekly_operations_digest/preview`
  → admin token required (safety/unauth → JSON 401/403, never HTML).
- **Dispatch:** `POST /api/operational-intelligence/weekly_operations_digest/dispatch`
  → admin token required.

## History API
- **Endpoint:** `GET /api/operational-intelligence/history`
- **Registered role:** admin-only (`require_admin` dependency in
  `routes.py`).
- **Enforcement:** the same admin gate used by the Track 19.45A
  recipient CRUD endpoints (`_make_oi_require_admin_only`). Safety
  tokens fail with JSON 401 · unauth fails with JSON 401.

## Audit API
- **Endpoint:** `GET /api/operational-intelligence/audit`
- **Registered role:** admin-only.
- **Enforcement:** identical to History API.

## Live-verified gates (2026-07-04 smoke)
| Endpoint | Admin | Safety | Unauth |
|---|:-:|:-:|:-:|
| `GET /operational-intelligence/weekly_operations_digest/preview` | 200 | 403 JSON | 401 JSON |
| `GET /operational-intelligence/history` | 200 | 401 JSON | 401 JSON |
| `GET /operational-intelligence/audit` | 200 | 401 JSON | 401 JSON |

## No-Auto-Decision compliance
Weekly Operations explicitly refuses to determine fault, discipline,
preventability, OSHA recordability, liability, or compliance status.
Every recommendation is a discussion prompt for the Monday operations
meeting — never an automatic executive decision.
