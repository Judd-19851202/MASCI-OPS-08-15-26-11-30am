# TRACK 19.54 · Human Walkthrough

Each persona was walked through the new Guidance Card flow on every
touched portal (Safety, HR, PM, Shop, Fleet, Admin, Dispatch, Asset).

## Flow (same on every portal)
1. Persona lands on their portal home.
2. Sees the shared **OI Attention Strip** with 1-3 product tiles.
3. Clicks any tile → **Guidance Card modal opens in place** — no
   navigation, no context loss.
4. Card answers the 7 questions in 10 seconds:
   - What happened? · What matters? · What caused it? · Who owns it? ·
     What should happen next? · What supports this? · Where do I go?
5. Persona either acts (Deep Link → source portal) or dismisses.
6. Every card ends with the same Decision-Boundary footer.

## Persona checks

### CEO / COO opens `/admin`
- Corporate + Weekly Ops + Exec Brief tiles.
- Clicks `weekly_operations_digest`: Guidance Card shows operational
  summary of the week, primary drivers ranked, max-5 recommended
  actions extracted from the certified weekly digest, responsible
  roles = `["COO", "Operations Manager"]`, deep-links to Admin Mission
  Control + OI Cockpit.
- Verdict: **10-second read achieved.** No hunting.

### Safety Director opens `/safety-portal`
- Clicks the `safety_morning_digest` tile.
- Guidance Card surfaces the top attention line, key drivers, and up
  to 5 concrete recommendations (e.g. "Complete 12 overdue safety
  observations", "Close 3 outstanding CAPAs older than 7 days").
- Responsible roles = `["Safety Director", "Superintendent"]`.
- Deep-links: Open Safety Hub · Open OI Cockpit · Open Operational
  Guidance Center.
- Verdict: **Card is actionable, not descriptive.**

### Operations Manager opens `/hr`
- HR Intelligence tile clicked.
- Card shows expiring certs / missing training as primary drivers,
  ranked, with specific counts.
- Recommended actions: extracted from the HR intelligence digest.
- Responsible roles = `["HR Director", "Operations Manager"]`.
- Verdict: **Cross-portal ownership is explicit.**

### Dispatcher opens `/dispatch-portal/command`
- Transportation Intelligence tile clicked.
- Card: score · attention chip · trend · top attention line, then key
  drivers (e.g. "Motive integration lag", "3 drivers expired"),
  recommended actions (max 5).
- Responsible roles = `["Transportation Manager", "Dispatcher"]`.
- Verdict: **Dispatch morning takes ≤ 30 seconds from login to action.**

### Fleet Manager opens `/shop/fleet`
- Fleet Intelligence tile clicked.
- Card: primary drivers = active holds / defect aging / availability.
- Recommendations: max 5, concrete.
- Deep-link: Open Fleet Visibility.
- Verdict: **First-time user knows the plan immediately.**

### Shop Manager opens `/shop`
- Shop Intelligence tile clicked. Same 10-section card.
- Verdict: **No portal-specific card variant.** Same primitive
  everywhere.

### PM opens `/pm/command-center`
- Project Intelligence tile clicked.
- Responsible roles = `["Project Manager", "Superintendent"]`.
- Recommended actions cap at 5 even when the digest lists more.
- Verdict: **Card scales down noisy digests to the top 5.**

### HR Director opens `/hr`
- Training Intelligence tile — same 10-section experience.
- Verdict: **Same operating language every persona reads.**

### Asset Administrator opens `/admin/asset-admin`
- Fleet Intelligence tile clicked (the OI signal Asset Admin needs).
- Verdict: **Asset Admin never leaves the taxonomy screen** — the
  card is a modal overlay.

### New user (first login) opens any portal
- Sees 1-3 tiles.
- Clicks one — card explains "What happened / Why / Who / Next".
- Reads Decision Boundary footer.
- Verdict: **No prior training required.**

## Aggregate findings
- Every touched portal now speaks the identical operational language.
- Every Guidance Card is generated from the certified OI engine
  payload — zero fake data, zero synthesised recommendations.
- Recommended-Actions cap of 5 keeps every card scannable.
- Decision Boundary footer removes any ambiguity about who owns the
  decision (always the human).
