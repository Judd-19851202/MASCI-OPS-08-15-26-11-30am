# WP-17C Icon System Standard

## Canonical icon family
`lucide-react` remains the canonical shared icon family for WP-17C.

## Why
- clean professional enterprise character
- minimal geometry
- consistent optical size
- strong small-size legibility
- neutral enough for white-label use
- already deeply integrated across portal shells and navigation

## Icon rules
- Use one outline language; avoid mixing thick fill sets with outline nav icons.
- Use consistent 16/18/20/24 sizing steps.
- Match icon semantics to the action, not decoration.
- Do not invent construction clip art.
- Do not create gothic, dark-industrial, or neon iconography.
- Only introduce a custom wrapper when normalizing size/color/active-state behavior.

## Canonical mappings
- home / dashboard → `Home` / `LayoutDashboard`
- operations / live → `Activity` / `Radar`
- people → `Users`
- jobs / projects → `Building2`
- fleet / transportation → `Truck`
- safety / trust → `Shield*`
- documents / reports → `FileText`, `BarChart3`
- settings / configuration → `Cog`
- notifications → `Bell`
- search → `Search`

## Migration rule
Existing route/action icons are mapped to canonical concepts in WP-17D; WP-17C only defines the standard and applies it to the representative surfaces.
