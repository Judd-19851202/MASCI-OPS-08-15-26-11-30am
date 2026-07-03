# TRACK 20.4 · Human Walkthrough

## HR / Administration (owner)
- Needs: full vendor record · documents · contracts · status · audit · all POs.
- Should not see: nothing hidden. Master owner.
- Today: hunts across `SupplierMasterPanel` (Admin) → `PoRequests` (per-vendor filter) → nothing for documents.
- Thread would improve: one-scroll ownership. Approve documents in the same context.
- Restricted: none.

## Accounting / AP
- Needs: PO history · invoices (future) · payment info (future) · W-9 · vendor status.
- Should not see: raw safety photos · attorney work product.
- Today: hunts across PO Requests filtered by vendor.
- Thread would improve: single scroll on financial-relevant fields.
- Restricted: raw safety photos.

## Admin
- Needs: everything HR sees + do-not-use flag write authority + audit.
- Restricted: none.

## Executive
- Needs: name · status · do-not-use · high-level PO throughput · risk flags.
- Should not see: tax ID · payment details raw · full document library.
- Today: hunts across dashboards.
- Thread would improve: executive-grade one-scroll.
- Restricted: tax ID · payment raw · attorney work product.

## PM
- Needs: contracts on their projects · COI / license status · open POs · vendor performance.
- Should not see: tax ID · payment info · contracts on OTHER PM's projects.
- Today: `PmSuppliers` (roster only) + `PoRequests` (per-project filter).
- Thread would improve: scoped read of vendors they can actually use on their projects.
- Restricted: tax ID · payment info · other PMs' contracts.

## Safety
- Needs: COI / license / incident history / prequalification.
- Should not see: contract value · payment info · tax ID.
- Today: hunts across HR + incident case cross-links.
- Thread would improve: safety-lens view.
- Restricted: contract value · payment info · tax ID.

## Shop
- Needs: repair vendor contacts · parts / warranty · service records.
- Should not see: tax / payment / contract value / safety internals.
- Today: shop intel screens.
- Thread would improve: shop-lens view of the same vendor.
- Restricted: tax / payment / contract value / safety internals.

## Fleet
- Needs: rental vendor / hauling carrier compliance / equipment / incidents.
- Should not see: tax / payment / contract value.
- Today: fleet + carrier compliance screens (fragmented).
- Thread would improve: consolidated fleet-lens view.
- Restricted: tax / payment / contract value.

## Dispatch
- Needs: carrier compliance · hauling history · route info.
- Should not see: contract value · tax · payment.
- Today: dispatch portal + carrier compliance.
- Thread would improve: dispatch-lens view.
- Restricted: contract value · tax · payment.

## Superintendent (Field)
- Needs: name · approved / do-not-use · phone contact.
- Should not see: any documents · tax · payment · contracts.
- Today: `SupplierCombo` name picker.
- Thread would improve: not directly — field crews should not access the thread.
- Restricted: everything except name + approved status.

## Owner / Client reviewer
- Needs: proof of vendor compliance if contract requires disclosure.
- Should not see: internal financial details.
- Today: manual PDF distribution.
- Thread would improve: nothing directly — thread is internal.
- Restricted: internal financials.

## Certification
Every persona either gains a scoped, permission-safe read of the same vendor, or continues on their current workflow unchanged. No persona receives anything they should not.
