"""
Field Leadership PDF renderer.

Produces a clean MASCI-styled PDF (WeasyPrint) for any of the 10 Field
Leadership form kinds. Schema-driven — the renderer reads `details` and
fans every key/value pair out into a printable section.

Footer: "Generated through MASCI HUB — Powered by ForgedOps LLC | © 2026 ForgedOps LLC"
(matches the rest of the system per the 2026-05-07 ForgedOps rebrand.)
"""

from __future__ import annotations

import html
from typing import Any, Dict, List

from weasyprint import HTML, CSS  # type: ignore

# Same kind-meta dict as the route file — duplicated to avoid a circular
# import (this file is imported from server.py at module load time).
_KIND_META: Dict[str, Dict[str, Any]] = {
    "write_up":                  {"title_en": "Employee Write-Up",                "title_es": "Amonestación al Empleado"},
    "verbal_coaching":           {"title_en": "Verbal Coaching Documentation",    "title_es": "Documentación de Asesoramiento Verbal"},
    "attendance":                {"title_en": "Attendance / Tardy Documentation", "title_es": "Documentación de Asistencia / Tardanza"},
    "recognition":               {"title_en": "Employee Recognition / Reward",    "title_es": "Reconocimiento al Empleado"},
    "equipment_checkout":        {"title_en": "Equipment Checkout & Accountability", "title_es": "Asignación y Responsabilidad de Equipo"},
    "new_employee_eval":         {"title_en": "New Employee Evaluation",          "title_es": "Evaluación de Nuevo Empleado"},
    "crew_eval":                 {"title_en": "Crew Evaluation",                  "title_es": "Evaluación de Cuadrilla"},
    "promotion_recommendation":  {"title_en": "Promotion Recommendation",         "title_es": "Recomendación de Ascenso"},
    "training_deficiency":       {"title_en": "Training Deficiency / Retraining", "title_es": "Deficiencia de Capacitación / Reentrenamiento"},
    "supervisor_notes":          {"title_en": "Supervisor Notes Log",             "title_es": "Registro de Notas del Supervisor"},
}


def _h(s: Any) -> str:
    return html.escape("" if s is None else str(s))


def _fmt_date(iso: str) -> str:
    if not iso:
        return ""
    return iso.replace("T", " ").split(".", 1)[0][:16]


def _section_rows(label_value_pairs: List) -> str:
    rows = []
    for label, value in label_value_pairs:
        v = _h(value) if value not in (None, "") else "<span class='muted'>—</span>"
        rows.append(
            f"<tr><th>{_h(label)}</th><td>{v}</td></tr>"
        )
    return "<table class='kv'>" + "".join(rows) + "</table>"


def _details_block(details: Dict[str, Any]) -> str:
    if not details:
        return ""
    blocks = []
    for k, v in details.items():
        label = k.replace("_", " ").title()
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v) or "—"
        elif isinstance(v, dict):
            # nested rating dict — render as sub-table
            sub_rows = "".join(
                f"<tr><th>{_h(kk.replace('_',' ').title())}</th><td>{_h(vv)}</td></tr>"
                for kk, vv in v.items()
            )
            blocks.append(
                f"<div class='detail'><h4>{_h(label)}</h4><table class='kv'>{sub_rows}</table></div>"
            )
            continue
        v_html = _h(v).replace("\n", "<br/>") if v else "<span class='muted'>—</span>"
        if isinstance(v, str) and len(v) > 80:
            blocks.append(f"<div class='detail'><h4>{_h(label)}</h4><div class='paragraph'>{v_html}</div></div>")
        else:
            blocks.append(f"<div class='detail-row'><span class='detail-label'>{_h(label)}</span><span class='detail-value'>{v_html}</span></div>")
    return f"<section><h3>Details</h3>{''.join(blocks)}</section>"


def _photos_block(photos: List[str]) -> str:
    if not photos:
        return ""
    imgs = "".join(
        f"<img src='{_h(p)}' alt='photo' />" for p in photos[:8]
    )
    return f"<section><h3>Photos</h3><div class='photos'>{imgs}</div></section>"


