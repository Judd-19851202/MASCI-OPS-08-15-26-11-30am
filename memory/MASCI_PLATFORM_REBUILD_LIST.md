# MASCI Platform — Rebuild List (Track 13.4C · Deliverable #5)

**Mode:** documentation only. Identifies surfaces that need redesign — NOT a redesign.

---

## R-01 · Status & Verbiage Engine

**Source findings:** V-10 · V-11 · V-12 · T-12 · R-11.

What requires rebuild:
- A central state-model registry: one place that names every status verb, its closure verb, and its translation key.
- Status verbs must flow through `t()` so the ES dictionary actually fires.
- Mixed case (`Open` / `open`) must collapse to one canonical form per workflow.
- The "what does `offline` mean here?" ambiguity (Dispatch · Driver · Asset) must be resolved by namespacing or renaming, not by hoping operators learn the difference.

Out of scope right now: which engine to use, how to migrate, what schema to choose.

---

## R-02 · Portal Identity & Header

**Source findings:** V-05 · V-06 · V-07 · V-13.

What requires rebuild:
- A single portal-shell component (header chrome + kicker + portal pill + portal switcher) that every portal mounts.
- Hub-file size variance (145 → 668 lines, 4.6×) collapses when the shell carries the chrome.
- Eliminate the ≥ 4 different header strategies observed today.
- The shell must work at desktop · iPad landscape · iPad portrait · phone — V-13 records the mobile evidence gap and the rebuild must close it.

Out of scope right now: which UI library primitives to lean on, how to migrate each hub.

---

## R-03 · Navigation Architecture

**Source findings:** V-09 · R-01 · R-03 · R-04 · R-05.

What requires rebuild:
- A single naming taxonomy for "Center" pages. 8 `*CommandCenter*` pages today need either a true unifying noun or distinct identities ("Trench Operations" is *not* the same as "PM Command Center").
- 8 distinct auth-flow variations collapse to a single flow with portal-aware fan-out post-login.
- Admin health (4 pages) collapse to one Platform Health surface with sub-tabs (Persistence · Production · Stability · Cluster Capacity).
- `AdminCompliance` and `AdminComplianceFindings` collapse to one surface.

Out of scope right now: which surface keeps which name, what the new IA looks like.

---

## R-04 · Theme Layer

**Source findings:** V-01 · V-02 · V-03 · V-04 · W-06 · W-07 · W-19.

What requires rebuild:
- `tokens.css` currently declared "PROPOSAL — NOT YET WIRED" must actually be wired. Every Tailwind color literal becomes a token reference. Until this happens, MASCI cannot retheme even *its own* portals consistently, let alone any future tenant.
- `portalPalette.js` becomes a *consumer* of tokens, not a duplicate source of truth.
- Shop · PM · Field Leadership documented drifts inside `portalPalette.js` get resolved.

Out of scope right now: per-tenant overlay model (that's a ForgedOps concern; here we only rebuild the MASCI theme layer to be ready for it).

---

## R-05 · Command Center Architecture

**Source findings:** V-09 · R-03.

What requires rebuild:
- 8 `*CommandCenter` pages with overlapping signals → either one "Center" per role with a strict role-first contract, or rename non-role centers (Trench, ODR, Operational Guidance) to non-"Center" nouns so the word "Center" reliably means "primary role landing for portal X".
- Each Center then carries the same skeleton: KPI strip · attention queue · domain tiles · expirations · governance chip.

Out of scope right now: which Center keeps which name, the skeleton's component API.

---

## R-06 · Forms Layer (overlap reduction)

**Source findings:** R-02.

What requires rebuild:
- Daily Report · Site Inspection · Incident share photos · crew · narrative fields. A shared sub-form ("event context block") should be authored once and embedded by all three.
- Equipment Issuance · Equipment Training share the same skeleton — same pattern.
- Auth flows (8) share their skeleton — same pattern.

Out of scope right now: form field ordering, validation strategy, mobile form layout.

---

## R-07 · Driver Portal

**Source findings:** V-15 · R-13.

What requires rebuild:
- Driver has tokenized URLs but no static "today" landing surface in `pages/`. Phase 1 inventory could not locate it.
- A real Driver Hub is missing and must be designed (not yet — rebuild list only).

Out of scope right now: what the Driver Hub looks like, what surfaces it owns.

---

## R-08 · Notification Layer

**Source findings:** R-07.

What requires rebuild:
- PO per-action email and PO digest can deliver the same event twice. The digest should suppress events already delivered as per-action.
- Bell, digest, and per-action notifications share no single ownership model — a single registry of notification kinds with audience tagging would resolve this.

Out of scope right now: registry schema, suppression algorithm.

---

## Rebuild discipline

For every Rebuild item:
- It must reference a Preserve-List boundary it will NOT cross.
- It must demonstrate operator value, not just engineering elegance.
- It must come with a migration story (not yet planned).
- It must NOT begin without operator authorisation for the corresponding implementation track.
