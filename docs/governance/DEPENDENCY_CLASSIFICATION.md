# DEPENDENCY CLASSIFICATION

Date: 2026-07-19  
Checkpoint: D4

## Governing decisions

1. `backend/requirements.txt` remains the deployment entrypoint for this checkpoint.
2. Absence of a static import is not treated as proof of disuse.
3. Optional providers remain separated when responsibilities differ or remain plausible.
4. D4 performs classification, reproducibility proof, and bounded cleanup only.

Machine-readable authority:
- `docs/governance/dependency_inventory.json`

## Isolated proof status

| Proof | Status | Command |
|---|---|---|
| Backend fresh install | PASSED | python3 -m venv <tmp>/venv && pip install --no-cache-dir -r backend/requirements.txt |
| Backend compileall | PASSED | python -m compileall backend |
| Frontend fresh install | PASSED | yarn install --frozen-lockfile --ignore-scripts |
| Frontend production build | PASSED | yarn build |

## Backend classification totals

| Classification | Count |
|---|---|
| CORE_RUNTIME | 6 |
| CORE_RUNTIME_AUTH_SUPPORT | 3 |
| CORE_RUNTIME_CAPABILITY | 1 |
| CORE_RUNTIME_SUPPORT | 5 |
| FEATURE_RUNTIME_CAPABILITY | 11 |
| GOVERNANCE_TOOLING | 4 |
| OPERATOR_AND_TEST_TOOLING | 1 |
| OPERATOR_TOOLING | 4 |
| OPTIONAL_RUNTIME_PROVIDER | 11 |
| REVIEW_REQUIRED_NO_RUNTIME_PROOF | 10 |
| RUNTIME_OBSERVABILITY | 2 |
| TEST_AND_OPERATOR_CAPABILITY | 2 |
| TEST_TOOLING | 7 |
| TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT | 13 |
| TRANSITIVE_RUNTIME_SUPPORT | 89 |

## Frontend classification totals

| Classification | Count |
|---|---|
| BUILD_COMPAT_SHIM | 1 |
| BUILD_TOOLCHAIN | 6 |
| CORE_RUNTIME_UI | 51 |
| DEV_PREVIEW_TOOLING | 1 |
| GOVERNANCE_TOOLING | 4 |
| REVIEW_REQUIRED_NO_PROVEN_USE | 6 |
| RUNTIME_PEER_SUPPORT | 1 |
| TEST_TOOLING | 2 |
| TRANSITIVE_BUILD_SUPPORT | 1148 |
| TRANSITIVE_GOVERNANCE_SUPPORT | 14 |
| TRANSITIVE_LOCKFILE_REVIEW_REQUIRED | 69 |
| TRANSITIVE_RUNTIME_SUPPORT | 139 |
| TRANSITIVE_TEST_SUPPORT | 13 |

## Backend notable decisions

| Package | Classification | Decision note |
|---|---|---|
| fastapi | CORE_RUNTIME | Primary backend API framework. |
| motor | CORE_RUNTIME | Canonical async MongoDB runtime driver. |
| pymongo | CORE_RUNTIME | MongoDB sync/runtime helper and canonical dependency chain. |
| emergentintegrations | OPTIONAL_RUNTIME_PROVIDER | Governed multi-provider integration surface; keep responsibilities distinct. |
| openai | OPTIONAL_RUNTIME_PROVIDER | Pinned provider surface retained under governance even where usage is indirect or emergent-managed. |
| litellm | OPTIONAL_RUNTIME_PROVIDER | Pinned provider orchestration surface retained under governance. |
| google-generativeai | OPTIONAL_RUNTIME_PROVIDER | Pinned Google provider surface retained under governance. |
| google-genai | OPTIONAL_RUNTIME_PROVIDER | Pinned Google provider surface retained under governance. |
| slowapi | REVIEW_REQUIRED_NO_RUNTIME_PROOF | Legacy rate-limit dependency has no current direct import proof after local extraction. |
| passlib | REVIEW_REQUIRED_NO_RUNTIME_PROOF | No current direct runtime import evidence; retain until independently disproven. |
| python-jose | REVIEW_REQUIRED_NO_RUNTIME_PROOF | No current direct runtime import evidence; retain until independently disproven. |

## Frontend notable decisions

| Package | Classification | Decision note |
|---|---|---|
| date-fns | RUNTIME_PEER_SUPPORT | Required peer support for react-day-picker even without direct imports. |
| @hookform/resolvers | REVIEW_REQUIRED_NO_PROVEN_USE | No current import proof; retain until separately disproven. |
| recharts | REVIEW_REQUIRED_NO_PROVEN_USE | No current import proof; retain until separately disproven. |
| zod | REVIEW_REQUIRED_NO_PROVEN_USE | No current import proof; retain until separately disproven. |
| @babel/plugin-proposal-private-property-in-object | BUILD_COMPAT_SHIM | Retained build compatibility package for CRA/Babel toolchain. |
| @emergentbase/visual-edits | DEV_PREVIEW_TOOLING | Preview-only visual editing integration loaded from custom tarball when available. |

## Cleanup executed in D4

| Package | Action | Status | Reason |
|---|---|---|---|
| cra-template | REMOVED_FROM_DIRECT_DEPENDENCIES | EXECUTED_WITH_PROOF | Removed only after isolated clean install/build proof; this package is not a runtime, build, script, provider, or peer dependency for the governed app. |

## Acceptance-sensitive findings

- `cra-template` was removed only after isolated clean install and isolated production build proof demonstrated it was unnecessary.
- `date-fns` is retained as runtime peer support for `react-day-picker`; it is not treated as unused just because no direct import remains in app code.
- `@babel/plugin-proposal-private-property-in-object` is retained as a build compatibility shim even without source imports.
- `@hookform/resolvers`, `recharts`, `zod`, `@eslint/js`, `eslint-plugin-import`, and `eslint-plugin-jsx-a11y` remain review-required rather than auto-removed.
- Distinct AI/provider packages remain separately governed; D4 does not collapse them without stronger proof.

## Custom/public package sources proven available without credentials

| Ecosystem | Package | Source | Fresh install proven |
|---|---|---|---|
| backend | emergentintegrations | https://d33sy5i8bnduwe.cloudfront.net/simple/ | YES |
| frontend | @emergentbase/visual-edits | https://assets.emergent.sh/npm/emergentbase-visual-edits-1.0.8.tgz | YES |