def _signatures_block(rec: Dict[str, Any]) -> str:
    """Renders supervisor + employee (or refusal-with-witness) signatures."""
    parts: List[str] = []
    sup = rec.get("supervisor_signature") or ""
    if sup:
        parts.append(
            f"<div class='sig-card'><div class='sig-label'>Supervisor Signature</div>"
            f"<img src='{_h(sup)}' /><div class='sig-name'>{_h(rec.get('supervisor_name') or '')}</div></div>"
        )

    if rec.get("employee_refused"):
        parts.append(
            "<div class='sig-card refused'><div class='sig-label'>Employee Refused to Sign</div>"
            f"<div class='sig-name'>{_h(rec.get('employee_name') or '')}</div></div>"
        )
        wsig = rec.get("witness_signature") or ""
        if wsig:
            parts.append(
                f"<div class='sig-card'><div class='sig-label'>Witness Signature</div>"
                f"<img src='{_h(wsig)}' /><div class='sig-name'>{_h(rec.get('witness_name') or '')}</div></div>"
            )
    elif rec.get("employee_signature"):
        parts.append(
            f"<div class='sig-card'><div class='sig-label'>Employee Signature</div>"
            f"<img src='{_h(rec['employee_signature'])}' /><div class='sig-name'>{_h(rec.get('employee_name') or '')}</div></div>"
        )

    if not parts:
        return ""

    ack = ("<p class='ack'>Employee signature acknowledges receipt of this "
           "document and does not necessarily indicate agreement with its contents.</p>")
    return f"<section><h3>Signatures</h3>{ack}<div class='sigs'>{''.join(parts)}</div></section>"


