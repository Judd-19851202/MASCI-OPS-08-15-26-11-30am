"""Operator walkthrough — the actual machine driver.

Operators sign Pre-Ops, receive Equipment Checkout (their personal
accountability record opens), report unit defects mid-day, and might
get pulled into an incident report. They live on the phone, often
with gloves on, in sun glare. Smaller workflow surface than a
foreman but every tap counts.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import (  # noqa: E402
    Walkthrough, run, FIND_HELPTIPS_JS, EXPAND_HELPTIPS_JS,
)


def operator_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    # ── 06:30 · Walk-around on the assigned skid steer ─────────────
    wt.begin_step("01-preop-walkaround", "06:30 · Operator opens the Pre-Op on their phone", base + "/equipment/submit")
    page.goto(base + "/equipment/submit", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)

    # Operator-critical: the signoff section is where their NAME goes
    # on the work. iter211 puts a 'pressure to sign' escalate tip there
    # — this is the most operationally consequential coaching surface
    # for an operator on the entire platform. Verify it lands.
    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(800)
    page.screenshot(path=wt.shot_path("signoff"), full_page=False)
    signoff_block = page.evaluate("""() => {
        const b = document.querySelector('[data-testid="helptip-block-preop-signoff"]');
        if (!b) return null;
        const toggles = b.querySelectorAll('[data-testid$="-toggle"]');
        return [...toggles].map(t => t.getAttribute('data-testid'));
    }""")
    if not signoff_block:
        wt.note(
            "discoverability-gap",
            "Pre-Op signoff section does NOT expose a HelpTip block at the operator's signature.",
            "Verify iter211 preop.signoff wiring; this is the highest-stakes operator surface.",
        )
    else:
        # Look for the 'escalate' tip (pressure-to-sign coaching)
        has_escalate = any("signoff-escalate" in tid for tid in signoff_block)
        if not has_escalate:
            wt.note(
                "no-escalation-path",
                "preop.signoff exposes tips but NO 'escalate' kind — operator gets no coaching on the "
                "'pressure to sign' scenario that's the entire reason this surface exists.",
                "Add an explicit preop.signoff escalate tip per iter211 spec.",
            )
        else:
            wt.note(
                "positive-observation",
                "preop.signoff exposes an 'escalate' tip — pressure-to-sign coaching is live at the operator's signature.",
            )

    # ── 07:30 · Sign Equipment Checkout — accountability transfer ──
    wt.begin_step("02-equipment-checkout-sign", "07:30 · Operator receives skid steer, walks it, signs", base + "/leadership/equipment_checkout/new")
    page.goto(base + "/leadership/equipment_checkout/new", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    if "/leadership/login" in page.url:
        # Real-world operator scenario: foreman might hand them the
        # tablet pre-authenticated. But if they hit this URL solo, a
        # password gate is friction.
        wt.note(
            "friction",
            "Equipment Checkout requires the leadership password — operator solo can't reach it.",
            "Document the 'foreman tablet' usage model OR consider whether checkout flows need an "
            "operator-self-signing surface.",
        )
    else:
        blocks = page.evaluate(FIND_HELPTIPS_JS)
        wt.record_helptips(blocks)
        page.screenshot(path=wt.shot_path(), full_page=False)
        # Verify the 'when NOT to sign' escalate tip is present and
        # operationally honest (operator's most important moment).
        esc_text = page.evaluate("""() => {
            const t = document.querySelector('[data-testid="helptip-checkout-escalate-body"]');
            return t ? (t.innerText || '').toLowerCase() : '';
        }""")
        if esc_text and ("damage" in esc_text or "undocumented" in esc_text):
            wt.note(
                "positive-observation",
                "checkout 'escalate' tip explicitly coaches stop-before-signing on undocumented damage.",
            )
        elif esc_text:
            wt.note(
                "weak-tip",
                f"checkout 'escalate' tip body present but doesn't coach the damage-found-before-signing scenario.",
                "Verify iter212 escalate body matches operator-stated 'when NOT to sign yet' language.",
            )

    # ── 11:00 · Mid-day: noticed hydraulic seep, flags via Daily ─
    wt.begin_step("03-mid-day-defect-aware", "11:00 · Operator notices defect — what do they do?", base + "/")
    page.goto(base + "/", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(1500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Question: from the public hub, does the operator have a CLEAR
    # path to report a mid-day defect? Daily Report is for end-of-day.
    # Pre-Op is for morning. Incident is for safety events. A simple
    # defect found at 11am has no obvious operational surface.
    paths_available = page.evaluate("""() => {
        const candidates = ['/equipment/submit', '/incidents/submit', '/daily/submit'];
        return candidates.map(p => ({
            path: p,
            link: !!document.querySelector(`a[href="${p}"]`),
        }));
    }""")
    wt.note(
        "workflow-confusion",
        f"Mid-day defect: no dedicated 'flag this unit' surface. Available paths: {paths_available}. "
        f"Operator might submit a redundant Pre-Op, an inappropriate Incident, or wait until EOD.",
        "Consider a lightweight 'flag-unit-defect' surface OR a HelpTip on the Pre-Op/Incident pages "
        "explicitly addressing 'I noticed something mid-day — where?'",
    )

    # ── 16:55 · End-of-day: operator hands phone back to foreman ─
    # Most operators don't fill the Daily Report directly — the foreman
    # does. So we're done with the operator's surface tour.
    wt.begin_step("04-eod-handoff", "16:55 · Operator hands phone back; foreman files Daily Report", base + "/")
    page.goto(base + "/", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(1000)
    page.screenshot(path=wt.shot_path(), full_page=False)
    wt.note(
        "positive-observation",
        "Operator's daily surface tour: Pre-Op (sign) → Checkout (sign) → flag defect → done. "
        "Workflow is genuinely lightweight for the operator persona — by design.",
    )


if __name__ == "__main__":
    report = run(
        operator_day,
        persona="operator",
        viewport={"width": 414, "height": 896},
        device_label="iPhone-Plus (414×896 · mobile · field)",
        auth_kind="leadership",
    )
    if report["finding_count"]:
        kinds = ", ".join(f"{k}={v}" for k, v in sorted(report["finding_tally"].items()))
        print(f"\nFINDINGS · {report['finding_count']} total · {kinds}")
        for f in report["findings"]:
            print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
