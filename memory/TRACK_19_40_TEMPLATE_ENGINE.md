# TRACK 19.40 · TEMPLATE ENGINE

**One template · one CSS · product-specific sections composed from data.**

The renderer accepts a digest object with:
```
{
  subject: string,
  engine_version, product_id, generated_at,
  sections: [
    { title, kind: "kv"|"table"|"list", rows|headers|items }
  ],
  no_auto_decision_notice: string
}
```

## Section kinds
- `kv` — key/value grid (auto-renders trend objects with ▲/▼/→ + colored tone).
- `table` — headers + rows. Cells that are `{href, text}` render as anchors. Cells that are trend objects render with arrows.
- `list` — bullets. Same cell semantics.

## Zero drift
No product implements its own HTML. Every product returns a `sections` array. Adding a new section kind is a change to `engine._render_sections`; a lock test asserts no product ships its own `<style>` block.

## PDF path
The same HTML is fed to the existing `html_to_pdf_bytes` (WeasyPrint) — no second PDF engine.
