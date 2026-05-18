"""Safety walkthrough — incident response, audit walks, training oversight.

Safety's day: respond to incident filings as they arrive, walk
jobsites with supers, file safety audits, sign training rosters.
Mobile + tablet hybrid — they're in the field more than HR/PM but
less than foremen.

STATUS: SCAFFOLDED — see hr.py for the run pattern.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import Walkthrough, run, FIND_HELPTIPS_JS  # noqa: E402


def safety_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    wt.begin_step("01-safety-portal-open", "07:00 · Safety opens portal, checks overnight incidents", base + "/safety-portal")
    page.goto(base + "/safety-portal", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)

    wt.begin_step("02-incident-review", "08:30 · Safety reviews the foreman's near-miss filing from yesterday", base + "/incidents/submit")
    page.goto(base + "/incidents/submit", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)

    # TODO: flesh out — audit submission, training roster, hazard tracker

    wt.note(
        "friction",
        "Safety walkthrough is SCAFFOLDED — audit/training/hazard steps are placeholder.",
        "Implement when Safety walkthrough runs are scheduled.",
    )


if __name__ == "__main__":
    report = run(safety_day, persona="safety",
                 viewport={"width": 768, "height": 1024},
                 device_label="iPad-class (768×1024 · tablet · field+office hybrid)",
                 auth_kind="multi")
    print(f"\nFINDINGS · {report['finding_count']} · {report['finding_tally']}")
    for f in report["findings"]:
        print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
