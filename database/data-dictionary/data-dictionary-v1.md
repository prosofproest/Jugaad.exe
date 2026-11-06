# Data dictionary v1

**Status:** Draft v1 — field contract, not a validated dataset.
**Owner:** Data engineer + agronomist (TBD)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/data-foundation.md` §2.4;
`final/docs-context/phase-plan.md` §4.1;
`final/feature-specs/05-data-layer.md`.

> **Scope note:** this dictionary defines the fields used for image training/evaluation
> and area forecasting. Crop-specific target codes, severity scales, crop calendars,
> horizon values and event thresholds are blocked on **D1** (crop/targets/zone) and
> **D2** (nowcast vs outlook). They are marked `TBD — D1/D2`. They must not be filled with
> plausible-looking values. Forecast label eligibility and sentinel negatives follow **D7**;
> abstention, calibration and OOD fields follow **D8**; retention and controller fields
> follow **D10**.

---

## 1. Reading conventions

### 1.1 Types

Types use PostgreSQL-style notation:

`uuid`, `text`, `boolean`, `integer`, `numeric(p,s)`, `date`, `timestamptz`,
`jsonb`, `geometry(Point,4326)`, `geometry(MultiPolygon,4326)`.

### 1.2 Origin

| Origin | Meaning |
|---|---|
| `observation` | Reported or captured by a user/device |
| `external` | Supplied by a provider or partner |
| `derivation` | Computed from other stored values |
| `adjudicated_label` | Human-reviewed label or verification decision |
| `config` | Approved configuration/reference data |

### 1.3 Missing-value semantics

| Convention | Meaning |
|---|---|
| `null` | Unknown, not provided, or not measured. **Never treat as zero.** |
| `0` | A measured or derived zero |
| `not_applicable` | The field does not apply to this record type |
| `withheld` / `suppressed` | Present but not disclosable at this aggregation level |
| `not_measured` | Instrument or provider did not produce a value |
| `quarantined` | Excluded from model-ready data pending resolution |

Rules:

- Never use `-1`, `999`, empty string or `"N/A"` as a numeric missing marker.
- Distinguish **unknown** from **zero** everywhere.
- Weather gaps are never imputed for a scored outlook; they force `insufficient_data`.
- A forced class is never a substitute for a missing label.
- Every imputation records the method and a flag.

### 1.4 Owners

Owners are roles, not individuals: Data engineer, Agronomist, Pathologist, ML lead,
Field operations lead, Product lead, Legal/privacy.

---

## 2. Common keys and lineage

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `observation_id` | uuid | — | System | Data engineer | Not permitted | observation | No |
| `image_id` | uuid | — | System | Data engineer | Not permitted for an image row | observation | No |
| `user_id` | uuid | — | Identity module | Data engineer | Not permitted | observation | Yes (identifier) |
| `geo_code` | text | Stable admin code | Boundary dataset | Data engineer | Unknown/unmatched; cannot aggregate | external | No |
| `boundary_version` | text | Version identifier | Boundary dataset | Data engineer | Unknown; do not default to latest | external | No |
| `dataset_id` | text | `DS-###` | Dataset register | Data engineer | Not permitted | config | No |
| `dataset_version` | text | Semantic version or provider release | Data pipeline | Data engineer | Not permitted for model use | derivation | No |
| `split_id` | text | Manifest identifier | Data pipeline | ML lead | Not permitted for evaluation | derivation | No |
| `is_demo` | boolean | `true` / `false` | System | Data engineer | Not permitted; default `false` only for real records | config | No |
| `created_at` | timestamptz | UTC | System | Data engineer | Not permitted | observation | No |

---

## 3. Identity and consent

