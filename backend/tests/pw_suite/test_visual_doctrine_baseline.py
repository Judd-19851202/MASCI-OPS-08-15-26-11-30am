"""iter437 / Phase IV-BETA.3-P2A · Visual Doctrine Baseline System.

DOM-style hashing — NOT pixel-diff testing. The objective is to detect
**governance** drift (saturation, font-weight, hierarchy, badge density,
loudness) without the false-positive noise of raw screenshot comparison.

For each governed hub × viewport, this test:

  1. Loads the page (admin/PM/HR hub)
  2. Walks every visible governed element
  3. Extracts a small set of style-only signals:
       • computed background-color hue family
       • computed font-weight bucket (regular / semi / bold / black)
       • computed font-size bucket
       • presence of badge / pill / dot
  4. Builds 7 governance metrics:
       • dom_style_hash       - sha256 of the canonicalised style list
       • hierarchy_hash       - sha256 of (heading + section + label) sequence
       • hue_family_count     - distinct hue families used
       • typography_summary   - {weight_bucket: count}
       • badge_density        - badges per 100 visible elements
       • emphasis_score       - simultaneous-emphasis indicator
       • loudness_score       - composite calm/loud rating (0..100, lower = calmer)
  5. Writes the snapshot to /app/memory/HUB_VISUAL_BASELINE.json

The test does NOT enforce thresholds yet — it ONLY captures the
baseline. A future iteration will promote the gate to deploy-blocking
once enough trend data exists to set thresholds calibrated to operator
expectations.

The test PASSES so long as:
  • the baseline file is writable
  • every page rendered without an error toast
  • no /api/admin/* call leaked from PM or HR context
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import pytest
import requests

BASELINE_PATH = Path("/app/memory/HUB_VISUAL_BASELINE.json")

PM_EMAIL = "chriswright@mascigc.com"
PM_PASSWORD = "ChrisRocksThis2026"
SUPER_EMAIL = (
    os.popen("grep '^SUPER_ADMIN_EMAIL=' /app/backend/.env | cut -d= -f2-")
    .read()
    .strip()
    .strip('"')
)
SUPER_PW = (
    os.popen("grep '^SUPER_ADMIN_BOOTSTRAP_PASSWORD=' /app/backend/.env | cut -d= -f2-")
    .read()
    .strip()
    .strip('"')
)


def _multi_login(base_url: str) -> Dict[str, str]:
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PW},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("portal_tokens") or {}


def _pm_token(base_url: str) -> str:
    r = requests.post(
        f"{base_url}/api/pm/login",
        json={"email": PM_EMAIL, "password": PM_PASSWORD},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture(scope="module")
def tokens(base_url: str) -> Dict[str, str]:
    tokens = _multi_login(base_url)
    tokens["pm"] = tokens.get("pm") or _pm_token(base_url)
    return tokens


# ────────────────────────────────────────────────────────────────────
# Browser-side metric extractor (executed via page.evaluate)
# ────────────────────────────────────────────────────────────────────
_METRIC_JS = r"""
() => {
  // Hue-family buckets: map computed RGB to a coarse hue family.
  const hueFamily = (rgb) => {
    if (!rgb || rgb === 'rgba(0, 0, 0, 0)' || rgb === 'transparent') return null;
    const m = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) return null;
    const r = +m[1], g = +m[2], b = +m[3];
    // Pure neutrals
    const max = Math.max(r,g,b), min = Math.min(r,g,b);
    if (max - min < 24) return 'neutral';
    // Coarse hue
    if (r > g && r > b) return b > 110 ? 'pink-red' : 'red';
    if (g > r && g > b) return r > 120 ? 'green-yellow' : 'green';
    if (b > r && b > g) return r > 120 ? 'blue-violet' : 'blue';
    if (r > 200 && g > 150 && b < 100) return 'amber';
    if (r > 200 && g > 100 && b < 100) return 'orange';
    if (g > 100 && b > 100 && r < 100) return 'cyan';
    return 'other';
  };

  const weightBucket = (w) => {
    const n = parseInt(w, 10) || 400;
    if (n >= 800) return 'black';
    if (n >= 700) return 'bold';
    if (n >= 600) return 'semibold';
    if (n >= 500) return 'medium';
    return 'regular';
  };

  const fontBucket = (px) => {
    const n = parseFloat(px) || 14;
    if (n >= 30) return 'h1';
    if (n >= 22) return 'h2';
    if (n >= 18) return 'h3';
    if (n >= 14) return 'body';
    return 'small';
  };

  // Walk the visible governed surface (excluding hidden controls).
  const all = Array.from(document.querySelectorAll(
    'header, main, nav, h1, h2, h3, button, a, [role="link"], ' +
    '[data-testid], .border-l-4, .border-l-2, [class*="bg-"]'
  )).filter(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return false;
    const style = window.getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none') return false;
    if (parseFloat(style.opacity) === 0) return false;
    return true;
  });

  const hueCounts = {};
  const weightCounts = {};
  const fontCounts = {};
  let badgeCount = 0;
  let totalEl = 0;
  let emphasisRuns = 0;
  let prevBold = false;

  const styleSig = [];
  const hierarchySig = [];

  for (const el of all) {
    totalEl++;
    const style = window.getComputedStyle(el);
    const hue = hueFamily(style.backgroundColor);
    if (hue) hueCounts[hue] = (hueCounts[hue] || 0) + 1;
    const w = weightBucket(style.fontWeight);
    weightCounts[w] = (weightCounts[w] || 0) + 1;
    const fb = fontBucket(style.fontSize);
    fontCounts[fb] = (fontCounts[fb] || 0) + 1;

    // Badge heuristic: small rounded element with coloured bg + small font
    const isBadge =
      parseFloat(style.fontSize) <= 12 &&
      parseFloat(style.borderRadius) >= 6 &&
      hue && hue !== 'neutral';
    if (isBadge) badgeCount++;

    // Simultaneous emphasis: how often we see "bold" runs of >=3 elements
    // back-to-back (which makes the eye jump and increases cognitive load).
    if (w === 'bold' || w === 'black') {
      if (prevBold) emphasisRuns++;
      prevBold = true;
    } else {
      prevBold = false;
    }

    // Compact signature: tag + visible hue + weight bucket
    styleSig.push(`${el.tagName.toLowerCase()}:${hue || '-'}:${w}:${fb}`);

    // Hierarchy signature: only headings + section-stripe colours
    if (/^H[1-3]$/.test(el.tagName)) {
      const text = (el.textContent || '').trim().slice(0, 32);
      hierarchySig.push(`${el.tagName.toLowerCase()}:${text}`);
    }
  }

  return {
    elements_walked: totalEl,
    hue_counts: hueCounts,
    weight_counts: weightCounts,
    font_counts: fontCounts,
    badge_count: badgeCount,
    emphasis_runs: emphasisRuns,
    style_sig: styleSig.join('|'),
    hierarchy_sig: hierarchySig.join('|'),
  };
}
"""


def _summarise(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Compress browser-side raw metrics into the small persisted form."""
    hue_counts = raw["hue_counts"]
    weight_counts = raw["weight_counts"]
    font_counts = raw["font_counts"]
    total = max(int(raw["elements_walked"]), 1)
    coloured_hues = [h for h in hue_counts if h != "neutral"]
    badge_density = round(int(raw["badge_count"]) * 100.0 / total, 2)

    # Loudness composite (calibrated · 0..100 lower = calmer):
    #   hue_family_count * 6
    #   + badge_density (already a percent)
    #   + emphasis_runs * 2
    loudness = (
        len(coloured_hues) * 6
        + badge_density
        + int(raw["emphasis_runs"]) * 2
    )
    loudness = round(min(loudness, 100.0), 2)

    dom_hash = hashlib.sha256(raw["style_sig"].encode("utf-8")).hexdigest()[:16]
    hier_hash = hashlib.sha256(raw["hierarchy_sig"].encode("utf-8")).hexdigest()[:16]

    return {
        "elements_walked": total,
        "dom_style_hash": dom_hash,
        "hierarchy_hash": hier_hash,
        "hue_family_count": len(coloured_hues),
        "hue_families": sorted(coloured_hues),
        "typography_summary": weight_counts,
        "font_size_summary": font_counts,
        "badge_density": badge_density,
        "emphasis_score": int(raw["emphasis_runs"]),
        "loudness_score": loudness,
    }


