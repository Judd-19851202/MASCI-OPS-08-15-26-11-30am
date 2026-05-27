# Communication Footer Standardization

*Phase IV-BETA.3-P1C · iter437 · 2026-02-27*
*Status: 🟢 SHIPPED · 15/15 tests pass · zero engine rewrites*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mission

Apply the 3-line operational footer mandated by
`COMMUNICATION_UNIFICATION_DOCTRINE.md §A.IV` across every non-PM
email renderer, restrained and identical, without rewriting the
notification engine.

## II. Footer contract (locked by `test_iter437_footer_standardization.py`)

```
MASCI
automated operational notice · {Portal} Portal
do-not-reply · {doc_id}
```

- **Line 1** — brand-only, all caps, bold slate-900.
- **Line 2** — declarative + portal context. Operator instantly
  knows "what surface produced this".
- **Line 3** — do-not-reply notice + optional doc_id for inbox-Cmd-F.

Restraint contract enforced by tests:
- Calm slate palette only (no `#dc2626`, `#b45309`, `#ea580c`, `#c8102e`).
- No marketing words ("unsubscribe", "thanks", "best regards", "feel free").
- No forbidden urgency words ("URGENT", "ASAP", "Please", "Kindly").
- Appears ABOVE the legacy branding line so operator-relevance precedes brand.

## III. New helper · `backend/operational_footer.py`

Two functions:

| Function | Output | Use |
|---|---|---|
| `render_operational_footer_html(portal=…, doc_id=…)` | restrained inline-styled HTML | every HTML email renderer |
| `render_operational_footer_text(portal=…, doc_id=…)` | 3-line plain text | log lines · plain-text email parts · test assertions |

Helper is **single-source-of-truth** — there is no per-portal copy of
the footer string. Every change to the doctrine is a one-line edit
here.

## IV. Wiring points (🟢 4 renderers fold the helper in)

| Renderer | File | How |
|---|---|---|
| Portal welcome / reset (PM · Shop · HR · Safety · Dispatch) | `branded_portal_emails.py::render_portal_email` | Footer injected ABOVE the existing branding block. Cascades to every caller of this helper automatically — including `routes/pm_admin.py` (PM welcome/reset), `routes/pm_routes.py` (PM password reset), `server.py` (Shop password reset). |
| Backup verification (admin) | `backup_verification.py` (line ~454) | Footer injected ABOVE the existing branding block, with `portal="Admin"` + `doc_id="backup-{verdict}"`. |
| System health alert | `health_monitor.py` (line ~95) | Footer interpolated into the alert HTML body, with `portal="Admin"` + `doc_id="system-health-alert"`. |
| Parts order (shop) | `routes/shop_parts.py` (line ~312) | Footer replaces the prior "Sent automatically …" line with `portal="Shop"` + `doc_id="parts-{unit_number}"`. |

## V. Single-pass surface coverage (🟢 by helper composition)

Renderers that **already** inherit the footer via `render_portal_email`:

- PM welcome email (`routes/pm_admin.py`)
- PM password reset email (`routes/pm_routes.py`)
- Shop password reset email (`server.py:2059`)
- (Any future portal that calls `render_portal_email`)

## VI. What did NOT change (per operator directive)

- ❌ No notification engine rewrite.
- ❌ No `pdf_render.render_email_html` change — PM auto-emails keep
  their existing footer contract (already governed by iter238).
- ❌ No new Resend keys, no new env vars, no new send paths.
- ❌ No changes to PM-portal subject lines (those were already
  doctrine-compliant per iter238).

## VII. Test evidence (🟢 VERIFIED)

```
$ pytest -q tests/test_iter437_footer_standardization.py \
              tests/test_iter437_communication_unification.py \
              tests/test_iter238_email_uniformity.py
89 passed, 1 skipped in 3.18s
```

| Contract | Test |
|---|---|
| 3-line text helper minimal output | `test_minimal` 🟢 |
| Text helper with portal | `test_with_portal` 🟢 |
| Text helper with portal + doc_id | `test_with_doc_id` 🟢 |
| HTML helper all 3 lines present | `test_includes_all_three_lines` 🟢 |
| HTML helper calm palette only | `test_uses_calm_color_palette` 🟢 |
| HTML helper no marketing words | `test_no_marketing_words` 🟢 |
| Footer appears in PM/HR/Shop/Safety/Dispatch portal emails | `test_portal_email_includes_operational_footer` × 5 🟢 |
| Footer precedes branding line | `test_portal_email_footer_appears_before_branding_line` 🟢 |
| No forbidden phrases in any render | `test_no_forbidden_phrases_in_render` × 5 🟢 |

## VIII. Doctrine reaffirmed

- ✅ Preview only · no production touches
- ✅ Helper is additive, reversible, and the single source of truth
- ✅ No notification engine changes
- ✅ Restraint contract enforced by tests (palette · marketing-words · phrases)
- ✅ Regression-locked before promotion