These are not model features, but they are required joins and gates.

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `phone_e164` | text | E.164 | User | Data engineer | Staff account may use email instead | observation | Yes |
| `email` | text | Valid email | User | Data engineer | Farmer account may use phone instead | observation | Yes |
| `locale` | text | BCP-47 | User | Product lead | Default locale TBD; do not assume | observation | No |
| `role_code` | text | `farmer`, `extension_worker`, `pathologist`, `agronomist`, `admin` | Config | Product lead | Not permitted | config | No |
| `consent_type` | text | `service_privacy`, `image_assessment`, `approximate_location`, `research_model_improvement`, `extension_contact` | Consent registry | Legal/privacy | Not captured | observation | Yes |
| `consent_version` | text | Published consent version | Consent registry | Legal/privacy | Not permitted | config | No |
| `consent_granted` | boolean | `true` / `false` | User | Legal/privacy | Not captured; never assume granted | observation | Yes |
| `consent_text_hash` | text | SHA-256 of exact text shown | Consent registry | Legal/privacy | Not permitted | config | No |
| `consent_channel` | text | Allowed values TBD (app/web/SMS/IVR/paper) | User/system | Legal/privacy | Unknown capture channel | observation | No |
| `consent_created_at` | timestamptz | UTC | System | Legal/privacy | Not permitted | observation | Yes |

---

## 4. Geography and crop context

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `geo_level` | text | `block`, `mandal`, `district`, `state` | Boundary dataset | Data engineer | Unknown; cannot aggregate | external | No |
| `parent_code` | text | Stable parent code | Boundary dataset | Data engineer | Top-level area or unknown | external | No |
| `geom` | geometry(MultiPolygon,4326) | SRID 4326 | Boundary dataset | Data engineer | Boundary missing; block forecast issue | external | No |
| `valid_from` / `valid_to` | date | ISO date | Boundary dataset | Data engineer | Unknown validity; do not assume current | external | No |
| `growing_area_id` | uuid | — | User | Data engineer | Not provided; allowed | observation | Yes (link) |
| `precision` | text | Default `block`; full allowed set TBD | User/system | Legal/privacy | Unknown; treat as most private | observation | Yes |
| `precise_geom` | geometry(Point,4326) | SRID 4326 | User/device | Legal/privacy | Not provided; allowed and preferred | observation | Yes |
| `crop_code` | text | Supported crop list — `TBD — D1` | Config | Agronomist | Unsupported/unknown; never map to nearest | config | No |
| `variety` | text | Crop-specific — `TBD — D1` | User | Agronomist | Unknown; not "other" | observation | No |
| `growth_stage` | text | Crop-specific stage set — `TBD — D1` | User/crop calendar | Agronomist | Unknown; no imputation for scored outlook | observation/derivation | No |
| `planting_date` | date | ISO date | User | Agronomist | Unknown; affects `days_since_planting` | observation | No |
| `stage_updated_at` | timestamptz | UTC | System | Data engineer | Unknown | observation | No |
| `season` | text | Crop-specific — `TBD — D1` | Crop calendar | Agronomist | Unknown | config | No |
| `planting_window_start` / `planting_window_end` | date | ISO date | Crop calendar | Agronomist | Calendar missing; no-score | config | No |
| `stage_window` | jsonb | Documented shape per crop — `TBD — D1` | Crop calendar | Agronomist | Calendar missing; no-score | config | No |

---

## 5. Observation and image capture

### 5.1 Observation

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `client_report_id` | text | Client-generated, unique per user | Device | Data engineer | Not permitted | observation | No |
| `subject_user_id` | uuid | — | Staff on-behalf capture | Data engineer | Same as creator | observation | Yes |
| `captured_at` | timestamptz | UTC; device time | Device | Field ops | Unknown; keep as metadata, never use for ordering | observation | No |
| `submitted_at` | timestamptz | UTC; server time | System | Data engineer | Not permitted | observation | No |
| `status` | text | `draft`, `pending_upload`, `uploaded`, `assessing`, `assessed`, `abstained`, `failed`, `pending_review`, `reviewed` | System | Data engineer | Not permitted | derivation | No |
| `notes` | text | Free text; no PII guidance | User | Field ops | Empty = no note, not unknown | observation | Potentially |

