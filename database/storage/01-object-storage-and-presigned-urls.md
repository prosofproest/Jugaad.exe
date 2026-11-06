# 01 — Object Storage Layout and Presigned URL Rules

**Status:** Approved Reference Spec  
**Authority:** `final/feature-specs/05-data-layer.md` §8; `database/collection/04-secure-upload-and-retention.md`; `final/TRD.md` §6.  
**Owner:** Data Engineer & Platform Lead  

---

## 1. Storage Architecture and Tenancy

Object storage is strictly private, encrypted at rest (AES-256 / AWS KMS SSE-S3/SSE-KMS), TLS 1.3 in transit, with **zero public read ACLs** and **public bucket access blocked** (`BlockPublicAcls=true`, `IgnorePublicAcls=true`, `BlockPublicPolicy=true`, `RestrictPublicBuckets=true`).

Bucket contents are divided into two distinct functional classes:
1. **Immutable Legal Records (Originals):** The raw, untouched photo captured by the client (with EXIF GPS sanitised). Stored exactly once. Never updated, modified, or replaced in-place.
2. **Regenerable Derivatives:** Processed, compressed, or resized assets (previews, thumbnails, model tensors). Derived under explicit pipeline versioning and can be dropped or re-generated at any time without data loss.

---

## 2. Canonical S3 Object Layout

All object keys are opaque and content-addressed. **Keys never contain farmer names, phone numbers, villages, or coordinates (R9).**

```
s3://<private-bucket>/
  ├── observations/
  │   └── <yyyy>/
  │       └── <mm>/
  │           └── <observation_id>/
  │               └── <image_id>/
  │                   ├── original.<ext>                         # Immutable legal capture record
  │                   └── derived/
  │                       └── <pipeline_version>/
  │                           ├── preview.jpg                    # High-quality display for pathologist review
  │                           ├── thumb.jpg                      # Low-res list view thumbnail
  │                           └── model-input-<w>x<h>.jpg        # Deterministic resized crop for inference
  ├── advisories/
  │   └── <advisory_id>/
  │       └── <version>/
  │           └── <file>                                         # Approved advisory infographics / diagrams
  ├── models/
  │   └── <kind>/
  │       └── <version>/
  │           └── <artefact>                                     # Checksummed weights (ONNX / Joblib)
  └── exports/
      └── <export_job_id>/
          └── <file>.zip                                         # Time-bound downloadable audit/training export
```

### 2.1 Object Key Formatting Rules
* `<observation_id>`: UUID v4 string.
* `<image_id>`: UUID v4 string.
* `<yyyy>/<mm>`: UTC timestamp of creation.
* `<ext>`: Normalized lowercase extension matching MIME: `.jpg` (`image/jpeg`), `.png` (`image/png`), `.webp` (`image/webp`).
* `<pipeline_version>`: Semantic version identifier (e.g., `v1.0.0`).

---

## 3. Presigned URL Specification and Security Rules

No client application connects with direct AWS IAM credentials. All uploads and downloads occur through **ephemeral, single-use, presigned URLs** issued by the authenticated backend.

### 3.1 Strict Security Rules
1. **TTL Limit (Rule P1):** Expiration duration must be **≤ 10 minutes (600 seconds)**. The recommended default is **300 seconds (5 minutes)**. Requests exceeding 600s are rejected with HTTP 400.
2. **Verb Restriction (Rule P2):**
   * Upload presigned URLs must use HTTP `PUT` only.
   * Read presigned URLs must use HTTP `GET` only.
3. **Payload Enclosure (Rule P3 - Uploads):**
   * Pre-signed PUT requests must bind and enforce headers:
     * `Content-Type`: Exactly matched to declared mime (`image/jpeg`, `image/png`, `image/webp`).
     * `Content-Length`: Minimum 50 KB, Maximum 15 MB.
     * `x-amz-checksum-sha256`: Client-declared SHA-256 base64 digest.
4. **Credential Isolation (Rule P4):** Presigned URLs are capabilities and are treated as secrets; they are never logged into application logs, audit logs, or query strings in traces.
5. **No Public Directory Listing (Rule P5):** `ListBucket` is prohibited for all client roles.

### 3.2 Role-Based Access Control (RBAC) Matrix

Every presigned URL request requires backend authorization against the relational database before the URL is signed:

| Actor Role | Action | Object Scope | Verification Query |
|---|---|---|---|
| **Farmer** | `PUT` | Own new observation original | `observations.user_id = :current_user_id` AND `status IN ('draft', 'pending_upload')` |
| **Farmer** | `GET` | Own observation images & derivatives | `observations.user_id = :current_user_id` AND `observations.deleted_at IS NULL` |
| **Extension Worker** | `PUT` | Captured-on-behalf observation original | `observations.user_id = :current_user_id` OR `observations.geo_code IN (:assigned_blocks)` |
| **Extension Worker** | `GET` | Area observations & derivatives | `observations.geo_code IN (:user_area_assignments)` |
| **Pathologist** | `GET` | Assigned reviews & verification queue | Valid active assignment in `review_assignments` OR review queue |
| **Agronomist** | `GET` | Advisories and approved models | `advisories` / `model_registry` status = 'approved' |
| **Admin** | `GET` | Audited troubleshooting only | Explicit `audit_events` row emitted; no bulk photo browsing without export approval |

---

## 4. Ingestion, EXIF GPS Stripping and Quarantine

1. **Client Capture:** Mobile app captures photo, records local timestamp and camera parameters.
2. **Pre-Upload Registration:** App requests upload authorization from `POST /api/v1/observations/{id}/images`. Server verifies user quota, creates `image_assets` with `upload_status = 'pending'`, and signs PUT URL.
3. **Upload to Staging/Original:** Client PUTs payload directly to S3.
4. **Sanitization Trigger (Worker):**
   * Worker downloads object, reads magic bytes to confirm MIME.
   * Calculates SHA-256. If hash mismatches client declaration, quarantine object and mark `upload_status = 'failed'`.
   * Checks for duplicate SHA-256 in `image_assets`. If duplicate exists, link to existing asset and delete duplicate file.
   * Strips EXIF metadata. If EXIF GPS tags were present, record `exif_gps_present = true` and `exif_stripped = true`.
   * **Quarantine Fallback:** If stripping fails or coordinates cannot be securely removed, the file is moved to `quarantine/` and never made readable.
5. **Derivative Generation:** Worker generates `preview.jpg` (1280px), `thumb.jpg` (256px), and `model-input-224x224.jpg` under `derived/<version>/`.

---

## 5. Lifecycle, Retention and Cascading Deletion

1. **Original Deletion Cascade:** When an observation is permanently deleted (following legal request or retention expiration under DPIA):
   * An async job removes `original.<ext>`.
   * S3 Lifecycle or cleanup worker executes prefix deletion on `derived/`.
   * Audit event recorded with deletion reason and entity UUID (no image bytes or PII in audit).
2. **Model Artefacts:** Models stored in `models/` are WORM (Write Once Read Many). Never deleted while any historical prediction references `model_version`.
3. **Exports:** Output archives in `exports/` carry an S3 Lifecycle expiration rule of **7 days**, after which S3 automatically purges the object.

