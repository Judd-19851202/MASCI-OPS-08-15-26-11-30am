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

from weasyprint import HTML

# Resolve photo:// refs (R2-backed) → base64 data URLs at render time so
# WeasyPrint can embed them. Pass-through for legacy data: URLs.
try:
    from photo_storage import resolve_to_data_url_sync as _resolve_photo_ref
except Exception:  # noqa: BLE001
    def _resolve_photo_ref(ref: str) -> str:  # type: ignore[misc]
        return ref or ""

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


def _equipment_lines_photos_block(lines: List[Dict[str, Any]],
                                  photo_field: str = "photos",
                                  heading: str = "Photos by Item",
                                  empty_label: str = "—") -> str:
    """Render a per-line photo gallery block.

    The Checkout/Return forms collect photos PER equipment line (not at
    the top of the record), but the canonical PDF photo block was reading
    ``rec.photos`` only and missing them entirely. This walks every line
    and emits a captioned grid for each line that has photos.

    Each grid limits to 8 photos to keep the PDF size reasonable when a
    foreman uploads dozens. Photos are passed through verbatim — they
    can be data URLs (data:image/...;base64,...) or HTTP URLs; WeasyPrint
    handles both.
    """
    if not lines:
        return ""
    blocks: List[str] = []
    for idx, line in enumerate(lines):
        photos = line.get(photo_field) or []
        if not photos:
            continue
        caption = " · ".join(p for p in [
            line.get("manufacturer") or "",
            line.get("name") or "",
            f"S/N {line.get('serial')}" if line.get("serial") else "",
        ] if p) or empty_label
        imgs_list = []
        for p in photos[:8]:
            if not isinstance(p, str):
                continue
            resolved = _resolve_photo_ref(p)
            if resolved:
                imgs_list.append(f"<img src='{_h(resolved)}' alt='Item {idx+1} photo' />")
        imgs = "".join(imgs_list)
        blocks.append(
            f"<div class='line-photos'>"
            f"<div class='line-photos-caption'>"
            f"<span class='line-photos-num'>Item #{idx + 1}</span>"
            f"<span class='line-photos-meta'>{_h(caption)}</span>"
            f"</div>"
            f"<div class='photos'>{imgs}</div>"
            f"</div>"
        )
    if not blocks:
        return ""
    return f"<section><h3>{_h(heading)}</h3>{''.join(blocks)}</section>"


def _photos_block(photos: List[str]) -> str:
    if not photos:
        return ""
    imgs_list = []
    for p in photos[:8]:
        if not isinstance(p, str):
            continue
        resolved = _resolve_photo_ref(p)
        if resolved:
            imgs_list.append(f"<img src='{_h(resolved)}' alt='photo' />")
    if not imgs_list:
        return ""
    imgs = "".join(imgs_list)
    return f"<section><h3>Photos</h3><div class='photos'>{imgs}</div></section>"


# ----- Equipment Checkout — line-items table + grand total ----------

def _money(v: Any) -> str:
    try:
        return f"${float(v or 0):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _equipment_lines_block(details: Dict[str, Any]) -> str:
    """Render the line-items table for equipment_checkout records."""
    lines = details.get("equipment_lines") or []
    if not lines:
        return ""
    rows: List[str] = []
    grand_total = 0.0
    for line in lines:
        try:
            qty = float(line.get("qty") or 1)
        except (TypeError, ValueError):
            qty = 1
        try:
            rv = float(line.get("replacement_value") or 0)
        except (TypeError, ValueError):
            rv = 0
        line_total = qty * rv
        grand_total += line_total
        rows.append(
            "<tr>"
            f"<td>{_h(line.get('manufacturer') or '—')}</td>"
            f"<td>{_h(line.get('name') or '—')}</td>"
            f"<td>{_h(line.get('model') or '')}</td>"
            f"<td>{_h(line.get('serial') or '')}</td>"
            f"<td class='num'>{int(qty) if qty == int(qty) else qty}</td>"
            f"<td>{_h(line.get('condition') or '')}</td>"
            f"<td class='num'>{_money(rv)}</td>"
            f"<td class='num'><strong>{_money(line_total)}</strong></td>"
            "</tr>"
        )
        notes = (line.get("notes") or "").strip()
        if notes:
            rows.append(
                f"<tr class='notes-row'><td colspan='8'>"
                f"<span class='notes-lbl'>Notes:</span> {_h(notes)}"
                "</td></tr>"
            )
    table = (
        "<table class='lines'>"
        "<thead><tr>"
        "<th>Manufacturer</th><th>Equipment / Tool</th><th>Model</th>"
        "<th>Serial / Asset ID</th><th class='num'>Qty</th>"
        "<th>Condition</th><th class='num'>Replacement</th>"
        "<th class='num'>Line Total</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "<tfoot><tr>"
        "<td colspan='7' class='grand-label'>Total Replacement Value Issued</td>"
        f"<td class='num grand'>{_money(grand_total)}</td>"
        "</tr></tfoot>"
        "</table>"
    )
    return f"<section><h3>Equipment Issued</h3>{table}</section>"