### 5.2 Image metadata

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `storage_key` | text | Private object key | System | Data engineer | Not permitted | observation | No |
| `content_hash` | text | SHA-256 | System | Data engineer | Not permitted | derivation | No |
| `perceptual_hash` | text | Algorithm and version recorded | System | Data engineer | Not computed | derivation | No |
| `mime` | text | Validated allowlist — `TBD` | Device/system | Data engineer | Not permitted | observation | No |
| `bytes` | integer | Bytes, > 0 | Device/system | Data engineer | Not permitted | observation | No |
| `width` / `height` | integer | Pixels, > 0 | Device/system | Data engineer | Not permitted | observation | No |
| `source` | text | `camera`, `gallery` | Device | Field ops | Not permitted | observation | No |
| `device_class` | text | `TBD — define low/mid/high or model classes` | Device/app | Field ops | Unknown | observation | No |
| `lighting` | text | `TBD — e.g. sun/shade/overcast/indoor` | User/app | Field ops | Unknown | observation | No |
| `background` | text | `TBD — e.g. soil/mulch/crop/hand/other` | User/app | Field ops | Unknown | observation | No |
| `distance_framing` | text | `TBD — e.g. close/medium/whole-plant` | User/app | Field ops | Unknown | observation | No |
| `plant_part` | text | `TBD — e.g. leaf/stem/fruit/whole-plant` | User/app | Agronomist | Unknown | observation | No |
| `protocol_version` | text | Capture protocol version | Field ops | Field ops | Unknown; cannot audit protocol compliance | config | No |
| `exif_gps_present` | boolean | `true` / `false` | Device | Legal/privacy | Unknown; treat as present and strip | observation | Yes |
| `exif_stripped` | boolean | `true` / `false` | Pipeline | Legal/privacy | Unknown; block use until verified | derivation | No |
| `upload_status` | text | Allowed set TBD (proposed `pending`, `uploading`, `complete`, `failed`) | System | Data engineer | Not permitted | derivation | No |

---

## 6. Image quality gate

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `quality_result_id` | uuid | — | System | Data engineer | Gate not run | derivation | No |
| `gate_version` | text | Versioned model/config | ML registry | ML lead | Not permitted; gate_version_missing | config | No |
| `quality_result` | text | Proposed `pass`, `fail`, `abstain`; confirm in spec | Quality gate | ML lead | Not run | derivation | No |
| `quality_flags` | jsonb | Documented shape: blur, exposure, resolution, no_plant, distance, orientation | Quality gate | ML lead | Not run | derivation | No |
| `quality_thresholds` | jsonb | Snapshot of thresholds used | Quality gate | ML lead | Not recorded; traceability broken | config | No |
| `blur_score` | numeric | Scale defined by `gate_version`; `TBD` | Quality gate | ML lead | Not measured | derivation | No |
| `exposure_score` | numeric | Scale defined by `gate_version`; `TBD` | Quality gate | ML lead | Not measured | derivation | No |
| `resolution_ok` | boolean | `true` / `false` | Quality gate | ML lead | Not measured | derivation | No |
| `plant_present` | boolean | `true` / `false` | Quality gate | ML lead | Not measured | derivation | No |
| `shipped_threshold` | text/numeric | Versioned threshold actually used | ML registry | ML lead | Not permitted for a served prediction | config | No |

### 6.1 Image prediction and decision (D8)

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `prediction_id` | uuid | — | System | Data engineer | Not permitted | derivation | No |
| `image_id` | uuid | FK to the image | System | Data engineer | Not permitted | derivation | No |
| `model_version` | text | Registry version | ML registry | ML lead | Not permitted | config | No |
| `candidates` | jsonb | Array of `{label, score}`; max 3 shown | Model | ML lead | Not available | derivation | No |
| `probabilities` | jsonb | Calibrated per-class probabilities; `null` unless calibration approved | Model | ML lead | Not calibrated/not approved | derivation | No |
| `confidence_band` | text | `low`, `medium`, `high`, `not_calibrated` | Model | ML lead | `not_calibrated`; never a percentage | derivation | No |
| `calibrated` | boolean | `true` / `false` | Model | ML lead | Treated as `false` | derivation | No |
| `calibration_version` | text | Required when `calibrated = true` | ML registry | ML lead | Calibration not approved | config | No |
| `abstained` | boolean | `true` / `false` | Decision function | ML lead | Not permitted | derivation | No |
| `abstain_reason` | text | `below_class_threshold`, `low_margin`, `high_entropy`, `out_of_distribution`, `unsupported_crop`, `quality_gate_failed` | Decision function | ML lead | Required when abstained | derivation | No |
| `decision_thresholds` | jsonb | Per-class `τ_c`, margin, entropy, `ood_max`; required | Decision function | ML lead | Not permitted; prediction not reproducible | config | No |
| `ood_score` | numeric | Scale defined by the OOD method and version | Model | ML lead | Unknown; treat as out-of-distribution | derivation | No |
| `generated_at` | timestamptz | UTC | System | Data engineer | Not permitted | derivation | No |
| `is_demo` | boolean | `true` / `false` | System | Data engineer | Not permitted | config | No |

