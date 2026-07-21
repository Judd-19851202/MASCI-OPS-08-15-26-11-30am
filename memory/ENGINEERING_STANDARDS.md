# Engineering Standards

## Controlled Certification Recipients

- Every environment (Development, Preview, and Production Certification) shall have one documented, owner-approved certification recipient or recipient group.
- Certification workflows must never default to:
  - project personnel
  - operational distribution lists
  - employee production addresses
  - placeholder addresses such as `example.com`
- If no approved certification recipient exists, this is an environment configuration deficiency, not a product defect.
- Environment setup must be corrected directly; do not create new product code, infrastructure, or repeated approval requests just to work around missing certification-recipient governance.