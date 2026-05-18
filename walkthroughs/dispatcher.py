"""Dispatcher walkthrough — Tier-2 office persona, multi-tab dashboard.

Dispatcher's day is fundamentally different from field roles. They
sit at a desk (or in a yard office), read Daily Reports from the
prior day to plan today's moves, juggle transfer requests, fight to
keep utilization up, and field 'we need it now' calls from foremen.
Desktop-class viewport, no mobile constraints.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import (  # noqa: E402
    Walkthrough, run, FIND_HELPTIPS_JS, EXPAND_HELPTIPS_JS,
)


def dispatcher_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    # ── 06:00 · Open Dispatch Hub, scan yesterday's wreckage ───────
    wt.begin_step("01-hub-overview", "06:00 · Dispatcher opens portal, looks at overdue + alerts", base + "/dispatch-portal")
    page.goto(base + "/dispatch-portal", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    if "/dispatch-portal/login" in page.url:
        wt.note(
            "friction",
            "Dispatch Hub did not auto-authenticate from the multi-login session token seed.",
            "Verify masci.dispatch.token persistence path.",
        )
        return
    page.screenshot(path=wt.shot_path(), full_page=False)
    # The Overview tab should be the dispatcher's first read. Verify
    # OPERATIONS-relevant stats are above the fold at 1024px.
    visible_stats = page.evaluate("""() => {
        const cards = document.querySelectorAll('[data-testid^="op-stat-"], [data-testid$="-overview"]');
        return [...cards].slice(0, 10).map(c => c.getAttribute('data-testid'));
    }""")
    if not visible_stats:
        wt.note(
            "discoverability-gap",
            "Dispatch Overview tab landing: no testid-marked stat cards immediately visible.",
            "Audit dh-tab-overview content for visibility and testid coverage.",
        )

    # ── 06:20 · Switch to Transfers tab — iter216 surface ──────────
    wt.begin_step("02-transfers-tab", "06:20 · Click Transfers tab, see request queue + coaching", base + "/dispatch-portal#transfers")
    tab = page.query_selector('[data-testid="dh-tab-transfers"]')
    if tab:
        tab.click()
        page.wait_for_timeout(2500)
    else:
        wt.note(
            "friction",
            "Could not find Transfers tab trigger [data-testid='dh-tab-transfers'].",
            "Verify DispatchHub.jsx tabs wiring.",
        )
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # iter216: verify the dispatch.transfers block is the very FIRST
    # thing the dispatcher sees on the tab — not buried.
    block_y = page.evaluate("""() => {
        const b = document.querySelector('[data-testid="helptip-block-dispatch-transfers"]');
        if (!b) return null;
        const r = b.getBoundingClientRect();
        return {y: Math.round(r.top), height: Math.round(r.height)};
    }""")
    if block_y is None:
        wt.note(
            "discoverability-gap",
            "iter216 dispatch.transfers HelpTip block did NOT render on Transfers tab.",
            "Critical — Tier-2 coaching is missing at the surface it was designed for.",
        )
    elif block_y["y"] > 600:
        wt.note(
            "discoverability-gap",
            f"dispatch.transfers HelpTip block renders at y={block_y['y']}px — below the fold for "
            f"common laptop viewports.",
            "Re-order: tips should sit immediately above the New Transfer / Refresh actions.",
        )
    else:
        wt.note(
            "positive-observation",
            f"iter216 dispatch.transfers block at y={block_y['y']}px — above the fold.",
        )
    # Expand all 4 canonical tips, screenshot
    page.evaluate(EXPAND_HELPTIPS_JS, "helptip-block-dispatch-transfers")
    page.wait_for_timeout(400)
    page.screenshot(path=wt.shot_path("expanded"), full_page=True)

    # ── 09:15 · Foreman calls: 'need the mini back today' ──────────
    # Dispatcher's most common operational moment. Verify the
    # lead-time / access / load-specs sub-coaching is reachable.
    wt.begin_step("03-foreman-rush-request", "09:15 · Rush request — does coaching reach the lead-time + access tips?", base + "/dispatch-portal#transfers")
    sub_coverage = page.evaluate("""() => {
        // Even though we only rendered the top block, the parent fall-up
        // means tips for dispatch.transfers.lead-time etc. are
        // server-side reachable. We check via the API directly.
        return fetch(window.location.origin + '/api/guidance/tips?form_key=dispatch.transfers.lead-time', {
            headers: {'X-Dispatch-Token': localStorage.getItem('masci.dispatch.token') || ''}
        }).then(r => r.json()).then(d => d.count || 0);
    }""")
    if sub_coverage < 6:
        wt.note(
            "weak-tip",
            f"dispatch.transfers.lead-time API returned only {sub_coverage} tips (parent fall-up expected ≥6).",
            "Audit dispatch.transfers.lead-time registry depth.",
        )
    else:
        wt.note(
            "positive-observation",
            f"dispatch.transfers.lead-time exposes {sub_coverage} tips via parent fall-up.",
        )

    # ── 11:30 · Switch to Idle Alerts — utilization play ───────────
    wt.begin_step("04-idle-alerts", "11:30 · Dispatcher checks idle units to plan an opportunistic transfer", base + "/dispatch-portal#idle")
    idle_tab = page.query_selector('[data-testid="dh-tab-idle"]')
    if idle_tab:
        idle_tab.click()
        page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Idle Alerts is a high-value workflow surface with NO coaching tip
    # surface yet. Flag as backlog.
    if not blocks:
        wt.note(
            "missing-coaching",
            "Idle Alerts tab has no HelpTip coverage — high-value opportunistic-transfer surface lacks "
            "operational coaching.",
            "Author Tier-2 dispatch.idle-alerts tips per the iter216 voice pattern. "
            "Sample: 'An idle unit on a yard while another job calls for the same model is a "
            "routing opportunity — surface it before finance does.'",
        )

    # ── 14:00 · Holds tab — equipment with safety/shop-blocked status
    wt.begin_step("05-holds-tab", "14:00 · Dispatcher reviews units on hold", base + "/dispatch-portal#holds")
    holds_tab = page.query_selector('[data-testid="dh-tab-holds"]')
    if holds_tab:
        holds_tab.click()
        page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    if not blocks:
        wt.note(
            "missing-coaching",
            "Holds tab has no HelpTip coverage — coordination-with-Safety/Shop workflow is operationally "
            "ambiguous for new dispatchers.",
            "Author Tier-2 dispatch.holds tips (when to call Safety vs Shop, what unblocks a hold, "
            "the foreman conversation about the held unit).",
        )


if __name__ == "__main__":
    report = run(
        dispatcher_day,
        persona="dispatcher",
        viewport={"width": 1280, "height": 800},
        device_label="laptop-1280 (1280×800 · desktop · office)",
        auth_kind="multi",
    )
    if report["finding_count"]:
        kinds = ", ".join(f"{k}={v}" for k, v in sorted(report["finding_tally"].items()))
        print(f"\nFINDINGS · {report['finding_count']} total · {kinds}")
        for f in report["findings"]:
            print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
