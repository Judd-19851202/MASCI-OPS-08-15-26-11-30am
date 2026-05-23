"""
lib/cdl_importer.py — iter352

Shared CDL / Approved Driver roster importer.

Two responsibilities:
  1. Parse incoming XLSX / CSV bytes into normalized driver rows.
  2. Match rows to existing `employees` documents using the seven-tier
     resolver from iter351's one-shot script.

Used by:
  - /api/hr/driver-qualification/import/preview  (no writes)
  - /api/hr/driver-qualification/import/apply    (writes + audit)

Design rules:
  * NEVER invents data. Empty source cells stay empty.
  * NEVER creates employees silently — unmatched rows are reported
    and only created when the caller explicitly opts in.
  * NEVER overwrites unrelated employee fields. PATCH payload is
    built ONLY from columns that were actually present in the source.
  * Pure functions where possible (matcher is a free function the
    routes layer composes into request handlers).
"""
from __future__ import annotations

import csv
import io
import re
from typing import Any, Dict, List, Optional, Tuple

import openpyxl


_WS = re.compile(r"\s+")

# Headers we recognize. Any other column in the source file is
# IGNORED (operator may include freeform notes columns).
HEADER_ALIASES: Dict[str, List[str]] = {
    "name":                          ["name", "full name", "employee name", "driver", "driver name"],
    "employee_id":                   ["employee_id", "employee id", "emp id", "emp_id"],
    "email":                         ["email", "email address"],
    "approved_company_driver":       ["approved_company_driver", "approved company driver", "approved", "insurance approved", "on insurance"],
    "cdl_holder":                    ["cdl_holder", "cdl holder", "cdl", "has cdl"],
    "cdl_license_number":            ["cdl_license_number", "cdl license number", "cdl license #", "cdl license", "license number", "license #"],
    "cdl_state":                     ["cdl_state", "cdl state", "license state", "state"],
    "cdl_expiration_date":           ["cdl_expiration_date", "cdl expiration", "cdl exp", "cdl expiration date", "license expiration"],
    "medical_card_expiration_date":  ["medical_card_expiration_date", "medical card expiration", "med card exp", "medical card exp", "medical expiration", "med card expiration date"],
    "cdl_endorsements":              ["cdl_endorsements", "endorsements", "endorsement"],
    "cdl_restrictions":              ["cdl_restrictions", "restrictions", "restriction"],
    "driver_status":                 ["driver_status", "driver status", "status"],
}

# Boolean-like values we accept in approved/cdl_holder cells.
_TRUE = {"y", "yes", "true", "t", "1", "x", "cdl", "approved", "active"}
_FALSE = {"n", "no", "false", "f", "0", "", "none", "inactive"}

# CDL endorsements taxonomy — used to canonicalise the endorsements
# column. Same set the dashboard filter uses.
_ENDORSEMENT_MAP = {
    "n": "N", "tanker": "N",
    "h": "H", "hazmat": "H",
    "x": "X", "tanker+hazmat": "X", "tanker + hazmat": "X",
    "t": "T", "doubles": "T", "doubles/triples": "T", "triples": "T",
    "p": "P", "passenger": "P",
    "s": "S", "school bus": "S", "schoolbus": "S",
}


def normalize_name(name: Optional[str]) -> str:
    if not name or not isinstance(name, str):
        return ""
    return _WS.sub(" ", name.strip()).lower()


def _norm_header(h: Any) -> str:
    if h is None:
        return ""
    return _WS.sub(" ", str(h).strip().lower())


def _resolve_header_index(header_row: List[Any]) -> Dict[str, int]:
    """Return {canonical_field: column_index}. Headers not recognized
    are ignored. Duplicate-column wins go to the FIRST occurrence."""
    canon: Dict[str, int] = {}
    normalized = [_norm_header(h) for h in header_row]
    for canonical, aliases in HEADER_ALIASES.items():
        for col_idx, header_text in enumerate(normalized):
            if header_text in aliases and canonical not in canon:
                canon[canonical] = col_idx
                break
    return canon


