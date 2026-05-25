"""iter417 · Phase 20.0 · Operational Attachments — ES translations.

Spanish translation for the dls-attachments-load-proof guidance article.
Style mirrors translations_es_iter414.py — field-accurate operational
Spanish, NOT robotic translation.

Vocabulary discipline:
  - "asphalt_ticket"      → "boleto de asfalto"
  - "scale_ticket"        → "boleto de báscula"
  - "tanker_BOL"          → "Carta de Porte de Cisterna (BOL)"
  - "fuel_receipt"        → "recibo de combustible"
  - "dump_receipt"        → "recibo de descarga"
  - "delivery_receipt"    → "recibo de entrega"
  - "load_photo"          → "foto de carga"
  - "damage_photo"        → "foto de daño"
  - "breakdown_photo"     → "foto de avería"
  - "inspection_photo"    → "foto de inspección"
  - "transfer_document"   → "documento de transferencia"
  - "operational_note_photo" → "foto de nota operacional"
"""
from __future__ import annotations

EXTRA_ES: dict[str, dict] = {
    "dls-attachments-load-proof": {
        "title_es": "DLS · Adjuntos Operacionales (Prueba de Carga · Boletos · Fotos)",
        "summary_es": "Cómo la prueba operacional viaja con el acarreo — boletos, BOLs, recibos de báscula, fotos de averías — sin convertirse en gestión de documentos.",
        "body_es": [
            {"type": "p", "text":
                "Los adjuntos operacionales NO son archivos. Son prueba "
                "operacional que viaja con el acarreo mismo. Un boleto de "
                "báscula adjunto a una asignación de Material se convierte "
                "en parte de la verdad de esa asignación — los consumidores "
                "río abajo (PM, Taller, gobernanza, revisión post-"
                "despliegue) ven la misma prueba ligada al mismo evento "
                "operacional."},
            {"type": "bullets", "items": [
                "Boleto de asfalto / Boleto de báscula — prueba de carga de material desde la planta o báscula",
                "Carta de Porte de Cisterna (BOL) — para acarreos de cisterna / asfalto líquido",
                "Recibo de combustible / Recibo de descarga / Recibo de entrega — puntos de prueba operacional",
                "Foto de carga / Foto de daño / Foto de avería — continuidad visual operacional",
                "Foto de inspección — seguimiento visual de pre-op o DVIR",
                "Documento de transferencia — cadena de custodia de movimiento de equipo",
                "Foto de nota operacional — cualquier otra cosa que operaciones necesite recordar",
            ]},
            {"type": "why", "text":
                "La verdad operacional se desvanece rápido en el campo — y los "
                "boletos en papel se pierden o se dañan. Atar cada foto y "
                "recibo a la asignación (no a una carpeta, no a un proyecto, "
                "no a una cuenta de usuario) mantiene la prueba pegada "
                "permanentemente a la verdad operacional que la creó. "
                "Despacho, PM, Taller y gobernanza leen la misma prueba "
                "desde el mismo registro de asignación."},
            {"type": "next", "items": [
                "El conductor o despachador adjunta vía la gaveta de contexto de la asignación · cámara primero",
                "El adjunto se convierte en prueba operacional para esa asignación para siempre",
                "Recuperación de error: el cargador original puede eliminar dentro de 5 minutos · luego permanente",
                "Cada adjunto lleva: tipo · cargador · tiempo · nota operacional opcional",
            ]},
            {"type": "tip", "text":
                "Tome fotos EN EL PUNTO DE CARGA o EN LA DESCARGA — no de "
                "memoria en la cabina del camión después. Cuanto más cerca "
                "se capture la prueba del momento operacional, más verdad "
                "operacional lleva."},
            {"type": "warn", "text":
                "Los adjuntos son prueba operacional. No los use como un "
                "álbum de fotos general · no adjunte documentos corporativos "
                "no relacionados · no adjunte registros de personal. Los 12 "
                "tipos canónicos existen para mantener la verdad operacional "
                "estrecha — cualquier cosa que no encaje es deriva de "
                "doctrina y pertenece a otra parte."},
        ],
    },
}