# Long acknowledgement text per company spec — exact wording.
EQUIPMENT_ACK_EN = (
    "I acknowledge receipt of the company equipment, tools, and/or property "
    "listed above. I understand that this equipment remains the property of "
    "MASCI General Contractors and is issued to me for company business "
    "purposes only.\n\n"
    "I agree to use, secure, care for, maintain, and return all issued "
    "equipment in accordance with company policy, manufacturer instructions, "
    "and applicable safety requirements.\n\n"
    "I understand that loss, theft, damage, misuse, neglect, abuse, "
    "unauthorized use, or failure to return company equipment may result "
    "in disciplinary action and may result in financial responsibility for "
    "repair or replacement costs, only to the extent permitted by applicable "
    "federal law, Florida law, and company policy. Any payroll deduction or "
    "reimbursement will be handled only where legally permitted and with "
    "any required authorization.\n\n"
    "My signature acknowledges receipt of the listed equipment and this "
    "responsibility notice."
)

EQUIPMENT_ACK_ES = (
    "Reconozco haber recibido el equipo, herramientas y/o propiedad de la "
    "empresa que se enumeran arriba. Entiendo que este equipo sigue siendo "
    "propiedad de MASCI General Contractors y se me entrega únicamente "
    "para fines comerciales de la empresa.\n\n"
    "Acepto usar, asegurar, cuidar, mantener y devolver todo el equipo "
    "entregado conforme a la política de la empresa, las instrucciones del "
    "fabricante y los requisitos de seguridad aplicables.\n\n"
    "Entiendo que la pérdida, robo, daño, uso indebido, negligencia, abuso, "
    "uso no autorizado o falta de devolución del equipo de la empresa "
    "puede resultar en acción disciplinaria y puede generar responsabilidad "
    "económica por costos de reparación o reemplazo, únicamente en la "
    "medida permitida por la ley federal aplicable, la ley de Florida y "
    "la política de la empresa. Cualquier deducción de nómina o "
    "reembolso se realizará solo donde sea legalmente permitido y con "
    "cualquier autorización requerida.\n\n"
    "Mi firma reconoce la recepción del equipo enumerado y este aviso "
    "de responsabilidad."
)


def _equipment_ack_block(language: str) -> str:
    text = EQUIPMENT_ACK_ES if language == "es" else EQUIPMENT_ACK_EN
    paragraphs = "".join(f"<p>{_h(p)}</p>" for p in text.split("\n\n"))
    return (
        "<section class='ack-section'><h3>Employee Responsibility Acknowledgement</h3>"
        f"<div class='ack-box'>{paragraphs}</div></section>"
    )


# ----- Equipment Return — line-items table with return condition + delta

def _equipment_return_block(details: Dict[str, Any]) -> str:
    lines = details.get("equipment_lines") or []
    if not lines:
        return ""
    rows: List[str] = []
    grand_value = 0.0
    grand_damage = 0.0
    for line in lines:
        try:
            qty = float(line.get("qty") or 1)
        except (TypeError, ValueError):
            qty = 1
        try:
            rv = float(line.get("replacement_value") or 0)
        except (TypeError, ValueError):
            rv = 0
        try:
            damage = float(line.get("damage_amount") or 0)
        except (TypeError, ValueError):
            damage = 0
        line_value = qty * rv
        grand_value += line_value
        grand_damage += damage
        rc = (line.get("return_condition") or "").strip()
        rc_class = "ret-good" if rc.lower() in ("good", "new", "fair") else (
            "ret-bad" if rc.lower() in ("damaged", "missing", "lost") else "ret-neutral"
        )
        rows.append(
            "<tr>"
            f"<td>{_h(line.get('manufacturer') or '—')}</td>"
            f"<td>{_h(line.get('name') or '—')}</td>"
            f"<td>{_h(line.get('model') or '')}</td>"
            f"<td>{_h(line.get('serial') or '')}</td>"
            f"<td class='num'>{int(qty) if qty == int(qty) else qty}</td>"
            f"<td>{_h(line.get('condition') or '')}</td>"
            f"<td class='{rc_class}'>{_h(rc or '—')}</td>"
            f"<td class='num'>{_money(line_value)}</td>"
            f"<td class='num damage'>{_money(damage)}</td>"
            "</tr>"
        )
        notes = (line.get("return_notes") or line.get("notes") or "").strip()
        if notes:
            rows.append(
                f"<tr class='notes-row'><td colspan='9'>"
                f"<span class='notes-lbl'>Notes:</span> {_h(notes)}"
                "</td></tr>"
            )
    table = (
        "<table class='lines'>"
        "<thead><tr>"
        "<th>Manufacturer</th><th>Equipment / Tool</th><th>Model</th>"
        "<th>Serial / Asset ID</th><th class='num'>Qty</th>"
        "<th>Issued Cond.</th><th>Return Cond.</th>"
        "<th class='num'>Replacement</th><th class='num'>Loss / Damage</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "<tfoot>"
        "<tr>"
        "<td colspan='7' class='grand-label'>Total Replacement Value</td>"
        f"<td class='num grand'>{_money(grand_value)}</td>"
        f"<td class='num grand damage'>{_money(grand_damage)}</td>"
        "</tr>"
        "</tfoot>"
        "</table>"
    )
    delta_callout = ""
    if grand_damage > 0:
        delta_callout = (
            "<div class='delta-callout'>"
            "<span class='delta-lbl'>Total Loss / Damage Owed</span>"
            f"<span class='delta-amt'>{_money(grand_damage)}</span>"
            "</div>"
        )
    return f"<section><h3>Equipment Returned</h3>{delta_callout}{table}</section>"


