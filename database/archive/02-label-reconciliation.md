# Archive label reconciliation

**Version:** `v1.0-draft`
**Status:** Draft — **no archive label has been seen, mapped or reconciled.**
**Owner:** Pathologist (taxonomy and label correction — D13), with Data engineer (pipeline)
and Agronomist (crop advice, **no verification authority**)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.3;
`final/docs-context/data-foundation.md` §8.2, §8.5;
`final/docs-context/AGENTS.md` R4, R6;
`final/feature-specs/04-expert-review.md`;
`final/feature-specs/05-data-layer.md`;
`final/docs-context/progress-tracker.md` D1, D13.

> **Boundary:** the project taxonomy is not fixed yet (D1). This document defines the
> *process* for mapping archive labels onto it once D1 is recorded. It does not invent
> class names, synonyms, severity scales or crop targets.

---

## 1. Why reconciliation is a separate step

An archive label was written by another institution, in another language, under another
taxonomy, at another time, possibly for a different purpose. It cannot be copied into
`target_code`. Doing so would silently import a foreign label scheme and make the training
set un-auditable.

Reconciliation is therefore an explicit, versioned, human-reviewed transformation:

```
archive original label
  → normalise (language, spacing, spelling only — meaning preserved)
  → candidate match to project taxonomy
  → pathologist decision: mapped / partially mapped / unmappable / conflict
  → mapped_label (+ taxonomy_version, reviewer, date, rationale)
  → quarantine any record that is not a clean map
```

The **original label is never overwritten**. The mapped label is a separate field.

---

## 2. Taxonomy pinning

1. Every mapping is made against one **named taxonomy version**.
2. The taxonomy version is resolved by **D1** (crop, targets, zone) and approved by the
   pathologist; it is not inferred from an archive. Class meaning, `class_kind` and boundary
   cases follow the labelling handbook (`../labelling/01-labelling-handbook.md`).
3. A mapping records `taxonomy_version` and `label_scheme_version`.
4. No mapping is made against an unversioned or draft taxonomy.
5. If the taxonomy changes later, the mapping is **re-run as a new version**. Existing
   mappings are never edited in place; the old mapping is retained with its version.
6. A change to the taxonomy is a change to the dataset; it requires a new dataset version
   and a new reconciliation report.

**Current state:** the taxonomy does not exist (D1 unresolved), so every archive mapping is
blocked. `mapped_label` may not be populated until D1 is recorded.

---

## 3. Mapping status vocabulary

| Status | Meaning | Downstream use |
|---|---|---|
| `exact` | Original label maps one-to-one to a project class | Usable as a label |
| `broad` | Original label is broader than a project class; mapped only if the project class is a safe superset | Usable only if the direction of error is recorded and accepted |
| `narrow` | Original label is narrower than a project class; mapped only with explicit approval | Usable only if approved; otherwise `partial` |
| `partial` | Only part of the original meaning maps; a qualifier is preserved | **Not** a clean training label without pathologist approval |
| `unmappable` | No defensible mapping to the project taxonomy | Quarantined; never forced into a class |
| `conflict` | Archive label contradicts the image, metadata or another label for the same record | Quarantined; pathologist review |
| `pending` | Not yet reviewed | Not usable |
| `not_applicable` | Record is out of scope (wrong crop, non-disease, non-image) | Excluded with a reason |

Only `exact` is a clean default. Any other status needs a recorded rationale and an
approver. `unmappable` is a **valid outcome**, not a failure of the reviewer.

---

## 4. Decision rules

1. **Never force a label.** If the mapping is not defensible, record `unmappable`.
2. **Never merge on similarity alone.** A near-synonym in another language is not a match
   until a pathologist confirms it.
3. **Preserve ambiguity.** If the archive says "leaf spot" without a causal agent, do not
   map it to a specific pathogen class; use `partial` or `unmappable`.
4. **Healthy and abiotic look-alikes are classes, not a default.** Do not map an unknown
   image to `healthy` or `abiotic_look_alike` to keep it in the dataset.
5. **Severity is separate from identity.** A mapped class does not imply a severity value;
   severity follows the project scale and is `TBD — D1`.
6. **One record, one primary label.** If the archive lists multiple conditions, record them
   as a multi-label conflict, not as one arbitrary choice.
7. **Crop gate first.** If the crop is unsupported (`crop_unknown`), stop; do not map the
   disease.
8. **Region and era do not change the label.** They are recorded as covariates, not as a
   reason to remap.
9. **The mapped label must be reproducible** from the original label, the mapping table
   version and the taxonomy version.

---

## 5. Reviewer identity and authority

