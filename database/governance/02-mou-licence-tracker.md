# MoU and licence tracker

**Status:** Draft — zero agreements executed.
**Owner:** Programme lead + legal (TBD)
**Last updated:** 2026-11-06
**Linked register:** `01-dataset-register.md`

> **Execution boundary:** an AI agent cannot sign, execute, vary or accept an agreement
> on behalf of the project. This tracker records what must be obtained, from whom, with
> which clauses, and where the signed record will live. Only an authorised human
> signatory may move an item to `executed`.

---

## 1. Status vocabulary

| Status | Meaning |
|---|---|
| `not_started` | No contact or request yet |
| `requested` | Agreement requested from the counterparty |
| `negotiating` | Terms under discussion |
| `legal_review` | With project legal/privacy counsel |
| `awaiting_signature` | Final text agreed; signatures pending |
| `executed` | Signed by all parties; record stored; effective date set |
| `expired` | Past expiry; use must stop until renewed |
| `declined` | Counterparty declined or terms unacceptable |

---

## 2. Tracker

| Dataset ID | Agreement type | Counterparty | Status | Signed by | Effective | Expiry | Record location | Notes |
|---|---|---|---|---|---|---|---|---|
| DS-001 | MoU + data-sharing schedule | TBD | `not_started` | — | — | — | — | Partner-collected field images |
| DS-002 | Archive access / licence | TBD | `not_started` | — | — | — | — | Plant-clinic or university archive |
| DS-003 | Public dataset licence review | Publisher (TBD per dataset) | `not_started` | — | — | — | — | Verify each licence; no field validation |
| DS-004 | Public dataset licence review | Publisher (TBD per dataset) | `not_started` | — | — | — | — | Pretraining/benchmarking only |
| DS-005 | Consent + terms of use | Farmer / field staff | `not_started` | — | — | — | — | Consent wording pending approval |
| DS-006 | Weather provider terms | Provider (TBD) | `not_started` | — | — | — | — | NASA POWER / ERA5-Land terms to confirm |
| DS-007 | Boundary dataset licence | Authority (TBD) | `not_started` | — | — | — | — | Versioning and redistribution rights |
| DS-008 | Soil dataset terms (optional) | Provider (TBD) | `not_started` | — | — | — | — | Optional context only |
| DS-010 | Historical records agreement | Record holder (TBD) | `not_started` | — | — | — | — | Permission and verification tier |
| DS-011 | Internal advisory approval | Internal authors/approvers | `not_started` | — | — | — | — | Not a third-party licence |

No counterparty names, dates or signatures are invented. All unknown fields are `TBD`.

---

## 3. Required clauses

Every third-party data agreement should address the clauses below. Legal counsel decides
the final wording; this checklist prevents omissions.

### 3.1 Purpose and scope

- [ ] Named parties and authorised signatories.
- [ ] Dataset description, version and delivery method.
- [ ] Exact permitted purposes.
- [ ] Explicit prohibited purposes.
- [ ] Whether use for model training is allowed.
- [ ] Whether use for evaluation or benchmarking is allowed.
- [ ] Whether commercial use is allowed or excluded.

### 3.2 Ownership and rights

- [ ] Data ownership remains with the source or is transferred as stated.
- [ ] Project ownership of derived labels, features and models is stated.
- [ ] Attribution requirements and citation format.
- [ ] Redistribution rights for data, derivatives and trained models.
- [ ] Publication rights for aggregate results and case studies.
- [ ] Whether the counterparty can withdraw permission and what happens to derived work.

### 3.3 Privacy and ethics

- [ ] Whether the dataset contains personal data or farm-identifying information.
- [ ] Lawful basis and consent evidence supplied by the counterparty.
- [ ] Whether images contain people, faces, documents or unrelated personal information.
- [ ] Whether precise location is included and whether it may be used.
- [ ] De-identification obligations and re-identification prohibition.
- [ ] Data-subject request handling responsibilities.

### 3.4 Security and incidents

- [ ] Storage location and access controls.
- [ ] Encryption in transit and at rest.
- [ ] Subprocessors and cross-border transfers.
- [ ] Breach notification timeline and contact.
- [ ] Audit or inspection rights.
- [ ] Return or destruction of data on termination.

### 3.5 Retention and deletion

- [ ] Retention period for the original data.
- [ ] Retention period for derivatives and model artefacts.
- [ ] Deletion method and evidence.
- [ ] Backup handling and propagation delay.
- [ ] Legal hold exceptions.

### 3.6 Commercial and liability

- [ ] Fees, if any, and payment terms.
- [ ] Liability and indemnity.
- [ ] Warranty of the right to share the data.
- [ ] Governing law and jurisdiction.
- [ ] Dispute resolution.
- [ ] Term, renewal and termination notice.

---

## 4. Execution workflow

1. **Identify the owner.** Name the counterparty and the internal accountable owner.
2. **Classify the data.** Personal, farm-identifying, precise location, commercial or
   public.
3. **Select the instrument.** MoU, data-sharing agreement, licence, terms acceptance or
   internal approval.
4. **Draft from the clause checklist.** Use project legal counsel; do not copy an
   unrelated agreement.
5. **Review.** Privacy/legal review for any personal or location data.
6. **Sign.** Authorised signatories only.
7. **Store.** Save the signed record in the agreed repository with access control.
8. **Register.** Update `01-dataset-register.md` with permitted use, retention, update
   schedule and status.
9. **Diarise.** Record the expiry and review date.
10. **Re-review.** Re-check on expiry, provider change or scope change.

---

## 5. Evidence standard for "executed"

An item is `executed` only when all of these exist:

- a complete signed agreement, or an accepted online licence with the acceptance record;
- the effective date and expiry;
- the named signatories;
- the permitted-use statement;
- the storage location of the record;
- the linked dataset ID and version;
- confirmation that legal/privacy review is complete where required.

A public URL, a download, an email from a colleague, or a verbal statement is not
sufficient.

---

## 6. Open issues

- No counterparties have been identified in the repository.
- The owning institution (D4) is unresolved.
- The pilot geography (D1) is unresolved, which affects boundary and archive sources.
- Legal jurisdiction and the applicable data-protection regime are unresolved.
- Weather, boundary and public-dataset licences have not been checked.
- No signature authority has been recorded.
- No record repository or retention schedule exists yet.