EQUIPMENT_RETURN_ACK_EN = (
    "I acknowledge that the equipment listed above has been returned to "
    "MASCI General Contractors in the condition documented on this form, "
    "with photographs and notes attached as evidence.\n\n"
    "I understand that any equipment listed as DAMAGED, MISSING, or LOST "
    "may result in financial responsibility for repair or replacement "
    "costs, only to the extent permitted by applicable federal law, "
    "Florida law, and company policy. Any payroll deduction or "
    "reimbursement will be handled only where legally permitted and "
    "with any required authorization.\n\n"
    "My signature confirms the return condition recorded above is "
    "accurate to the best of my knowledge."
)

EQUIPMENT_RETURN_ACK_ES = (
    "Reconozco que el equipo enumerado arriba ha sido devuelto a "
    "MASCI General Contractors en la condición documentada en este "
    "formulario, con fotografías y notas adjuntas como evidencia.\n\n"
    "Entiendo que cualquier equipo registrado como DAÑADO, FALTANTE o "
    "PERDIDO puede generar responsabilidad económica por costos de "
    "reparación o reemplazo, únicamente en la medida permitida por la "
    "ley federal aplicable, la ley de Florida y la política de la "
    "empresa. Cualquier deducción de nómina o reembolso se realizará "
    "solo donde sea legalmente permitido y con cualquier autorización "
    "requerida.\n\n"
    "Mi firma confirma que la condición de devolución registrada arriba "
    "es precisa al mejor de mi conocimiento."
)


