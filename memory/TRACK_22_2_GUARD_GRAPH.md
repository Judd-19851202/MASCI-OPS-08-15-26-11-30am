# TRACK 22.2 · Guard Graph

**Date:** 2026-02-04

Guard aliases declared at the top of `frontend/src/App.js` (lines 408–425). Each alias is a single-arg lambda that wraps its child element in the corresponding `RequireX` component from `@/lib/guards` / inline definitions.

| Alias | Line | Wrapper component | Routes gated | Role coverage |
|---|---:|---|---:|---|
| `A` | 408 | `RequireAdmin` | 65 | Admin |
| `TX` | 413 | `RequireTransportationPortal` | 1 | Dispatch/Admin (transportation-ops) |
| `AP` | 414 | `RequireAdminOrPm` | 45 | Admin OR PM |
| `APS` | 418 | `RequireAdminPmOrSafety` | 3 | Admin OR PM OR Safety (read-only review) |
| `P` | 419 | `RequirePm` | 22 | PM |
| `S` | 420 | `RequireShop` | 25 | Shop |
| `H` | 421 | `RequireHr` | 28 | HR |
| `FL` | 422 | `RequireFl` | 4 | Field Leadership |
| `SF` | 423 | `RequireSafety` | 33 | Safety |
| `DP` | 424 | `RequireDispatch` | 10 | Dispatch |
| `D` | 425 | `RequireDev` | 6 | Developer (internal) |
| *(none)* | — | *public* | 143 | Anonymous / cross-portal |

## Constitutional invariant
Every route in the new modular tree MUST carry the SAME guard alias as the current App.js. Parity harness verifies:
- `path` unchanged
- `guard_alias` unchanged
- `guard_component` (`RequireX` resolution) unchanged
- `target_component` unchanged
- `load` (lazy vs eager vs inline_or_local) unchanged

No collapse of `AP` into `A ∪ P`. No promotion of `P` to `AP`. Guard chain preserved verbatim.

## Extraction pattern
```jsx
// feature-routes/admin.jsx
import { AdminGuard as A } from "../guards";
import { lazy } from "react";
const AdminHubV2 = lazy(() => import("@/pages/AdminHubV2"));
export const adminRoutes = [
  { path: "/admin/qaqc", element: <A><AdminQaqcList /></A> },
  ...
];
```

Or, alternatively, wrap the entire group under a nested `<Route element={<AdminGuard />}>` boundary using React Router v6 outlets — but this changes the React tree shape. Per the user's decision on question 2 ("URL surface + guard chain identical"), either form is acceptable so long as external behavior is proven identical by parity harness + Playwright.
