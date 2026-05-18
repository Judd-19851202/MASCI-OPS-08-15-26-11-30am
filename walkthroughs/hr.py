"""HR walkthrough — payroll integrity + people operations.

HR's day touches: Time Verification (the iter213 surface), new-hire
onboarding, write-up filings landing from foremen, and the directory
records. Desktop viewport, frequent multi-tab use.

STATUS: SCAFFOLDED — Tier-1 day-skeleton documented below. Flesh out
in a follow-up iter when HR walkthrough runs are scheduled.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import Walkthrough, run, FIND_HELPTIPS_JS  # noqa: E402


def hr_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    # ── 07:45 · Open HR portal, scan the morning's filings ─────────
    wt.begin_step("01-hr-portal-open", "07:45 · HR opens portal, reviews overnight write-ups + onboardings", base + "/hr-portal")
    page.goto(base + "/hr-portal", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)

    # ── 09:00 · Time Verification — iter213 surface ────────────────
    wt.begin_step("02-time-verification", "09:00 · HR runs Time Verification to clear yesterday's payroll", base + "/hr/time-verification")
    page.goto(base + "/hr/time-verification", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # iter213 verification anchor: should see top block + discrepancy block
    expected = {"helptip-block-time-verification", "helptip-block-time-verification-discrepancy"}
    seen = set(blocks.keys())
    missing = expected - seen
    if missing:
        wt.note(
            "discoverability-gap",
            f"Time Verification missing expected iter213 blocks: {sorted(missing)}.",
            "Re-verify HrTimeVerification.jsx wiring.",
        )
    else:
        wt.note(
            "positive-observation",
            "Time Verification exposes both iter213 blocks (top + discrepancy).",
        )

    # ── 11:30 · Onboard a new hire ─────────────────────────────────
    wt.begin_step("03-new-hire-onboard", "11:30 · HR onboards a new operator", base + "/hr-portal")
    # TODO: flesh out — directory entry flow + welcome-pack issuance

    # ── 14:00 · Review write-ups that landed overnight ─────────────
    wt.begin_step("04-writeup-review", "14:00 · HR reviews newly filed write-ups", base + "/hr-portal")
    # TODO: flesh out — write-up records list + due-process coaching check

    wt.note(
        "friction",
        "HR walkthrough is SCAFFOLDED — steps 03 and 04 are placeholder. "
        "Flesh out when HR walkthrough runs are scheduled.",
        "Implement directory + write-up-list steps with proper coaching checks.",
    )


if __name__ == "__main__":
    report = run(hr_day, persona="hr",
                 viewport={"width": 1280, "height": 800},
                 device_label="laptop-1280 (1280×800 · desktop · office)",
                 auth_kind="multi")
    print(f"\nFINDINGS · {report['finding_count']} · {report['finding_tally']}")
    for f in report["findings"]:
        print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
