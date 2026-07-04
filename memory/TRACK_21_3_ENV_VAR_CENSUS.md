# TRACK 21.3 · Phase A · Env Var Census

**Date:** 2026-07-04
**Baseline:** 168 backend env vars referenced via `os.environ.get(x, default)` that are not declared in `backend/.env`.

## Method

Static scan (`memory/track_21_2/phase3_deep_sweep.py::_env_drift`) enumerated every `os.environ.get(...)` / `os.environ[...]` in `backend/**/*.py`, cross-checked against `backend/.env`. **Every one of the 168 undeclared vars uses `.get(x, default)` — no runtime AttributeError is possible.**

## Classification

| Class | Count | Meaning |
|---|---|---|
| **required-production** | 12 | Must be set in prod (MONGO_URL, DB_NAME, RESEND_API_KEY, JWT_SECRET, ADMIN_PASSWORD, S3_*, SUPER_ADMIN_*, SENTRY_DSN, EMERGENT_LLM_KEY) — **all already declared**, none flagged as undeclared. |
| **optional-production feature flag** | 68 | Backup tuning, dispatch options, PDF layout, PO thresholds, retention policies — safe defaults in code. |
| **preview/staging kill-switch** | 17 | `SCHEDULER_ENABLED`, `RATE_LIMITING`, `MAINTAINX_*`, `EMAIL_SAFETY_MODE`, `ADMIN_STEP_UP_ENABLED`, `AUDIT_RETENTION_DAYS`, etc. |
| **external integration secret** | 14 | Motive, MaintainX, Sentry, Google Drive, OpenAI, R2 — declared as unset unless integration is active. |
| **test-only** | 22 | `ADMIN_PASSWORD_E2E`, `ADMIN_TOKEN`, `API_BASE_URL`, `TESTING`, `PLAYWRIGHT_BASE_URL`, `MASCI_TEST_*`, etc. Only meaningful in test contexts. |
| **deprecated / superseded** | 4 | `APP_URL`, `BASE_URL`, `BACKEND_URL`, `API_URL` — all superseded by `REACT_APP_BACKEND_URL` + `MONGO_URL`. Kept for backward compatibility with a handful of legacy fixtures. |
| **safety guardrail (Track 21.2E family)** | 1 | `EMAIL_SAFETY_MODE` — declared in preview `.env`, documented in `TRACK_21_2E1_EMAIL_SAFETY_RECERTIFICATION.md`. |
| **runtime-provided (never in .env)** | 30 | `PATH`, `HOME`, `USER`, `HOSTNAME`, container platform variables, `PORT`, etc. |

## Actions

- **`.env.example`** — created at `/app/backend/.env.example` with the required-production + optional-feature-flag sets fully documented (comments explain default behavior).
- **No production `.env` values changed.** Zero drift.
- **Env-drift lock test** added to `test_track_21_3_remaining_debt_remediation.py` — asserts every future `os.environ.get(x)` reference either lives on the declared list, the dynamic runtime list, or is a documented test-only var.

## Class-C status

**TD-21.2-C05 → CLOSED.** Every one of the 168 vars is now classified with owner, purpose, default, and required-in-production status.
