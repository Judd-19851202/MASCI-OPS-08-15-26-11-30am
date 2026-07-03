"""Track 19.36 · Executive Report HTML → PDF renderer.

Consumes the Executive Intelligence Model returned by
``assemble_executive_intelligence`` and returns a boardroom-quality HTML
document that WeasyPrint can convert to PDF.

Design constraints
------------------
- Print-safe. A4/Letter friendly.
- No decorative clutter.
- Executive summary first · timeline second · evidence · findings ·
  CAPAs · regulatory review · decisions · readiness · lessons learned.
- Every "Not documented yet." placeholder is emitted where a field is
  missing — never fabricated.
"""
from __future__ import annotations

import html as _html
from typing import Any, Dict, List


def _esc(v: Any) -> str:
    return _html.escape("" if v is None else str(v))


def _row(label: str, value: Any) -> str:
    v = _esc(value) if str(value or "").strip() else '<span class="muted">Not documented yet.</span>'
    return (
        f'<div class="row"><div class="lbl">{_esc(label)}</div>'
        f'<div class="val">{v}</div></div>'
    )


def _section(title: str, body: str, testid: str = "") -> str:
    tid = f' data-section="{_esc(testid)}"' if testid else ""
    return (
        f'<section class="sec"{tid}>'
        f'<h2 class="sec-title">{_esc(title)}</h2>{body}</section>'
    )


def _list_or_empty(items: List[str], empty_text: str = "Not documented yet.") -> str:
    if not items:
        return f'<p class="muted">{_esc(empty_text)}</p>'
    lis = "".join(f"<li>{_esc(i)}</li>" for i in items)
    return f'<ul class="list">{lis}</ul>'


def _render_hero(case_ref: Dict[str, Any], summary: Dict[str, Any]) -> str:
    band = summary.get("severity_band") or "low"
    return f"""
    <header class="hero">
      <div class="hero-brand">MASCI · FORGEDOPS · EXECUTIVE INCIDENT REPORT</div>
      <h1 class="hero-title">{_esc(summary.get("headline") or "Incident")}</h1>
      <div class="hero-meta">
        <span class="chip chip-{_esc(band)}">Severity · {_esc(band).upper()}</span>
        <span class="chip">Case · {_esc(case_ref.get("case_number") or case_ref.get("case_id"))}</span>
        <span class="chip">State · {_esc(case_ref.get("state") or "—")}</span>
      </div>
    </header>
    """


def _render_why(why: Dict[str, Any]) -> str:
    body = (
        _row("What happened", why.get("what_happened"))
        + _row("Why leadership should care", why.get("why_leadership_should_care"))
        + _row("Current risk if no action", why.get("current_risk_if_no_action"))
        + _row("Recommended executive decision", why.get("recommended_executive_decision"))
        + _row("Expected outcome if implemented", why.get("expected_outcome_if_implemented"))
        + f'<p class="source-note">{_esc(why.get("source_note") or "")}</p>'
    )
    return _section("Why It Matters — Executive Briefing", body, "why")


def _render_summary(summary: Dict[str, Any], case_ref: Dict[str, Any]) -> str:
    body = (
        _row("Headline", summary.get("headline"))
        + _row("Occurred at", summary.get("occurred_at"))
        + _row("Location", summary.get("location"))
        + _row("Job number", summary.get("job_number"))
        + _row("Reporter", summary.get("reporter"))
        + _row("Severity band", summary.get("severity_band"))
        + _row("Severity rationale", summary.get("severity_rationale"))
        + _row("Root cause summary", summary.get("root_cause_summary"))
        + _row("Case state", case_ref.get("state"))
    )
    return _section("Executive Summary", body, "exec-summary")


