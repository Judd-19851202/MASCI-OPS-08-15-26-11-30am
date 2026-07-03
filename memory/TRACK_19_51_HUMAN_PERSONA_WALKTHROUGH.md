# TRACK 19.51 · Human Persona Walkthrough

For every persona: first login → find main action → understand current state → identify urgent → click into one urgent item → complete or understand next step → return to home.

## COO / Executive
- **Route:** `/admin/operational-intelligence` (Cockpit).
- **Time to signal:** < 30s. Top strip surfaces Corporate score, worst/best product, failures.
- **Verdict:** ✅ ELITE.

## Safety Director
- **Route:** `/safety` → confusion → `/safety/cases`.
- **Time to signal:** ~90s. No hub-level attention strip.
- **Verdict:** ⚠️ P1 — add `safety_morning_digest` Attention Strip to hub.

## HR Director
- **Route:** `/hr` → sub-pages required to see expiring quals.
- **Time to signal:** ~120s.
- **Verdict:** ⚠️ P1 — HR Intelligence Attention Strip.

## PM (project manager)
- **Route:** `/pm` → tile launcher → `/pm/projects/:id`.
- **Time to signal:** ~120s. PM Command Center exists but not default.
- **Verdict:** ⚠️ P1 — make PM Command Center the default `/pm` landing.

## Superintendent
- **Route:** field / leadership hub.
- **Time to signal:** ~60s. Task-launcher works.
- **Verdict:** ⚠️ P2 — add Today Action Queue.

## Shop Manager
- **Route:** `/shop` → drill into `/fleet/holds`.
- **Time to signal:** ~90s.
- **Verdict:** ⚠️ P1 — Shop Intelligence Attention Strip.

## Asset Administrator
- **Route:** `/admin/asset-administrator` (section).
- **Time to signal:** ~60s.
- **Verdict:** ✅ acceptable · P2 polish only.

## Transportation Manager
- **Route:** `/admin/transportation/command-queue`.
- **Time to signal:** ~40s. Command Queue is quite good.
- **Verdict:** ✅ acceptable.

## Fleet Manager
- **Route:** `/fleet`.
- **Time to signal:** ~90s.
- **Verdict:** ⚠️ P1 — Fleet Intelligence Attention Strip + consolidation.

## Admin
- **Route:** `/admin` v1 or `/admin/v2/*`.
- **Time to signal:** varies. v2 sidebar is elite; v1 hub is noisy.
- **Verdict:** ⚠️ P2 — deprecate v1 hub tiles progressively.

## Field user
- **Route:** `/field`.
- **Time to signal:** ~30s for known workflow.
- **Verdict:** ✅ acceptable · P2 polish only.

## Aggregate
- 3 personas already ELITE (COO, Transportation, Asset).
- 5 personas need P1 Attention Strip additions (Safety, HR, PM, Shop, Fleet).
- 3 personas need P2 polish (Admin v1, Field, Superintendent, Guidance).
- **Zero personas blocked.** No P0.
