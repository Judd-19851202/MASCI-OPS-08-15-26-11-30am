"""Standard Operational Intelligence Product Layout — Track 19.41.

Every implemented Operational Intelligence product renders sections in
this order. Products may mark a section as *not applicable* with a
canonical empty-state row (never ugly N/A spam).

Section keys (locked · pytest-enforced):
  1.  executive_summary
  2.  operational_intelligence_score
  3.  trend_direction
  4.  top_wins
  5.  needs_immediate_attention
  6.  top_5_items
  7.  core_metrics
  8.  trend_table
  9.  recommendations
  10. upcoming_risks
  11. recent_changes
  12. deep_links
  13. no_auto_decision_notice
  14. audit_footer

`build_standard_layout(product_id, ...)` returns a validated
``digest_object`` in the Track 19.40 engine section shape.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


STANDARD_SECTION_ORDER: List[str] = [
    "executive_summary",
    "operational_intelligence_score",
    "trend_direction",
    "top_wins",
    "needs_immediate_attention",
    "top_5_items",
    "core_metrics",
    "trend_table",
    "recommendations",
    "upcoming_risks",
    "recent_changes",
    "deep_links",
    "no_auto_decision_notice",
    "audit_footer",
]

# Optional sections may be marked not-applicable with this canonical
# empty-state row (never blank white space).
EMPTY_STATE_ITEM = "— Not applicable for this product this period. —"


def not_applicable_section(key: str, title: str) -> Dict[str, Any]:
    return {
        "section_key": key,
        "title": title,
        "kind": "list",
        "items": [EMPTY_STATE_ITEM],
    }


def build_standard_layout(
    *,
    product_id: str,
    subject: str,
    period_label: str,
    executive_summary: Dict[str, Any],
    score: Dict[str, Any],
    trend_direction: Dict[str, Any],
    top_wins: List[Any],
    needs_immediate_attention: List[Any],
    top_5_items: Optional[Dict[str, Any]],
    core_metrics: Dict[str, Any],
    trend_table: Optional[Dict[str, Any]] = None,
    recommendations: Optional[List[Any]] = None,
    upcoming_risks: Optional[List[Any]] = None,
    recent_changes: Optional[List[Any]] = None,
    deep_links: Optional[List[Dict[str, str]]] = None,
    no_auto_decision_notice: str = "",
    audit_footer: str = "",
) -> Dict[str, Any]:
    """Compose the canonical 14-section digest object.

    Every implemented Track 19.4x product MUST route through this
    builder. The lock test grep-checks for the presence of the section
    keys 1..14.
    """
    generated_at = datetime.now(timezone.utc).isoformat()
    sections: List[Dict[str, Any]] = [
        {"section_key": "executive_summary", "title": "Executive Summary",
         "kind": "kv", "rows": executive_summary or {}},
        {"section_key": "operational_intelligence_score",
         "title": "Operational Intelligence Score",
         "kind": "kv", "rows": {
             "Overall Score":     score.get("overall_score", 0),
             "Attention Level":   score.get("attention_level", "CRITICAL"),
             "Confidence":        score.get("confidence", "insufficient_data"),
             "Data Freshness":    score.get("data_freshness", "unknown"),
         }},
        {"section_key": "trend_direction", "title": "Trend Direction",
         "kind": "kv", "rows": {
             "Direction":         trend_direction.get("arrow", "→"),
             "Tone":              trend_direction.get("tone", "flat"),
             "% Change":          trend_direction.get("pct_change"),
             "Current period":    trend_direction.get("current"),
             "Previous period":   trend_direction.get("previous"),
         }},
        {"section_key": "top_wins", "title": "Top Wins",
         "kind": "list", "items": list(top_wins or []) or [EMPTY_STATE_ITEM]},
        {"section_key": "needs_immediate_attention",
         "title": "Needs Immediate Attention",
         "kind": "list",
         "items": list(needs_immediate_attention or []) or [EMPTY_STATE_ITEM]},
    ]

    if top_5_items and top_5_items.get("rows"):
        sections.append({
            "section_key": "top_5_items",
            "title": top_5_items.get("title") or "Top 5 Items",
            "kind": "table",
            "headers": top_5_items.get("headers") or [],
            "rows": top_5_items.get("rows") or [],
        })
    else:
        sections.append(not_applicable_section("top_5_items", "Top 5 Items"))

    sections.append({"section_key": "core_metrics", "title": "Core Metrics",
                     "kind": "kv", "rows": core_metrics or {}})

    if trend_table and trend_table.get("rows"):
        sections.append({
            "section_key": "trend_table", "title": "Trend Table",
            "kind": "table",
            "headers": trend_table.get("headers") or [],
            "rows": trend_table.get("rows") or [],
        })
    else:
        sections.append(not_applicable_section("trend_table", "Trend Table"))

    sections.append({"section_key": "recommendations", "title": "Recommendations",
                     "kind": "list",
                     "items": list(recommendations or []) or [EMPTY_STATE_ITEM]})
    sections.append({"section_key": "upcoming_risks", "title": "Upcoming Risks",
                     "kind": "list",
                     "items": list(upcoming_risks or []) or [EMPTY_STATE_ITEM]})
    sections.append({"section_key": "recent_changes", "title": "Recent Changes",
                     "kind": "list",
                     "items": list(recent_changes or []) or [EMPTY_STATE_ITEM]})

    if deep_links:
        sections.append({
            "section_key": "deep_links", "title": "Deep Links",
            "kind": "list",
            "items": [{"href": d["href"], "text": d["text"]}
                      for d in deep_links if d.get("href") and d.get("text")]
                     or [EMPTY_STATE_ITEM],
        })
    else:
        sections.append(not_applicable_section("deep_links", "Deep Links"))

    if no_auto_decision_notice:
        sections.append({
            "section_key": "no_auto_decision_notice",
            "title": "No-Auto-Decision Notice",
            "kind": "list", "items": [no_auto_decision_notice],
        })
    else:
        sections.append(not_applicable_section(
            "no_auto_decision_notice", "No-Auto-Decision Notice"))

    sections.append({
        "section_key": "audit_footer", "title": "Audit",
        "kind": "kv", "rows": {
            "Product":       product_id,
            "Period":        period_label,
            "Generated at":  generated_at,
            "Note":          audit_footer or (
                "Attention signal only. Domain owners investigate and classify."
            ),
        }})

    return {
        "product_id": product_id,
        "subject": subject,
        "generated_at": generated_at,
        "sections": sections,
        "no_auto_decision_notice": no_auto_decision_notice or "",
        "operational_intelligence_score": score,
        "trend_direction": trend_direction,
    }


__all__ = [
    "STANDARD_SECTION_ORDER",
    "EMPTY_STATE_ITEM",
    "not_applicable_section",
    "build_standard_layout",
]
