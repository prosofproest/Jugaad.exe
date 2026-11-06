# Dataset register

**Status:** Draft — no dataset is cleared for use.
**Owner:** Data engineer (TBD)
**Last updated:** 2026-11-06
**Authority:** `final/docs-context/phase-plan.md` §4.1 and §4.3;
`final/docs-context/data-foundation.md` §2.

> A dataset is not usable because it exists. It is usable only when its owner,
> permission, permitted use, retention rule, update schedule and quality check are
> recorded and the status is `cleared`.

---

## 1. Register rules

1. Every dataset gets a stable ID (`DS-###`). IDs are never reused.
2. No dataset may be used for training, evaluation, forecasting or demonstration before
   its status is `cleared`.
3. `cleared` requires a signed permission record. A verbal assurance, email in a
   personal inbox, public download link or "it is publicly available" is not a
   permission record.
4. Public datasets may be used for pretraining and benchmarking only. They are never the
   field validation set.
5. Retention and update schedule are `TBD` until the owning institution and legal position
   are settled (D4 for the institution, D10 for the data controller and retention policy).
6. Annotation, split role and version are recorded per dataset version, not only per
   dataset.
7. A dataset containing real personal data, farm-identifying images or exact locations
   must never appear in tests, fixtures or demo content.

---

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| `candidate` | Identified but not requested and not in hand |
| `requested` | Agreement or access requested |
| `under_review` | Legal, privacy or data-quality review in progress |
| `cleared` | Signed permission recorded; use allowed exactly as stated |
| `restricted` | Cleared with conditions or exclusions |
| `expired` | Permission lapsed; use must stop |
| `rejected` | Not usable; reason recorded |
| `not_acquired` | No data in hand |

---

## 3. Register

| ID | Dataset / source | Family | Status | Permission record | Permitted use | Owner | Retention rule | Update schedule | Quality check |
|---|---|---|---|---|---|---|---|---|---|
| DS-001 | Partner-collected field images | Field images | `candidate` | None — not executed | None yet | TBD | TBD | TBD | TBD |
| DS-002 | Plant-clinic / university archive images | Archive images | `candidate` | None — not executed | None yet | TBD | TBD | TBD | TBD |
| DS-003 | Public field image datasets (PlantDoc, Cassava, Rice Leaf, AgriPest, IP102) | Public field images | `candidate` | Licence terms not recorded | Pretraining / benchmarking only; never validation | TBD | Follow publisher terms (not recorded) | Per publisher release | Licence and checksum verification |
| DS-004 | Public laboratory image datasets (PlantVillage-style) | Public lab images | `candidate` | Licence terms not recorded | Pretraining / benchmarking only; never validation | TBD | Follow publisher terms (not recorded) | Per publisher release | Licence and checksum verification |
| DS-005 | Farmer-submitted pilot reports and images | Field reports | `not_acquired` | Consent not yet implemented | None yet | TBD | TBD | Continuous during pilot | Consent, quality gate, provenance |
| DS-006 | Weather: NASA POWER / ERA5-Land | Weather | `candidate` | Terms not recorded | Area outlook only; never a label | TBD | TBD | TBD | Source timestamp, completeness, freshness |
| DS-007 | Administrative boundaries | Boundaries | `candidate` | Licence not recorded | Aggregation, mapping, area scoping | TBD | TBD | Versioned releases | Geometry validity, code stability, version |
| DS-008 | Soil: SoilGrids (optional) | Environmental | `candidate` | Terms not recorded | Context feature only; not v1-critical | TBD | TBD | Per provider release | Resolution, coverage, units |
| DS-009 | Satellite: Sentinel-2 (deferred) | Environmental | `not_acquired` | Not applicable in v1 | Out of v1 scope | TBD | TBD | Not applicable | Not applicable |
| DS-010 | Historical occurrence records | Historical labels | `candidate` | Permission not recorded | Forecast features after verification only | TBD | TBD | TBD | Provenance, event vs report date, dedupe |
| DS-011 | Expert-approved advisories | Advisory content | `not_acquired` | Authored internally; approval workflow required | Advisory retrieval only | TBD | Versioned; expiry mandatory | On approval | Agronomic and legal approval, validator |
| DS-012 | Demo / synthetic fixtures | Demo only | `restricted` | Internal | Demo and testing only; never operational | TBD | Until demo reset | On schema change | `is_demo` label, no real identifiers |

**No row is `cleared`.** This is intentional: no permission records exist yet.

---

## 4. Required detail per dataset version

When a dataset moves beyond `candidate`, record all of the following in the register
entry or a linked permission record:

| Field | Requirement |
|---|---|
| Dataset ID and version | Stable ID plus semantic version or provider release |
| Source and owner | Named institution and named internal data owner |
| Permission record | Signed MoU, licence, terms acceptance or equivalent, with location |
| Permitted use | Exact purposes; explicitly state prohibited uses |
| Model role | Pretraining, training, validation, test, benchmark, or not machine learning |
| Redistribution | Whether derivatives or models may be shared or published |
| Retention | Period and deletion trigger |
| Update schedule | Frequency and responsible party |
| Quality check | Automated and manual checks, plus acceptance criteria |
| Sensitivity | Personal data, farm-identifying images, precise location, commercial sensitivity |
| Geography and time coverage | Where and when the data applies |
| Provenance | Source link, collection method, original labels, reviewer identity where permitted |
| Checksum | Content hash for the received version |
| Split manifest | Grouping rule and split version if used for modelling |
| Quarantine status | Count of quarantined records and open resolutions |

---

## 5. Intake procedure

1. Assign the next `DS-###` ID.
2. Record the source, owner and intended use.
3. Start the agreement in `02-mou-licence-tracker.md`.
4. Obtain legal/privacy review for any personal or farm-identifying data.
5. Record permitted use, retention and update schedule.
6. Define the quality checks and the quarantine path before ingestion.
7. Ingest a small sample; run quality checks; record the result.
8. Attach the signed permission record and mark `cleared` or `restricted`.
9. Record the dataset version, checksum and split role.
10. Re-review at the recorded expiry or when the provider changes terms.

---

## 6. Current gaps

- No permission records exist for any dataset.
- No named data owner exists yet.
- Retention periods are unset because the data controller (D10), owning institution (D4) and
  legal position are unresolved.
- Weather provider terms, boundary licence and archive access are unverified.
- Public dataset licences have not been checked against the intended use.
- The project taxonomy and crop/target list are unresolved (D1), so label compatibility
  cannot be assessed.
- No split manifest or frozen test set exists.

---

## 7. Change log

| Date | Change | Owner |
|---|---|---|
| 2026-11-06 | Register created with candidate rows; no dataset cleared | Draft — Data engineer (TBD) |
