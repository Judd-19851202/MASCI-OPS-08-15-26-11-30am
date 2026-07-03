# TRACK 19.40 · RECIPIENT ENGINE

## Collections (canonical)
- **`morning_digest_recipients`** (existing, from Track 19.39 · zero-drift). Row-per-individual with `digest_type` selecting which product they receive.
- **`operational_recipient_groups`** (additive, new). Row-per-group with `products: [product_id, ...]` and embedded `members: [{email, display_name, role_label, active}]`.

## Resolution (`list_recipients_for(product_id)`)
Union of directly-subscribed individuals (where `digest_type == product_id AND active == True`) and members of groups where `product_id` appears in `products`. Deduped by lowercase email; direct rows win over group rows.

## Public API
- `list_recipients_for(db, product_id=…, active_only=True)`
- `list_groups(db)`
- `add_group(db, group_id=…, group_name=…, products=[…])`
- `add_group_member(db, group_id=…, email=…, display_name=…, role_label=…)`

Groups persist across recipient turnover — people come and go, groups stay.
