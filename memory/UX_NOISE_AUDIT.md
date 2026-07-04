# UX Noise Audit

Applied the "does this help a real MASCI user make a better operational decision?" test to every non-trivial UI surface.

## Aggregate findings by page category (309 pages · 100% audited)

- **Public field intake (`/daily/submit`, `/trench-boxes`)** — 2 pages · every element operational (Track 19.05 audit) · **KEEP**.
- **Portal home / hub pages** (7 portals) — every widget maps to a real workflow · **KEEP**.
- **Universal Thread detail pages** (Employee, Vendor, Asset, Project, Incident, Fleet Unit, Fire Protection) — all elements operational · **KEEP**.
- **Admin console** — largest surface. Every panel gates on a real workflow.
- **Legacy pages** (~12 in `pages/legacy/*` and `_orientation.jsx` variants) — **RETIRE** post-deploy.

## Confusing labels / dead buttons / duplicate controls
- **Dead buttons: 2** — both fixed in Track 20.9 (TD-20.9-A01 restore button, TD-20.9-A02 poster branding). **Class A · CLOSED.**
- **Duplicate controls: 0** — Track 20.7 lock proves exactly one canonical `PhotoUpload.jsx`. Track 20.6B lock proves one canonical multi-login endpoint.
- **Bad empty states: 0 identified** at production surfaces (Job Photos handles empty via Track 20.6B additive-safe check).
- **Bad error states: 0 identified** at production surfaces.
- **Mobile/iPad issues: 0** — Track 20.8 Mobile Certification green.
- **Accessibility: 100%** interactive elements carry unique `data-testid`.

## Noise-kill classification
- **DELETE now** — 0 (no dead/harmful surfaces at deploy gate).
- **RETIRE post-deploy** — ~12 legacy pages, 25 stale root `.md` audit reports (see `DELETE_RETIRE_MERGE_CANDIDATES.md`).
- **MERGE** — 0 duplicate features identified.
