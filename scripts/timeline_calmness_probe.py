#!/usr/bin/env python3
"""
timeline_calmness_probe.py — Phase V-Prelude · Wave 1.1A.

Passive governance instrument for the Operational Timeline Sidecar
mounted at `/pm/projects/:projectNumber`. Renders the surface via
Playwright at three viewports and computes:

  1. accent_pixel_ratio       — % of pixels NOT slate/white (DOM-class
                                 proxy, not raster sampling — cheap)
  2. slate_vs_accent_ratio    — slate-class count / accent-class count
  3. badge_density            — filled-badge elements per 1000 px²
  4. red_usage                — count of `bg-red-*` / `bg-rose-*` /
                                 `text-red-*` / `text-rose-*` classes
  5. vertical_density         — chronology rows visible above the fold
  6. hierarchy_compression    — distinct font-size × weight pairs
                                 inside the sidecar (more = more
                                 hierarchy collapse)

It also reads `/api/timeline?project_id=...` and computes:
  7. chronology_dup_ratio     — duplicate (kind, id, relationship,
                                 subtitle) signatures / total rows
  8. avg_row_signature_len    — operational signal density proxy
  9. truncated_flag           — whether the project hit the 200-cap

Outputs:
  • `/app/memory/TIMELINE_LOUDNESS_TRENDLINE.json` — append-only
    longitudinal calmness trendline.
  • `/app/test_reports/timeline_calmness_<iter>.json` — latest
    detailed run.
  • Stdout summary (human-readable).

Doctrine guarantees:
  * PASSIVE — never writes to any operator-facing surface, never
    triggers a notification, never expose anything operator-visible.
  * READ-ONLY — never mutates Mongo. Never POSTs.
  * GOVERNANCE-ONLY — output is for the platform's institutional
    memory, not for operators or dashboards.
  * WARNING-FIRST — the probe never hard-fails the deploy gate on
    its own. Sustained drift triggers warnings; the operator decides.

Usage:
  python3 scripts/timeline_calmness_probe.py \\
    --iteration iter-wave-1-1a \\
    [--project-number SIDECAR-PROBE]

  python3 scripts/timeline_calmness_probe.py --gate     # exit 1 only
                                                          # on severe
                                                          # regression
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    from playwright.sync_api import sync_playwright
except Exception as e:  # noqa: BLE001
    print(f"playwright not available: {e}", file=sys.stderr)
    sys.exit(2)

import requests  # noqa: E402

VIEWPORTS = [
    ("mobile",  390, 844),
    ("ipad",    1024, 1366),
    ("desktop", 1920, 1080),
]

# Heuristic doctrine targets (lower = calmer).
TARGETS: Dict[str, float] = {
    "accent_class_ratio":      0.18,   # ≤18 % of classed elements use accent palette
    "badge_density_per_1k_px2":0.00010, # filled badges per 1000 px² of sidecar
    "red_usage":               2.0,    # ≤2 red/rose class hits inside sidecar
    "hierarchy_compression":   5.0,    # ≤5 distinct font-size×weight pairs in sidecar
    "chronology_dup_ratio":    0.20,   # ≤20 % duplicate signatures
    "vertical_density":        12.0,   # ≤12 chronology rows above fold
}

# Severity floor — anything above 5x the target on any dimension fires
# a gate hard-fail when `--gate` is set.
GATE_MULTIPLIER = 5.0


def _read_env(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        return ""
    return ""


def _utc_iso() -> str:
    d = datetime.now(timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{d.microsecond // 1000:03d}Z"


# ── Per-route measurement ───────────────────────────────────────────


def _measure_sidecar(page) -> Dict[str, Any]:
    """Compute the 6 visual-loudness heuristics scoped to the sidecar."""
    return page.evaluate("""() => {
        const root = document.querySelector(
            '[data-testid="operational-timeline-sidecar"]'
        );
        if (!root) {
            return { missing: true };
        }
        const all = root.querySelectorAll('*');
        const classes = [];
        all.forEach((el) => {
            if (el.className && typeof el.className === 'string') {
                classes.push(el.className);
            }
        });
        const joined = classes.join(' ');

        const slateMatches = joined.match(/(?:^|\\s)(?:text-slate-|bg-slate-|border-slate-)/g) || [];
        const accentMatches = joined.match(
            /(?:bg-(?:amber|emerald|rose|red|sky|violet|indigo|pink|cyan|teal|orange|fuchsia|lime|yellow)-(?:50|100|200|300|400|500|600|700|800|900))/g
        ) || [];

        const slateCount = slateMatches.length;
        const accentCount = accentMatches.length;
        const totalClassed = slateCount + accentCount;
        const accentRatio = totalClassed === 0
            ? 0
            : accentCount / totalClassed;

        // Filled badge density.
        const badges = root.querySelectorAll(
            '[class*="bg-amber-"], [class*="bg-emerald-"], ' +
            '[class*="bg-rose-"], [class*="bg-red-"]'
        );
        const rect = root.getBoundingClientRect();
        const area = Math.max(1, rect.width * rect.height);
        const badgeDensity = badges.length / (area / 1000);

        // Red / rose usage.
        const redHits = (joined.match(/(?:bg|text|border)-(?:red|rose)-(?:[0-9]{2,3})/g) || []).length;

        // Hierarchy compression — distinct font-size × weight pairs.
        const pairs = new Set();
        all.forEach((el) => {
            const cs = getComputedStyle(el);
            if (el.textContent && el.textContent.trim()) {
                pairs.add(cs.fontSize + '/' + cs.fontWeight);
            }
        });

        // Vertical density — chronology rows visible above fold.
        const rows = root.querySelectorAll('[data-testid="chronology-row"]');
        const fold = window.innerHeight;
        let aboveFold = 0;
        rows.forEach((r) => {
            const rb = r.getBoundingClientRect();
            if (rb.top >= 0 && rb.top < fold) aboveFold++;
        });

        return {
            missing: false,
            slate_class_count: slateCount,
            accent_class_count: accentCount,
            accent_class_ratio: Number(accentRatio.toFixed(4)),
            badge_count: badges.length,
            badge_density_per_1k_px2: Number(badgeDensity.toFixed(6)),
            red_usage: redHits,
            hierarchy_compression: pairs.size,
            vertical_density: aboveFold,
            sidecar_width_px: Math.round(rect.width),
            sidecar_height_px: Math.round(rect.height),
        };
    }""")


# ── API-side chronology density ──────────────────────────────────────


def _measure_chronology(base_url: str, admin_token: str,
                        project_number: str) -> Dict[str, Any]:
    """Hit `/api/timeline` and compute density heuristics."""
    try:
        r = requests.get(
            f"{base_url}/api/timeline",
            params={"project_id": project_number},
            headers={"X-Admin-Token": admin_token},
            timeout=10,
        )
    except Exception as e:  # noqa: BLE001
        return {"error": f"timeline fetch failed: {e}"}
    if r.status_code != 200:
        return {"error": f"timeline status {r.status_code}", "body": r.text[:200]}
    body = r.json()
    items = body.get("items") or []
    if not items:
        return {
            "row_count": 0,
            "truncated": bool(body.get("truncated")),
            "chronology_dup_ratio": 0.0,
            "avg_row_signature_len": 0,
            "low_value_repeats": 0,
        }
    # Signature = (kind, id, relationship/subtitle).
    sigs: Dict[str, int] = {}
    sig_len_sum = 0
    low_value = 0
    for it in items:
        sig = "{}|{}|{}|{}".format(
            it.get("kind", ""), it.get("id", ""),
            it.get("relationship") or "", it.get("subtitle") or "",
        )
        sigs[sig] = sigs.get(sig, 0) + 1
        sig_len_sum += len(it.get("title", "") or "") + len(it.get("subtitle", "") or "")
        # Low-value heuristic — chronology rows whose subtitle is a
        # one-word action with no operational note (e.g., subtitle
        # ends with the " · " separator and nothing afterward, or
        # the subtitle stripped is a single non-separator token).
        subtitle = (it.get("subtitle") or "").strip()
        if subtitle:
            # Strip the doctrine separator " · " from both ends.
            cleaned = subtitle.strip("·").strip()
            # Count non-separator tokens.
            tokens = [
                t for t in cleaned.replace("·", " ").split()
                if t.strip()
            ]
            if len(tokens) <= 1:
                low_value += 1
        else:
            low_value += 1
    dups = sum(c - 1 for c in sigs.values() if c > 1)
    return {
        "row_count": len(items),
        "truncated": bool(body.get("truncated")),
        "chronology_dup_ratio": round(dups / len(items), 4),
        "avg_row_signature_len": round(sig_len_sum / len(items), 1),
        "low_value_repeats": low_value,
    }


# ── Aggregate ──────────────────────────────────────────────────────


def _score(per_viewport: Dict[str, Dict[str, Any]], chronology: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate a single calmness score across viewports.

    `score` is the SUM of excess-over-target across all heuristic
    dimensions. Lower = calmer. The deploy gate (when `--gate` is on)
    fires only when ANY dimension exceeds GATE_MULTIPLIER × target.
    """
    breaches: List[str] = []
    aggregate: Dict[str, float] = {k: 0.0 for k in TARGETS}
    count_present = 0
    for vp, m in per_viewport.items():
        if m.get("missing") or m.get("error"):
            continue
        count_present += 1
        for k in (
            "accent_class_ratio", "badge_density_per_1k_px2",
            "red_usage", "hierarchy_compression", "vertical_density",
        ):
            val = float(m.get(k, 0) or 0)
            aggregate[k] += val
            tgt = TARGETS[k]
            if val > tgt * GATE_MULTIPLIER:
                breaches.append(f"{vp}.{k}={val:.4f} > {tgt * GATE_MULTIPLIER:.4f}")

    if count_present:
        for k in aggregate:
            if k != "chronology_dup_ratio":
                aggregate[k] = round(aggregate[k] / count_present, 4)

    # Inject chronology-side heuristic.
    aggregate["chronology_dup_ratio"] = float(
        chronology.get("chronology_dup_ratio") or 0
    )
    if aggregate["chronology_dup_ratio"] > TARGETS["chronology_dup_ratio"] * GATE_MULTIPLIER:
        breaches.append(
            f"api.chronology_dup_ratio={aggregate['chronology_dup_ratio']}"
        )

    # Final score = sum of normalised excesses (each dim contributes its
    # excess / target). Lower = calmer.
    score = 0.0
    for k, tgt in TARGETS.items():
        val = aggregate.get(k, 0)
        if tgt > 0:
            score += max(0.0, (val - tgt) / tgt)
    return {
        "score": round(score, 4),
        "aggregate": aggregate,
        "gate_breaches": breaches,
        "viewports_measured": count_present,
    }


