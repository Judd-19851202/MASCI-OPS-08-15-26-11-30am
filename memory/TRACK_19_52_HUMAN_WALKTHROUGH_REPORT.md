# TRACK 19.52 · Human Walkthrough Report

Each persona was walked through the touched portal:
first-login → identify what matters → click into workflow → return.

## Safety Director opens `/safety-portal`
- **Can I tell what this portal is for?** ✅ PortalShell header "MASCI · Safety Operations" · pageTitle answers "What safety work requires attention right now?".
- **What matters first?** ✅ New OI Attention Strip shows `Safety Morning Digest` score + attention level + top attention label BEFORE the CAPA cards.
- **Where do I click?** ✅ Click Cockpit link for full drill-down; click any CAPA card for domain workflow.
- **Noise?** ❌ None — strip is 1 tile.
- **Hidden?** ❌ Nothing hidden; every prior link preserved.

## HR Director opens `/hr`
- Purpose obvious (PortalShell "MASCI · Human Resources").
- New OI strip surfaces `HR Intelligence` and `Training Intelligence` together — the two highest-value HR signals.
- Employee directory search still directly beneath — no disruption to the classic "find a person" workflow.
- Noise? ❌ Strip has ≤ 2 tiles.

## PM opens `/pm`
- Redirect to `/pm/command-center` (already live).
- OI strip surfaces `Project Intelligence` at the very top of the command center body.
- Below: PmProjectSelector, PmCommandStrip, project-first home. Unchanged.
- Noise? ❌ Strip is 1 tile; slots cleanly above the existing project selector.

## Shop Manager opens `/shop`
- OI strip surfaces `Shop Intelligence` at the top — safety holds / aging critical defects / OOS.
- Below: Unit Search, Your Queue, 4-tile Attention grid — unchanged.
- Noise? ❌ Strip is 1 tile.

## Dispatcher / Shop Manager opens `/shop/fleet` (Fleet Visibility)
- OI strip surfaces `Fleet Intelligence` — active holds, critical defects, availability.
- Chip counters and unit cards below — unchanged.
- Noise? ❌ Strip is 1 tile.

## Cross-persona findings
- No confusion introduced; every strip is a single row (or two-tile row for HR) with a clear "Open in Cockpit" deep-link.
- Every tile is clickable → drills into `/admin/operational-intelligence` (Cockpit) which was already the reference implementation certified in Track 19.47.
- No new sidebars, no new dashboards, no new frameworks were introduced.
- 5:30-AM readability preserved — one glance tells the operator whether their portal has an OI attention item.
