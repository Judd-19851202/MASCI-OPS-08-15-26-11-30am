# ODR Platform Inheritance Doctrine

_Phase V.1 · M0.35 Doctrine Lock #2 · 2026-05-29 · permanent inheritance contract._

> **ODR is NOT a standalone product. ODR is a module of MASCI Ops.**

A foreman, superintendent, PM, dispatcher, safety manager, and executive
must feel they are using **one operating system** — never multiple
systems stitched together. ODR inherits the platform's visual, navigational,
and operational doctrines without exception. Divergence requires
documented justification and explicit operator approval.

---

## 1 · The single test

> **Does this ODR surface feel like "MASCI Ops" — or like "a separate
> application inside MASCI Ops"?**

If the answer is "a separate application," the surface fails this
doctrine and must be brought into platform alignment before merge.

## 2 · Mandatory inherited doctrines

ODR MUST inherit and conform to every one of the following platform
doctrines. These are non-negotiable inheritance points.

| Doctrine | File | What ODR must respect |
|---|---|---|
| **Platform Navigation** | `PLATFORM_WIDE_NAVIGATION_DOCTRINE.md` | Sidebar shape · breadcrumb pattern · back-link inheritance · context retention |
| **Shared Component Governance** | `SHARED_COMPONENT_GOVERNANCE.md` | Card shells · dialog shells · table shells · empty states · skeleton loaders |
| **Cross-Portal Consistency** | `CROSS_PORTAL_CONSISTENCY_STANDARD.md` | Visual hierarchy across Admin / PM / FL / Safety / Dispatch |
| **Operational Calmness** | `OPERATIONAL_CALMNESS_AUDIT.md` + `CALM_OBSERVABILITY_UI.md` | Single-red doctrine · no exclamation marks · no urgency pills on routine state |
| **Timeline Doctrine** | `OPERATIONAL_TIMELINE_FOUNDATION.md` + `TIMELINE_CALMNESS_CERTIFICATION.md` | Sidecar position · row shape · density heuristics |
| **Operational Linking Rules** | `OPERATIONAL_LINKING_RULES.md` | `operational_links` substrate · cross-artifact tie semantics |
| **Photo Governance** | `PHOTO_GOVERNANCE_STANDARD.md` | Photo-as-evidence · attachment lifecycle · audit footer |
| **Field Leadership Visibility** | `FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md` | Superintendent / FL inbox shape · review queue ergonomics |

## 3 · Inheritance scope (what must look platform-native)

ODR surfaces must visually and behaviorally match MASCI Ops on every
one of these dimensions:

| Dimension | Inheritance requirement |
|---|---|
| **Navigation** | Sidebar entries · top-nav slot · breadcrumb chain · back-button behavior |
| **Cards** | Border radius · shadow scale · padding scale · header pattern |
| **Dialogs** | Width · scroll behavior · footer button order · close-on-escape semantics |
| **Filters** | Filter chip shape · clear-all affordance · saved-filter persistence |
| **Tables** | Row height · zebra rule · hover state · column header weight |
| **Coaching** | Tone (calm · operational · non-corporate) · bilingual placement · drawer pattern |
| **Colors** | Single-red doctrine · status palette · neutral surface ramp |
| **Timelines** | Sidecar pattern · density · grouping · skeleton |
| **Mobile interactions** | Touch target ≥ 44pt · gesture fall-throughs · iOS Safari quirks already absorbed |
| **Spacing** | 4 / 8 / 12 / 16 / 24 / 32 scale (platform-wide) |
| **Typography** | Platform font stack · weight scale · line-height ramp |
| **Hierarchy** | H1 / H2 / body / accent scale matches platform standard |

If an ODR surface introduces a new shape on any of these dimensions
without going through the divergence flow, it is in violation of this
doctrine.

## 4 · Divergence flow (the only path to deviation)

When a legitimate ODR-specific need cannot be satisfied by inherited
doctrines, the divergence MUST follow this four-step flow:

| Step | Required artifact |
|---|---|
| **1 · Documentation** | Markdown file in `/app/memory/` explaining the precise divergence |
| **2 · Justification** | Why the inherited doctrine cannot satisfy the field need |
| **3 · Review** | Cross-portal review (PM + FL + Safety + Admin owner) |
| **4 · Approval** | Explicit operator approval logged in `PRD.md` |

PRs introducing divergence without all four steps are **not eligible
for merge.** Reviewers treat undocumented divergence as a doctrine
violation.

## 5 · The "one operating system" promise

The user-facing promise this doctrine protects:

> A foreman opening ODR feels they opened the same MASCI app they
> use for daily reports, photos, and timelines.
>
> A PM opening the ODR Panel feels they opened the same MASCI app
> they use for project status and dispatch.
>
> A superintendent opening the FL ODR Center feels they opened the
> same MASCI app they use for crew oversight.

Every persona must perceive **continuity**, not a new product they
have to learn. ODR is a feature of MASCI Ops — not a tenant of it.

## 6 · Anti-patterns this doctrine forbids

1. **Custom sidebar inside ODR** — must use the platform sidebar
2. **Custom card shape inside ODR** — must use shared `Card` shell
3. **Custom dialog framework inside ODR** — must use shadcn `Dialog` shell
4. **Custom color tokens inside ODR** — must use platform tokens
5. **Custom font stack inside ODR** — must use platform font stack
6. **Custom timeline visualization inside ODR** — must use sidecar pattern
7. **Custom filter UX inside ODR** — must use platform filter chips
8. **Custom photo viewer inside ODR** — must use photo-governance shell
9. **Custom auth gate inside ODR** — must use platform auth context
10. **Custom toast / banner system inside ODR** — must use `sonner` + platform banners

## 7 · Probe / regression coverage

The Cross-Portal Consistency probe (planned for M2+) will surface
inheritance violations programmatically. Until that probe ships, the
following manual gates apply on every ODR PR:

- [ ] Visual diff against existing platform surfaces (PM Hub · FL Center · Admin)
- [ ] Inherited component imports verified (no new card / dialog / filter)
- [ ] Color tokens verified (no hex literals · no off-palette colors)
- [ ] Mobile interaction parity verified (44pt targets · iOS Safari fall-throughs)
- [ ] Coaching tone parity verified against `CROSS_PORTAL_COACHING_STANDARD.md`

## 8 · Relationship to Simplicity Test Doctrine

This doctrine and `ODR_SIMPLICITY_TEST_DOCTRINE.md` operate together:

| Doctrine | Question it answers |
|---|---|
| **Simplicity Test** | Can a tired foreman in mud complete this? |
| **Platform Inheritance** | Does this feel like the same MASCI app? |

A change must pass **both** doctrines. Passing one and failing the
other is a hard block on merge.

## 9 · M1 authorization gate

🛑 **M1 (migration · dual-write · pilot) may not begin** until this
doctrine is registered and acknowledged by the operator review.

This is a **Doctrine Lock** — ODR will not be allowed to drift into
its own visual/behavioral kingdom, no matter how operationally
ambitious the next phase becomes.

---

_End of ODR_PLATFORM_INHERITANCE_DOCTRINE.md · permanent ODR inheritance contract._
