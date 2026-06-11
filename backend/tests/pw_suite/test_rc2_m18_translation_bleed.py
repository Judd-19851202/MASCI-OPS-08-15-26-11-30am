"""RC-2 · M-18 GUARDRAIL — Spanish Bleed-Through Smoke Test.

Permanent regression test that fails if ANY trigger English string
leaks into ES mode on a critical route. Catches M-18-class drift
(`Saved just now`, `Section 01`, `Saving draft…` etc.) at PR time.

Doctrine
--------
* English text is OK inside form values, placeholders the user typed,
  email addresses, tracking-number prefixes (`DR-2026-…`), and brand
  proper-nouns (`MASCI`, `Basecamp`, `OnStation`, `FleetWatcher`,
  `MaintainX`, `Motive`, `OSHA`).
* Otherwise, the watch-list words below must not appear as visible
  body text on `/daily/new`, `/jha`, `/inspection/new`, `/meeting/new`,
  `/incident/new`, `/sign-in` while `localStorage.masci.lang === 'es'`.
"""
from __future__ import annotations

import re
import pytest

ROUTES = [
    "/daily/new",
    "/jha",
    "/inspection/new",
    "/meeting/new",
    "/incident/new",
    "/sign-in",
]

# Bleed triggers. \\b enforces whole-word boundaries so "saved-as-draft"
# class names or "Saved" inside an English brand link don't false-match.
TRIGGERS = [
    "Saved",
    "Saving",
    "Save failed",
    "Section",
    "Draft",
    "Unsaved",
    "Recovered",
    "Restore",
    "Submit",
    "Submitted",
    "Loading",
    "Retry",
    "just now",
    r"\d+s ago",
    r"\d+m ago",
    r"\d+h ago",
    r"\d+d ago",
    "on this device",
]

# Allow-list — proper nouns / brands / tracking codes that may appear
# verbatim in any language without being considered bleed-through.
WHITELIST = re.compile(
    r"\b(MASCI|Basecamp|OnStation|FleetWatcher|MaintainX|Motive|OSHA|FORGEDOPS|"
    r"R2|API|DR-\d|EQ-\d|INSP-\d|MTG-\d|JHP-\d|INC-\d|PDF|GPS|VIN|"
    r"yourname@|mascigc\.com|email@|@mascigc|@example|PreviewOnly)\b"
)


def _scan(page) -> list[dict]:
    pattern = "|".join(TRIGGERS)
    return page.evaluate(
        f"""() => {{
          const RX = new RegExp('\\\\b(' + {pattern!r} + ')\\\\b');
          const samples = [];
          const walker = document.createTreeWalker(
            document.body, NodeFilter.SHOW_TEXT, null, false
          );
          let node;
          while ((node = walker.nextNode())) {{
            const text = node.textContent || '';
            if (!text.trim()) continue;
            if (text.trim().length > 200) continue;
            const m = text.match(RX);
            if (!m) continue;
            const p = node.parentElement;
            if (!p || p.offsetParent === null) continue;
            samples.push({{
              word: m[0],
              text: text.trim().slice(0, 120),
              tag: p.tagName,
              tid: p.getAttribute('data-testid') || '',
            }});
            if (samples.length >= 25) break;
          }}
          return samples;
        }}"""
    )


def _filter_brand_only(hits: list[dict]) -> list[dict]:
    out = []
    for h in hits:
        snippet = h.get("text", "")
        if WHITELIST.search(snippet):
            continue
        out.append(h)
    return out


@pytest.mark.parametrize("route", ROUTES)
def test_rc2_m18_no_english_bleed_in_es(base_url, route):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()
        page.goto(f"{base_url}/", wait_until="domcontentloaded", timeout=30_000)
        page.evaluate("() => localStorage.setItem('masci.lang', 'es')")
        page.goto(f"{base_url}{route}", wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(2000)

        bleed = _filter_brand_only(_scan(page))
        browser.close()

        assert not bleed, (
            f"M-18 REGRESSED on {route} in ES mode. English bleed-through: {bleed[:5]}"
        )


def test_rc2_m18_ee_round_trip(base_url):
    """EN → ES → EN round-trip on /sign-in must end where it started."""
    from playwright.sync_api import sync_playwright

    def _wait_h1(page, expected: str, label: str) -> str:
        """Poll for the H1 text to settle to the expected i18n value.

        The i18n hook reads `localStorage.masci.lang` on mount; on slow
        cold-start renders the H1 can briefly read the default-language
        value before the hook runs. Poll for up to 6 s so this test is
        deterministic across the suite (it passes in isolation but
        occasionally raced when chained behind the M-15 sweep).
        """
        deadline_ms = 6_000
        elapsed = 0
        last = ""
        while elapsed <= deadline_ms:
            last = page.locator("h1").first.inner_text().strip()
            if last == expected:
                return last
            page.wait_for_timeout(300)
            elapsed += 300
        return last

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()

        page.goto(f"{base_url}/sign-in", wait_until="networkidle", timeout=30_000)
        page.evaluate("() => localStorage.setItem('masci.lang', 'en')")
        page.reload(wait_until="networkidle")
        h1_en_a = _wait_h1(page, "Sign In", "EN-pre")

        page.evaluate("() => localStorage.setItem('masci.lang', 'es')")
        page.reload(wait_until="networkidle")
        h1_es = _wait_h1(page, "Iniciar Sesión", "ES")

        page.evaluate("() => localStorage.setItem('masci.lang', 'en')")
        page.reload(wait_until="networkidle")
        h1_en_b = _wait_h1(page, "Sign In", "EN-post")

        browser.close()

        assert h1_en_a == "Sign In", f"EN H1 unexpected: {h1_en_a!r}"
        assert h1_es == "Iniciar Sesión", f"ES H1 unexpected: {h1_es!r}"
        assert h1_en_b == "Sign In", f"EN round-trip drifted: {h1_en_b!r}"