Predictions are append-only. No UI or API control overwrites a prediction; manual review is a
separate audited record.

---

## 7. Labels and verification

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `target_code` | text | Supported targets + `healthy` + `abiotic_look_alike` + `unknown` + `mixed_symptoms` + `insufficient_evidence` — `TBD — D1` | Label handbook | Agronomist | Unlabelled; never force a class | adjudicated_label | No |
| `label_origin` | text | `suspected`, `expert_confirmed`, `lab_confirmed` | Review | Agronomist | Unknown provenance; not usable as a training label | adjudicated_label | No |
| `verification_tier` | text | `confirmed`, `probable`, `unverified`, `rejected`, `duplicate`, `needs_visit`, `unresolved` | Review | Pathologist | Unverified; never treat as confirmed. Forecast eligibility is `confirmed` or `probable` with tier, inside the D7 as-of cutoffs | adjudicated_label | No |
| `review_decision` | text | `confirmed`, `probable`, `rejected`, `duplicate`, `needs_visit`, `unresolved` | Review | Pathologist | No decision | adjudicated_label | No |
| `reviewer_id` | uuid | — | Identity | Pathologist | Unknown reviewer; label not auditable | adjudicated_label | Yes |
| `review_reason_code` | text | Controlled list — `TBD` | Review | Pathologist | Not recorded | adjudicated_label | No |
| `corrected_from_label` | text | Prior label | Review | Pathologist | No correction | adjudicated_label | No |
| `severity` | text/ordinal | Crop-specific scale — `TBD — D1` | Review/agronomist | Agronomist | Unknown; do not assume zero | adjudicated_label | No |
| `label_confidence` | numeric/text | Scale `TBD` | Review | Pathologist | Unknown | adjudicated_label | No |
| `evidence_type` | text | `image_note`, `field_observation`, `lab_result` | Review | Pathologist | No evidence | adjudicated_label | No |
| `event_date` | date | ISO date; when the event occurred | User/reviewer | Agronomist | Unknown; do not substitute report date | observation | No |
| `report_date` | timestamptz | UTC; when reported | System | Data engineer | Not permitted | observation | No |
| `provenance_source` | text | Source link/identifier | Field/archive | Data engineer | Unknown; record unusable for audit | observation | No |
| `split_group_type` | text | `farm`, `field`, `collection_event`, `plant` | Data pipeline | ML lead | Unknown; cannot guarantee leakage-safe split | derivation | No |
| `split_group_id` | text | Stable group identifier | Data pipeline | ML lead | Unknown; exclude from evaluation | derivation | No |
| `is_frozen_test` | boolean | `true` / `false` | Data pipeline | ML lead | Unknown; must be `false` unless explicitly frozen | config | No |
| `frozen_at` | timestamptz | UTC | Data pipeline | ML lead | Not frozen | config | No |

---

