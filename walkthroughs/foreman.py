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
    # iter219 refinement — recognize the legitimate /field aggregator
    # IA pattern. The public hub intentionally routes through /field
    # (the field-tools aggregator) and /leadership (the supervisor
    # entry), NOT direct /equipment/submit / /daily/submit deeplinks.
    # First-screen reach for the FOREMAN means the /field tile is
    # above the fold; from /field they have one tap to Pre-Op + DR.
    tiles = page.evaluate("""() => {
        const hits = {};
        // /field is the aggregator; /leadership is the supervisor route.
        // The Day-1 banner is a third valid above-the-fold target for
        // a foreman who's also onboarding a new hire that morning.
        ['/field', '/leadership', '#hub-day-one-start-here'].forEach(href => {
            let a = null;
            if (href.startsWith('#')) {
                a = document.querySelector('[data-testid="' + href.slice(1) + '"]');
            } else {
                a = document.querySelector(`a[href="${href}"], a[href^="${href}"]`);
            }
            if (a) {
                const r = a.getBoundingClientRect();
                hits[href] = {visible: r.top >= 0 && r.top < window.innerHeight, top: Math.round(r.top)};
            } else {
                hits[href] = null;
            }
        });
        return hits;
    }""")
    field_tile = tiles.get("/field") or {}
    if not field_tile.get("visible"):
        wt.note(
            "discoverability-gap",
            "Field aggregator tile (gateway to Pre-Op + Daily Report) is not "
            "within first-screen reach on the public hub at 414px width.",
            "Re-check public-hub IA: /field should be the first BigTile in "
            "the 'Today in the Field' section.",
        )
    else:
        wt.note(
            "positive-observation",
            f"/field aggregator tile is in first-screen reach at "
            f"y={field_tile['top']}px — foreman has 1 tap to Pre-Op + DR.",
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


    # ── 07:00 · Crew check — first leadership moment of the day ─────
    # The foreman's first POST-arrival operational moment is crew
    # check: who showed up, who's late, who's on what unit. This is
    # a verbal/operational moment for most field leaders — the
    # walkthrough's job here is to surface whether the platform offers
    # a digital surface that supports this moment (or document the
    # absence honestly).
    wt.begin_step(
        "02b-crew-check",
        "07:00 · Foreman opens the Leadership hub to confirm today's crew",
        base + "/leadership",
    )
    page.goto(base + "/leadership", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    # Discovery-only — operator directive: no coaching authored yet,
    # just surface honest gaps. Three discovery checks:
    #   (a) Is there any crew/headcount/muster surface visible from
    #       the leadership hub at 414px?
    #   (b) Does the leadership hub have ANY contextual coaching?
    #   (c) If a foreman is supposed to "take headcount" digitally,
    #       where would they actually do it?
    has_crew_surface = page.evaluate("""() => {
        const candidates = [
            '[data-testid*="crew"]', '[data-testid*="muster"]',
            '[data-testid*="headcount"]', '[data-testid*="attendance"]',
            'a[href*="crew"]', 'a[href*="muster"]',
        ];
        for (const sel of candidates) {
            if (document.querySelector(sel)) return sel;
        }
        return null;
    }""")
    if not has_crew_surface:
        wt.note(
            "discoverability-gap",
            "Leadership hub at 414px exposes NO crew-check / muster / "
            "headcount surface. The foreman's 07:00 'who showed up, who's "
            "late, who's on what unit' moment has no platform support — "
            "they're tracking it on a clipboard or in their head.",
            "Operator-decision-required: does the platform need a digital "
            "crew-check surface, or is this intentionally a verbal moment? "
            "Document the architectural decision either way.",
        )
    if not blocks:
        wt.note(
            "missing-coaching",
            "Leadership hub itself has no contextual coaching at 414px. "
            "It's a navigation surface, but a new foreman arriving here "
            "has no operational framing for which records to file when, "
            "or what the crew-check moment is supposed to feel like.",
            "Consider whether the leadership hub deserves a top-level "
            "'why this portal exists for foremen' tip (canonical-4) or "
            "whether the navigation pattern itself is the coaching.",
        )

    # ── 11:00 · Dispatch interaction — foreman reads transfer ───────
    # Mid-morning, Dispatch sends a transfer request. The foreman
    # opens it from the truck cab. This is the bidirectional moment
    # iter226 Dispatch coaching anticipated ("call the receiving
    # foreman before opening the Transfer") — does the foreman SIDE
    # of that conversation have its own coaching?
    wt.begin_step(
        "04b-dispatch-interaction",
        "11:00 · Foreman reads incoming transfer request from Dispatch",
        base + "/asset-transfers",
    )
    page.goto(base + "/asset-transfers", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    landed = page.url
    if "/login" in landed or "/access-denied" in landed:
        wt.note(
            "workflow-confusion",
            f"Asset Transfers page redirected the foreman to {landed!r} — "
            f"the receiving-foreman side of the Transfer workflow may not "
            f"be accessible to the leadership token at all.",
            "Audit whether the foreman receives Transfers via this URL or "
            "via a different surface (e.g. Daily Report annotation, "
            "notification bell, push). Operator-decision-required.",
        )
    else:
        blocks = page.evaluate(FIND_HELPTIPS_JS)
        wt.record_helptips(blocks)
        if not blocks:
            wt.note(
                "missing-coaching",
                "Foreman-side of the Transfer interaction has no coaching "
                "surface. iter226 authored the dispatcher's side ('call "
                "before opening the Transfer'); the receiving foreman has "
                "no parallel coaching for what to do when a transfer "
                "lands in their queue.",
                "Consider authoring a foreman-scoped `transfer.receive` "
                "family — but only after operator review of this finding. "
                "Voice anchor candidate (operator-decision-required): "
                "'A transfer landing in your queue is a conversation, not "
                "an order — confirm it before the truck rolls.'",
            )

    # ── 12:30 · Field interruption (non-mid-day-defect) ─────────────
    # The foreman takes a 90-second break in the truck cab and pulls
    # up the leadership records page to remember a phone number, or
    # to check whether they filed yesterday's recognition note. This
    # is the "mid-shift reading moment" — different from mid-day
    # DEFECT routing (strategic hold) — and surfaces whether the
    # field-leadership records reader-side IA works for the person
    # who FILED them too.
    wt.begin_step(
        "05b-mid-shift-records-read",
        "12:30 · Foreman pulls up their own leadership records in the truck cab",
        base + "/leadership/records",
    )
    page.goto(base + "/leadership/records", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    landed = page.url
    if "/login" in landed:
        wt.note(
            "workflow-confusion",
            f"Leadership records redirected to login despite leadership "
            f"token; landed at {landed!r}.",
            "Audit auth persistence for the records list at mobile width.",
        )
    else:
        blocks = page.evaluate(FIND_HELPTIPS_JS)
        wt.record_helptips(blocks)
        # iter218 authored REVIEWER-SIDE coaching for HR reading
        # records. The FILER side (the foreman who filed them) may
        # need a different coaching — "go back and read your own
        # filings to remember context."
        records_block = "helptip-block-field-leadership-records" in blocks
        if records_block:
            wt.note(
                "positive-observation",
                "Leadership records page renders the iter218 coaching "
                "block — but currently scoped to REVIEWER (HR) voice. "
                "Operator-decision-required: does the FILER side need a "
                "parallel coaching surface?",
            )
        else:
            wt.note(
                "discoverability-gap",
                "Leadership records page at 414px does not render any "
                "coaching block visible to the foreman (filer-side). "
                "The iter218 block exists but may be scoped to HR-only.",
                "Audit `field-leadership.records` scope: is it intentionally "
                "reviewer-only, or should the filer also see context-of-use "
                "coaching when reading their own records?",
            )

    # ── 18:00 · End-of-day wrap — different from filing the DR ──────
    # After the Daily Report is filed (step 06 above), the foreman
    # has one more operational moment: confirming nothing is left
    # undone before driving off the site. This is the "did I file
    # the recognition note · did I close yesterday's open write-up
    # · did I tell the super about tomorrow's headcount gap" check.
    # The Daily Report doesn't cover all of these — they live in
    # different surfaces.
    wt.begin_step(
        "07-end-of-day-wrap",
        "18:00 · Foreman returns to Leadership hub for end-of-day wrap",
        base + "/leadership",
    )
    page.goto(base + "/leadership", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Discovery checks for the EOD wrap:
    #   (a) Is there a "what's still open from today" surface visible?
    #   (b) Is there an "anything to tell the super" handoff surface
    #       (analogous to iter226 dispatch.handoff)?
    open_items_surface = page.evaluate("""() => {
        const candidates = [
            '[data-testid*="open"]', '[data-testid*="pending"]',
            '[data-testid*="incomplete"]', '[data-testid*="draft"]',
            '[data-testid*="unfinished"]',
        ];
        for (const sel of candidates) {
            if (document.querySelector(sel)) return sel;
        }
        return null;
    }""")
    if not open_items_surface:
        wt.note(
            "discoverability-gap",
            "Leadership hub at 414px exposes no 'what's still open from "
            "today' surface for the foreman's end-of-day wrap. They have "
            "to remember what they didn't finish — or skip it and "
            "rediscover the gap tomorrow morning.",
            "Operator-decision-required: does the platform need a foreman "
            "EOD-wrap surface (analogous to iter226 dispatch.handoff)? "
            "Or is the assumption that the foreman has zero pending items "
            "at EOD? Document the architectural decision.",
        )
    handoff_surface = page.evaluate("""() => {
        const candidates = [
            'a[href*="handoff"]', '[data-testid*="handoff"]',
            'a[href*="supervisor"]', '[data-testid*="super-note"]',
            '[data-testid*="to-super"]', '[data-testid*="brief"]',
        ];
        for (const sel of candidates) {
            if (document.querySelector(sel)) return sel;
        }
        return null;
    }""")
    if not handoff_surface:
        wt.note(
            "discoverability-gap",
            "Leadership hub at 414px exposes no 'anything for the super "
            "to know' handoff surface — the foreman's mirror of the "
            "iter226 dispatch.handoff discipline. Currently the foreman's "
            "end-of-day communication to the super is either a phone "
            "call (no platform support) or buried inside the Daily "
            "Report narrative.",
            "Operator-decision-required: should there be a structured "
            "foreman → super handoff surface (held until Supervisor "
            "first-14-days coaching is unblocked — these architectures "
            "are likely interconnected)?",
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
