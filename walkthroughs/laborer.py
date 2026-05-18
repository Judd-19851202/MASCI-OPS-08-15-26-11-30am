"""Laborer / new-employee walkthrough — Day 1 on the job.

A new laborer's first day on the platform: QR poster at the yard,
landing on the public onboarding article, navigating to Pre-Op for
the first time, signing their first Equipment Checkout. The
discoverability bar is set HIGHEST here — anything ambiguous to a
seasoned foreman is invisible to a Day-1 employee.

Mobile-only viewport. Often performed with the device shared between
the new hire and a foreman pointing at the screen.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import Walkthrough, run, FIND_HELPTIPS_JS  # noqa: E402


def laborer_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    # ── 06:15 · QR poster lands them on the public hub ─────────────
    wt.begin_step("01-qr-landing", "06:15 · New hire scans the yard QR poster", base + "/")
    page.goto(base + "/", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2000)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Critical Day-1 question: is there a 'NEW HERE? START HERE' tile
    # within first-screen reach? (iter202 added 'First week here?'
    # links to login footers — but for the laborer hitting the public
    # hub, the visibility check is here.)
    new_here_link = page.evaluate("""() => {
        // Look for any tile/link explicitly addressing new hires
        const all = document.querySelectorAll('a, button');
        const hits = [...all].filter(el => {
            const txt = (el.innerText || '').toLowerCase();
            return /first week|start here|new (hire|employee)|onboard|day one|day 1/.test(txt);
        });
        return hits.length;
    }""")
    if new_here_link == 0:
        wt.note(
            "discoverability-gap",
            "Public hub has NO obvious 'new here / first week / start here' entry point for a "
            "Day-1 laborer arriving via QR poster.",
            "Add a discoverable 'Start here — first week on the platform' tile or banner to the public hub.",
        )
    else:
        wt.note(
            "positive-observation",
            f"Public hub exposes {new_here_link} 'start here'-style link(s) — Day-1 discoverability intact.",
        )

    # ── 06:25 · Foreman walks them through the Pre-Op ──────────────
    wt.begin_step("02-first-preop", "06:25 · Foreman walks new hire through their FIRST Pre-Op", base + "/equipment/submit")
    page.goto(base + "/equipment/submit", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # For a new hire, the iter211 counter ("X coaching tips available")
    # is the single most-important piece of UI — it's what signals
    # "this form will tell you what it wants from you."
    counter_visible = page.evaluate("""() => {
        const c = document.querySelector('[data-testid$="-counter"]');
        if (!c) return null;
        const r = c.getBoundingClientRect();
        return r.top >= 0 && r.top < window.innerHeight ? c.textContent : null;
    }""")
    if not counter_visible:
        wt.note(
            "discoverability-gap",
            "Pre-Op coaching counter NOT visible on first paint at 414px viewport — Day-1 hire "
            "may not realize coaching exists.",
            "Verify iter211 counter visibility above the fold on mobile.",
        )
    else:
        wt.note(
            "positive-observation",
            f"Pre-Op counter visible to new hire: {counter_visible!r}",
        )

    # ── 07:15 · First Equipment Checkout signature ────────────────
    wt.begin_step("03-first-checkout", "07:15 · New hire signs first Equipment Checkout", base + "/leadership/equipment_checkout/new")
    page.goto(base + "/leadership/equipment_checkout/new", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    if "/leadership/login" in page.url:
        wt.note(
            "friction",
            "Equipment Checkout gated behind leadership password — Day-1 laborer cannot reach unaided.",
            "Foreman-tablet usage model is implicit; consider documenting it OR adding a "
            "self-signing operator surface for the checkout flow.",
        )

    # ── End-of-day reflection ─────────────────────────────────────
    wt.note(
        "positive-observation",
        "Laborer Day-1 surface tour: QR → Pre-Op (with foreman) → Checkout (with foreman). "
        "Lightweight by design.",
    )


if __name__ == "__main__":
    report = run(laborer_day, persona="laborer",
                 viewport={"width": 414, "height": 896},
                 device_label="iPhone-Plus (414×896 · mobile · day-1)",
                 auth_kind=None)  # laborer is unauthenticated by default
    print(f"\nFINDINGS · {report['finding_count']} · {report['finding_tally']}")
    for f in report["findings"]:
        print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