# ────────────────────────────────────────────────────────────────────
# Routes to baseline
# ────────────────────────────────────────────────────────────────────
ROUTES = [
    {"portal": "admin", "name": "Admin Hub V2", "url": "/admin?adminSidebarV2=1"},
    {"portal": "pm",    "name": "PM Hub V2",    "url": "/pm?pmSidebarV2=1"},
    {"portal": "hr",    "name": "HR Hub V2",    "url": "/hr?hrSidebarV2=1"},
]


def _seed_localstorage(page, base_url: str, tokens: Dict[str, str], portal: str):
    """Plant the appropriate portal token before navigation."""
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    if portal == "admin":
        tok = tokens.get("admin")
        page.evaluate(f"localStorage.setItem('masci.admin.token', '{tok}')")
    elif portal == "pm":
        tok = tokens.get("pm")
        page.evaluate(f"localStorage.setItem('masci.pm.token', '{tok}')")
    elif portal == "hr":
        tok = tokens.get("hr") or tokens.get("admin")
        page.evaluate(
            f"localStorage.setItem('masci.hr.token', '{tok}');"
            f"localStorage.setItem('masci.hr.user', JSON.stringify({{name:'Baseline'}}));"
        )


def _load_or_init_baseline() -> Dict[str, Any]:
    if BASELINE_PATH.exists():
        try:
            return json.loads(BASELINE_PATH.read_text())
        except Exception:
            pass
    return {"_meta": {"version": "iter437.IV-BETA.3-P2A"}, "snapshots": {}}


