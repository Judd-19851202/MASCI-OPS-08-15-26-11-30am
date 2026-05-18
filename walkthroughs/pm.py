"""PM walkthrough — project margin + change-order vigilance.

PM's day: review Daily Reports for cost-code accuracy, watch material
usage for over/under flags, field change-order requests, talk to
supers about projects. Desktop-heavy, occasionally on a phone for
jobsite walks.

STATUS: SCAFFOLDED.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import Walkthrough, run, FIND_HELPTIPS_JS  # noqa: E402


def pm_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    wt.begin_step("01-pm-portal-open", "07:30 · PM opens portal, reviews margin alerts", base + "/pm-portal")
    page.goto(base + "/pm-portal", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)

    wt.begin_step("02-daily-report-review", "08:00 · PM reads yesterday's Daily Reports for cost-code accuracy", base + "/pm-portal")
    page.wait_for_timeout(1500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # TODO: navigate to the project-scoped Daily Report list + check
    # reviewer-side coaching

    wt.note(
        "friction",
        "PM walkthrough is SCAFFOLDED — daily-report-review + change-order + material-flag steps "
        "are placeholder.",
        "Implement when PM walkthrough runs are scheduled.",
    )


if __name__ == "__main__":
    report = run(pm_day, persona="pm",
                 viewport={"width": 1280, "height": 800},
                 device_label="laptop-1280 (1280×800 · desktop · office)",
                 auth_kind="multi")
    print(f"\nFINDINGS · {report['finding_count']} · {report['finding_tally']}")
    for f in report["findings"]:
        print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
