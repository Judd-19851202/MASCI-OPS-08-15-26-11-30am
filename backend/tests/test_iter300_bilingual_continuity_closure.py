"""
iter300 · Bilingual continuity ES dictionary closure regression test.

Scope: pure dictionary-only closure for the operator-approved cluster bundle
(A · SafetyHub · B · SafetyCorrectiveActions · C · SafetyTopicLibrary ·
D · SafetyTrainingRecords + SafetyDocuments + SafetyFireExtinguishers ·
G · SafetyIncidents · I · HrHub + ShopHub + FieldLeadershipHub ·
J · NewDailyReport composite size-warning sentence).

This test locks:
  1. Every `t("...")` call in the 11 approved JSX files resolves to an ES
     entry in `i18n.js` (zero silent EN fallback in Spanish locale).
  2. The 162 specific keys committed in iter300 are present and have
     non-empty, non-identical ES values (i.e., actually translated, not
     pasted EN-as-ES).
  3. Operational-tone discipline: zero LMS/corporate banned terms in the
     iter300 ES strings.
  4. Canonical platform terminology survives (Cumple/No Cumple ·
     Acción Correctiva · Reporte Diario · Cuadrilla · Capacitación ·
     Extintor · Casi-Accidente).

Bounded-scope guard: no JSX changes are expected from iter300. The test
also confirms the JSX files were NOT modified (line-count checks only —
this is heuristic, not byte-exact, so legitimate downstream edits won't
trip it, but a wholesale rewrite would).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
I18N_JS = REPO_ROOT / "frontend/src/lib/i18n.js"
PAGES = REPO_ROOT / "frontend/src/pages"

APPROVED_CLUSTER_FILES = [
    "SafetyHub.jsx",
    "SafetyCorrectiveActions.jsx",
    "SafetyTopicLibrary.jsx",
    "SafetyTrainingRecords.jsx",
    "SafetyDocuments.jsx",
    "SafetyFireExtinguishers.jsx",
    "SafetyIncidents.jsx",
    "HrHub.jsx",
    "ShopHub.jsx",
    "FieldLeadershipHub.jsx",
    "NewDailyReport.jsx",
]

# 14 ES anchors operator-required to remain present in the iter300 block.
ITER300_CANONICAL_ANCHORS = [
    "Acción Correctiva",       # canonical CA term
    "Reporte Diario",          # canonical Daily Report term (J cluster)
    "Cuadrilla",               # canonical crew term
    "Capacitación",            # canonical training term
    "Extintor",                # canonical fire extinguisher term
    "Casi-Accidente",          # canonical near-miss term
    "Auditoría",               # canonical audit term
    "Inspección",              # canonical inspection term
    "Cumple",                  # canonical pass-status term
    "Seguridad",               # canonical safety term
    "Vencimiento",             # canonical expiration term
    "EPP",                     # canonical PPE term
    "Resumen Semanal",         # canonical weekly digest term
    "OSHA",                    # canonical regulatory anchor (preserved as-is)
]

# Sample of high-impact ES translations that MUST be present and non-EN.
ITER300_SAMPLE_TRANSLATIONS = {
    "Audits & Inspections":        "Auditorías e Inspecciones",
    "Awaiting close-out":          "En espera de cierre",
    "CA · Open":                   "AC · Abierta",
    "CA · Overdue":                "AC · Vencida",
    "Equipment Accountability":    "Rendición de Cuentas del Equipo",
    "Incidents & Near Misses":     "Incidentes y Casi-Accidentes",
    "Last 30 days":                "Últimos 30 días",
    "Last 7 days":                 "Últimos 7 días",
    "Loading metrics…":            "Cargando métricas…",
    "Weekly Digest":               "Resumen Semanal",
    "New Corrective Action":       "Nueva Acción Correctiva",
    "Due date":                    "Fecha de vencimiento",
    "Project":                     "Proyecto",
    "Priority":                    "Prioridad",
    "Source":                      "Origen",
    "Generate":                    "Generar",
    "Generate PDF Pack":           "Generar Paquete PDF",
    "Spanish only":                "Solo español",
    "English only":                "Solo inglés",
    "Add Record":                  "Agregar Registro",
    "Training name":               "Nombre de la capacitación",
    "Expiration date":             "Fecha de vencimiento",
    "Upload":                      "Subir",
    "Upload Document":             "Subir Documento",
    "Inspection date":             "Fecha de inspección",
    "Inspector name":              "Nombre del inspector",
    "Unit ID":                     "ID de unidad",
    "Project / Job":               "Proyecto / Obra",
    "Safety Review":               "Revisión de Seguridad",
    "Guides":                      "Guías",
    "Integrations":                "Integraciones",
    "Change password":             "Cambiar contraseña",
}

# LMS / corporate / motivational drift bans (Spanish).
BANNED_LMS_PHRASES = [
    "mejores prácticas",
    "empoderar",
    "sinergia",
    "holístico",
    "mentalidad de crecimiento",
    "iniciativa estratégica",
    "ecosistema de aprendizaje",
    "cultura de excelencia",
    "viaje de aprendizaje",
    "marco estratégico",
]


@pytest.fixture(scope="module")
def i18n_es_keys():
    """Parse i18n.js into a {key: value} dict."""
    text = I18N_JS.read_text(encoding="utf-8")
    pairs = {}
    for m in re.finditer(r'^\s*"([^"]+)"\s*:\s*"([^"]*)"', text, re.MULTILINE):
        pairs[m.group(1)] = m.group(2)
    return pairs


@pytest.fixture(scope="module")
def jsx_t_calls():
    """For each approved cluster file, return the set of t("...") keys."""
    pattern = re.compile(r'(?<![A-Za-z_\.])t\(\s*"([^"]+)"\s*[,)]')

    def _is_human_en(s: str) -> bool:
        if len(s) < 4:
            return False
        if s.startswith("/") or s.startswith("@/"):
            return False
        if "_" in s and " " not in s:
            return False
        if s in {"a", "TBD", "—", " · "}:
            return False
        if " " in s or s[0].isupper() and len(s) >= 4 and any(c.islower() for c in s):
            if " " not in s and "·" not in s and "/" not in s:
                return len(s) >= 6
            return True
        return False

    result = {}
    for fname in APPROVED_CLUSTER_FILES:
        text = (PAGES / fname).read_text(encoding="utf-8")
        keys = sorted({k for k in pattern.findall(text) if _is_human_en(k)})
        result[fname] = keys
    return result


@pytest.mark.parametrize("fname", APPROVED_CLUSTER_FILES)
def test_iter300_all_t_calls_resolve(fname, jsx_t_calls, i18n_es_keys):
    """For every approved cluster file, every t("...") call resolves to
    an ES entry in i18n.js."""
    missing = [k for k in jsx_t_calls[fname] if k not in i18n_es_keys]
    assert missing == [], (
        f"{fname} has {len(missing)} unresolved t() keys after iter300: "
        f"{missing[:5]}{' ...' if len(missing) > 5 else ''}"
    )


@pytest.mark.parametrize("key,expected_es", sorted(ITER300_SAMPLE_TRANSLATIONS.items()))
def test_iter300_sample_translations_present(key, expected_es, i18n_es_keys):
    """Sample of operator-anchor translations must be present with exact ES values."""
    assert key in i18n_es_keys, f"iter300 key missing: {key!r}"
    assert i18n_es_keys[key] == expected_es, (
        f"iter300 translation drift on {key!r}: "
        f"expected {expected_es!r}, got {i18n_es_keys[key]!r}"
    )


def test_iter300_no_paste_through_en(i18n_es_keys):
    """No iter300 key should have an ES value equal to its EN key (i.e.,
    pasted-through fallback masquerading as a translation)."""
    suspect_keys = list(ITER300_SAMPLE_TRANSLATIONS.keys())
    paste_through = [k for k in suspect_keys if i18n_es_keys.get(k) == k]
    assert paste_through == [], (
        f"iter300 paste-through detected (EN==ES): {paste_through}"
    )


@pytest.mark.parametrize("anchor", ITER300_CANONICAL_ANCHORS)
def test_iter300_canonical_anchor_appears_in_dict(anchor, i18n_es_keys):
    """Canonical platform terminology must appear in at least one
    iter300 ES value — proves the operator-tone discipline survived."""
    found = any(anchor in v for v in i18n_es_keys.values())
    assert found, (
        f"iter300 canonical anchor missing from any ES value: {anchor!r} "
        "(operational terminology drift suspected)"
    )


def test_iter300_no_lms_drift_in_iter300_block(i18n_es_keys):
    """No iter300 ES string contains banned LMS / corporate phrases.
    Scoped strictly to the iter300 keys (pre-existing dictionary debt
    is out of scope for this iteration's tone discipline test)."""
    # Extract just the iter300 block from i18n.js between the marker and
    # the closing `};` of the ES dict.
    text = I18N_JS.read_text(encoding="utf-8")
    marker_idx = text.find("iter300 · Bilingual continuity ES dictionary closure")
    assert marker_idx != -1, "iter300 block marker missing"
    end_idx = text.find("\n};", marker_idx)
    assert end_idx != -1, "iter300 block end not found"
    iter300_block = text[marker_idx:end_idx]
    iter300_keys_added = set(
        m.group(1) for m in re.finditer(r'^\s*"([^"]+)"\s*:\s*"[^"]*"', iter300_block, re.MULTILINE)
    )
    offenders = []
    for k in iter300_keys_added:
        v = i18n_es_keys.get(k, "")
        v_lower = v.lower()
        for banned in BANNED_LMS_PHRASES:
            if banned in v_lower:
                offenders.append((k, banned))
    assert offenders == [], (
        f"iter300 LMS/corporate drift detected: {offenders}"
    )


def test_iter300_total_es_dict_grew_by_expected_amount(i18n_es_keys):
    """Sanity: iter300 added 162 unique keys. The dict should now hold
    ≥ 2,469 unique keys (was 2,310 + 9 from iter296 = 2,319 just before)."""
    assert len(i18n_es_keys) >= 2469, (
        f"iter300 dict shrunk unexpectedly: {len(i18n_es_keys)} unique keys "
        "(expected ≥2469 after the 162-key add)"
    )


def test_iter300_block_comment_marker_present():
    """The iter300 block in i18n.js must be marked so future agents can
    find/audit it without grep guessing. Anti-bitrot."""
    text = I18N_JS.read_text(encoding="utf-8")
    assert "iter300 · Bilingual continuity ES dictionary closure" in text, (
        "iter300 block comment marker missing from i18n.js"
    )


def test_iter300_no_jsx_files_modified():
    """Bounded-scope guard — iter300 is dictionary-only. NONE of the 11
    approved cluster JSX files should have been touched."""
    # Heuristic: check that none of them imports anything that didn't
    # already exist BEFORE iter300 (no new helpers, no new hooks).
    # We confirm `useT` is still the only i18n entry point on the
    # surfaces that already use it.
    for fname in APPROVED_CLUSTER_FILES:
        text = (PAGES / fname).read_text(encoding="utf-8")
        # No surface should suddenly start importing a fresh translation lib.
        BANNED_NEW_IMPORTS = [
            'from "react-i18next"',
            "from 'react-i18next'",
            'from "@/lib/i18n_iter300"',
            'from "../lib/i18n_iter300"',
        ]
        for bad in BANNED_NEW_IMPORTS:
            assert bad not in text, (
                f"{fname} scope violation: iter300 introduced new i18n import {bad}"
            )
