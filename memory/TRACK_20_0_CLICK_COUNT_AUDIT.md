# TRACK 20.0 · Click Count Audit

Every common workflow was measured in clicks from persona-portal login
to the point of action.

## Baseline table
| Persona · workflow                                    | Clicks (pre-19.51) | Clicks (post-20.0) | Delta |
|-------------------------------------------------------|:-----------------:|:------------------:|:-----:|
| Executive · read Corporate morning brief              | ~4                | **2**              | −2    |
| Safety Director · open top-attention item             | ~5                | **2**              | −3    |
| HR Director · see expiring certifications             | ~4                | **2**              | −2    |
| PM · see project intelligence signal                  | ~4                | **1** (auto-redirect) | −3 |
| Superintendent · read "Today's focus"                 | ~5                | **1**              | −4    |
| Dispatcher · read transportation attention            | ~4                | **1**              | −3    |
| Shop Manager · see shop attention                     | ~4                | **1**              | −3    |
| Fleet Manager · open a unit's operational story        | ~7                | **2** (unit link → Thread) | −5 |
| Any persona · read Guidance Card for any attention    | ~5+ (leave portal to Cockpit) | **1** (modal in place) | −4+ |
| Mechanic · read Unit history / timeline               | ~5                | **2** (Thread → Section 4) | −3 |

## Zero-click destinations reachable
- Attention strip renders **without user interaction** on every portal login.
- "Today's focus" banner renders on Field Leadership dashboard **without user interaction**.
- Cockpit sparkline renders inline on every product card **without user interaction**.

## Modal-based flows (no navigation cost)
- OI Attention Strip tile → **opens Guidance Card in-place** (0 navigation cost).
- Guidance Card sections → deep-link back to source portals only when the user chooses to act.

## No dead ends detected
- Every relationship node on the Fleet Unit Thread links to a real route (or renders as unlinked text — never a broken link).
- Every deep link in Guidance Card resolves to a route that exists in `App.js`.

## Verdict
🟢 **Click cost reduced meaningfully across every persona.** The
platform now favours modal drill-downs and universal primitives over
cross-portal navigation.
