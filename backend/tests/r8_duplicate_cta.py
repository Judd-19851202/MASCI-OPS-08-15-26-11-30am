"""R8 — Duplicate CTA inside a single Card (Track 18.11).

Conservative, allow-list-first, high-confidence scanner. Only fires
when a single `<Card>...</Card>` block contains two or more `<Button>`
elements that pass the **primary CTA signature** (default variant —
no `outline` / `ghost` / `link` / `secondary` / `destructive`)
**after** exempt subtrees (tables, dropdowns, tabs, navigation,
popovers, selects, breadcrumbs, pagination) are stripped from the
card body.

The design principles:
* Scan only `<Card>...</Card>` — never proximity.
* Strip exempt subtrees before counting — never count buttons inside
  a `<TableRow>` / `<DropdownMenu*>` / `<Tabs>` / etc.
* Count only `<Button>` with a primary-CTA signature.
* Allow-list managed via `memory/R8_DUPLICATE_CTA_ALLOWLIST.md`.
* Ignore `aria-label`, `title`, `data-*` strings — only visible
  button text + variant matter.
"""
from __future__ import annotations

import re
from typing import List


# Non-primary variants. A `<Button>` with any of these is NOT counted
# as a primary CTA candidate.
R8_PRIMARY_VARIANT_BLOCKERS = (
    "outline",
    "ghost",
    "link",
    "secondary",
    "destructive",
)

# Subtree tags whose contents are stripped from the card body before
# counting. These contain repeated row actions, menu items, tab
# triggers, nav links, breadcrumb links, pagination buttons,
# popover/select content — none of which should ever participate in
# the duplicate-primary-CTA signal.
R8_EXEMPT_SUBTREE_TAGS = (
    "Table",
    "TableHeader",
    "TableBody",
    "TableRow",
    "TableCell",
    "TableHead",
    "DropdownMenu",
    "DropdownMenuTrigger",
    "DropdownMenuContent",
    "DropdownMenuItem",
    "DropdownMenuLabel",
    "DropdownMenuGroup",
    "DropdownMenuSub",
    "DropdownMenuSubTrigger",
    "DropdownMenuSubContent",
    "Tabs",
    "TabsList",
    "TabsTrigger",
    "TabsContent",
    "NavigationMenu",
    "NavigationMenuItem",
    "Pagination",
    "PaginationItem",
    "Breadcrumb",
    "BreadcrumbItem",
    "Popover",
    "PopoverContent",
    "Select",
    "SelectContent",
    "Sheet",
    "SheetContent",
    "Dialog",
    "DialogContent",
    "DialogFooter",
    "AlertDialog",
    "AlertDialogContent",
    "AlertDialogFooter",
)


def _strip_exempt_subtrees(src: str) -> str:
    """Remove any `<Tag ...>...</Tag>` block whose tag appears in
    `R8_EXEMPT_SUBTREE_TAGS`. The regex is greedy across newlines and
    is iterated until no more matches are found (handles nesting from
    the outside in)."""
    for tag in R8_EXEMPT_SUBTREE_TAGS:
        pat = re.compile(
            r"<" + re.escape(tag) + r"\b[^>]*>.*?</" + re.escape(tag) + r">",
            flags=re.DOTALL,
        )
        prev = None
        while prev != src:
            prev = src
            src = pat.sub("", src)
    return src


def _find_card_blocks(src: str) -> List[tuple]:
    """Yield (start_line_1based, body_text) for every `<Card>` block
    in the source. Uses a simple depth counter so we never close a
    Card prematurely. Self-closing `<Card />` is ignored (no body to
    scan)."""
    blocks: List[tuple] = []
    # Find every `<Card` opening (must be followed by whitespace, `>`,
    # or attributes; not `<Cards` etc.).
    open_re = re.compile(r"<Card(?:\s[^>]*)?>")
    close_re = re.compile(r"</Card>")
    pos = 0
    while True:
        m = open_re.search(src, pos)
        if not m:
            break
        # Walk forward, counting nested <Card> / </Card>.
        depth = 1
        scan = m.end()
        while depth > 0:
            next_open = open_re.search(src, scan)
            next_close = close_re.search(src, scan)
            if not next_close:
                # Unbalanced — give up on this block.
                depth = 0
                scan = len(src)
                break
            if next_open and next_open.start() < next_close.start():
                depth += 1
                scan = next_open.end()
            else:
                depth -= 1
                scan = next_close.end()
        # Compute the 1-based line number of the opening <Card>.
        start_line = src.count("\n", 0, m.start()) + 1
        body = src[m.end(): scan - len("</Card>")]
        blocks.append((start_line, body))
        pos = scan
    return blocks


_BUTTON_RE = re.compile(
    r"<Button(?P<attrs>(?:\s[^>]*)?)(?P<selfclose>\s*/?)>",
)
_VARIANT_RE = re.compile(r'variant\s*=\s*"([^"]+)"')
_VARIANT_DYNAMIC_RE = re.compile(r"variant\s*=\s*\{")


def _is_primary_button(attrs: str) -> bool:
    """A Button is a "primary CTA" candidate when it has no `variant=`
    or when the variant value is not in `R8_PRIMARY_VARIANT_BLOCKERS`.

    A Button with a **dynamic** `variant={...}` JSX expression is
    *not* counted as a primary CTA — these are almost always
    state-driven toggle/filter buttons (e.g., active filter rendered
    as default, inactive as outline). The directive explicitly says
    R8 must not flag filter buttons / toggle buttons / repeated list
    actions.
    """
    if _VARIANT_DYNAMIC_RE.search(attrs):
        return False
    m = _VARIANT_RE.search(attrs)
    if not m:
        return True
    variant = m.group(1).strip().lower()
    return variant not in R8_PRIMARY_VARIANT_BLOCKERS


def find_r8_violations(src: str) -> List[dict]:
    """Return the list of R8 violations in `src`. Each violation is
    `{card_line, primary_count}`."""
    violations: List[dict] = []
    for start_line, body in _find_card_blocks(src):
        cleaned = _strip_exempt_subtrees(body)
        primary = 0
        for m in _BUTTON_RE.finditer(cleaned):
            if _is_primary_button(m.group("attrs") or ""):
                primary += 1
        if primary >= 2:
            violations.append(
                {"card_line": start_line, "primary_count": primary}
            )
    return violations
