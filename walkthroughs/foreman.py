"""Foreman walkthrough — mobile, field-first, the platform's most operationally dense user.

A foreman runs the crew. Their day touches more workflows than any
other persona: Pre-Op (every machine, every morning) → Equipment
Checkout (when assigning gear) → live incident response → mid-day
write-ups → end-of-day Daily Report submission. We simulate the
canonical day at mobile-phone width (414px — iPhone Plus / Pixel),
glove-friendly, sun-glare-resistant scenarios.

Findings emitted: friction, missing-coaching, weak-tip,
unclear-wording, discoverability-gap, mobile-clipping,
workflow-confusion, no-escalation-path, voice-drift,
positive-observation.
"""
import sys
from pathlib import Path

# Allow `python /app/walkthroughs/foreman.py` to find the runner
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import (  # noqa: E402
    Walkthrough, run, FIND_HELPTIPS_JS, EXPAND_HELPTIPS_JS,
)


def foreman_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    # ── 06:15 · Yard arrival — open the public hub on the phone ────
    wt.begin_step("01-yard-arrival", "06:15 · Open the platform from the yard parking lot", base + "/")
    page.goto(base + "/", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(1500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # On the public hub, a foreman expects to see the Pre-Op tile and
    # the Daily Report tile within thumb-reach (no horizontal scroll).
    tiles = page.evaluate("""() => {
        const hits = {};
        ['/equipment/submit', '/daily/submit', '/incidents/submit', '/leadership']
          .forEach(href => {
            const a = document.querySelector(`a[href="${href}"], a[href^="${href}"]`);
            if (a) {
                const r = a.getBoundingClientRect();
                hits[href] = {visible: r.top >= 0 && r.top < window.innerHeight, top: Math.round(r.top)};
            } else {
                hits[href] = null;
            }
          });
        return hits;
    }""")
    if not tiles.get("/equipment/submit") or not tiles["/equipment/submit"].get("visible"):
        wt.note(
            "discoverability-gap",
            "Pre-Op tile is not within first-screen reach on the public hub at 414px width.",
            "Re-order the hub tiles so Pre-Op + Daily Report are above the fold for mobile foremen.",
        )
    else:
        wt.note(
            "positive-observation",
            f"Pre-Op tile is in first-screen reach at y={tiles['/equipment/submit']['top']}px.",
        )

    # ── 06:25 · First machine Pre-Op ───────────────────────────────
    wt.begin_step("02-preop-first-machine", "06:25 · Foreman walks first operator through Pre-Op", base + "/equipment/submit")
    page.goto(base + "/equipment/submit", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Foreman should see ≥1 top-of-form coaching surface + the
    # iter211 discoverability counter.
    counter = page.evaluate("""() => {
        const e = document.querySelector('[data-testid$="-counter"]');
        return e ? e.textContent : null;
    }""")
    if not counter or "coaching tips available" not in counter.lower():
        wt.note(
            "discoverability-gap",
            "Pre-Op form opens WITHOUT a visible 'N coaching tips available' counter.",
            "Confirm iter211 counter wiring on /equipment/submit at mobile width.",
        )
    elif "4" not in counter and "5" not in counter and "6" not in counter:
        wt.note(
            "weak-tip",
            f"Pre-Op counter shows {counter!r} — fewer tips than expected for the operator's #1 ROI surface.",
            "Audit preop tips registry for completeness against iter211 spec.",
        )
    else:
        wt.note(
            "positive-observation",
            f"Pre-Op opens with counter: {counter!r}.",
        )

    # Expand all top-of-form tips to verify the coaching body lands
    page.evaluate(EXPAND_HELPTIPS_JS, "helptip-block-preop")
    page.wait_for_timeout(400)
    page.screenshot(path=wt.shot_path("expanded"), full_page=True)
    # Check that no tip body wraps awkwardly at 414px (over 6 lines is
    # a soft signal that the body is too long for thumb-scrolling)
    bodies = page.evaluate("""() => {
        const bs = document.querySelectorAll('[data-testid$="-body"]');
        return [...bs].map(b => ({
            id: b.getAttribute('data-testid'),
            height: b.getBoundingClientRect().height,
            text_len: (b.innerText || '').length,
        }));
    }""")
    over_threshold = [b for b in bodies if b.get("height", 0) > 220]
    if over_threshold:
        for b in over_threshold:
            wt.note(
                "mobile-clipping",
                f"HelpTip body {b['id']!r} renders {int(b['height'])}px tall (>220px) at 414px viewport — "
                f"approaches thumb-scroll fatigue threshold.",
                f"Consider tightening this tip to ≤60 words or splitting it.",
            )

    # ── 07:15 · Foreman assigns the skid to operator B ─────────────
    wt.begin_step("03-equipment-checkout", "07:15 · Assign equipment to operator (Leadership portal)", base + "/leadership/equipment_checkout/new")
    page.goto(base + "/leadership/equipment_checkout/new", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    # If we land on the login page, the leadership auth didn't seed.
    if "/leadership/login" in page.url:
        wt.note(
            "workflow-confusion",
            f"Equipment Checkout redirected to login despite leadership token; current URL: {page.url}",
            "Investigate sessionStorage token persistence across navigations.",
        )
    else:
        blocks = page.evaluate(FIND_HELPTIPS_JS)
        wt.record_helptips(blocks)
        page.screenshot(path=wt.shot_path(), full_page=False)
        page.evaluate(EXPAND_HELPTIPS_JS, "helptip-block-checkout")
        page.wait_for_timeout(400)
        page.screenshot(path=wt.shot_path("expanded"), full_page=True)
        # Foreman-specific check: the 'who sees this' tip should
        # mention Shop + Dispatch + HR (the downstream readers).
        who_text = page.evaluate("""() => {
            const t = document.querySelector('[data-testid="helptip-checkout-who-body"]');
            return t ? (t.innerText || '').toLowerCase() : '';
        }""")
        for required in ("shop", "dispatch", "hr"):
            if required not in who_text:
                wt.note(
                    "weak-tip",
                    f"checkout 'who' tip omits {required!r} from the downstream-reader list.",
                    f"Ensure the foreman knows {required} reads this within the minute of signing.",
                )

    # ── 10:40 · Operator B reports a near-miss — Safety Incident ─
    wt.begin_step("04-incident-near-miss", "10:40 · Near-miss reported, foreman opens Safety Incident form", base + "/incidents/submit")
    page.goto(base + "/incidents/submit", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Critical check: the foreman, panicking after a near-miss, must
    # see the 'escalate' coaching prominently — Safety calls before
    # paperwork. If the canonical 4 tips aren't visible up top, the
    # operational coaching is failing at exactly the moment it matters.
    top_kinds = page.evaluate("""() => {
        const block = document.querySelector('[data-testid="helptip-block-incident"]');
        if (!block) return [];
        return [...block.querySelectorAll('[data-testid$="-toggle"]')].map(t => {
            const tid = t.getAttribute('data-testid') || '';
            // testid shape: helptip-incident-{kind}-toggle
            const m = tid.match(/incident-([a-z]+)-toggle$/);
            return m ? m[1] : tid;
        });
    }""")
    for required in ("why", "who", "next", "escalate"):
        if required not in top_kinds:
            wt.note(
                "no-escalation-path",
                f"Incident form missing canonical {required!r} tip at top — coaching gap at "
                f"the highest-stakes operational moment.",
                f"Verify iter210 incident.{required} wiring.",
            )

    # ── 14:30 · Document chronic late arrival (write-up) ───────────
    wt.begin_step("05-writeup-late-arrival", "14:30 · Foreman opens Write-Up after the third late day", base + "/leadership/write_up/new")
    page.goto(base + "/leadership/write_up/new", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    if "/leadership/login" in page.url:
        wt.note(
            "workflow-confusion",
            "Write-Up redirected to leadership login — auth not persisting.",
            "See step 03 finding.",
        )
    else:
        blocks = page.evaluate(FIND_HELPTIPS_JS)
        wt.record_helptips(blocks)
        page.evaluate(EXPAND_HELPTIPS_JS, "helptip-block-writeup")
        page.wait_for_timeout(400)
        page.screenshot(path=wt.shot_path("expanded"), full_page=True)
        # The iter214 anchor: "the paper is the evidence; the
        # conversation is the work" should be in the top-level why tip.
        why_text = page.evaluate("""() => {
            const t = document.querySelector('[data-testid="helptip-writeup-why-body"]');
            return t ? (t.innerText || '').toLowerCase() : '';
        }""")
        if "conversation" not in why_text:
            wt.note(
                "voice-drift",
                "writeup 'why' tip body does not contain the iter214 'conversation comes first' anchor.",
                "Restore the operator-stated cultural anchor language.",
            )
        else:
            wt.note(
                "positive-observation",
                "writeup 'why' contains the conversation-first anchor (iter214 voice preserved).",
            )

    # ── 17:30 · End-of-day Daily Report ────────────────────────────
    wt.begin_step("06-daily-report-eod", "17:30 · Foreman files the Daily Report from the truck cab", base + "/daily/submit")
    page.goto(base + "/daily/submit", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Daily Report should expose ≥5 contextual blocks per iter209
    # (top, crew, equipment, materials, narrative, photos)
    block_count = len(blocks)
    if block_count < 4:
        wt.note(
            "discoverability-gap",
            f"Daily Report exposes only {block_count} HelpTip blocks on mobile — expected ≥5 per iter209 spec.",
            "Re-verify iter209 wiring on NewDailyReport.jsx at 414px width.",
        )
    else:
        wt.note(
            "positive-observation",
            f"Daily Report exposes {block_count} HelpTip blocks; iter209 multi-section coverage intact.",
        )
    # Scroll to the materials section to check the iter215 deepening
    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight * 0.6)")
    page.wait_for_timeout(800)
    page.screenshot(path=wt.shot_path("materials"), full_page=False)
    materials_block = page.evaluate("""() => {
        const b = document.querySelector('[data-testid="helptip-block-daily-report-materials"]');
        if (!b) return null;
        return b.querySelectorAll('[data-testid$="-toggle"]').length;
    }""")
    if materials_block is None:
        wt.note(
            "discoverability-gap",
            "daily-report.materials block did not render after scrolling to the materials section.",
            "Investigate viewport/render race for iter209 leaf blocks.",
        )
    elif materials_block < 7:
        wt.note(
            "weak-tip",
            f"daily-report.materials only renders {materials_block} tips — iter215 deepened "
            f"this to 5 leaf + 4 parent = 9 expected.",
            "Re-check daily-report.materials registry depth.",
        )
    else:
        wt.note(
            "positive-observation",
            f"daily-report.materials renders {materials_block} tips (iter215 deepening intact).",
        )


if __name__ == "__main__":
    # iPhone 14-class mobile viewport — the foreman's actual device.
    report = run(
        foreman_day,
        persona="foreman",
        viewport={"width": 414, "height": 896},
        device_label="iPhone-Plus (414×896 · mobile · field)",
        auth_kind="leadership",
    )
    if report["finding_count"]:
        kinds = ", ".join(f"{k}={v}" for k, v in sorted(report["finding_tally"].items()))
        print(f"\nFINDINGS · {report['finding_count']} total · {kinds}")
        for f in report["findings"]:
            print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
