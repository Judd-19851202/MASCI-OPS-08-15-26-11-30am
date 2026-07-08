"""TRACK 24.13 · Material ticket normalization + reconciliation.

Turns diverse ticket inputs (supervisor rows · extracted CSV/XLSX rows
· PDF text · photo captions) into a single :class:`NormalizedTicket`
shape, then reconciles what the supervisor typed against what the
attachments actually contain.

Reconciliation is **advisory only** — we never overwrite supervisor
data. The output is fed into the AI summary and the PDF material
evidence block so the PM sees whether uploaded evidence matches the
typed rows.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Normalized ticket shape ─────────────────────────────────────────

@dataclass
class NormalizedTicket:
    ticket_number: str = ""
    supplier: str = ""
    material: str = ""
    quantity: Optional[float] = None
    unit: str = ""
    truck: str = ""
    date: str = ""
    direction: str = ""       # "inbound" | "outbound" | ""
    project: str = ""
    notes: str = ""
    source: str = ""          # "entered" | "xlsx" | "csv" | "pdf_text" | "caption"
    confidence: float = 0.5
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Header canonicalization ─────────────────────────────────────────

_HEADER_MAP: Dict[str, str] = {
    # ticket_number
    "ticket": "ticket_number", "ticket_number": "ticket_number",
    "ticket_no": "ticket_number", "ticket#": "ticket_number",
    "load_ticket": "ticket_number",
    # supplier
    "supplier": "supplier", "vendor": "supplier",
    "from": "supplier", "source": "supplier", "origin": "supplier",
    # material
    "material": "material", "product": "material",
    "commodity": "material", "type": "material", "description": "material",
    # quantity
    "qty": "quantity", "quantity": "quantity", "tons": "quantity",
    "cy": "quantity", "cu_yd": "quantity", "cubic_yards": "quantity",
    "loads": "quantity", "count": "quantity", "each": "quantity",
    "net_tons": "quantity", "net_weight": "quantity",
    # unit
    "unit": "unit", "uom": "unit", "units": "unit",
    # truck
    "truck": "truck", "truck_no": "truck", "hauler": "truck",
    # date
    "date": "date", "delivery_date": "date", "haul_date": "date",
    # direction
    "direction": "direction", "in_out": "direction",
    # project
    "project": "project", "project_no": "project",
    "job": "project", "job_no": "project",
    # notes
    "note": "notes", "notes": "notes", "remarks": "notes",
}


def _normalize_header(h: str) -> str:
    """Fold a spreadsheet/CSV header into a canonical key."""
    k = re.sub(r"[^a-z0-9]+", "_", (h or "").strip().lower()).strip("_")
    return _HEADER_MAP.get(k, "")


def _parse_qty(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # Strip common unit suffixes / comma thousands.
    s = re.sub(r"[a-zA-Z%$]", "", s).replace(",", "").strip()
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


# ── Supervisor row → NormalizedTicket ───────────────────────────────

def normalize_ticket_row(
    row: Dict[str, Any], *, source: str = "entered",
) -> NormalizedTicket:
    """Coerce a dict-shape ticket (either a supervisor row or an
    extracted CSV/XLSX record) into :class:`NormalizedTicket`."""
    t = NormalizedTicket(source=source)
    # Accept both exact keys (from supervisor entry) and canonical
    # mapped keys (from spreadsheet header normalization).
    for k, v in (row or {}).items():
        canon = k if k in {
            "ticket_number", "supplier", "material", "quantity", "unit",
            "truck", "date", "direction", "project", "notes",
        } else _normalize_header(str(k))
        if not canon:
            continue
        if canon == "quantity":
            t.quantity = _parse_qty(v)
        else:
            setattr(t, canon, str(v or "").strip())
    if source == "entered":
        t.confidence = 0.95
    if source in ("xlsx", "csv"):
        t.confidence = 0.85 if t.ticket_number else 0.65
    if source == "pdf_text":
        t.confidence = 0.6
    if source == "caption":
        t.confidence = 0.4
    if t.direction:
        t.direction = t.direction.lower()
        if t.direction not in ("inbound", "outbound"):
            t.direction = ""
    return t


# ── Header-row row list → tickets ───────────────────────────────────

def tickets_from_rows(
    rows: List[List[str]], *, source: str,
) -> List[NormalizedTicket]:
    """Detect a header row and yield normalized tickets.

    We look for the first row whose cells contain enough canonical
    headers to justify treating the rest of the sheet as tickets. If
    no such header is found we return an empty list (the sheet is not
    a ticket log)."""
    if not rows:
        return []
    header_idx = -1
    header_map: List[str] = []
    for i, row in enumerate(rows[:5]):  # only sniff the first 5 rows
        # Strip a leading `[[SHEET:...]]` marker cell from XLSX extraction.
        cells = list(row)
        if cells and cells[0].startswith("[[SHEET:"):
            cells = cells[1:]
        canon = [_normalize_header(c) for c in cells]
        hits = sum(1 for c in canon if c)
        if hits >= 3:
            header_idx = i
            header_map = canon
            break
    if header_idx < 0:
        return []
    tickets: List[NormalizedTicket] = []
    for row in rows[header_idx + 1:]:
        cells = list(row)
        if cells and cells and cells[0].startswith("[[SHEET:"):
            cells = cells[1:]
        rec: Dict[str, Any] = {}
        for j, cell in enumerate(cells):
            if j >= len(header_map):
                break
            canon = header_map[j]
            if not canon or not cell:
                continue
            rec[canon] = cell
        if not rec:
            continue
        t = normalize_ticket_row(rec, source=source)
        # A row without at least material or ticket_number is noise.
        if not t.material and not t.ticket_number and t.quantity is None:
            continue
        tickets.append(t)
    return tickets


# ── Reconciliation ──────────────────────────────────────────────────

@dataclass
class ReconciliationResult:
    entered: List[NormalizedTicket] = field(default_factory=list)
    extracted: List[NormalizedTicket] = field(default_factory=list)
    matched: List[Dict[str, Any]] = field(default_factory=list)
    unmatched_entered: List[NormalizedTicket] = field(default_factory=list)
    unmatched_extracted: List[NormalizedTicket] = field(default_factory=list)
    quantity_totals: Dict[str, Dict[str, float]] = field(default_factory=dict)
    advisories: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entered": [t.to_dict() for t in self.entered],
            "extracted": [t.to_dict() for t in self.extracted],
            "matched": self.matched,
            "unmatched_entered": [t.to_dict() for t in self.unmatched_entered],
            "unmatched_extracted": [t.to_dict() for t in self.unmatched_extracted],
            "quantity_totals": self.quantity_totals,
            "advisories": self.advisories,
            "confidence": self.confidence,
        }


def _pair_key(t: NormalizedTicket) -> Tuple[str, str]:
    return (
        (t.ticket_number or "").strip().lower(),
        (t.material or "").strip().lower(),
    )


def reconcile_tickets(
    entered: List[NormalizedTicket],
    extracted: List[NormalizedTicket],
) -> ReconciliationResult:
    """Advisory-only reconciliation.

    * Exact ticket_number match wins first.
    * Otherwise fuzzy on (material + quantity) within ±5 %.
    * Everything else surfaces on the ``unmatched_*`` lists.
    """
    result = ReconciliationResult(entered=entered, extracted=extracted)

    # Index extracted by ticket number for O(1) lookups.
    by_ticket: Dict[str, NormalizedTicket] = {}
    for t in extracted:
        if t.ticket_number:
            by_ticket[t.ticket_number.strip().lower()] = t

    consumed_extracted: set = set()

    for e in entered:
        k = (e.ticket_number or "").strip().lower()
        if k and k in by_ticket:
            x = by_ticket[k]
            match = {
                "kind": "ticket_number", "ticket_number": e.ticket_number,
                "entered": e.to_dict(), "extracted": x.to_dict(),
                "delta_quantity": (
                    None if (e.quantity is None or x.quantity is None)
                    else round((x.quantity or 0) - (e.quantity or 0), 3)
                ),
            }
            result.matched.append(match)
            consumed_extracted.add(id(x))
            continue
        # Fuzzy material + quantity
        best: Optional[NormalizedTicket] = None
        best_delta = 1e9
        for x in extracted:
            if id(x) in consumed_extracted:
                continue
            if not e.material or not x.material:
                continue
            if e.material.strip().lower() != x.material.strip().lower():
                continue
            if e.quantity is None or x.quantity is None:
                continue
            base = max(abs(e.quantity), 1e-6)
            delta = abs(e.quantity - x.quantity) / base
            if delta < best_delta and delta <= 0.05:
                best, best_delta = x, delta
        if best is not None:
            result.matched.append({
                "kind": "fuzzy_material_quantity",
                "delta_ratio": round(best_delta, 4),
                "entered": e.to_dict(),
                "extracted": best.to_dict(),
            })
            consumed_extracted.add(id(best))
        else:
            result.unmatched_entered.append(e)

    for x in extracted:
        if id(x) not in consumed_extracted:
            result.unmatched_extracted.append(x)

    # Quantity totals by material.
    totals: Dict[str, Dict[str, float]] = {}
    for t in entered + extracted:
        if not t.material or t.quantity is None:
            continue
        mat = t.material.strip().lower()
        bucket = totals.setdefault(
            mat, {"entered": 0.0, "extracted": 0.0},
        )
        bucket["entered" if t.source == "entered" else "extracted"] += float(t.quantity)
    result.quantity_totals = totals

    # Advisories the AI + PDF may cite verbatim.
    if result.unmatched_extracted:
        result.advisories.append(
            f"{len(result.unmatched_extracted)} extracted ticket(s) do not "
            "match any supervisor-entered row."
        )
    if result.unmatched_entered:
        result.advisories.append(
            f"{len(result.unmatched_entered)} supervisor-entered row(s) "
            "have no matching uploaded ticket evidence."
        )
    for mat, bucket in totals.items():
        e_val, x_val = bucket["entered"], bucket["extracted"]
        if e_val and x_val:
            base = max(abs(e_val), 1e-6)
            delta = abs(e_val - x_val) / base
            if delta > 0.05:
                result.advisories.append(
                    f"Quantity delta on {mat!s}: entered "
                    f"{e_val:g} vs extracted {x_val:g} (~"
                    f"{delta * 100:.1f}% variance)."
                )

    # Overall confidence is the weakest link.
    all_conf = (
        [t.confidence for t in entered]
        + [t.confidence for t in extracted]
    )
    result.confidence = round(min(all_conf), 3) if all_conf else 0.0
    return result


__all__ = [
    "NormalizedTicket",
    "ReconciliationResult",
    "normalize_ticket_row",
    "tickets_from_rows",
    "reconcile_tickets",
]
