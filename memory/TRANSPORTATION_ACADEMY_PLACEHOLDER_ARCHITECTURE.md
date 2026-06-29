TRANSPORTATION ACADEMY · PLACEHOLDER ARCHITECTURE
==================================================

The "placeholder" experience is the production-quality state shown to
users for any Academy module that has metadata but no published video.

────────────────────────────────────────────────────────────────────────────
DESIGN PRINCIPLE
────────────────────────────────────────────────────────────────────────────
A Transportation Academy module is NEVER an empty card, a "Coming
Soon" graphic, or a blank route. Even when the video is in production,
the module must look intentional, complete, premium, and enterprise-grade
— consistent with the Six Pillars of the ForgedOps Constitution.

────────────────────────────────────────────────────────────────────────────
TWO PLACEMENT SURFACES
────────────────────────────────────────────────────────────────────────────
1. ACADEMY GRID CARD (`/transportation-operations/academy`)
   File: `TransportationAcademy.jsx :: ModuleCard`.

   Every card displays:
     · "Module N" eyebrow (uppercase mono, slate-500)
     · Status chip (Published = emerald · In Development = amber)
     · Title (lg, semibold)
     · 3-line description
     · Metadata strip: runtime · language · topic count · Required badge
     · CTA button:
        - Published → primary "Watch" with Play icon
        - In Development → outline "View details" with Wrench icon

   Both states share the same shadow, padding, border, and hover
   behaviour. There is no visual class system that signals
   "unfinished" — the Status chip alone communicates state.

2. MODULE DETAIL (`/transportation-operations/academy/:moduleKey`)
   File: `TransportationAcademy.jsx :: TransportationAcademyModule`.

   Published modules render `PublishedVideo`:
     · Native HTML5 `<video src controls>` from `placeholders.en.video_url`
     · Title bar with module number + runtime
     · Reserved quiz disclosure footer

   In-Development modules render `InDevelopmentPanel`:
     · Dark gradient (slate-900 → amber-950) with `Wrench` glyph
     · Headline: "Module in production"
     · Canonical professional copy (no "Coming Soon", no spinner):

         "This Transportation Academy module is currently in
          production and will be published in a future platform
          release. Continue completing the currently available
          modules while additional training becomes available."

   Below the panel (both states):
     · Learning Objectives list (emerald check icon · 3-5 items)
     · Topics Covered list (emerald check icon · 3-10 items)
     · Previous / Next module navigation cards
     · Reserved knowledge-check disclosure
       "Knowledge check reserved for a future release
        (passing score 80% · 5 questions)."

────────────────────────────────────────────────────────────────────────────
VIDEO PLAYER FALLBACK (for legacy / non-Academy surfaces)
────────────────────────────────────────────────────────────────────────────
File: `MasciVideoPlayer.jsx`.

Render order is explicit:
  1. `placeholder.video_url` (or `module.video_url`) → native `<video src>`
     with controls. PRIMARY Academy path.
  2. Legacy `placeholder.sky_asset_id` → Sky-AI placeholder mode
     (existing Track 16.08 behaviour for admin previews of pre-Academy
     content).
  3. NEITHER present → the same canonical "Module in production" copy
     used by the Academy detail page. The legacy
     "Sky AI video placeholder · {title}" copy has been removed from
     the Academy user-facing path.

────────────────────────────────────────────────────────────────────────────
WHY THIS ARCHITECTURE STAYS STABLE
────────────────────────────────────────────────────────────────────────────
  · One canonical "In Development" treatment everywhere. Switching to
    Published is a metadata patch — no copy hunting, no dead routes.
  · The placeholder copy is one sentence. It is the same on the card,
    the detail panel, and the legacy player fallback. Operators only
    edit one canonical string when they want to refine the message.
  · `video_url` is independent of `sky_asset_id`. Future Sky-AI runs,
    re-hosting to R2, and direct mp4 uploads all flow through the
    same field with no architecture change.
  · Quiz fields are already reserved. The Track 19.02 quiz engine
    plugs in without touching this architecture.

────────────────────────────────────────────────────────────────────────────
ANTI-PATTERNS (explicitly NOT used)
────────────────────────────────────────────────────────────────────────────
  · No "Coming Soon" graphics.
  · No animated spinners or loading bars on In-Development cards.
  · No `[Coming in v2]` badges.
  · No greyed-out / disabled cards. Every card is interactive.
  · No `404 · Module not yet live` style redirects.
  · No "Sky AI placeholder" surfaced to Transportation users.

────────────────────────────────────────────────────────────────────────────
TESTIDS (frontend QA hooks)
────────────────────────────────────────────────────────────────────────────
  · `transportation-academy-page`
  · `academy-progress-strip` · `academy-progress-pct` · `academy-progress-bar`
  · `academy-modules-grid`
  · `academy-card-{key}` · `academy-card-{key}-status` · `academy-card-{key}-open`
  · `academy-detail-{key}` · `academy-detail-status` · `academy-detail-back`
  · `academy-detail-objectives` · `academy-detail-topics`
  · `academy-detail-prev` · `academy-detail-next`
  · `academy-published-video` · `academy-video-element`
  · `academy-in-development-panel`
  · `txops-nav-academy` (sidebar)
  · `masci-video-placeholder` (legacy player fallback path)
