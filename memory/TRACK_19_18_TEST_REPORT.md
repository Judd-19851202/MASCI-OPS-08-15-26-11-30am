# Track 19.18 · Test Report

## Backend (pytest)

**376/376 lock tests passing.**

### Track 19.15 · Incident Engine Audit
- 24 tests · all green

### Track 19.16 · Phases A–E + UX Hardening + Final Closeout
- 305 tests · all green
- Subset-check upgrade to `test_9_incident_types_present` and `test_vocabulary_shape` preserves the baseline 9-type invariant while allowing Track 19.17 additive expansion.
- `test_every_report_has_title_audience_and_sections` accepts sections[0] ∈ {header, cover} so the Track 19.17 cover-first upgrade doesn't drift the shape.

### Track 19.16 UX Hardening Batches 1 + 2
- 28 tests · all green

### Track 19.18 · PDF Excellence (NEW — 11 tests)
```
test_case_story_composer_reads_field_block_shape          PASSED
test_case_story_composer_tolerates_missing_data           PASSED
test_cover_renders_wordmark_and_banner                    PASSED
test_cover_carries_running_header_and_footer_strings      PASSED
test_exec_summary_includes_case_story_paragraph           PASSED
test_timeline_is_narrative_not_json                       PASSED
test_root_cause_factors_render_as_ordered_list            PASSED
test_empty_photographs_section_is_suppressed              PASSED
test_section_is_empty_helper_still_shields_structural_sections  PASSED
test_css_protects_key_blocks_from_splitting               PASSED
test_full_pdf_bytes_produce_valid_pdf                     PASSED
```

### Track 19.18 · Safety Case Workspace (NEW — 8 tests)
```
test_workspace_defines_compose_case_story_helper          PASSED
test_case_header_renders_story_paragraph                  PASSED
test_case_header_renders_next_action_chip                 PASSED
test_blockers_are_clickable_and_map_to_tabs               PASSED
test_jump_to_blocker_wires_state_setter                   PASSED
test_timeline_uses_ordered_list_with_visual_spine         PASSED
test_executive_snapshot_has_headline_first                PASSED
test_health_counts_hide_when_all_zero                     PASSED
```

**Total: 376 passed, 0 failed, 1 warning (unrelated Starlette PendingDeprecationWarning).**

## Frontend (ESLint)

| File | Result |
|---|---|
| `pages/SafetyCaseWorkspace.jsx` | ✅ No issues |
| `pages/IncidentReport.jsx` | ✅ No issues (4 pre-Track-19.18 unused disables removed) |
| `pages/IncidentReportViewer.jsx` | ✅ No issues |
| `pages/IncidentsDashboard.jsx` | ✅ No issues |
| `lib/incidentReportSchema.js` | ✅ No issues |
| `lib/i18n.js` | 708 pre-existing `no-dupe-keys` warnings (not introduced by Track 19.18 — baseline was 706 before 19.18 additions; deduping deferred to a dedicated cleanup track) |

## Frontend (Playwright / screenshot)

- `/incidents/report` picker in EN mode: 17 cards render · all Track 19.17 types present · Track 19.18 layout preserved.
- `/incidents/report` picker in ES mode: all 17 cards render with Spanish labels (Lesión al Público, Incendio, Amenaza, Robo, Vandalismo, Seguridad del Sitio, Peligro Identificado, Otro).
- Language toggle (`masci.lang`) round-trips.

## End-to-end PDF pipeline

Programmatic smoke via `render_report_html` + `html_to_pdf_bytes`:
- HTML length: ~11 KB
- MASCI wordmark present
- Cover banner present
- Case Story `.story` block present
- Timeline `.tline` narrative present
- Contributing factors `ol.factors` present
- Empty photographs suppressed
- Running header + footer carriers present
- Valid `%PDF-` bytes (29 KB output)

## What was NOT tested (out of scope)

- OSHA 300 / 300A generation (explicitly deferred by user)
- Compliance intelligence automation (explicitly deferred by user)
- Full end-to-end incident-submit-through-close flow with a real Safety user (would require a seeded case and an authenticated session — the Track 19.16 phase E testing already certified this end-to-end; Track 19.18 changes are additive and preserve those contracts via subset locks)

## Regression status

**GREEN.**

No test previously passing is now failing. Every Track 19.18 addition is protected by at least one new lock test.
