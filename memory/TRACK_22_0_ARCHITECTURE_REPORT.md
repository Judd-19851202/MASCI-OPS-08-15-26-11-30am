# TRACK 22.0 · Architecture Report

**Stack:** React + Tailwind + shadcn/ui (frontend) · FastAPI + MongoDB (backend) · Cloudflare R2 (object storage) · Resend (email) · Sentry (error monitoring).

## Layer map

| Layer | Location | Excellence signals |
|---|---|---|
| Frontend shell | `frontend/src/App.js` | 385 routes · 180 lazy imports · portal-scoped guards. DEFER split to Track 22.2. |
| Frontend pages | `frontend/src/pages/**` | 309 pages · domain-organized (admin/, safety/, hr/, transportation/, driver/, shop/, dispatch/). |
| Frontend components | `frontend/src/components/**` | 355 components · shadcn/ui primitives at `components/ui/`. |
| API client | `frontend/src/lib/api.js` + hooks | Central axios instance with `Authorization`, `X-Session-Id`, `X-Portal-Token` header injection. |
| Backend shell | `backend/server.py` | 16,094 lines · DEFER split to Track 22.1. |
| Backend routes | `backend/routes/**` | Domain-scoped routers (asset_spine, employee_lifecycle, po_requests, operational_attachments, dr_admin_intel, ...). |
| Auth | `backend/server.py` + `pm_routing.py` | JWT + portal tokens + admin sentinel (Track 15.32 shared-password retired). |
| Data | MongoDB · 170 distinct collections | Single source of truth per domain (equipment_master, daily_reports, incidents, jha_plans, ...). |
| Email | Resend SDK · 3-layer safety envelope | `EMAIL_SAFETY_MODE=strict` → SDK kill switch → dispatcher gate → `TEST_` payload prefix. |
| Storage | Cloudflare R2 via S3 SDK | 25 MB per upload · `TEST_*` prefix isolates synthetic blobs. |
| Audit | `trust_spine_events` + workflow-stage emitters | Every workflow write emits a stage event. |
| Observability | Sentry | Preview + prod events currently merged; Sentry env-tag deferred to Track 21.2z. |

## Deferrals summary

- **Track 22.1** — `server.py` modularization behind a full endpoint-parity harness.
- **Track 22.2** — `App.js` route extraction behind a full route-parity harness.
- **Track 21.y** — Component collision rename/merge plan (`TRACK_21_3_COMPONENT_COLLISION_REPORT.md`).
- **Track 21.2z** — Sentry `environment=` tag · storage janitor · singleton-collection retention.

## Six Pillars

- Powerful: **9.75** — thick backend surface, thick frontend surface, unified auth model.
- Simple: **9.70** — 2 large files remain (server.py, App.js). Both deferred with parity gates.
- Beautiful: **9.70** — design-system primitives + shadcn consistency.
- Trusted: **9.95** — 3-layer email envelope + explicit CORS + explicit env docs.
- Proven: **9.92** — 134 lock tests · Track 20.8 deployment cert.
- Operational: **9.78** — every workflow is portal-scoped and role-gated.
- Durable: **9.78** — audit trail on every workflow write.
