# Collection progress tracking

**Version:** `v1.0-draft`
**Status:** Draft — no collection has started.
**Owner:** Data engineer (TBD) + Field operations lead (TBD)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.2, §4.3, §4.8;
`final/docs-context/data-foundation.md` §2, §3.1;
`02-sampling-matrix.md`.

> **Rule:** progress is **coverage of the sampling matrix**, not a total image count.
> "We have 12,000 images" is not a progress statement. "Tier A cells met: 34 of 60; Tier B
> device quota unmet on `DEV-LOW`" is.

---

## 1. Why total counts mislead

A total count can rise while the dataset becomes less useful:

- every new image may come from the same district, crop and phone;
- duplicates and re-takes inflate the count;
- rejected images may be hidden from the denominator;
- archive images may be counted as field data;
- advanced symptoms are easier to photograph, so early symptoms are missed;
- hard negatives and healthy controls do not appear unless deliberately collected.

The tracking model therefore counts **accepted cases per matrix cell**, and reports the
excluded records separately.

---

## 2. Counting unit

| Unit | Definition |
|---|---|
| **Case** | One observation (`observation_id`), one plant/area, one visit |
| **Accepted case** | A case that passed consent, metadata and quality requirements and has at least one usable image |
| **Accepted image** | An image with a quality result of `pass` and no open quarantine |
| **Excluded** | Quarantined, rejected, duplicate, unconsented or metadata-incomplete records |

**Cases, not images, fill the matrix.** Extra shots within one case do not add coverage.
A case can satisfy more than one cell (for example a Tier A cell and a Tier B lighting
quota), but it is counted once in case totals.

---

## 3. Progress model

For every required cell in `02-sampling-matrix.md`:

```
n_accepted   = accepted cases matching every constrained stratum
n_quarantined = quarantined records matching the cell
coverage     = n_accepted / n_min
status       = not_started | unmet | partial | met | exceeded | not_applicable | blocked
```

Aggregate progress:

| Metric | Definition |
|---|---|
| **Cell coverage rate** | Cells with `status = met` ÷ required cells |
| **Cell touch rate** | Cells with `n_accepted > 0` ÷ required cells |
| Tier A coverage | Tier A cells met ÷ Tier A cells |
| Tier B quota coverage | Tier B strata at quota ÷ Tier B strata |
| Tier D coverage | Special strata at quota ÷ special strata |

**The headline number is cell coverage rate, not total images.**

---

## 4. Required views

These views are required for the weekly review. Until the platform exists they are produced
from a versioned tracking sheet, clearly marked **provisional**.

### 4.1 Matrix heatmap

One row per cell, one column per status, with `n_accepted` and `n_min`. Colour by status.
This is the primary view. A total count may appear in a footer, never as the headline.

### 4.2 Coverage by dimension

| View | Question it answers |
|---|---|
| District × condition | Which districts lack a condition? |
| Season × severity | Are early symptoms captured across seasons? |
| Crop × target | Which crop/condition pairs are thin? |
| Lighting × device | Are we only collecting in good light on good phones? |
| Background × context | Are farmer-submitted backgrounds represented? |
| Variety × plant age | Which varieties and ages are missing? |

### 4.3 Class balance

Counts for `T-HEALTHY`, each target class, `T-ABIOTIC`, `T-PEST`, `T-MIXED`, `T-UNKNOWN`,
`T-HARDNEG`, and rejected images. Report the share of total accepted cases.

### 4.4 Quality funnel

```
captured shots
  → submitted
  → upload confirmed
  → quality pass / fail
  → metadata complete
  → consent valid
  → accepted case
  → quarantined / rejected / duplicate
```

Every stage has a count and a reason distribution. The funnel must reconcile: the sum of
exits equals the input minus the output.

### 4.5 Throughput trend

Cases per collector-day, median time per case and upload success over time. A falling trend
is investigated; it is not averaged away.

### 4.6 Gap list

Every `unmet`, `blocked` or `not_applicable` cell with:

- cell ID;
- reason;
- owner;
- action (schedule, reallocate, procure, record limitation);
- review date.

---

## 5. Metric definitions

| Metric | Formula | Notes |
|---|---|---|
| Required cells | Count of cells with `tier` in scope | Includes `blocked` and `not_applicable` in the denominator until formally waived |
| Cells met | `status = met` | |
| Cell coverage rate | `cells_met / required_cells` | Headline |
| Cases collected | All submitted cases | Not a progress headline |
| Cases accepted | Accepted cases | |
| Acceptance rate | `cases_accepted / cases_submitted` | |
| Image acceptance rate | `accepted_images / submitted_images` | |
| Quarantine rate | `quarantined / ingested` | By reason |
| Duplicate rate | `duplicates / submitted_images` | |
| Metadata completeness | Cases with all required fields ÷ submitted cases | |
| Silent losses | Queued cases never uploaded and never reported | Must be zero |
| Special-stratum share | `T-HEALTHY` + `T-ABIOTIC` + `T-MIXED` + `T-UNKNOWN` + `T-HARDNEG` ÷ accepted | Should not trend to zero |
| Farmer-context share | `CTX-FARMER` ÷ accepted | Deployment condition |
| Low-device share | `DEV-LOW` ÷ accepted | Realistic device |
| Projection to target | Based on the last `N` days, per cell | Never project from total counts |

