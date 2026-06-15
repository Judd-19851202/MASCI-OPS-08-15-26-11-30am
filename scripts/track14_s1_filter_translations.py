"""Filter out poor translations (identical to source or contain too much English).

Reads /app/test_reports/track14_s1_critical_translations.json and emits a
JSON file with only high-confidence translations to append to i18n.js.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

IN_PATH = Path("/app/test_reports/track14_s1_critical_translations.json")
OUT_PATH = Path("/app/test_reports/track14_s1_critical_translations_filtered.json")

# Spanish character / word markers — if the "translation" has none of
# these, it's most likely still English noise.
SPANISH_MARKERS = re.compile(
    r"(ñ|á|é|í|ó|ú|¿|¡|"
    r"\b(de|el|la|los|las|un|una|y|o|en|con|por|para|que|no|sí|"
    r"se|al|del|sin|sobre|antes|después|aún|también|este|esta|"
    r"estos|estas|ese|esa|esos|esas)\b)",
    re.IGNORECASE,
)


def main() -> int:
    data = json.loads(IN_PATH.read_text())
    kept = {}
    dropped = []
    for en, es in data.items():
        e = en.strip()
        s = es.strip()
        if not s:
            dropped.append((en, "empty"))
            continue
        if e.lower() == s.lower():
            dropped.append((en, "identical"))
            continue
        # Tiny strings (<= 4 chars) — keep only if explicitly different.
        if len(e) <= 4:
            if e == s:
                dropped.append((en, "tiny-identical"))
                continue
            kept[en] = es
            continue
        if not SPANISH_MARKERS.search(s):
            # Allow strings where the English has technical content the
            # LLM rightly preserved (e.g. "Pay Code (Exact)").
            # If the only diff is whitespace/punct, drop it.
            if e.replace(" ", "").lower() == s.replace(" ", "").lower():
                dropped.append((en, "no-spanish-markers"))
                continue
        kept[en] = es

    OUT_PATH.write_text(json.dumps(kept, indent=2, ensure_ascii=False, sort_keys=True))
    print(f"Kept:    {len(kept)}")
    print(f"Dropped: {len(dropped)}")
    for k, why in dropped[:20]:
        print(f"  ! {why}: {k!r}")
    print(f"\nWrote → {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