## 8. Weather and environmental features

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `weather_snapshot_id` | uuid | — | System | Data engineer | Not permitted for a scored forecast | external | No |
| `provider` | text | `NASA POWER`, `ERA5-Land`, other approved — `TBD` | Provider | Data engineer | Unknown | external | No |
| `provider_version` | text | Provider release/model version | Provider | Data engineer | Unknown; traceability incomplete | external | No |
| `grid_id` / `station_id` | text | Provider identifier | Provider | Data engineer | Unknown; cannot match spatially | external | No |
| `grid_resolution_km` | numeric | Kilometres | Provider | Data engineer | Unknown | external | No |
| `spatial_match_method` | text | Documented method | Pipeline | Data engineer | Unknown | derivation | No |
| `match_distance_km` | numeric | Kilometres, ≥ 0 | Pipeline | Data engineer | Unknown | derivation | No |
| `source_timestamp` | timestamptz | UTC; provider observation time | Provider | Data engineer | Not permitted | external | No |
| `fetched_at` | timestamptz | UTC | System | Data engineer | Not permitted | external | No |
| `rainfall_mm` | numeric | Millimetres, ≥ 0 | Provider | Agronomist | Unknown; never `0` | external | No |
| `temp_min_c` / `temp_max_c` / `temp_mean_c` | numeric | °C | Provider | Agronomist | Unknown | external | No |
| `rh_pct` | numeric | Percent, 0–100 | Provider | Agronomist | Unknown | external | No |
| `consecutive_wet_days` | integer | Days, ≥ 0 | Derivation | Agronomist | Unknown; never `0` | derivation | No |
| `wind_ms` | numeric | Metres/second, ≥ 0 | Provider | Agronomist | Unknown | external | No |
| `leaf_wetness_proxy` | numeric/text | Definition and unit `TBD` | Provider/derivation | Agronomist | Unknown | derivation | No |
| `aggregation_window_start` / `_end` | timestamptz | UTC | Pipeline | Data engineer | Unknown | derivation | No |
| `aggregation_function` | text | `sum`, `mean`, `min`, `max`, `run_length` | Pipeline | Data engineer | Unknown | derivation | No |
| `completeness` | numeric | 0–1 | Pipeline | Data engineer | Unknown; no-score | derivation | No |
| `is_stale` | boolean | `true` / `false` | Pipeline | Data engineer | Unknown; treat as stale | derivation | No |
| `imputation_flag` | boolean | `true` / `false` | Pipeline | Data engineer | Unknown; treat as imputed | derivation | No |
| `imputation_method` | text | Documented method or `null` | Pipeline | Data engineer | Not imputed | derivation | No |

**Weather rule:** missing or stale weather produces `insufficient_data`; it is not imputed
for a scored area outlook.

---

## 9. Forecast features

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `feature_snapshot_id` | uuid | — | System | Data engineer | Not permitted | derivation | No |
| `feature_version` | text | Versioned feature config | ML pipeline | ML lead | Not permitted | config | No |
| `issue_time` | timestamptz | UTC | Scheduler | Data engineer | Not permitted | derivation | No |
| `horizon_days` | integer | `0` for nowcast or `7` for outlook — `TBD — D2` | Config | Agronomist | Not permitted | config | No |
| `days_since_planting` | integer | Days, ≥ 0 | Derivation | Agronomist | Unknown | derivation | No |
| `week_of_year` | integer | 1–53 | Derivation | ML lead | Not applicable | derivation | No |
| `monsoon_period` | text/boolean | Crop/zone definition — `TBD — D1` | Crop calendar | Agronomist | Unknown | config | No |
| `lagged_verified_cases` | integer | Count, ≥ 0 over a defined window; D7-eligible labels (`confirmed`, or `probable` with tier) only | Eligible reviews | ML lead | Unknown; never `0` | derivation | No |
| `nearby_verified_reports` | integer | Count, ≥ 0; D7-eligible labels only | Eligible reviews | ML lead | Unknown | derivation | No |
| `distance_decay_km` | numeric | Kilometres | Config | Agronomist | Not configured; feature not used | config | No |
| `prior_season_occurrence` | boolean/numeric | Definition `TBD` | Historical records | Agronomist | Unknown | derivation | No |
| `active_reporters` | integer | Count, ≥ 0 | Observations | Data engineer | Unknown | derivation | No |
| `visits` | integer | Count, ≥ 0 | Field records | Field ops | Unknown | derivation | No |
| `coverage_completeness` | numeric | 0–1 | Pipeline | Data engineer | Unknown; no-score | derivation | No |
| `surveillance_intensity` | numeric/text | Definition `TBD`; documented | Pipeline | Data engineer | Unknown; no-score | derivation | No |
| `event_definition` | text | `first_eligible_case` / `incidence_threshold` / `escalation`; exact outcome `TBD — D1/D5` | Config | Agronomist | Not permitted | config | No |
| `negative_definition` | text | Verified absence from a pre-registered sentinel-panel visit (D7); never "no report" and never "no visit" | Config | Agronomist | Not permitted | config | No |
| `sentinel_panel_version` | text | Version of the registered site list and visit schedule | Config | Field ops | Not permitted for a negative | config | No |
| `label_window_start` / `label_window_end` | date | Inclusive window in which a scheduled visit can yield a negative | Config | Field ops | Not permitted | config | No |

