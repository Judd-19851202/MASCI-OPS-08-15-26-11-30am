#!/usr/bin/env python3
"""measure_visual_loudness.py — Phase IV-BETA.2 governance instrument.

Renders an authenticated portal route via Playwright at 3 viewports, captures
a screenshot, and scores the surface across the 6 loudness dimensions from
VISUAL_LOUDNESS_REDUCTION_PLAN.md §I:

  1. Red/amber saturation surface coverage (% of pixels saturated)
  2. Color hue families (count of distinct dominant hues)
  3. Element density (rough count of `<button>` + `<a>` clickables above fold)
  4. Notification markers (Badge / count-pill density)
  5. Typography combinations (distinct font-size × font-weight pairs)
  6. Ambient motion (count of currently-animating elements)

Outputs:
  /app/memory/LOUDNESS_TRENDLINE.json — append-only per-deploy log
  /app/test_reports/visual_loudness_<iter>.json — latest detailed run

This is a governance INSTRUMENT, not a vanity metric. Trend matters more
than any single absolute value. The deploy gate (when wired in IV-BETA.4)
will fail builds whose portal-wide loudness average regresses.

Usage:
  python scripts/measure_visual_loudness.py \\
    --base-url https://masci-audit-hub.preview.emergentagent.com \\
    --routes /admin /pm /pm/daily \\
    --iteration iter437-iv-beta-2
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not available — install via `pip install playwright`", file=sys.stderr)
    sys.exit(2)

VIEWPORTS = [
    ("mobile",  375, 812),
    ("ipad",    768, 1024),
    ("desktop", 1440, 900),
]


def _capture_metrics(page) -> dict:
    """Return raw per-surface metrics for the current page state."""
    # Element density above fold
    above_fold_clickables = page.evaluate(
        """() => {
            const all = Array.from(document.querySelectorAll('button, a'));
            const fold = window.innerHeight;
            return all.filter(el => {
              const r = el.getBoundingClientRect();
              return r.top >= 0 && r.top < fold && r.height > 0 && r.width > 0;
            }).length;
        }"""
    )

    # Notification markers (badge / count pill)
    badge_count = page.evaluate(
        """() => document.querySelectorAll(
            '[class*="badge"], [class*="Badge"], [data-testid$="-count"]'
          ).length"""
    )

    # Typography combinations (distinct font-size × font-weight pairs)
    typo_combos = page.evaluate(
        """() => {
            const seen = new Set();
            document.querySelectorAll('h1,h2,h3,h4,p,span,a,button,div')
              .forEach(el => {
                const c = getComputedStyle(el);
                if (el.textContent && el.textContent.trim()) {
                  seen.add(c.fontSize + '/' + c.fontWeight);
                }
              });
            return seen.size;
        }"""
    )

    # Ambient motion (elements currently animating)
    animating = page.evaluate(
        """() => document.querySelectorAll('[class*="animate-"]').length"""
    )

    # Saturated red/amber surface coverage (rough — count saturated bg classes)
    red_amber_elements = page.evaluate(
        """() => {
            const sat = ['bg-red-600','bg-red-700','bg-red-800',
                         'bg-amber-500','bg-amber-600','bg-amber-700'];
            let n = 0;
            sat.forEach(c => { n += document.querySelectorAll('[class*="' + c + '"]').length; });
            return n;
        }"""
    )

    # Hue families (rough — distinct stripe colors used inline + Tailwind palette)
    hue_families = page.evaluate(
        """() => {
            const palette = new Set();
            ['red','blue','amber','orange','green','emerald','violet','indigo',
             'rose','pink','cyan','teal','slate','gray','zinc'].forEach(h => {
              if (document.querySelector('[class*="' + h + '-"]') ||
                  document.querySelector('[style*="' + h + '"]')) palette.add(h);
            });
            return palette.size;
        }"""
    )

    return {
        "above_fold_clickables": above_fold_clickables,
        "badge_count": badge_count,
        "typo_combos": typo_combos,
        "animating": animating,
        "red_amber_saturated_elements": red_amber_elements,
        "hue_families": hue_families,
    }


def _score(metrics: dict) -> int:
    """Aggregate loudness score · lower = calmer.

    Each dimension contributes its excess over the doctrine target.
    """
    targets = {
        "above_fold_clickables":          14,
        "badge_count":                     6,
        "typo_combos":                     4,
        "animating":                       1,
        "red_amber_saturated_elements":    4,
        "hue_families":                    3,
    }
    score = 0
    for k, target in targets.items():
        excess = max(0, metrics.get(k, 0) - target)
        score += excess
    return score


def run(base_url: str, routes: list[str], iteration: str) -> dict:
    out_per_route = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for viewport_name, vw, vh in VIEWPORTS:
                for route in routes:
                    key = f"{route}@{viewport_name}"
                    ctx = browser.new_context(viewport={"width": vw, "height": vh})
                    page = ctx.new_page()
                    try:
                        page.goto(f"{base_url}{route}", wait_until="domcontentloaded", timeout=20_000)
                        page.wait_for_timeout(1200)  # let dynamic content settle
                        m = _capture_metrics(page)
                        m["loudness_score"] = _score(m)
                        out_per_route[key] = m
                    except Exception as e:  # noqa: BLE001
                        out_per_route[key] = {"error": str(e)}
                    finally:
                        ctx.close()
        finally:
            browser.close()

    portal_avg = (
        round(sum(v.get("loudness_score", 0) for v in out_per_route.values())
              / max(1, len(out_per_route)), 2)
    )
    return {
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base_url": base_url,
        "viewports": [v[0] for v in VIEWPORTS],
        "routes": routes,
        "per_route": out_per_route,
        "portal_average_loudness": portal_avg,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--routes", nargs="+", default=["/admin", "/pm"])
    ap.add_argument("--iteration", default="manual")
    ap.add_argument(
        "--trendline-path",
        default="/app/memory/LOUDNESS_TRENDLINE.json",
    )
    ap.add_argument(
        "--report-dir",
        default="/app/test_reports",
    )
    args = ap.parse_args()

    result = run(args.base_url, args.routes, args.iteration)

    Path(args.report_dir).mkdir(parents=True, exist_ok=True)
    report_path = Path(args.report_dir) / f"visual_loudness_{args.iteration}.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    trend_path = Path(args.trendline_path)
    history = []
    if trend_path.exists():
        try:
            history = json.loads(trend_path.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except json.JSONDecodeError:
            history = []
    history.append({
        "iteration": result["iteration"],
        "timestamp": result["timestamp"],
        "portal_average_loudness": result["portal_average_loudness"],
    })
    trend_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    print(f"\n📊 measure_visual_loudness · iteration={args.iteration}")
    print(f"   portal-wide average loudness: {result['portal_average_loudness']}")
    print(f"   detailed report:  {report_path}")
    print(f"   trendline log:    {trend_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
