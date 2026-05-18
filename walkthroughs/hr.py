"""HR walkthrough — payroll integrity · people-ops · reviewer-side coaching.

iter221 — operator-stated priority deepening. HR's day is the highest
cultural-drift risk in the platform: communication-sensitive, policy-
sensitive, escalation-sensitive. The walkthrough validates the
operational continuity of HR's actual day:

  07:45  Hub open — scan overnight filings
  08:30  Field Leadership Records review — read overnight write-ups
         (iter218 reviewer-side coaching MUST be visible)
  09:00  Time Verification — clear yesterday's payroll
         (iter213 paycheck-trust anchor MUST land)
  10:15  Employee Accountability — answer 'my check is short' query
  11:30  New-hire onboarding — Employee Lifecycle entry
  13:30  Time Off requests — approve/deny with realistic human judgment
  14:30  Document Expirations — outreach planning

This is mobile NOT mobile — HR works on a desktop. Viewport: 1280×800.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _runner import Walkthrough, run, FIND_HELPTIPS_JS, EXPAND_HELPTIPS_JS  # noqa: E402


def hr_day(page, wt: Walkthrough) -> None:
    base = wt.base_url

    # ── 07:45 · Open HR portal, scan overnight filings ─────────────
    wt.begin_step("01-hr-portal-open", "07:45 · HR opens portal · scan overnight filings + tile badges", base + "/hr")
    page.goto(base + "/hr", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Persona-tagged <title> (iter219). Browser-tab orientation is a
    # genuine HR friction — they bounce between MASCI + Exact + email
    # all morning, and unmarked tabs cost real seconds.
    page_title = page.evaluate("() => (document.title || '').toLowerCase()")
    if "hr · masci" in page_title:
        wt.note(
            "positive-observation",
            f"HR hub <title> persona-tagged: {page_title!r}",
        )
    else:
        wt.note(
            "unclear-wording",
            f"HR hub <title> not persona-tagged at the canonical 'HR · MASCI' — got: {page_title!r}",
            "Verify iter219 usePageTitle wiring on HrHub.jsx.",
        )
    # Tile-badge visibility — HR's at-a-glance morning scan depends on
    # the Time Off pending badge being visible without scrolling.
    badges = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('[data-testid^="hr-tile-badge-"]').forEach(b => {
            const r = b.getBoundingClientRect();
            out.push({
                testid: b.getAttribute('data-testid'),
                visible: r.top >= 0 && r.top < window.innerHeight,
                text: (b.innerText || '').trim(),
            });
        });
        return out;
    }""")
    if not badges:
        wt.note(
            "positive-observation",
            "HR hub renders without overdue/pending badges today — clean queue.",
        )

    # ── 08:30 · Field Leadership Records review (iter218 surface) ─
    wt.begin_step("02-records-review", "08:30 · HR reviews overnight write-ups + crew records (iter218 reviewer-side)",
                  base + "/hr/field-leadership")
    page.goto(base + "/hr/field-leadership", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # CRITICAL operational moment: HR reading overnight write-ups
    # without iter218 reviewer-side coaching is exactly the tone-drift
    # risk the operator named (legal/corporate/auditing tone creep).
    # The iter218 'reviewing isn't auditing' anchor MUST land here.
    records_block_visible = "helptip-block-field-leadership-records" in blocks
    if not records_block_visible:
        wt.note(
            "discoverability-gap",
            "HR /hr/field-leadership records list does NOT render the iter218 "
            "field-leadership.records reviewer-side coaching block. This is "
            "the page HR uses every morning to read overnight write-ups — "
            "the coaching anchor 'reviewing isn't auditing' is invisible here.",
            "Wire <HelpTipBlock formKey='field-leadership.records' /> into "
            "HrFieldLeadership.jsx at the page header (same pattern as "
            "FieldLeadershipRecords.jsx).",
        )
    else:
        # Verify the iter218 anchor actually lands in the body
        page.evaluate(EXPAND_HELPTIPS_JS, "helptip-block-field-leadership-records")
        page.wait_for_timeout(400)
        why_text = page.evaluate("""() => {
            const b = document.querySelector('[data-testid="helptip-field-leadership.records-why-body"]');
            return b ? (b.innerText || '').toLowerCase() : '';
        }""")
        if "auditing" in why_text:
            wt.note(
                "positive-observation",
                "iter218 'reviewing isn't auditing' anchor lands on the HR records page.",
            )
        page.screenshot(path=wt.shot_path("expanded"), full_page=True)

    # ── 09:00 · Time Verification — iter213 surface ────────────────
    wt.begin_step("03-time-verification", "09:00 · HR clears yesterday's payroll · Time Verification",
                  base + "/hr/time-verification")
    page.goto(base + "/hr/time-verification", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    expected = {"helptip-block-time-verification", "helptip-block-time-verification-discrepancy"}
    missing = expected - set(blocks.keys())
    if missing:
        wt.note(
            "discoverability-gap",
            f"Time Verification missing expected iter213 blocks: {sorted(missing)}",
            "Re-verify HrTimeVerification.jsx wiring.",
        )
    else:
        wt.note(
            "positive-observation",
            "Time Verification exposes both iter213 blocks (top + discrepancy).",
        )

    # ── 10:15 · 'My check is short' — Employee Accountability ─────
    wt.begin_step("04-check-short-query", "10:15 · Employee says 'my check is short' · HR opens Accountability",
                  base + "/hr/employee-accountability")
    page.goto(base + "/hr/employee-accountability", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # This is THE high-tension HR moment: an employee at the counter
    # convinced their pay is wrong. The right HR response is to read
    # the record before responding. No coaching surface here means HR
    # has to remember the operational discipline on its own.
    if not blocks:
        wt.note(
            "missing-coaching",
            "Employee Accountability page has NO contextual coaching for the "
            "'my check is short' / 'where's my last paycheck stub' interactions. "
            "These are the moments where HR's response either preserves trust "
            "or burns it.",
            "Author a new HR-scoped tip family `employee-accountability` with "
            "canonical why/who/next/escalate. Voice anchor candidate: 'When an "
            "employee asks about their pay, the answer lives in the record — "
            "read first, respond second.'",
        )

    # ── 11:30 · Onboard a new operator — Employee Lifecycle ───────
    wt.begin_step("05-new-hire-onboard", "11:30 · HR onboards a new operator · Employee Lifecycle",
                  base + "/hr/employees")
    page.goto(base + "/hr/employees", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Onboarding is policy-sensitive AND culturally sensitive. The
    # new-hire's Day-1 experience is set HERE. No coaching here is a
    # genuine gap — the operator explicitly named cultural sensitivity
    # as a top HR-walkthrough validation reason.
    if not blocks:
        wt.note(
            "missing-coaching",
            "Employee Lifecycle (new-hire onboarding) has NO coaching surface. "
            "This is the surface that decides what the new operator's Day-1 "
            "experience looks like — the operator-stated cultural-sensitivity "
            "concern lands hardest here.",
            "Author a new HR-scoped `employee-lifecycle` tip family. Voice "
            "anchor candidate: 'The new hire's first impression of MASCI is "
            "this form. Get it right and they hear about the company; get it "
            "wrong and they hear about the bureaucracy.'",
        )

    # ── 13:30 · Time Off requests — judgment moments ──────────────
    wt.begin_step("06-time-off-review", "13:30 · HR reviews pending Time Off requests · approve/deny with judgment",
                  base + "/hr/time-off")
    page.goto(base + "/hr/time-off", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    # Time-off is the highest-escalation-sensitivity HR surface:
    # bereavement vs. vacation vs. pattern-of-call-outs are three
    # totally different judgment calls. No coaching here is exactly
    # where unprincipled HR happens.
    if not blocks:
        wt.note(
            "missing-coaching",
            "Time Off Requests page has NO coaching surface for the judgment "
            "moments (bereavement-vs-vacation-vs-pattern). HR's decisions "
            "here cascade into trust + retention + EEOC exposure.",
            "Author a new HR-scoped `time-off-review` tip family. Voice "
            "anchor candidate: 'Bereavement is granted, never debated. A "
            "pattern is a conversation, not a denial. Vacation is a yes "
            "with timing.'",
        )

    # ── 14:30 · Document Expirations · outreach planning ──────────
    wt.begin_step("07-doc-expirations", "14:30 · HR scans expiring docs · plans this-week outreach",
                  base + "/document-expirations")
    page.goto(base + "/document-expirations", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2500)
    blocks = page.evaluate(FIND_HELPTIPS_JS)
    wt.record_helptips(blocks)
    page.screenshot(path=wt.shot_path(), full_page=False)
    if not blocks:
        wt.note(
            "missing-coaching",
            "Document Expirations page has no coaching surface for the "
            "outreach-vs-email-blast decision. A bulk email about expiring "
            "CDLs misses the human moment; a phone call to the operator "
            "doesn't.",
            "Consider authoring `document-expirations` tip family with the "
            "'phone call beats email blast' anchor.",
        )


if __name__ == "__main__":
    report = run(hr_day, persona="hr",
                 viewport={"width": 1280, "height": 800},
                 device_label="laptop-1280 (1280×800 · desktop · office)",
                 auth_kind="multi")
    print(f"\nFINDINGS · {report['finding_count']} · {report['finding_tally']}")
    for f in report["findings"]:
        print(f"  [{f['kind']}] step={f['step']} :: {f['observation']}")