**Leakage rule:** every feature must be computable at `issue_time`. If it cannot be, it is
not a feature.

### 9.1 Sentinel panel and visits (D7)

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `sentinel_site_id` | uuid | — | System | Field ops | Not permitted | config | No |
| `site_geo_code` | text | Supported area code | Registered panel | Field ops | Not permitted | config | No |
| `site_precision` | text | `approximate`, `exact`; precise geometry access is role-gated | Registered panel | Field ops | Treated as approximate | config | No |
| `panel_version` | text | Monotonic version; no post-hoc site selection | Registered panel | Field ops | Not permitted | config | No |
| `visit_id` | uuid | — | System | Field ops | Not permitted | observation | No |
| `visit_date` | date | ISO date | Observer | Field ops | Not permitted | observation | No |
| `scheduled` | boolean | `true` / `false`; must be `true` to yield a negative | Registered schedule | Field ops | Treated as `false` | config | No |
| `observer_id` | uuid | — | Identity | Field ops | Unknown observer; visit not usable | observation | Yes |
| `target_code` | text | Supported target — `TBD — D1` | Label handbook | Agronomist | Not usable | observation | No |
| `observed` | text | `present`, `absent`, `indeterminate` | Observer | Pathologist | Not a negative | observation | No |
| `evidence_ref` | text | Photo/field-note reference | Observer | Field ops | Visit not auditable | observation | Potentially |

A visit is a forecast negative only when `scheduled = true`, `observed = 'absent'`, the target
is supported, the visit is inside the label window, and the D9 coverage gate passed. A missing
visit is never a negative.

---

## 10. Forecast outputs

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `forecast_id` | uuid | — | System | Data engineer | Not permitted | derivation | No |
| `risk_band` | text | `low`, `moderate`, `high`, `urgent`, `insufficient_data` | Model | Agronomist | Not permitted | derivation | No |
| `probability` | numeric(4,3) | 0–1; `null` unless calibration approved | Model | ML lead | Not calibrated/not approved | derivation | No |
| `confidence_band` | text | Proposed `low`/`medium`/`high`; confirm | Model | ML lead | Not available | derivation | No |
| `coverage` | text | `good`, `partial`, `low`, `unknown` | Pipeline | Data engineer | Unknown | derivation | No |
| `coverage_detail` | jsonb | Documented shape: verified reports, active reporters, completeness | Pipeline | Data engineer | Unknown | derivation | No |
| `drivers` | jsonb | Array of driver codes | Model | Agronomist | Not available | derivation | No |
| `reason_code` | text | No-score code: `weather_stale`, `coverage_low`, `calendar_missing`, `boundary_mismatch`, `model_not_approved` | Pipeline | Data engineer | Not applicable when scored | derivation | No |
| `valid_from` / `valid_to` | timestamptz | UTC | Config | Agronomist | Not permitted | config | No |
| `model_version` | text | Registry version | ML registry | ML lead | Not permitted | config | No |
| `is_stale` | boolean | `true` / `false` | Pipeline | Data engineer | Unknown; treat as stale | derivation | No |
| `is_demo` | boolean | `true` / `false` | System | Data engineer | Not permitted | config | No |

---