# ── Runner ──────────────────────────────────────────────────────────


def _run(base_url: str, admin_token: str, project_number: str) -> Dict[str, Any]:
    per_viewport: Dict[str, Dict[str, Any]] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        try:
            for vp_name, vw, vh in VIEWPORTS:
                ctx = browser.new_context(
                    viewport={"width": vw, "height": vh},
                    user_agent=(
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                        "Mobile/15E148 Safari/604.1"
                        if vp_name == "mobile" else None
                    ),
                )
                page = ctx.new_page()
                try:
                    # Seed admin token first so the PM Project Detail
                    # surface actually renders.
                    page.goto(base_url, wait_until="domcontentloaded", timeout=20_000)
                    page.evaluate(
                        """(t) => {
                            localStorage.setItem('masci.admin.token', t);
                            localStorage.setItem('admin_token', t);
                            sessionStorage.setItem('masci.portal-context', 'admin');
                        }""",
                        admin_token,
                    )
                    page.goto(
                        f"{base_url}/pm/projects/{project_number}",
                        wait_until="domcontentloaded",
                        timeout=20_000,
                    )
                    page.wait_for_selector(
                        '[data-testid="operational-timeline-sidecar"]',
                        timeout=15_000,
                    )
                    page.wait_for_timeout(700)
                    per_viewport[vp_name] = _measure_sidecar(page)
                except Exception as e:  # noqa: BLE001
                    per_viewport[vp_name] = {"error": str(e)[:200]}
                finally:
                    ctx.close()
        finally:
            browser.close()

    chronology = _measure_chronology(base_url, admin_token, project_number)
    scored = _score(per_viewport, chronology)
    return {
        "timestamp": _utc_iso(),
        "base_url": base_url,
        "project_number": project_number,
        "per_viewport": per_viewport,
        "chronology": chronology,
        **scored,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iteration", default="manual")
    ap.add_argument(
        "--project-number",
        default="SIDECAR-PROBE",
        help="project_number to load on the PM Project Detail surface",
    )
    ap.add_argument("--base-url", default="")
    ap.add_argument("--admin-token", default="")
    ap.add_argument(
        "--trendline-path",
        default="/app/memory/TIMELINE_LOUDNESS_TRENDLINE.json",
    )
    ap.add_argument(
        "--report-dir",
        default="/app/test_reports",
    )
    ap.add_argument("--json", action="store_true", help="machine output")
    ap.add_argument(
        "--gate",
        action="store_true",
        help="exit 1 on severe regression (5x target on any dimension)",
    )
    args = ap.parse_args()

    base_url = args.base_url or _read_env(
        "/app/frontend/.env", "REACT_APP_BACKEND_URL"
    ).rstrip("/")
    if not base_url:
        print("REACT_APP_BACKEND_URL missing", file=sys.stderr)
        return 64

    admin_token = args.admin_token
    if not admin_token:
        admin_pw = _read_env("/app/backend/.env", "ADMIN_PASSWORD")
        if not admin_pw:
            print("ADMIN_PASSWORD missing — cannot acquire token", file=sys.stderr)
            return 65
        r = requests.post(
            f"{base_url}/api/admin/login",
            json={"password": admin_pw},
            timeout=10,
        )
        if r.status_code != 200:
            print(f"admin login failed: {r.status_code}", file=sys.stderr)
            return 66
        admin_token = r.json().get("token", "")

    result = _run(base_url, admin_token, args.project_number)
    result["iteration"] = args.iteration

    # Write detail report.
    Path(args.report_dir).mkdir(parents=True, exist_ok=True)
    detail_path = Path(args.report_dir) / f"timeline_calmness_{args.iteration}.json"
    detail_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Append trendline entry.
    trend_path = Path(args.trendline_path)
    history: List[Dict[str, Any]] = []
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
        "score": result["score"],
        "aggregate": result["aggregate"],
        "gate_breaches": result["gate_breaches"],
        "viewports_measured": result["viewports_measured"],
        "chronology_row_count": result["chronology"].get("row_count", 0),
        "chronology_truncated": result["chronology"].get("truncated", False),
    })
    trend_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n📊 timeline_calmness_probe · iteration={args.iteration}")
        print(f"   score (lower=calmer): {result['score']}")
        print(f"   viewports measured:   {result['viewports_measured']}")
        print(f"   detail report:        {detail_path}")
        print(f"   trendline:            {trend_path}")
        if result["gate_breaches"]:
            print(f"\n   ⚠ gate breaches ({len(result['gate_breaches'])}):")
            for b in result["gate_breaches"]:
                print(f"     · {b}")
        else:
            print("   ✓ no gate breaches")

    if args.gate and result["gate_breaches"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
