"""Superintendent walkthrough — multi-job oversight, multi-portal handoff.

A superintendent runs 2-5 jobs. They review what foremen filed, talk
to PMs, walk safety with the Safety team, and field surprise calls
from Dispatch. Cross-portal handoff is the operational heart of
their day. Tablet-class viewport (wider than a phone but mobile-ish).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import Walkthrough, run, FIND_HELPTIPS_JS, EXPAND_HELPTIPS_JS  # noqa: E402


def superintendent_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    # ── 05:50 · Open the leadership hub, scan the night's records ──
    wt.begin_step("01-leadership-hub", "05:50 · Super opens /leadership to scan field records", base + "/leadership")
    page.goto(base + "/leadership", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # The leadership hub is the super's daily entry. Verify it's
    # immediately legible (no "what is this place?" friction).
    page_title = page.evaluate("() => (document.title || '').toLowerCase()")
    if "leadership" not in page_title and "field" not in page_title:
        wt.note(
            "unclear-wording",
            f"Leadership hub <title> tag does not signal the persona — got: {page_title!r}.",
            "Set a descriptive document.title for crew/super orientation.",
        )

    # ── 07:00 · Review yesterday's daily reports (cross-portal) ───
    wt.begin_step("02-review-daily-reports", "07:00 · Super reviews crew Daily Reports filed last night", base + "/leadership/records")
    page.goto(base + "/leadership/records", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    if not blocks:
        wt.note(
            "missing-coaching",
            "Leadership records list has no HelpTip coverage — supers reviewing crew filings get no "
            "reviewer-side coaching ('what to look for', 'when to push back', 'when to escalate').",
            "Author Tier-2 reviewer-coaching tips for the leadership records list page (field-leadership.records).",
        )

    # ── 09:30 · Crew-evaluation entry on a new operator ───────────
    wt.begin_step("03-crew-eval", "09:30 · Super writes a crew evaluation on a 6-mo operator", base + "/leadership/crew_eval/new")
    page.goto(base + "/leadership/crew_eval/new", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    if "/leadership/login" in page.url:
        wt.note(
            "friction",
            "Crew eval redirected to leadership login despite seeded session token.",
            "See foreman walkthrough step 03 finding.",
        )
    else:
        blocks = page.evaluate(FIND_HELPTIPS_JS)
        wt.record_helptips(blocks)
        page.screenshot(path=wt.shot_path(), full_page=False)
        # Crew evaluations are currently using the legacy WhyItMattersPanel,
        # not the HelpTip engine. Verify and flag.
        legacy_panel = page.evaluate("""() => {
            const els = document.querySelectorAll('[data-why-it-matters], .why-it-matters, [data-testid*="why-matters"]');
            return els.length;
        }""")
        helptip_count = sum(blocks.values())
        if helptip_count == 0 and legacy_panel == 0:
            wt.note(
                "missing-coaching",
                "Crew evaluation form has no contextual coaching surface at all — neither HelpTip "
                "block nor legacy WhyItMattersPanel.",
                "Author Tier-1 crew-eval tips (calibration, evidence basis, blind-spot awareness).",
            )
        elif helptip_count == 0:
            wt.note(
                "voice-drift",
                "Crew evaluation uses the legacy WhyItMattersPanel instead of the iter209+ HelpTip engine — "
                "voice and visual consistency drift from the modern coaching pattern.",
                "Migrate crew_eval kind to the HelpTip engine; author the tips registry entries.",
            )
        else:
            wt.note(
                "positive-observation",
                f"crew_eval surface exposes {helptip_count} HelpTip toggles.",
            )

    # ── 13:00 · Walks the jobsite with Safety, files an audit ─────
    wt.begin_step("04-safety-cross-portal", "13:00 · Super walks the jobsite with Safety; Safety files an audit", base + "/safety-portal/login")
    page.goto(base + "/safety-portal/login", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(1500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Cross-portal handoff: the super doesn't usually have a Safety
    # login, but the page should explain what to do if they DON'T.
    help_block_exists = page.evaluate("""() => {
        return !!document.querySelector('[data-testid="portal-login-help-block"], a[href*="onboard-safety"], a[href*="tshoot-safety"]');
    }""")
    if not help_block_exists:
        wt.note(
            "missing-coaching",
            "Safety login page does not surface the iter202 PortalLoginHelp triple (onboard/identity/troubleshoot) "
            "to a super arriving without a Safety account.",
            "Verify PortalLoginHelp wiring on SafetyLogin.jsx.",
        )
    else:
        wt.note(
            "positive-observation",
            "Safety login surfaces the iter202 onboarding/troubleshoot triple — cross-portal handoff "
            "is operationally legible to a super with no Safety account.",
        )

    # ── 17:00 · End-of-day: super skims tomorrow's expected loads ─
    wt.begin_step("05-tomorrow-planning", "17:00 · Super reviews dispatch + tomorrow's expected loads", base + "/asset-transfers")
    page.goto(base + "/asset-transfers", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # asset-transfers is the public asset-transfer ledger — verify
    # supers can read it without a dispatch account.
    is_blocked = "login" in page.url or "unauthorized" in (page.content() or "").lower()[:500]
    if is_blocked:
        wt.note(
            "workflow-confusion",
            f"/asset-transfers requires authentication that a super may not have — current URL: {page.url}.",
            "Document whether asset-transfers is super-readable OR add a cross-portal read pattern.",
        )
    else:
        wt.note(
            "positive-observation",
            "/asset-transfers is reachable for the super — cross-portal asset visibility intact.",
        )


if __name__ == "__main__":
    report = run(
        superintendent_day,
        persona="superintendent",
        viewport={"width": 768, "height": 1024},
        device_label="iPad-class (768×1024 · tablet · field+office hybrid)",
        auth_kind="leadership",
    )
    if report["finding_count"]:
        kinds = ", ".join(f"{k}={v}" for k, v in sorted(report["finding_tally"].items()))
        print(f"\nFINDINGS · {report['finding_count']} total · {kinds}")
        for f in report["findings"]:
            print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
