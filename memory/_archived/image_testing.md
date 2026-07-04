# Image Integration — Test Agent Rules

## Image Handling Rules
- Always use base64-encoded images for all tests and requests.
- Accepted formats: JPEG, PNG, WEBP only.
- Do not use SVG, BMP, HEIC, or other formats.
- Do not upload blank, solid-color, or uniform-variance images.
- Every image must contain real visual features (objects, edges, textures, shadows).
- If image is not PNG/JPEG/WEBP, transcode to PNG/JPEG before upload.
- If image is animated (GIF/APNG/WEBP animation), extract first frame only.
- Resize large images to reasonable bounds (avoid oversized payloads).
- Always re-detect and update MIME after transformations.