## 11. Advisory and alert data

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `advisory_id` | uuid | — | System | Agronomist | Not permitted | config | No |
| `advisory_version` | text/integer | Monotonic version | Approval workflow | Agronomist | Not permitted | config | No |
| `body_md` | text | Approved non-chemical content | Author | Agronomist | Not permitted | config | No |
| `action_types` | jsonb | `scout`, `monitor`, `sanitise`, `crop_management`, `escalate`, `record` | Author | Agronomist | Not permitted | config | No |
| `approver_id` | uuid | — | Review | Agronomist/pathologist | Not approved | adjudicated_label | Yes |
| `approved_at` | timestamptz | UTC | Review | Agronomist | Not approved | adjudicated_label | No |
| `valid_from` / `valid_to` | timestamptz | UTC; expiry mandatory | Author | Agronomist | Not permitted | config | No |
| `content_hash` | text | SHA-256 | System | Agronomist | Not permitted | derivation | No |
| `advisory_status` | text | `draft`, `review`, `approved`, `published`, `expired`, `withdrawn` | Workflow | Agronomist | Unknown; do not serve | derivation | No |
| `alert_dedupe_key` | text | Unique per area/target/band/window | System | Data engineer | Not permitted | derivation | No |
| `delivery_status` | text | `queued`, `sent`, `delivered`, `failed`, `suppressed`, `opted_out` | Provider/system | Data engineer | Unknown; do not mark sent | derivation | No |
| `feedback_rating` | text/integer | Scale `TBD` | User | Product lead | No feedback | observation | No |

---

## 12. Dataset governance and splits

| Field | Type | Unit / allowed values | Source | Owner | Missing meaning | Origin | PII |
|---|---|---|---|---|---|---|---|
| `permission_id` | text | Agreement/tracker ID | Legal | Legal/privacy | No permission; dataset not usable | config | No |
| `permitted_use` | text | Exact purposes | Agreement | Legal/privacy | No permission; not usable | config | No |
| `retention_rule` | text | Approved period/trigger | Retention schedule | Legal/privacy | Unset; dataset cannot be cleared | config | No |
| `update_schedule` | text | Frequency/owner | Agreement | Data engineer | Unknown | config | No |
| `quality_check_id` | text | Versioned check set | Data pipeline | Data engineer | Not checked; not model-ready | config | No |
| `split_manifest_id` | text | Versioned manifest | Data pipeline | ML lead | No split; not usable for evaluation | config | No |
| `split_group_type` | text | `farm`, `field`, `collection_event`, `plant` | Data pipeline | ML lead | Unknown; leakage risk | config | No |
| `freeze_date` | timestamptz | UTC | Data pipeline | ML lead | Not frozen | config | No |
| `checksum` | text | SHA-256 | Data pipeline | Data engineer | Unknown; integrity unverified | derivation | No |
| `dataset_status` | text | `candidate`, `requested`, `under_review`, `cleared`, `restricted`, `expired`, `rejected`, `not_acquired` | Register | Data engineer | Not cleared | config | No |

---

## 13. Unresolved fields — do not invent values

| Field / decision | Blocked on | Owner |
|---|---|---|
| Supported crop list | D1 | Agronomist + product lead |
| Target class list and taxonomy | D1 | Agronomist |
| `healthy`, `abiotic_look_alike`, `unknown`, mixed/insufficient labels | D1 | Agronomist |
| Severity scale | D1 | Agronomist |
| Crop calendar and stage windows | D1 | Agronomist |
| Geography, boundary source and levels | D1 | Data engineer |
| Horizon (`0` nowcast vs `7` days) | D2 | Agronomist + ML lead |
| Event definition | D1/D5 | Agronomist + product lead |
| Weather thresholds | Local validation | Agronomist |
| Quality-gate score scales and thresholds | Model validation | ML lead |
| Label confidence scale | Labelling handbook | Agronomist |
| Retention periods | Legal/D10 | Legal + programme lead |
| Consent jurisdiction, controller and contact | Legal/D10 | Legal |
| Notification channel allowlist | Pilot partner | Product lead |
| Device class, lighting, background, framing categories | Capture protocol | Field ops |
| Imputation policy details | Data foundation review | Data engineer + agronomist |

---

## 14. Prohibited data practices

- No real farmer data in tests, fixtures, demos or screenshots.
- No forced class for an unlabelled or ambiguous image.
- No `-1`/`999`/empty-string missing markers.
- No imputation of weather for a scored outlook.
- No unverified report used as a confirmed forecast feature.
- No label overwritten without an audit record.
- No precise location in dashboards, exports or logs.
- No fabricated metrics, dataset sizes, partner names or thresholds.
- No chemical names, doses, mixtures or intervals in advisory content.

---

## 15. Change log

| Date | Change | Owner |
|---|---|---|
| 2026-11-06 | Data dictionary v1 drafted; field contract only; D1/D2-dependent values left TBD | Draft — data engineer (TBD) |
