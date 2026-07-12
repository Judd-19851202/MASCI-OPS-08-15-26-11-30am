"""Operator-flow walkthrough runner (iter217).

Lightweight, operational, NOT a generic-UI-automation framework.
Each walkthrough simulates a real persona's day on the MASCI platform,
observes coaching-surface quality, and captures FINDINGS that become
the editorial refinement backlog for the HelpTip engine.

Design rules:
  • One Python file per persona. Each is a runnable script.
  • Findings are typed (friction · missing-coaching · weak-tip ·
    unclear-wording · discoverability-gap · mobile-clipping ·
    workflow-confusion · no-escalation-path).
  • Every step captures a screenshot. Screenshots live under
    /app/walkthrough_reports/{persona}/{step}.png.
  • Findings live at /app/walkthrough_reports/{persona}_findings.json
    so the editorial workflow can read them with grep/jq.
  • No analytics. No telemetry. No new Mongo collections. Walkthroughs
    are an EDITORIAL TOOL, not a production feature.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# Allowed finding kinds — guards against drift in vocabulary.
FINDING_KINDS = {
    "friction",
    "missing-coaching",
    "weak-tip",
    "unclear-wording",
    "discoverability-gap",
    "mobile-clipping",
    "workflow-confusion",
    "no-escalation-path",
    "voice-drift",
    "positive-observation",   # not a problem — captures what's working well
}

REPORT_DIR = Path("/app/walkthrough_reports")
DEFAULT_BASE_URL = os.environ.get(
    "WALKTHROUGH_BASE_URL",
    os.environ.get(
        "REACT_APP_BACKEND_URL",
        "https://backup-forensics.preview.emergentagent.com",
    ),
)


class Walkthrough:
    """Per-persona walkthrough session — runner + finding log + shotter."""

    def __init__(
        self,
        persona: str,
        viewport: dict[str, int],
        base_url: Optional[str] = None,
        device_label: str = "",
    ):
        if not re.match(r"^[a-z][a-z0-9_-]*$", persona):
            raise ValueError(f"persona slug must be lowercase-kebab: got {persona!r}")
        self.persona = persona
        self.viewport = viewport
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.device_label = device_label or f"{viewport['width']}x{viewport['height']}"
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.steps: list[dict] = []
        self.findings: list[dict] = []
        self.shots_dir = REPORT_DIR / persona
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        self.current_step: Optional[str] = None

    # ── lifecycle ────────────────────────────────────────────────────
    def begin_step(self, slug: str, label: str, url: str = "") -> None:
        if not re.match(r"^[a-z0-9-]+$", slug):
            raise ValueError(f"step slug must be lowercase-kebab: got {slug!r}")
        self.current_step = slug
        self.steps.append({
            "slug": slug,
            "label": label,
            "url": url,
            "ts": datetime.now(timezone.utc).isoformat(),
            "helptips": None,
            "shot": None,
        })

    def record_helptips(self, helptip_blocks: dict[str, int]) -> None:
        """Record the HelpTip surfaces visible at the current step.

        helptip_blocks is the mapping returned by find_helptips_js() in
        the page's JS context: {block_testid -> toggle_count}.
        """
        if not self.steps:
            return
        self.steps[-1]["helptips"] = helptip_blocks
        if not helptip_blocks:
            # Auto-flag: a workflow step with zero coaching surface is
            # a discoverability gap by default (the operator can mark
            # it as intentional later).
            self.note(
                "discoverability-gap",
                f"Step {self.current_step!r} ({self.steps[-1]['label']}) has zero HelpTip blocks rendered.",
                f"Consider whether this step needs a coaching surface, or document why it does not.",
            )

    def shot_path(self, label: str = "") -> str:
        slug = self.current_step or "shot"
        suffix = f"_{label}" if label else ""
        return str(self.shots_dir / f"{slug}{suffix}.png")

    def note(self, kind: str, observation: str, action: str = "") -> None:
        """Record a finding tied to the current step."""
        if kind not in FINDING_KINDS:
            raise ValueError(
                f"unknown finding kind {kind!r}; allowed: {sorted(FINDING_KINDS)}"
            )
        self.findings.append({
            "persona": self.persona,
            "step": self.current_step,
            "kind": kind,
            "observation": observation.strip(),
            "suggested_action_item": action.strip(),
            "ts": datetime.now(timezone.utc).isoformat(),
        })

    def finalize(self) -> dict:
        """Emit the findings + step log JSON. Returns the report dict."""
        # Tally findings by kind for the editorial summary.
        tally: dict[str, int] = {}
        for f in self.findings:
            tally[f["kind"]] = tally.get(f["kind"], 0) + 1
        report = {
            "persona": self.persona,
            "device": self.device_label,
            "viewport": self.viewport,
            "base_url": self.base_url,
            "started_at": self.started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "step_count": len(self.steps),
            "finding_count": len(self.findings),
            "finding_tally": tally,
            "steps": self.steps,
            "findings": self.findings,
        }
        out_path = REPORT_DIR / f"{self.persona}_findings.json"
        out_path.write_text(json.dumps(report, indent=2))
        return report


# ─────────────────────────────────────────────────────────────────────
# JS payloads — kept here so each persona walkthrough stays focused on
# operational steps, not DOM-introspection code.
# ─────────────────────────────────────────────────────────────────────

FIND_HELPTIPS_JS = """() => {
  const out = {};
  document.querySelectorAll('[data-testid^="helptip-block-"]').forEach(el => {
    const id = el.getAttribute('data-testid');
    if (id && !id.endsWith('-counter')) {
      out[id] = el.querySelectorAll('[data-testid$="-toggle"]').length;
    }
  });
  return out;
}"""

EXPAND_HELPTIPS_JS = """(blockId) => {
  const block = document.querySelector('[data-testid="' + blockId + '"]');
  if (!block) return 0;
  const toggles = block.querySelectorAll('[data-testid$="-toggle"]');
  toggles.forEach(t => { try { t.click(); } catch(e) {} });
  return toggles.length;
}"""


# ─────────────────────────────────────────────────────────────────────
# Persona authentication helpers — operator-tested credentials only.
# All come from /app/memory/test_credentials.md.
# ─────────────────────────────────────────────────────────────────────

PERSONA_LOGIN_JS = {
    # Field Leadership shared password (foremen, supers, ops oversight)
    "leadership": """async (baseUrl) => {
        const r = await fetch(baseUrl + '/api/field-leadership/login', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({password: 'MASCIGC'})
        });
        const d = await r.json();
        if (d.token) {
            window.sessionStorage.setItem('masci.leadership.token', d.token);
            window.sessionStorage.setItem('masci.leadership.issued', String(Date.now()));
        }
        return d.token ? true : false;
    }""",
    # Multi-portal super-admin (gives admin/pm/shop/hr/safety/dispatch tokens)
    "multi": """async (baseUrl) => {
        const r = await fetch(baseUrl + '/api/auth/multi-login', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({email:'jaymn.judd@mascigc.com', password:'Maddix123!'})
        });
        const d = await r.json();
        if (d.portal_tokens) {
            for (const role of Object.keys(d.portal_tokens)) {
                window.localStorage.setItem('masci.' + role + '.token', d.portal_tokens[role]);
            }
        }
        return d.ok === true;
    }""",
}


def auth_persona(page, persona_kind: str, base_url: str) -> bool:
    """Sync-Playwright helper. Seeds the right session token for the
    persona. persona_kind ∈ {'leadership', 'multi'}."""
    js = PERSONA_LOGIN_JS.get(persona_kind)
    if not js:
        return False
    return bool(page.evaluate(js, base_url))


# ─────────────────────────────────────────────────────────────────────
# Runner main entrypoint — used by each persona script's __main__.
# ─────────────────────────────────────────────────────────────────────

def run(persona_fn: Callable[[Any, "Walkthrough"], None],
        persona: str,
        viewport: dict,
        device_label: str = "",
        auth_kind: Optional[str] = None) -> dict:
    """Boot Playwright, run the walkthrough function, finalize the report."""
    from playwright.sync_api import sync_playwright

    wt = Walkthrough(persona, viewport, device_label=device_label)
    print(f"[walkthrough] {persona} · {wt.device_label} · {wt.base_url}")

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception as e:
            print(f"[walkthrough] chromium unavailable: {e}")
            wt.note(
                "friction",
                f"Walkthrough could not run: chromium binary unavailable ({e}).",
                "Install/repair Playwright chromium for editorial walkthrough runs.",
            )
            return wt.finalize()

        ctx = browser.new_context(viewport=viewport, ignore_https_errors=True)
        page = ctx.new_page()

        # Land on the public hub first so authentication seed can hit
        # the right origin (cookies / storage are origin-scoped).
        page.goto(wt.base_url + "/", wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(500)

        if auth_kind:
            ok = auth_persona(page, auth_kind, wt.base_url)
            if not ok:
                wt.note(
                    "friction",
                    f"Persona authentication ({auth_kind}) failed at session boot.",
                    "Verify test_credentials.md and the corresponding /api/.../login endpoint.",
                )

        try:
            persona_fn(page, wt)
        except Exception as e:
            wt.note(
                "friction",
                f"Walkthrough aborted mid-script: {type(e).__name__}: {e}",
                "Investigate the offending step — likely a route change or selector drift.",
            )
            # Always capture a final-state shot so we know where it died.
            try:
                page.screenshot(path=wt.shot_path("abort"), full_page=False)
            except Exception:
                pass

        ctx.close()
        browser.close()

    report = wt.finalize()
    print(f"[walkthrough] {persona} · {report['step_count']} steps · "
          f"{report['finding_count']} findings · tally={report['finding_tally']}")
    return report