| Action | Role | Authority |
|---|---|---|
| Propose a mapping | Data engineer or trained reviewer | No approval |
| Approve a mapping | **Pathologist** | Final |
| Advise on crop/agronomy | Agronomist | Advisory only — **cannot** approve a label |
| Resolve a conflict against the image | **Pathologist** | Final |
| Set `confirmed` verification tier | **Pathologist** | Sole authority (D13) |
| Approve taxonomy version | Pathologist + product lead, after D1 | Required |

Every mapping stores `mapped_by`, `mapped_at`, `reviewed_by`, `reviewed_at` and
`mapping_rationale`. A mapping without a named pathologist reviewer is `pending`, not
approved. Reviewer identities are personal data: store the account ID, not a name or phone
number, and expose it only to authorised roles.

---

## 6. Unmappable records

An unmappable record is **not** discarded.

1. Quarantine with reason `label_unmappable` (`../governance/06-quarantine-policy.md`).
2. Preserve the original label, image, source link and provenance exactly.
3. Record the closest candidate class (if any) and why it was rejected.
4. Record whether the gap is a **taxonomy gap** (the project lacks the class) or a
   **label-quality gap** (the archive label is insufficient).
5. A taxonomy gap is fed back to D1 as evidence; it is not resolved by inventing a class.
6. Re-review is allowed if the taxonomy later adds a defensible class; the record is then
   remapped under a new version, with the old decision retained.
7. Unmappable records may be used for **unsupervised pretraining** only if the permission
   record allows it and no label is asserted. They are never used as labelled training,
   validation or test data.

### 6.1 Conflict records

`label_conflict` is quarantined and escalated to the pathologist. Resolution is one of:
`mapped` (with reason), `rejected`, or `unmappable`. A conflict is never resolved by
majority vote among archive metadata fields.

---

## 7. Mapping table (proposed)

The mapping table is configuration, versioned and reviewed. It is not embedded in code.

| Field | Type | Requirement |
|---|---|---|
| `mapping_id` | uuid | Primary key |
| `taxonomy_version` | text | Required; pins the target taxonomy |
| `handbook_version` | text | Labelling handbook version used for the mapping |
| `label_scheme_version` | text | Archive scheme and version |
| `source_id` | text | `ARC-###` |
| `original_label` | text | Verbatim, original language |
| `original_language` | text | ISO code or `unknown` |
| `original_label_code` | text | Archive's own code, if any |
| `normalised_label` | text | Spacing/spelling only; meaning preserved |
| `mapped_label` | text | Project class, or `null` when unmappable |
| `mapping_status` | text | `exact`, `broad`, `narrow`, `partial`, `unmappable`, `conflict`, `pending`, `not_applicable` |
| `mapping_rationale` | text | No PII; states the evidence and direction of error |
| `confidence` | numeric/text | Scale `TBD`; never used to auto-approve |
| `mapped_by` | uuid | Proposer |
| `mapped_at` | timestamptz | UTC |
| `reviewed_by` | uuid | Pathologist account ID |
| `reviewed_at` | timestamptz | UTC |
| `supersedes_mapping_id` | uuid | Previous version, if re-mapped |
| `notes` | text | No PII |

---

## 8. Metrics

Reported per archive batch and per source, with denominators:

- records received, mapped, partial, unmappable, conflicting, pending;
- mapping status counts by class and by archive scheme;
- **unmappable rate** = unmappable / received (never hidden by dropping records);
- conflict rate and resolution time;
- taxonomy-gap count (evidence for D1), separate from label-quality gaps;
- re-map count after a taxonomy version change.

A high unmappable rate is a finding about taxonomy fit or archive quality. It is not
something to improve by loosening the rules.

---

## 9. What must never happen

- Copying an archive label into `target_code` without reconciliation.
- Overwriting the original label.
- Forcing an unmappable record into the nearest class.
- Mapping to an unversioned or unapproved taxonomy.
- Letting an agronomist or an AI agent approve a label.
- Using `pending` or `conflict` records as training labels.
- Deleting a record because it could not be mapped.
- Reporting a mapping accuracy or unmappable rate without a denominator.
- Re-mapping historical records in place without a new version.

---

## 10. Acceptance criteria

- [ ] Every archive record has an original label and a mapping status, or a recorded reason
      why not.
- [ ] Every mapping names a `taxonomy_version` and `handbook_version`.
- [ ] Every approved mapping names a pathologist reviewer.
- [ ] Unmappable and conflicting records are quarantined, preserved and counted.
- [ ] No unmappable record is forced into a class or deleted.
- [ ] Mapping and unmappable rates are reported with denominators.
- [ ] Re-mapping creates a new version; history is retained.
- [ ] No archive label is treated as a field label.
- [ ] Taxonomy gaps are recorded as D1 evidence, not invented classes.
