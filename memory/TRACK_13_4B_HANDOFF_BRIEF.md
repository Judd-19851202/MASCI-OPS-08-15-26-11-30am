# Track 13.4B — MASCI Platform Identity Recovery Audit · Handoff Brief

**Predecessor:** Track 13.4A (Known Defect Correction) — Conditionally Accepted, see  
`/app/memory/TRACK_13_4A_KNOWN_DEFECT_CORRECTION_REPORT.md`.

**Mode:** READ-ONLY audit by default. No new features, no deploy, no GitHub save, no merge.  
Any defect found should be **documented** in this track's report, not silently fixed.

---

## 1. Mission

Re-establish a single, coherent platform identity across **every** MASCI
operator surface. After Track 13.4A's dispatch + HR clean-up the platform
is **defectless-but-not-identity-coherent**: language, status verbs, role
clarity, theme cues, and tile cohesion still drift between portals.

---

## 2. Surfaces in scope

Each of the following must be audited and graded against the Five Pillars
(Powerful · Simple · Beautiful · Trusted · Proven). All audit screenshots
**must** be operator-view, NOT DOM-only, NOT super-admin substitution.

| # | Surface | Auth | Notes |
|---|---|---|---|
| 1 | Admin | `jaymn.judd@mascigc.com / Maddix123!` | Multi-portal owner; super-admin distinct from `/admin/login` legacy gate. |
| 2 | Dispatch | `dispatch@mascigc.com / DispatchTest2026!` | Use 13.4A guardrail values as baseline. |
| 3 | PM | **`pm.demo@mascigc.com / PmTest2026!`** (NEW — 13.4A fixture) | Scoped to projects `20-07`, `21-06`. Don't substitute super-admin. |
| 4 | Safety | `safety@mascigc.com / SafetyTest2026!` (rotated in iter323; use multi-login fallback if stale) | Cross-portal read gates. |
| 5 | Shop | `testmech@mascigc.com / ResetWorks2026!` | Mechanic role. |
| 6 | HR | `hrmanager@mascigc.com / HRTesting2026!` | Cleaned in 13.4A; baseline screenshots in evidence dir. |
| 7 | Leadership | `MASCIGC` (shared) | `/leadership` gate. |
| 8 | Field Leadership Portal | `fieldleader@mascigc.com` was deactivated 2026-05-31. Reactivate per `/app/memory/test_credentials.md` or skip. | |
| 9 | Driver | TBD — see `dispatch_users` / driver auth model. | |
| 10 | Field Tile | Public field entry tile from `/`. | |
| 11 | Safety Tile | `/safety/forms/login` (password `1982`). | |
| 12 | Public Safety Tile | Public surfaces at `/inspect/new`, `/meetings/new`, etc. | |
| 13 | Public QR access | QR + cheatsheet (`/cheatsheet`). | |
| 14 | Asset lookup | `/operations-map?asset=…`, public asset detail surface if any. | |
| 15 | Training surfaces | `/hr/training-records`, `/safety-portal/training`, training tile flows. | |
| 16 | Governance surfaces | `GovernanceHealthChip` placements + `/admin/governance` deep links. | |
| 17 | Guides | `/guidance?from=<portal>` family. | |

---

## 3. Audit dimensions (per surface)

For each surface, capture and score:

1. **Verbiage** — operator words; no engineering jargon; no
   "Operations Center" appearing inside HR; etc.
2. **Status language** — does "Live", "Stale", "Idle", "No Recent
   Updates", "Open", "Active", "Working", etc. mean the same thing
   across portals? Flag inconsistencies.
3. **Theme consistency** — accent colour per portal (HR violet/green
   stripes, Dispatch orange, Safety cyan, Shop orange, PM indigo,
   Field Leadership red, Leadership red); ensure tile stripes,
   buttons, and badges follow the palette table in `portalPalette.js`.
4. **Role clarity** — could an operator who lands cold tell *which*
   portal they're in within 3 seconds? Title strip, kicker, chip, and
   page heading must agree.
5. **Portal cohesion** — same layout DNA (header chrome, KPI strip,
   group sections, expirations card if applicable). No leftover
   admin-style sections leaking into operator portals (this was the
   13.4A pattern; verify it's gone everywhere, not just HR).
6. **Coaching / guidance presence** — does every surface link to its
   Training Center & Guides entry? Are CTAs verbiage-aligned?

Score each dimension 0 / 1 / 2 (0 = wrong portal, 1 = drift, 2 = clean).

---

## 4. Dedicated subsection — Dispatch Data Integrity / Motive Reality

Per operator directive, Track 13.4B's report MUST include a separate
**Dispatch Data Integrity / Motive Reality** appendix that captures:

- **Production Motive webhook activity** — verify `db.motive_events`
  growth rate on production. Sample latest 24h and document arrival
  cadence.
- **Preview vs production feed behaviour** — explicit comparison of
  `feed_status`, `as_of` lag, GPS coverage rate, and band distribution.
- **GPS coverage rate** — per `marker_kind` and per equipment age.
  Triage which "no-GPS" assets are *expected dark* (shop equipment,
  trailers without telematics) vs *should-be-live*.
- **Stale position root causes** — list the top 10 oldest position
  events per `unit_number`, what equipment type they are, and
  whether they are still in active service.
- **Motive mapping completeness** — orphans in `db.asset_mappings`
  vs `db.equipment_master` (both directions).
- **Marker category accuracy** — `marker_kind` is heuristically
  derived from the equipment label; cross-check against
  `equipment_master.type`.
- **Operational summary count accuracy** — independently rederive
  `total / attention / no_recent / working / idle / assigned` from
  raw collections and confirm `/snapshot` is right.
- **Geofence rendering** — including the 67 circle geofences that
  currently render as 0 (`_polygon_from_motive` skips circles).
  Decide whether 13.4D fixes circle→polygon conversion or whether it
  becomes its own backlog item.
- **Trust verdict** — can Dispatch be trusted as operational truth
  in its current state?

---

## 5. Inputs the next agent should pre-load

- `/app/memory/TRACK_13_4A_KNOWN_DEFECT_CORRECTION_REPORT.md`
- `/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md` (appended for 13.4A)
- `/app/memory/MASCI_BRUTAL_PORTAL_VARIANCE_AUDIT.md`
- `/app/memory/MASCI_ROLE_FIRST_PORTAL_PATTERN.md`
- `/app/memory/test_credentials.md` (NEW PM fixture row added)
- Existing audit-style memory files: `HR_INFORMATION_PRIORITY_MAP.json`,
  `CROSS_PORTAL_COACHING_STANDARD.md`, etc.

---

## 6. Output

- `/app/memory/MASCI_PLATFORM_IDENTITY_RECOVERY_AUDIT.md`
- Append a `Track 13.4B` section to `/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md`.
- Screenshots under `/app/memory/track_13_4b_evidence/`.
- Verdict (one of):
  - `Not Ready — Continue Audit`
  - `Not Ready — Fix List Remains`
  - `Ready for Operator Review`
- **NOT** `Ready to Deploy`. Deploy remains forbidden until at minimum
  Tracks 13.4C and 13.4D also complete.

---

## 7. Rules (carried over from 13.4A)

- No deploy.
- No GitHub save / push / merge.
- No new features.
- No DOM-only validation — operator-view screenshots win.
- Defects found should be **documented** here, not silently patched
  (unless explicitly escalated to a sub-track like 13.4A).
- Don't use super-admin to fake a per-portal operator view.
- Don't ship certification language ("PASS", "Ready to Deploy", etc.).