def _render_timeline(timeline: List[Dict[str, Any]]) -> str:
    if not timeline:
        body = '<p class="muted">Not documented yet.</p>'
    else:
        rows = []
        for e in timeline:
            rows.append(
                '<tr>'
                f'<td class="mono">{_esc(e.get("at"))}</td>'
                f'<td>{_esc(e.get("summary"))}</td>'
                f'<td>{_esc(e.get("actor_name") or e.get("actor_role"))}</td>'
                '</tr>'
            )
        body = (
            '<table class="tbl"><thead><tr>'
            '<th>Timestamp</th><th>Event</th><th>Actor</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )
    return _section("Timeline (traceable)", body, "timeline")


def _render_evidence(evidence: List[Dict[str, Any]]) -> str:
    if not evidence:
        body = '<p class="muted">Not documented yet.</p>'
    else:
        rows = []
        for e in evidence:
            state = "Withdrawn" if e.get("withdrawn") else "Active"
            rows.append(
                '<tr>'
                f'<td>{_esc(e.get("label") or e.get("evidence_type"))}</td>'
                f'<td class="mono">{_esc(e.get("evidence_type"))}</td>'
                f'<td>{_esc(e.get("added_by"))}</td>'
                f'<td class="mono">{_esc(e.get("added_at"))}</td>'
                f'<td>{_esc(state)}</td>'
                '</tr>'
            )
        body = (
            '<table class="tbl"><thead><tr>'
            '<th>Item</th><th>Type</th><th>Uploaded by</th>'
            '<th>Uploaded at</th><th>Status</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )
    return _section("Evidence Chain", body, "evidence")


def _render_capa(capa: Dict[str, Any]) -> str:
    items = capa.get("items") or []
    totals = capa.get("totals") or {}
    if not items:
        body = '<p class="muted">Not documented yet.</p>'
    else:
        rows = []
        for a in items:
            rows.append(
                '<tr>'
                f'<td>{_esc(a.get("title"))}</td>'
                f'<td class="mono">{_esc(a.get("action_class"))}</td>'
                f'<td class="mono">{_esc(a.get("state"))}</td>'
                f'<td>{_esc(a.get("assigned_to_name"))}</td>'
                f'<td class="mono">{_esc(a.get("due_at"))}</td>'
                '</tr>'
            )
        body = (
            '<table class="tbl"><thead><tr>'
            '<th>Corrective action</th><th>Class</th><th>State</th>'
            '<th>Assigned to</th><th>Due</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
            f'<p class="totals">Total {totals.get("total",0)} · '
            f'Open {totals.get("open",0)} · '
            f'Verified {totals.get("verified",0)}</p>'
        )
    return _section("Corrective Actions (CAPA)", body, "capa")


def _render_regulatory(reg: Dict[str, Any]) -> str:
    osha = reg.get("osha_review") or {}
    ins = reg.get("insurance_review") or {}
    legal = reg.get("legal_review") or {}
    exe = reg.get("executive_review") or {}
    body = (
        '<h3 class="sub">OSHA Review</h3>'
        + _row("Recordable", (
            "Yes" if osha.get("osha_recordable") is True
            else "No" if osha.get("osha_recordable") is False
            else ""
        ))
        + _row("OSHA case number", osha.get("osha_case_number"))
        + _row("Recordability reason", osha.get("recordability_reason"))
        + '<h3 class="sub">Insurance / Workers\' Comp Review</h3>'
        + _row("Days lost", ins.get("workers_comp_days_lost"))
        + _row("Days restricted", ins.get("workers_comp_days_restricted"))
        + _row("Medical summary", ins.get("medical_summary"))
        + '<h3 class="sub">Legal / Agency Review</h3>'
        + _row("Police case number", legal.get("police_case_number"))
        + '<h3 class="sub">Executive Review</h3>'
        + _row("Executive reviewer", exe.get("reviewer"))
        + _row("Executive review notes", exe.get("notes"))
    )
    return _section("Regulatory · Insurance · Legal · Executive Review", body, "regulatory")


def _render_readiness(readiness: Dict[str, Any]) -> str:
    subs = readiness.get("sub_scores") or []
    rows = []
    for s in subs:
        rows.append(
            '<tr>'
            f'<td class="mono">{_esc(s.get("key"))}</td>'
            f'<td>{_esc(s.get("num"))}/{_esc(s.get("den"))}</td>'
            f'<td>{_esc(s.get("pct"))}%</td>'
            f'<td>{_esc(s.get("rationale"))}</td>'
            '</tr>'
        )
    body = (
        f'<p class="hero-meta"><span class="chip">Overall '
        f'{_esc(readiness.get("overall_pct",0))}% · '
        f'{_esc(readiness.get("band","low")).upper()}</span></p>'
        '<table class="tbl"><thead><tr>'
        '<th>Sub-score</th><th>Numerator</th><th>%</th><th>Rationale</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
    )
    return _section("Readiness Score (explainable)", body, "readiness")


def _render_decisions(decisions: List[Dict[str, Any]]) -> str:
    if not decisions:
        body = '<p class="muted">Not documented yet.</p>'
    else:
        rows = []
        for d in decisions:
            rows.append(
                '<tr>'
                f'<td class="mono">{_esc(d.get("at"))}</td>'
                f'<td>{_esc(d.get("decision"))}</td>'
                f'<td>{_esc(d.get("from_state"))} → {_esc(d.get("to_state"))}</td>'
                f'<td>{_esc(d.get("actor_name") or d.get("actor_role"))}</td>'
                f'<td>{_esc(d.get("reason"))}</td>'
                '</tr>'
            )
        body = (
            '<table class="tbl"><thead><tr>'
            '<th>When</th><th>Decision</th><th>Transition</th>'
            '<th>Decision maker</th><th>Reason</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )
    return _section("Decision Records", body, "decisions")


def _render_ops(ops: Dict[str, Any]) -> str:
    body = (
        _row("Occurred at", ops.get("occurred_at"))
        + _row("Reported at", ops.get("reported_at"))
        + _row("Safety intake at", ops.get("safety_intake_at"))
        + _row("First CAPA at", ops.get("first_capa_at"))
        + _row("Closed at", ops.get("closed_at"))
        + _row("Time to intake (days)", ops.get("time_to_intake_days"))
        + _row("Time to CAPA (days)", ops.get("time_to_capa_days"))
        + _row("Time to closure (days)", ops.get("time_to_closure_days"))
        + _row("Days open", ops.get("days_open"))
    )
    return _section("Operational Intelligence", body, "ops")


def _render_lessons(why: Dict[str, Any]) -> str:
    body = (
        _row("Recommended decision", why.get("recommended_executive_decision"))
        + _row("Expected outcome", why.get("expected_outcome_if_implemented"))
    )
    return _section("Lessons Learned · Forward Prevention", body, "lessons")


# ---------------------------------------------------------------------------
# Top-level template
# ---------------------------------------------------------------------------
_CSS = """
@page { size: Letter; margin: 0.75in; }
body { font-family: 'Helvetica Neue', 'Helvetica', Arial, sans-serif;
       color: #0f172a; font-size: 10.5pt; line-height: 1.42; }
.hero { border-bottom: 3px solid #0f172a; padding-bottom: 8pt;
        margin-bottom: 14pt; }
.hero-brand { font-size: 8pt; letter-spacing: 0.24em; color: #64748b;
              text-transform: uppercase; }
.hero-title { font-size: 20pt; margin: 4pt 0 6pt 0; font-weight: 900; }
.hero-meta .chip { display: inline-block; padding: 2pt 8pt; border: 1pt solid #cbd5e1;
                    border-radius: 12pt; margin-right: 6pt; font-size: 8.5pt;
                    letter-spacing: 0.06em; text-transform: uppercase; }
.chip-high      { background: #fee2e2; border-color: #fca5a5; color: #7f1d1d; }
.chip-elevated  { background: #fef3c7; border-color: #fcd34d; color: #78350f; }
.chip-moderate  { background: #ffedd5; border-color: #fdba74; color: #7c2d12; }
.chip-low       { background: #ecfeff; border-color: #67e8f9; color: #164e63; }
.sec { border-top: 1pt solid #e2e8f0; padding-top: 8pt; margin-top: 10pt; }
.sec-title { font-size: 12pt; margin: 0 0 6pt 0; letter-spacing: 0.02em; }
.sub { font-size: 10pt; margin: 8pt 0 4pt 0; color: #334155; }
.row { display: flex; margin: 2pt 0; page-break-inside: avoid; }
.lbl { flex: 0 0 30%; color: #64748b; font-size: 9pt;
       text-transform: uppercase; letter-spacing: 0.08em; }
.val { flex: 1 1 70%; }
.muted { color: #94a3b8; font-style: italic; }
.mono { font-family: 'SFMono-Regular', Menlo, monospace; font-size: 9pt; }
.tbl { width: 100%; border-collapse: collapse; margin-top: 4pt; }
.tbl th, .tbl td { border: 0.5pt solid #cbd5e1; padding: 3pt 5pt;
                   text-align: left; vertical-align: top; font-size: 9pt; }
.tbl th { background: #f1f5f9; }
.totals { font-size: 9pt; color: #475569; margin-top: 4pt; }
.source-note { font-size: 8.5pt; color: #64748b; margin-top: 6pt;
               border-left: 2pt solid #cbd5e1; padding-left: 6pt; }
.list li { margin: 1pt 0; }
"""


def render_executive_report_html(model: Dict[str, Any]) -> str:
    case_ref = model.get("case_ref") or {}
    summary = model.get("executive_summary") or {}
    why = model.get("why_it_matters") or {}
    timeline = model.get("timeline") or []
    evidence = model.get("evidence_chain") or []
    capa = model.get("corrective_actions") or {}
    regulatory = model.get("regulatory_review") or {}
    readiness = model.get("readiness") or {}
    decisions = model.get("decision_records") or []
    ops = model.get("operational_intelligence") or {}

    body_parts = [
        _render_hero(case_ref, summary),
        _render_why(why),
        _render_summary(summary, case_ref),
        _render_timeline(timeline),
        _render_evidence(evidence),
        _render_capa(capa),
        _render_regulatory(regulatory),
        _render_ops(ops),
        _render_readiness(readiness),
        _render_decisions(decisions),
        _render_lessons(why),
    ]
    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="utf-8"/>'
        f"<title>Executive Report · {_esc(case_ref.get('case_number') or '')}</title>"
        f"<style>{_CSS}</style></head><body>" + "".join(body_parts) + "</body></html>"
    )


__all__ = ["render_executive_report_html"]
