# TRACK 18.11 · R8 Duplicate CTA Linter Calibration

**Status:** ✅ GO · R8 active · 0 current violations · Permanent forward-looking guardrail
**Date:** 2026-02-10

---

## Executive Summary

Track 18.09 attempted R8 ("Duplicate CTA on a single card") and **correctly deferred** when the initial naive proximity scanner tripped on `aria-label`s, status pills, dropdown items, and i18n catalog entries. Track 18.10 then locked the governance boundary linter (administration vs operations) — leaving R8 as the last open item in the design-system enforcement stack.

Track 18.11 finishes R8 with a **conservative, allow-list-first, high-confidence** implementation that matches the directive's explicit rule: *"This rule must be conservative and high confidence."*

* The audit reviewed **15 operational workspace surfaces**. **Zero** current R8 violations.
* The R8 implementation scans only `<Card>...</Card>` blocks and only counts buttons that pass a **primary-CTA signature** (no `outline` / `ghost` / `link` / `secondary` / `destructive` variant).
* The implementation **excludes** Buttons inside `<Table*>`, `<DropdownMenu*>`, `<Tabs>`, `<NavigationMenu>`, `<Pagination>`, `<Breadcrumb>`, `<Popover>`, `<Select>`, `<TableRow>`, `<TableCell>` subtrees before counting.
* The implementation **ignores** `<Badge>`, `<StatusChip>`, `<BandChip>` (status chips), `aria-label`, `title`, and i18n catalog strings.
* **R8 ships with 4 seeded "should-fail" fixtures and 8 seeded "should-not-fail" fixtures** to permanently lock false-positive behavior.

---

## Workstream summary

| Workstream | Result |
|---|---|
| 1 · Audit CTA patterns | `R8_CTA_PATTERN_AUDIT.md` — 15 workspaces audited; 0 violations |
| 2 · Define CTA hierarchy registry | Documented in `R8_CTA_PATTERN_AUDIT.md` (PRIMARY / SECONDARY / UTILITY / ROW-LIST / PAIRED / NAVIGATION / DROPDOWN ITEM / STATUS CHIP / EXEMPT) |
| 3 · Implement R8 linter | Added to `backend/tests/test_track_18_07_design_system_linter.py` (rule activated; deferral marker replaced with the live rule) |
| 4 · Seed test fixtures | 4 should-fail + 8 should-not-fail inline string fixtures in the new lock file |
| 5 · Apply low-risk fixes | **None required** — audit found zero violations |
| 6 · Document allow-list | `R8_DUPLICATE_CTA_ALLOWLIST.md` — empty at ship time; documented exception process |

---

## R8 rule (precise)

A file is flagged if **all** of the following are true within a single `<Card>...</Card>` block (after excluding the exemption subtrees below):

1. **≥ 2** `<Button` elements remain.
2. **None** of those `<Button`s have a `variant=` attribute equal to `outline`, `ghost`, `link`, `secondary`, or `destructive`.
3. The file does **not** appear in `R8_DUPLICATE_CTA_ALLOWLIST.md`.

### Exemption subtrees (stripped before counting)
* `<Table>...</Table>`, `<TableRow>...</TableRow>`, `<TableCell>...</TableCell>`
* `<DropdownMenu>...</DropdownMenu>` and any `<DropdownMenu*>` variants
* `<Tabs>...</Tabs>`, `<TabsList>...</TabsList>`
* `<NavigationMenu>...</NavigationMenu>`
* `<Pagination>...</Pagination>`
* `<Breadcrumb>...</Breadcrumb>`
* `<Popover>...</Popover>`
* `<Select>...</Select>`

### Ignored entirely
* `<Badge>`, `<StatusChip>`, `<BandChip>`, `<Chip>` (status chips are not Buttons).
* `aria-label`, `title`, `data-*` attribute strings (not user-visible CTA text).
* i18n keys / catalog entries.
* Icon-only Buttons with `aria-label` + `title` (covered separately by 18.09A).

### Error message
```
R8 Duplicate CTA: <file>:<line> — this operational card appears to
contain multiple competing primary actions. Keep one primary CTA and
downgrade the rest to secondary (variant="outline") / utility
(variant="ghost") / icon-only with aria-label. If this is an approved
paired workflow (e.g., Save/Cancel, Approve/Needs Correction), add an
allow-list entry to R8_DUPLICATE_CTA_ALLOWLIST.md.
```

---

## CTA hierarchy registry

See `R8_CTA_PATTERN_AUDIT.md` for the full registry.

| Category | Visual treatment |
|---|---|
| PRIMARY CTA | Button default (no `variant=`) — one per card |
| SECONDARY CTA | `variant="outline"` |
| UTILITY ACTION | `variant="ghost"` or icon-only with `aria-label` |
| ROW / LIST ACTION | Buttons inside `<TableRow>` / list maps |
| PAIRED DECISION | One primary + one outline/ghost (Save/Cancel, Approve/Needs Correction) |

---

## Audit result

**0 R8 violations** across:
* Public Hub · Sign-In · Mission Control · Dispatch Board · Dispatch Command Center · Live Operations Map · Haul Ledger · Project Management home · Human Resources · Safety Operations · Shop Operations · Field Leadership · Administration oversight cards · Operational Guidance Center · Right Rail · Search results · PO Requests

No code fixes were required.

---

## Routes / Auth / RBAC

| Concern | Status |
|---|:---:|
| Routes | ✅ Zero changes |
| Auth helpers (`A`, `TX`, `adminAuth`) | ✅ Preserved |
| RBAC | ✅ Preserved |
| Dispatch portal (`/dispatch-portal/*`) | ✅ Preserved |
| Driver-token surfaces (`/dr/*`) | ✅ Preserved |
| Backend collections | ✅ Preserved |
| Backend endpoints | ✅ Preserved |
| Track 18.07 R1–R7 linter rules | ✅ Preserved |
| Track 18.09C dual doorway | ✅ Preserved |
| Track 18.10 governance boundary linter | ✅ Preserved |

---

## Linter preservation

Track 18.07 R1–R7 + R8 active. The deferral marker at the bottom of `test_track_18_07_design_system_linter.py` is now replaced with the live R8 implementation. All existing 18.07 / 18.08 / 18.10 design-system tests pass unchanged.

---

## Six-Pillar self-check
* **Powerful** ✅ — One clear primary action per card.
* **Simple** ✅ — Operators don't hesitate between competing CTAs.
* **Beautiful** ✅ — CTA hierarchy looks intentional.
* **Trusted** ✅ — Buttons mean what they appear to mean.
* **Proven** ✅ — Enforced by CI with 4 seeded violations + 8 seeded non-violations.
* **Operational** ✅ — Operators can act quickly under pressure.

---

## Risks
None blocking. Minor: future operator may legitimately need a paired action that isn't a documented `outline`/`ghost` combination — the allow-list process documents the resolution path.

## Deferrals
None.

---

## Final certification

🟢 **GO. R8 is active. Future CTA drift fails the gate.**
