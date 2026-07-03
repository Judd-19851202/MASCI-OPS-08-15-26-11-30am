# TRACK 19.52 · P1 Remediation Execution

Traceability map from every P1 roadmap item → executed change.

## Shared primitive (new · one file · pure consumer)
`/app/frontend/src/components/operational_intelligence/OiAttentionStrip.jsx`

Consumes `GET /api/operational-intelligence/summary`. Reads
`products[]` and filters client-side to the requested `productIds`.
Renders one tile per matched product with:
- display name
- attention level chip (LOW / MEDIUM / HIGH / CRITICAL colour ramp)
- overall score
- trend arrow + trend percent
- top attention label (first item of `needs_immediate_attention`)
- deep-link to `/admin/operational-intelligence` (Cockpit)

Zero-drift guarantees enforced in the file header comment.

## P1 #1 — Safety Hub Attention Strip
- Roadmap: "surface the `safety_morning_digest` top-attention label + open-CAPA count at the top of `/safety`".
- Executed: `SafetyHubV2.jsx` (mounted at `/safety-portal` and `/safety-portal/hub_v2`) now renders `OiAttentionStrip` with `productIds=["safety_morning_digest"]` at the top of the shell, above the CAPA section.
- Open-CAPA count already lived in the "Corrective Actions" section directly beneath the new strip — no duplication.
- Zero-drift risk: LOW. Read-only.

## P1 #2 — HR Hub Attention Strip
- Roadmap: "surface `hr_intelligence` + `training_intelligence` combined".
- Executed: `HrHubV2.jsx` (mounted at `/hr` and `/hr/hub_v2`) renders `OiAttentionStrip` with both product IDs above the existing HR Compliance At Risk widget.
- Zero-drift risk: LOW.

## P1 #3 — PM landing = PM Command Center
- Roadmap: "retire the PM Hub as the default `/pm` route in favour of `PmCommandCenter.jsx`. Add `project_intelligence` snapshot."
- Executed:
  - `/pm` already redirects to `/pm/command-center` via `PmHomeRedirect.jsx` (Phase 4C, 2026-02-10) — no code change required for the route swap.
  - `PmCommandCenter.jsx` now renders `OiAttentionStrip` with `productIds=["project_intelligence"]` as the first child of the command-center body.
- Zero-drift risk: LOW.

## P1 #4 — Shop Hub Attention Strip
- Roadmap: "surface `shop_intelligence` (safety holds → aging critical defects → OOS)".
- Executed: `ShopHubV2.jsx` (mounted at `/shop` and `/shop/hub_v2`) renders `OiAttentionStrip` with `productIds=["shop_intelligence"]` at the top of the shell body, above Unit Search / Attention grid.
- Zero-drift risk: LOW.

## P1 #5 — Fleet Visibility Attention Strip + mobile fix
- Roadmap: "surface `fleet_intelligence` and repair the >900px table blowout".
- Executed:
  - `FleetVisibility.jsx` (mounted at `/shop/fleet`, `/safety-portal/fleet`, `/dispatch-portal/fleet`) renders `OiAttentionStrip` with `productIds=["fleet_intelligence"]` directly under the FocusBanner.
  - Table-blowout scan: FleetVisibility does **not** use `<table>` — it renders a responsive `space-y-3` list of `UnitCard`s and a `grid-cols-2 sm:grid-cols-4 lg:grid-cols-5` chip counter. Verified no horizontal overflow at iPad portrait (768px), iPad landscape (1024px), or 900px intermediate. No further layout change required.
- Zero-drift risk: LOW.

## Not executed (deferred by design)
- P2 items #6-#12 — remain on the roadmap; out of scope for this surgical track.
- P3 items #13-#19 — remain on the roadmap; out of scope.
- "Command Center Snapshot" export — explicitly forbidden by the Track 19.52 rules.

## No backend change · no schema change · no permission change
Verified: engine directory inventory unchanged, no new files under
`/app/backend/operational_intelligence/`, no new routes, no new
collections, no new environment variables.
