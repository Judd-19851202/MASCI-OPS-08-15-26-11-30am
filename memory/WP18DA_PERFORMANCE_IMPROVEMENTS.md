# WP-18DA Performance Improvements

## Changes implemented

### Frontend
- `frontend/scripts/stamp-build-version.js`
  - build identity writes are now idempotent (`writeIfChanged`) instead of rewriting watched files on every compile
- `frontend/craco.config.js`
  - CRA eslint disabled in live dev runtime (`enable: !isDevServer`)
  - webpack filesystem cache enabled
  - visual edits gated behind `ENABLE_VISUAL_EDITS=true`

### Backend
- `backend/lib/singleton_scheduler.py`
  - singleton schedulers now retain the runtime DB proxy instead of a stale resolved Mongo handle
- `backend/routes/job_photos.py`
  - thumbnail auto-warm now records failure timestamps, backs off recent failures for `6h`, and avoids repeated hot-loop retries
  - startup index added for `thumb_warm_last_failed_at`
- `backend/routes/safety_forms.py`
  - startup index ensure added for issuance/training employee + project filters
- `backend/routes/field_leadership.py`
  - startup index ensure added for kind / project / employee list filters
- `backend/server.py`
  - runtime index bootstrap registered as a lifecycle step
  - public probe fast-path added for `/api/health`, `/api/healthz`, `/api/ready`

## Measured outcome

- Preview home route improved from earlier unstable/slow dev-shell behavior to:
  - `domContentLoaded 926ms`
  - `loadEventEnd 1682ms`
- Final frontend verification further measured preview at:
  - `domContentLoaded 915ms`
  - `loadEventEnd 1302ms`
- Preview warmed API fetches now verify at:
  - health `47-49ms`
  - version `50-51ms`
  - public grouped JHA `74-141ms`
- Production build completed successfully in `50.53s`

## Reliability outcome

- Final backend verification confirmed **no active `Cannot use MongoClient after close` errors** in the current runtime after the scheduler fix.