def _equipment_return_ack_block(language: str) -> str:
    text = EQUIPMENT_RETURN_ACK_ES if language == "es" else EQUIPMENT_RETURN_ACK_EN
    paragraphs = "".join(f"<p>{_h(p)}</p>" for p in text.split("\n\n"))
    return (
        "<section class='ack-section'><h3>Equipment Return Acknowledgement</h3>"
        f"<div class='ack-box'>{paragraphs}</div></section>"
    )


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

    # Equipment Checkout uses a custom line-items table + acknowledgement
    # in place of the generic _details_block. Equipment Return uses a
    # similar but distinct table with return condition, return photos, and
    # a damage delta column.
    if kind == "equipment_checkout":
        equipment_lines_for_pdf = details_for_pdf.get("equipment_lines") or []
        body_blocks = (
            _equipment_lines_block(details_for_pdf)
            + _equipment_lines_photos_block(
                equipment_lines_for_pdf,
                photo_field="photos",
                heading="Equipment Photos by Item",
            )
            + _photos_block(rec.get("photos") or [])
            + _equipment_ack_block(rec.get("language") or "en")
            + _signatures_block(rec)
        )
    elif kind == "equipment_return":
        equipment_lines_for_pdf = details_for_pdf.get("equipment_lines") or []
        body_blocks = (
            _equipment_return_block(details_for_pdf)
            + _equipment_lines_photos_block(
                equipment_lines_for_pdf,
                photo_field="original_photos",
                heading="Original Checkout Photos (for comparison)",
            )
            + _equipment_lines_photos_block(
                equipment_lines_for_pdf,
                photo_field="return_photos",
                heading="Return Condition Photos by Item",
            )
            + _photos_block(rec.get("photos") or [])
            + _equipment_return_ack_block(rec.get("language") or "en")
            + _signatures_block(rec)
        )
    else:
        body_blocks = (
            _details_block(details_for_pdf)
            + _photos_block(rec.get("photos") or [])
            + _signatures_block(rec)
        )

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
.line-photos {{ margin:10pt 0 14pt; padding:8pt 10pt; background:#f8fafc; border-left:3px solid #b91c1c; border-radius:3pt; page-break-inside: avoid; }}
.line-photos-caption {{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6pt; gap:10pt; flex-wrap:wrap; }}
.line-photos-num {{ font-family: ui-monospace, monospace; font-size:8.5pt; font-weight:700; color:#b91c1c; letter-spacing:.18em; text-transform:uppercase; }}
.line-photos-meta {{ font-size:9pt; color:#475569; font-weight:600; }}
.line-photos .photos img {{ width:31%; max-height:200pt; }}
.sigs {{ display:flex; gap:14pt; flex-wrap:wrap; margin-top:8pt; }}
.sig-card {{ flex:1; min-width:180pt; border:1px solid #cbd5e1; border-radius:4pt; padding:10pt; background:#fff; }}
.sig-card.refused {{ background:#fef2f2; border-color:#fca5a5; }}
.sig-label {{ font-family: ui-monospace, monospace; font-size:8pt; letter-spacing:.18em; text-transform:uppercase; color:#475569; margin-bottom:6pt; }}
.sig-card img {{ max-height:60pt; max-width:100%; }}
.sig-name {{ margin-top:4pt; font-weight:600; font-size:9pt; }}
.ack {{ font-size:8pt; color:#475569; font-style:italic; margin:0 0 8pt; }}
table.lines {{ width:100%; border-collapse:collapse; font-size:9pt; margin-top:6pt; }}
table.lines th, table.lines td {{ border:1px solid #cbd5e1; padding:5pt 6pt; text-align:left; vertical-align:top; }}
table.lines th {{ background:#f1f5f9; font-family: ui-monospace, monospace; font-size:8pt; letter-spacing:.1em; text-transform:uppercase; color:#475569; }}
table.lines td.num, table.lines th.num {{ text-align:right; font-variant-numeric: tabular-nums; }}
table.lines tfoot td {{ background:#fef3c7; border-top:2px solid #b45309; padding:7pt; }}
table.lines tfoot td.grand {{ font-size:11pt; font-weight:900; color:#0f172a; }}
table.lines tfoot td.grand-label {{ text-align:right; font-family: ui-monospace, monospace; letter-spacing:.12em; text-transform:uppercase; font-weight:700; color:#92400e; }}
table.lines tr.notes-row td {{ background:#f8fafc; font-size:8.5pt; color:#475569; padding:3pt 6pt 5pt 6pt; }}
table.lines tr.notes-row .notes-lbl {{ font-family: ui-monospace, monospace; font-size:7.5pt; letter-spacing:.12em; text-transform:uppercase; color:#94a3b8; margin-right:4pt; }}
.ack-section .ack-box {{ background:#f8fafc; border:1px solid #cbd5e1; border-left:3px solid #b91c1c; padding:10pt 12pt; font-size:9pt; line-height:1.55; }}
.ack-section .ack-box p {{ margin:0 0 6pt 0; }}
.ack-section .ack-box p:last-child {{ margin:0; }}
table.lines td.damage {{ color:#b91c1c; font-weight:700; }}
table.lines td.ret-good {{ color:#15803d; font-weight:700; }}
table.lines td.ret-bad {{ color:#b91c1c; font-weight:700; }}
table.lines td.ret-neutral {{ color:#92400e; font-weight:700; }}
.delta-callout {{ display:flex; justify-content:space-between; align-items:center; background:#fef2f2; border:2px solid #b91c1c; border-radius:4px; padding:8pt 12pt; margin:6pt 0 8pt; }}
.delta-callout .delta-lbl {{ font-family: ui-monospace, monospace; font-size:8pt; letter-spacing:.15em; text-transform:uppercase; color:#b91c1c; font-weight:700; }}
.delta-callout .delta-amt {{ font-size:14pt; font-weight:900; color:#b91c1c; font-variant-numeric: tabular-nums; }}
</style></head><body>
  <div class='header'>
    <div>
      <div class='brand'>MASCI HUB · Field Leadership</div>
      <div class='title'>{_h(title)}</div>
      <div class='kicker'>{_h(rec.get('project_number') or '')} · {_h(rec.get('project_name') or '')}</div>
    </div>
    <div style='text-align:right;font-size:9pt;color:#64748b'>
      <div style='font-family:ui-monospace,monospace;font-size:11pt;font-weight:800;color:#b91c1c;letter-spacing:.05em;margin-bottom:2pt'>{_h(rec.get('doc_id') or '')}</div>
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

  {body_blocks}

</body></html>"""

    return HTML(string=doc_html).write_pdf()