def render_field_leadership_pdf(rec: Dict[str, Any]) -> bytes:
    """Render a single Field Leadership record to a PDF byte string."""
    kind = rec.get("kind", "")
    meta = _KIND_META.get(kind, {})
    title = meta.get("title_en") or kind.replace("_", " ").title()

    job_block = _section_rows([
        ("Project #", rec.get("project_number")),
        ("Project Name", rec.get("project_name")),
        ("Location", rec.get("location") or rec.get("work_area")),
        ("Client", rec.get("client")),
        ("Assigned PM", rec.get("assigned_pm")),
    ])
    employee_block = _section_rows([
        ("Employee Name", rec.get("employee_name")),
        ("Position", rec.get("employee_position")),
        ("Employee ID", (rec.get("details") or {}).get("employee_id_hint") or ""),
    ])
    submission_block = _section_rows([
        ("Supervisor", rec.get("supervisor_name")),
        ("Date / Time", _fmt_date(rec.get("occurred_at") or rec.get("created_at") or "")),
        ("Work Area", rec.get("work_area")),
        ("Language", "Spanish (translated to English)" if rec.get("language") == "es" else "English"),
    ])

    # Prefer the EN-translated details when available so the PDF is always
    # legible to office staff, even if the foreman submitted in Spanish.
    details_for_pdf = rec.get("details_en") or rec.get("details") or {}

    doc_html = f"""<!doctype html><html><head><meta charset='utf-8'>
<title>{_h(title)} — MASCI HUB</title>
<style>
@page {{
  size: Letter;
  margin: 18mm 14mm 22mm 14mm;
  @bottom-center {{
    content: "Generated through MASCI HUB — Powered by ForgedOps LLC | © 2026 ForgedOps LLC";
    font-family: -apple-system, sans-serif;
    font-size: 8pt;
    color: #475569;
    letter-spacing: 0.04em;
  }}
  @bottom-right {{
    content: counter(page) " / " counter(pages);
    font-family: -apple-system, sans-serif;
    font-size: 8pt;
    color: #94a3b8;
  }}
}}
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif; color:#0f172a; font-size:10pt; line-height:1.45; margin:0; }}
.header {{ border-bottom:3px solid #b91c1c; padding-bottom:10pt; margin-bottom:18pt; display:flex; justify-content:space-between; align-items:flex-end; }}
.brand {{ font-family: ui-monospace, monospace; font-size:9pt; letter-spacing:.22em; text-transform:uppercase; color:#64748b; }}
.title {{ font-size:22pt; font-weight:900; color:#0f172a; margin-top:4pt; line-height:1.05; }}
.kicker {{ font-family: ui-monospace, monospace; font-size:8pt; letter-spacing:.18em; text-transform:uppercase; color:#b91c1c; font-weight:700; }}
section {{ margin:14pt 0; page-break-inside: avoid; }}
section h3 {{ font-size:11pt; text-transform:uppercase; letter-spacing:.18em; color:#0f172a; border-bottom:1px solid #e2e8f0; padding-bottom:4pt; margin-bottom:8pt; }}
section h4 {{ font-size:9pt; text-transform:uppercase; letter-spacing:.12em; color:#475569; margin:10pt 0 4pt; }}
.three-col {{ display:flex; gap:12pt; }}
.three-col > div {{ flex:1; }}
.three-col h4 {{ font-size:8.5pt; color:#b91c1c; margin:0 0 4pt; letter-spacing:.18em; }}
table.kv {{ width:100%; border-collapse:collapse; }}
table.kv th, table.kv td {{ border:1px solid #e2e8f0; padding:5pt 7pt; text-align:left; vertical-align:top; font-size:9.5pt; }}
table.kv th {{ background:#f8fafc; font-weight:600; width:38%; color:#475569; }}
.muted {{ color:#94a3b8; }}
.detail {{ margin:8pt 0; }}
.paragraph {{ background:#f8fafc; border-left:3px solid #cbd5e1; padding:7pt 10pt; white-space:pre-wrap; }}
.detail-row {{ display:flex; justify-content:space-between; padding:4pt 0; border-bottom:1px dotted #e2e8f0; }}
.detail-label {{ font-weight:600; color:#475569; }}
.detail-value {{ text-align:right; max-width:60%; }}
.photos {{ display:flex; flex-wrap:wrap; gap:8pt; }}
.photos img {{ width:48%; max-height:280pt; object-fit:contain; border:1px solid #e2e8f0; padding:3pt; background:#f8fafc; }}
.sigs {{ display:flex; gap:14pt; flex-wrap:wrap; margin-top:8pt; }}
.sig-card {{ flex:1; min-width:180pt; border:1px solid #cbd5e1; border-radius:4pt; padding:10pt; background:#fff; }}
.sig-card.refused {{ background:#fef2f2; border-color:#fca5a5; }}
.sig-label {{ font-family: ui-monospace, monospace; font-size:8pt; letter-spacing:.18em; text-transform:uppercase; color:#475569; margin-bottom:6pt; }}
.sig-card img {{ max-height:60pt; max-width:100%; }}
.sig-name {{ margin-top:4pt; font-weight:600; font-size:9pt; }}
.ack {{ font-size:8pt; color:#475569; font-style:italic; margin:0 0 8pt; }}
</style></head><body>
  <div class='header'>
    <div>
      <div class='brand'>MASCI HUB · Field Leadership</div>
      <div class='title'>{_h(title)}</div>
      <div class='kicker'>{_h(rec.get('project_number') or '')} · {_h(rec.get('project_name') or '')}</div>
    </div>
    <div style='text-align:right;font-size:9pt;color:#64748b'>
      <div>{_fmt_date(rec.get('occurred_at') or '')}</div>
      <div>ID {_h((rec.get('id') or '')[:8])}</div>
    </div>
  </div>

  <section>
    <div class='three-col'>
      <div><h4>Job Information</h4>{job_block}</div>
      <div><h4>Employee</h4>{employee_block}</div>
      <div><h4>Submission</h4>{submission_block}</div>
    </div>
  </section>

  {_details_block(details_for_pdf)}
  {_photos_block(rec.get("photos") or [])}
  {_signatures_block(rec)}

</body></html>"""

    return HTML(string=doc_html).write_pdf()