`N` for the projection window is `TBD`.

---

## 6. Cadence and owners

| Cadence | Output | Owner |
|---|---|---|
| Daily (collection days) | Queue state, upload failures, silent-loss check | Field ops |
| Per batch | Quality funnel, quarantine reasons, accepted counts | Data engineer |
| Weekly | Matrix heatmap, gap list, throughput trend | Field ops + data engineer |
| Monthly | Coverage against plan, reallocation decisions | Programme lead |
| Phase checkpoint | Full coverage report, limitations, Gate 1 evidence | Programme lead + data engineer |

A report without a denominator, a date and a matrix version is not accepted.

---

## 7. Source of truth

1. **Primary:** database queries over `observations`, `image_assets`,
   `image_quality_results`, quarantine records and consent records.
2. **Secondary:** app telemetry for retries, crashes and queue state.
3. **Provisional:** a versioned tracking sheet, used only before the platform exists. It must
   carry `provisional = true`, the matrix version, the date and the owner. It is reconciled
   with system records before any external report.

Spreadsheet-only tracking is a known risk: it drifts, duplicates and hides exclusions. It is
temporary and must be replaced before scale-up.

---

## 8. Anti-gaming rules

The following are prohibited. Each one makes the progress report invalid.

- Counting images instead of cases.
- Counting re-takes, duplicates or rejected images as accepted.
- Counting archive images as field coverage.
- Counting stock, borrowed or downloaded images at all.
- Counting unconsented or metadata-incomplete cases as accepted.
- Removing rejected images from the denominator.
- Lowering `n_min` after seeing results.
- Marking a cell `met` when its cases fail the quality gate.
- Counting the same case in multiple cells for case totals.
- Reporting a single aggregate number without per-cell coverage.
- Projecting completion from a total count.

---

## 9. Escalation

| Trigger | Action | Owner |
|---|---|---|
| A required cell is `unmet` at the weekly review | Assign an action and a date | Field ops |
| A cell is `blocked` for two reviews | Escalate to programme lead; record a limitation or change the plan | Programme lead |
| `DEV-LOW` or `CTX-FARMER` share below quota | Rebalance collection before adding volume | Field ops |
| Special-stratum share falling | Add deliberate prompts; do not rely on chance | Field ops + agronomist |
| Silent losses > 0 | Stop collection; fix the queue | Data engineer |
| Quarantine backlog ageing past target | Escalate per `../governance/06-quarantine-policy.md` | Data owner |
| Acceptance rate falling | Diagnose the funnel stage; revise protocol or training | Field ops + data engineer |

---

## 10. Report template

```md
# Collection progress — <date>

Matrix version: <v>
Protocol version: <v>
Reporting period: <from> to <to>
Provisional: <yes/no>

## Headline
- Cell coverage rate: <met>/<required> (<%>)
- Tier A: <met>/<required>
- Tier B quota: <met>/<required>
- Special strata: <met>/<required>

## Accepted volume (context only)
- Cases submitted: <n>
- Cases accepted: <n>
- Images accepted: <n>
- Acceptance rate: <n>

## Excluded
- Quarantined: <n> (top reasons)
- Rejected: <n>
- Duplicates: <n>
- Metadata incomplete: <n>
- Consent invalid: <n>
- Silent losses: <n>  (must be 0)

## Coverage
<table or link to heatmap>

## Gaps
| cell_id | status | reason | owner | action | review date |

## Risks
- ...

## Decisions requested
- ...
```

---

## 11. Gate 1 evidence

At the Phase 1 checkpoint this document contributes:

- the matrix version and `n_min` derivation;
- coverage by cell, tier and dimension;
- the accepted/excluded funnel with denominators;
- the special-stratum counts;
- the device and farmer-context shares;
- the list of `blocked` cells and recorded limitations;
- the protocol revisions and their triggers.

A total image count is not Gate 1 evidence.

---

## 12. Acceptance criteria

- [ ] Progress is reported as cell coverage, with a matrix version and a date.
- [ ] Cases, not images, are the counting unit for coverage.
- [ ] Accepted and excluded records are reported separately.
- [ ] Rejected and duplicate images remain in the denominator.
- [ ] Archive data is excluded from field coverage.
- [ ] Special strata are reported individually.
- [ ] Silent losses are measured and are zero.
- [ ] Every gap has an owner, an action and a review date.
- [ ] The funnel reconciles: input = accepted + excluded.
- [ ] `n_min` changes are versioned and never made to flatter a result.
- [ ] Provisional spreadsheet tracking is labelled and replaced before scale-up.
