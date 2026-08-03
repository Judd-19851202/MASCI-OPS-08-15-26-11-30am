# Operator Banned Language Register

## Purpose
Operator-facing MASCI screens must use business language only. Internal implementation terms, engineering shorthand, QA wording, and project code names must stay out of the production experience.

## Banned Terms
- WP-14F
- WP-17
- Certification
- Canonical
- Backend
- Frontend
- Mutation
- Governed
- Runtime
- Preview
- Fixture
- Audit
- Developer terminology
- Engineering terminology
- Same shell
- Shared workspace
- Navigation system
- Responsive behavior
- Information hierarchy
- Internal project names
- Code names

## Approved Replacements
- Certification → Review / readiness / alignment
- Canonical → Platform / source / primary
- Backend / Frontend → Platform / system
- Mutation → Update / change
- Governed → Approved / shared / standard
- Runtime → Live
- Preview → Review / draft / staged
- Fixture → Record / example
- Audit → History / review / activity history
- Same shell / shared workspace → One place / work area
- Navigation system / information hierarchy → Clear path / clear priorities
- Responsive behavior → Mobile and desktop support

## Constitutional Rule
Any screen that looks like an engineering, QA, certification, debugging, or developer utility must either:
1. be converted into the MASCI Operations Platform experience, or
2. be hidden behind administrator/developer permissions if it is not intended for operational users.

## Enforcement
- Shared navigation labels must avoid banned terms.
- Operator-visible buttons, headings, cards, chips, and helper text must avoid banned terms.
- Dynamic data that contains internal project names or code names must be sanitized before display.
- `/app/scripts/wp17d_constitution_guard.py` now includes an operator-language scan for high-risk operator surfaces.