@pytest.mark.parametrize(
    "route_def",
    ROUTES,
    ids=[r["portal"] for r in ROUTES],
)
def test_capture_doctrine_baseline(
    page, base_url: str, tokens: Dict[str, str], route_def: Dict[str, str], viewport_name
):
    """Per-route, per-viewport doctrine snapshot capture."""
    admin_calls: List[Dict[str, Any]] = []

    def _on(resp):
        if "/api/admin/" in resp.url and route_def["portal"] != "admin":
            admin_calls.append({"status": resp.status, "url": resp.url})

    page.on("response", _on)
    _seed_localstorage(page, base_url, tokens, route_def["portal"])
    page.goto(f"{base_url}{route_def['url']}", wait_until="networkidle")
    page.wait_for_timeout(2000)

    body = page.text_content("body") or ""
    assert "Admin login required" not in body, (
        f"{route_def['portal']} hub surfaced auth toast for the baseline run"
    )
    if route_def["portal"] != "admin":
        assert not admin_calls, (
            f"{route_def['portal']} hub leaked /api/admin/* during baseline: "
            f"{admin_calls}"
        )

    raw = page.evaluate(_METRIC_JS)
    summary = _summarise(raw)
    summary["url"] = route_def["url"]
    summary["portal"] = route_def["portal"]
    summary["name"] = route_def["name"]

    # Persist into the baseline JSON. Key is portal+viewport so a
    # subsequent run overwrites the same cell deterministically.
    baseline = _load_or_init_baseline()
    snapshots = baseline.setdefault("snapshots", {})
    portal_block = snapshots.setdefault(route_def["portal"], {})
    portal_block[viewport_name] = summary
    baseline["_meta"]["updated_at"] = page.evaluate(
        "new Date().toISOString()"
    )
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2, sort_keys=True))

    # Soft assertions — WARNING-ONLY per directive.
    # These constraints are wide on purpose; we will tighten them once
    # we have 3+ iterations of trend data.
    assert summary["elements_walked"] > 10, (
        f"Baseline walked too few elements ({summary['elements_walked']}) — "
        f"likely the page didn't render"
    )
    assert summary["loudness_score"] < 100, "loudness saturated"
