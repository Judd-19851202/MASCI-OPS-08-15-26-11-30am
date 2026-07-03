# TRACK 19.40 · ARCHITECTURE

```
Product Registry ──► Aggregator (per product) ──► Digest object
                                                       │
                                                       ▼
                                             Canonical HTML/PDF Renderer
                                                       │
                            ┌──────────────────────────┼──────────────────────────┐
                            ▼                          ▼                          ▼
                    Preview (in-app)             Email dispatch              History write
                                                   │                          │
                                            fsi_send_email               operational_intelligence_history
                                                   │
                                             Dedupe guard
                                                   │
                                             Audit write
                                                   │
                                      operational_intelligence_audit
```

## One of each
| Concern | ONE canonical module |
|---|---|
| Registry | `operational_intelligence/registry.py` |
| Compose · render · dispatch · trend · audit · history · dedupe | `operational_intelligence/engine.py` |
| Recipients + groups | `operational_intelligence/recipients.py` |
| Scheduler contract | `operational_intelligence/scheduler.py` |
| Products (all 10) | `operational_intelligence/products.py` |
| HTTP surface | `operational_intelligence/routes.py` |
| Email provider | existing `lib/fsi_email_sender.fsi_send_email` |
| PDF renderer | existing WeasyPrint (`incident_engine/report_render.html_to_pdf_bytes`) |

The lock test enforces "one of each" by grepping the codebase for duplicate scheduler / renderer / email-provider patterns.
