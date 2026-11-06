# Model card — <model_version>

> **<SYNTHETIC FIXTURE | REAL MODEL> — <NOT FOR FIELD USE | REVIEW STATUS>.**
> State plainly whether this card describes pipeline verification or a model that
> was evaluated on licensed data. Never present fixture numbers as performance.

## Intended use

- <what the model may be used for, at which operating point and for which crop/target set>

## Not intended for

- <explicit exclusions: diagnosis, chemical advice, other crops, unvalidated regions, ...>

## Data

| Field | Value |
|---|---|
| Dataset id | `<dataset_id>` |
| Fixture kind | `<synthetic_fixture | field_dataset>` |
| Licence | `<licence>` |
| Provenance | `<provenance>` |
| Items / groups | `<count>` / `<count>` |
| Data fingerprint | `<sha256>` |
| Split fingerprint | `<sha256>` |

### Split sizes

| Split | Items |
|---|---|
| train | `<count>` |
| val | `<count>` |
| test | `<count>` |

## Model

| Field | Value |
|---|---|
| Family / architecture | `<...>` |
| Version | `<...>` |
| Feature/preprocessing contract | `<...>` |
| Taxonomy version | `<...>` |
| Calibration version | `<... or NOT FITTED>` |
| Operating point (D8) | `<... or NOT CHOSEN>` |
| Artefact sha256 | `<sha256>` |

## Evaluation

| Metric | Value | Provenance |
|---|---|---|
| Macro F1 | `<...>` | `<synthetic_fixture | validation | field_test>` |
| Top-1 accuracy | `<...>` | `<...>` |
| Abstention rate | `<...>` | `<...>` |
| ECE / Brier / NLL | `<... or NOT APPROVED>` | `<...>` |

Per-class precision, recall, F1, support and confusion matrix: `<link or table>`.

Subgroup analysis (crop, region, device, lighting): `<link or NOT DONE>`.

## Promotion status

`<trained | evaluated | approved>` — approved by `<name/role>` on `<date>`.
Synthetic fixtures stop at `evaluated`; they can never be approved.

## Limitations

- <class imbalance, geography, device, lighting, labelling uncertainty, ...>
- <what the model abstains on and how often>
- <known failure modes>

## Reproduction

```bash
<exact command, commit SHA, seed and artefact path>
```