def _parse_bool(v: Any) -> Optional[bool]:
    """Parse a boolean-like cell. Returns None if cell is empty/unknown
    so the caller can choose to leave the field untouched."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v != 0
    s = str(v).strip().lower()
    if s in _TRUE:
        return True
    if s in _FALSE:
        return None if s == "" else False
    return None


def _parse_date(v: Any) -> Optional[str]:
    """Return ISO-8601 'YYYY-MM-DD' string or None. Accepts excel
    datetime cells, strings in common US formats, and plain ISO."""
    if v is None or v == "":
        return None
    # Excel cell already arrives as a datetime/date when data_only=True
    if hasattr(v, "isoformat"):
        try:
            iso = v.isoformat()
            return iso[:10]
        except Exception:  # noqa: BLE001
            return None
    s = str(v).strip()
    if not s:
        return None
    # ISO already (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # US formats: M/D/YYYY, MM/DD/YYYY, M-D-YYYY
    m = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})$", s)
    if m:
        mo, dy, yr = m.group(1), m.group(2), m.group(3)
        if len(yr) == 2:
            yr = "20" + yr
        return f"{int(yr):04d}-{int(mo):02d}-{int(dy):02d}"
    return None


def _parse_list(v: Any) -> Optional[List[str]]:
    """Parse a comma/pipe/space-separated list of endorsement or
    restriction codes. Returns None for empty cells (leave field
    untouched) and a [] for explicit '-' or 'none' markers."""
    if v is None or v == "":
        return None
    if isinstance(v, list):
        out = [str(x).strip().upper() for x in v if str(x).strip()]
        return out
    s = str(v).strip()
    if not s or s.lower() in ("none", "n/a", "-", "—"):
        return []
    tokens = re.split(r"[,;|/\s]+", s)
    out: List[str] = []
    for tok in tokens:
        t = tok.strip().lower()
        if not t:
            continue
        if t in _ENDORSEMENT_MAP:
            out.append(_ENDORSEMENT_MAP[t])
        else:
            out.append(tok.strip().upper())
    # de-dup preserve order
    seen = set()
    deduped = []
    for x in out:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    return deduped


def _parse_status(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    s = str(v).strip().lower()
    if s in ("active", "restricted", "suspended", "inactive"):
        return s
    return None


# ─────────────────────────────────────────────────────────────────────
# PUBLIC · file → normalized rows
# ─────────────────────────────────────────────────────────────────────
def parse_xlsx(data: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse an XLSX file. Returns (rows, source_columns).
    `source_columns` lists the canonical fields actually present in
    the file — the caller uses this to know which fields to write."""
    bio = io.BytesIO(data)
    wb = openpyxl.load_workbook(bio, data_only=True, read_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    try:
        header = next(rows_iter)
    except StopIteration:
        return [], []
    canon = _resolve_header_index(list(header))
    if "name" not in canon:
        raise ValueError("Required column 'name' not found in uploaded file")
    rows: List[Dict[str, Any]] = []
    for raw in rows_iter:
        row = _build_row(raw, canon)
        if row:
            rows.append(row)
    return rows, list(canon.keys())


def parse_csv(data: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse a CSV file. Returns (rows, source_columns)."""
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return [], []
    canon = _resolve_header_index(list(header))
    if "name" not in canon:
        raise ValueError("Required column 'name' not found in uploaded file")
    rows: List[Dict[str, Any]] = []
    for raw in reader:
        row = _build_row(raw, canon)
        if row:
            rows.append(row)
    return rows, list(canon.keys())


def _build_row(raw: Any, canon: Dict[str, int]) -> Optional[Dict[str, Any]]:
    """Turn one source-file row into a normalized internal row dict.
    Returns None for blank rows (no name cell)."""
    if raw is None:
        return None
    name_idx = canon.get("name")
    if name_idx is None or name_idx >= len(raw):
        return None
    raw_name = raw[name_idx]
    if raw_name is None or str(raw_name).strip() == "":
        return None
    row: Dict[str, Any] = {"raw_name": str(raw_name).strip()}

    def get(field):
        idx = canon.get(field)
        if idx is None or idx >= len(raw):
            return None
        return raw[idx]

    # Identity fallbacks
    if "employee_id" in canon:
        eid = get("employee_id")
        row["employee_id"] = str(eid).strip() if eid not in (None, "") else None
    if "email" in canon:
        em = get("email")
        row["email"] = str(em).strip().lower() if em not in (None, "") else None

    # Driver fields — only include keys whose column is present in the
    # source. _parse_* returns None when blank → caller decides.
    if "approved_company_driver" in canon:
        row["approved_company_driver"] = _parse_bool(get("approved_company_driver"))
    if "cdl_holder" in canon:
        row["cdl_holder"] = _parse_bool(get("cdl_holder"))
    if "cdl_license_number" in canon:
        v = get("cdl_license_number")
        row["cdl_license_number"] = str(v).strip() if v not in (None, "") else None
    if "cdl_state" in canon:
        v = get("cdl_state")
        row["cdl_state"] = str(v).strip().upper()[:2] if v not in (None, "") else None
    if "cdl_expiration_date" in canon:
        row["cdl_expiration_date"] = _parse_date(get("cdl_expiration_date"))
    if "medical_card_expiration_date" in canon:
        row["medical_card_expiration_date"] = _parse_date(get("medical_card_expiration_date"))
    if "cdl_endorsements" in canon:
        row["cdl_endorsements"] = _parse_list(get("cdl_endorsements"))
    if "cdl_restrictions" in canon:
        row["cdl_restrictions"] = _parse_list(get("cdl_restrictions"))
    if "driver_status" in canon:
        row["driver_status"] = _parse_status(get("driver_status"))

    return row


# ─────────────────────────────────────────────────────────────────────
# PUBLIC · seven-tier employee matcher (lifted from iter351 script)
# ─────────────────────────────────────────────────────────────────────
def _strip_suffix_middle(name: str) -> str:
    n = normalize_name(name)
    if not n:
        return n
    tokens = n.split(" ")
    out = []
    suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}
    for i, tok in enumerate(tokens):
        if tok in suffixes:
            continue
        if 0 < i < len(tokens) - 1 and len(tok.replace(".", "")) <= 2:
            continue
        out.append(tok)
    return " ".join(out)


def _is_one_char_typo(a: str, b: str) -> bool:
    if not a or not b or a == b:
        return False
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        diff = sum(1 for x, y in zip(a, b) if x != y)
        if diff == 1:
            return True
        if diff == 2:
            for i in range(len(a) - 1):
                if a[i] == b[i + 1] and a[i + 1] == b[i] and a[:i] == b[:i] and a[i + 2:] == b[i + 2:]:
                    return True
        return False
    long, short = (a, b) if len(a) > len(b) else (b, a)
    for i in range(len(long)):
        if long[:i] + long[i + 1:] == short:
            return True
    return False


def build_indexes(employees: List[Dict[str, Any]]):
    by_id: Dict[str, Dict[str, Any]] = {}
    by_emp_code: Dict[str, Dict[str, Any]] = {}
    by_norm: Dict[str, List[Dict[str, Any]]] = {}
    by_lfi: Dict[str, List[Dict[str, Any]]] = {}
    by_email: Dict[str, Dict[str, Any]] = {}
    for e in employees:
        eid = (e.get("id") or "").strip()
        if eid:
            by_id[eid] = e
        code = (e.get("employee_id") or "").strip()
        if code:
            by_emp_code[code] = e
        em = (e.get("email") or "").strip().lower()
        if em:
            by_email[em] = e
        n = normalize_name(e.get("name"))
        if n:
            by_norm.setdefault(n, []).append(e)
            parts = n.split(" ")
            if len(parts) >= 2:
                by_lfi.setdefault(f"{parts[-1]}|{parts[0][:1]}", []).append(e)
    return {
        "by_id": by_id, "by_emp_code": by_emp_code,
        "by_norm": by_norm, "by_lfi": by_lfi,
        "by_email": by_email, "all": employees,
    }


def match_row(row: Dict[str, Any], idx) -> Tuple[Optional[Dict[str, Any]], str, str]:
    """Returns (matched_employee, method, confidence).
    confidence ∈ {'high', 'medium', 'low', 'none'}."""
    # ── Tier 0 · explicit identity ───────────────────────────────────
    eid = (row.get("employee_id") or "").strip()
    if eid and eid in idx["by_id"]:
        return idx["by_id"][eid], "employee_id", "high"
    if eid and eid in idx["by_emp_code"]:
        return idx["by_emp_code"][eid], "employee_code", "high"
    em = (row.get("email") or "").strip().lower()
    if em and em in idx["by_email"]:
        return idx["by_email"][em], "email", "high"

    n = normalize_name(row.get("raw_name"))
    # ── Tier 1 · exact normalized name ───────────────────────────────
    if n in idx["by_norm"]:
        matches = idx["by_norm"][n]
        if len(matches) == 1:
            return matches[0], "name_exact", "high"
        # ambiguous — caller flags this as duplicate-risk
        return matches[0], f"name_exact_ambiguous({len(matches)})", "low"
    parts = n.split(" ")
    # ── Tier 2 · last + first-initial ────────────────────────────────
    if len(parts) >= 2:
        key = f"{parts[-1]}|{parts[0][:1]}"
        if key in idx["by_lfi"]:
            cands = idx["by_lfi"][key]
            if len(cands) == 1:
                return cands[0], "last_first_initial", "high"
            tight = [m for m in cands if normalize_name(m.get("name")).split(" ")[0].startswith(parts[0][:3])]
            if len(tight) == 1:
                return tight[0], "last_first_three", "medium"
    # ── Tier 3 · suffix / middle-initial stripped ────────────────────
    src_stripped = _strip_suffix_middle(row.get("raw_name") or "")
    if src_stripped:
        for e in idx["all"]:
            if _strip_suffix_middle(e.get("name") or "") == src_stripped:
                return e, "stripped_suffix_middle", "medium"
    # ── Tier 4 · source-name is prefix of roster ─────────────────────
    for e in idx["all"]:
        en = normalize_name(e.get("name"))
        if en.startswith(n + " ") or en.startswith(n + "-"):
            return e, "prefix_of_roster", "medium"
        if parts and len(parts) >= 2:
            eparts = en.split(" ")
            if eparts and eparts[0] == parts[0]:
                last_tokens = eparts[-1].replace("-", " ").split()
                if parts[-1] in last_tokens:
                    return e, "first_name_hyphen_last", "medium"
    # ── Tier 5 · single-char typo (incl. transposition) ──────────────
    if parts and len(parts) >= 2:
        src_last, src_first = parts[-1], parts[0]
        for e in idx["all"]:
            en = normalize_name(e.get("name"))
            eparts = en.split(" ")
            if not eparts or len(eparts) < 2:
                continue
            if eparts[0] == src_first and _is_one_char_typo(src_last, eparts[-1]):
                return e, "typo_last_name", "low"
            if eparts[-1] == src_last and _is_one_char_typo(src_first, eparts[0]):
                return e, "typo_first_name", "low"
    return None, "unmatched", "none"


# ─────────────────────────────────────────────────────────────────────
# PUBLIC · diff builder
# ─────────────────────────────────────────────────────────────────────
DRIVER_FIELDS = (
    "approved_company_driver", "cdl_holder",
    "cdl_license_number", "cdl_state",
    "cdl_expiration_date", "medical_card_expiration_date",
    "cdl_endorsements", "cdl_restrictions",
    "driver_status",
)


def build_payload(row: Dict[str, Any], employee: Dict[str, Any], source_columns: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Build the PATCH payload + before/after diff for one row.
    Only includes a field if (a) the source file had that column and
    (b) the new value differs from the existing employee value.
    Returns ({field: new_value, ...}, {field: {'before': x, 'after': y}, ...}).
    Empty list (`[]`) is treated as a meaningful clear for endorsements/restrictions
    only when source value differs from existing. None values are
    SKIPPED — never overwrite a populated field with a blank cell."""
    payload: Dict[str, Any] = {}
    diff: Dict[str, Any] = {}
    for f in DRIVER_FIELDS:
        if f not in source_columns:
            continue  # column not in source — never touch
        new_v = row.get(f)
        if new_v is None:
            continue  # blank cell — preserve existing value
        old_v = employee.get(f)
        # Normalize list comparison
        if isinstance(new_v, list) and isinstance(old_v, list):
            if sorted(new_v) == sorted(old_v):
                continue
        elif new_v == old_v:
            continue
        payload[f] = new_v
        diff[f] = {"before": old_v, "after": new_v}
    return payload, diff


__all__ = [
    "HEADER_ALIASES",
    "DRIVER_FIELDS",
    "normalize_name",
    "parse_xlsx",
    "parse_csv",
    "build_indexes",
    "match_row",
    "build_payload",
]
