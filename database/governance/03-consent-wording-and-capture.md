# Consent wording and capture design

**Status:** Draft — requires legal, privacy and local-language review before use.
**Owner:** Programme lead + legal/privacy (TBD)
**Last updated:** 2026-11-06
**Build phase:** Design now; implementation in Phase 2 (identity module).
**Authorities:** `final/feature-specs/03-auth-and-roles.md` §5–7;
`final/docs-context/data-foundation.md` §3.3; `final/feature-specs/05-data-layer.md` §4.1.

> **Boundary:** this is plain-language drafting support, not legal advice. The wording,
> lawful basis, controller identity, contact details, retention periods and local-language
> translation must be approved by the responsible legal/privacy owner before use.

---

## 1. Design principles

- Consent is captured **before the first report**.
- Required consent is not bundled with optional consent.
- Optional research consent is off by default and never gates core functionality.
- Withdrawal is as easy as granting.
- The exact text shown is versioned and hashed; changing the text requires re-consent.
- Consent records are append-only; withdrawal is a new event, not an overwrite.
- Consent is not a substitute for the other safety rules: no chemical advice, no
  diagnosis claim, no confirmed-outbreak claim.
- A user can read the wording without granting it.
- A user cannot submit a report while a required consent is missing or outdated.

---

## 2. Consent types

| Code | Type | Required | Gates reporting | Revocable | Purpose |
|---|---|---|---|---|---|
| `service_privacy` | Service terms and privacy notice | Yes | Yes | Yes, but withdrawal ends service use | Explain what is collected, why, who sees it, retention and rights |
| `image_assessment` | Image analysis and storage | Yes | Yes | Yes | Analyse the submitted image and store it with the case |
| `approximate_location` | Approximate location use | Yes | Yes | Yes | Use block/mandal area for risk, routing and aggregation |
| `research_model_improvement` | Optional research and model improvement | No | No | Yes | Use images and labels to improve the system |
| `extension_contact` | Optional contact by extension worker | No | No | Yes | Follow up on a case |

The authoritative consent-type list is in `feature-specs/03-auth-and-roles.md` §5. This
table expands it for implementation; it does not add a new legal basis.

---

## 3. Draft wording (English)

The publication version must include the controller name, contact details, retention
period and complaint route. Those are `TBD` and must be completed by the legal owner.

### 3.1 Service terms and privacy — required

> **Before you send your first report**
>
> We need your agreement to use your information to provide this service.
>
> **What we collect:** your phone number, the crop and approximate area you select, the
> photos you send, your answers about the plant, and basic device and app information.
>
> **Why we use it:** to check the photo, show you a local outlook, ask an expert to review
> your case when needed, and keep a record of what happened.
>
> **Who sees it:** the project team and authorised reviewers. We do not sell your data.
> We do not show your name or exact farm location on public maps. We may publish
> aggregated information that does not identify you.
>
> **How long we keep it:** `TBD — programme and legal decision`.
>
> **Your choices:** you can ask to see, correct or delete your information, and you can
> withdraw this consent. Withdrawing means you can no longer submit reports.
>
> **What this service is not:** it is not a laboratory test, a confirmed diagnosis, or a
> confirmed outbreak warning. It can say that it does not have enough evidence.
>
> If you do not agree, you can still read general information, but you cannot submit a
> report.

### 3.2 Image analysis and storage — required

> **Your photo**
>
> Your photo will be checked for quality and analysed by an automated system. The result
> is a suggestion about what may be visible, not a diagnosis. A trained reviewer may look
> at it.
>
> The photo is stored with your case so that you and authorised reviewers can see it. We
> remove location information from the photo unless you separately agree to keep it.
>
> We do not use your photo for advertising. We do not publish your photo without your
> permission.

### 3.3 Approximate location — required

> **Your area**
>
> We use the block, mandal or district you select, not your exact farm location. This
> helps us show local risk, route your case to the right reviewer, and produce area
> summaries.
>
> Exact coordinates are optional. If you provide them, they are restricted to authorised
> staff and are not shown to other users or on public maps.

### 3.4 Optional research and model improvement — opt-in, off by default

> **Optional: help improve the system**
>
> You can choose whether your photos and case details may be used to improve the system.
> This is optional. Saying no does not change your reports or the help you receive.
>
> If you agree, we remove or mask personal information before research use, and we use the
> data only for the purposes described in the project's data governance record. You can
> change your mind at any time.
>
> [ ] Yes, you may use my data for research and model improvement
> [ ] No, do not use my data for research

### 3.5 Optional extension contact — opt-in, off by default

> **Optional: contact about your case**
>
> An extension worker may contact you about this case. This is optional. Saying no does
> not affect your reports.
>
> [ ] Yes, an extension worker may contact me
> [ ] No, do not contact me

---

## 4. Wording rules

- Use short sentences and concrete verbs.
- Say "suggestion" or "assessment", never "diagnosis".
- Say "area outlook", never "outbreak alert".
- Say "we do not have enough evidence" when describing abstention.
- Do not promise a specific outcome, accuracy or speed.
- Do not use "guaranteed", "confirmed", "cure", "prevent" or "safe" as an absolute.
- Do not mention pesticide names, doses, mixtures or intervals anywhere.
- Put optional consent in a separate, unticked control.
- Do not use pre-ticked boxes, bundling or dark patterns.
- Provide the same withdrawal path as the grant path.
- Externalise all strings for translation; do not machine-translate legal wording.

---

## 5. Consent capture design

### 5.1 Existing schema

`final/feature-specs/05-data-layer.md` defines:

| Column | Requirement |
|---|---|
| `id` | UUID |
| `user_id` | FK to users |
| `type` | Consent type |
| `version` | Consent text version |
| `granted` | Boolean |
| `text_hash` | Hash of the exact text shown |
| `channel` | Capture channel |
| `created_at` | Timestamp |

The table is append-only.

### 5.2 Proposed additions — reconcile with `05-data-layer.md` before build

These are design notes, not changes to the authoritative schema:

| Proposal | Reason |
|---|---|
| `consent_texts` table: `version`, `locale`, `body`, `text_hash`, `effective_from`, `retired_at` | The exact wording must be retrievable, not only hashed |
| `event_type` on consent events: `grant`, `decline`, `withdraw`, `reconsent` | `granted` boolean alone cannot express decline vs withdrawal |
| `locale` on the event | The language shown must be auditable |
| `controller_version` or `notice_version` | Distinguishes terms from privacy notice if they diverge |
| `source` / `channel` values | Define allowed values: app, web, SMS, IVR, paper-assisted (TBD) |

If these additions are not accepted, the same information must be captured another way;
it must not be lost.

### 5.3 Required consent states

```
not_requested
  → granted
  → declined
  → withdrawn
  → outdated_version  (re-consent required)
```

Rules:

- `not_requested` is not consent.
- `declined` and `withdrawn` block required-consent actions.
- `outdated_version` blocks new submissions until re-consent; existing cases remain
  readable.
- Optional consents never block reporting.
- A withdrawal stops future processing but does not delete historical records unless a
  deletion request is made.

### 5.4 Enforcement points

| Point | Behaviour |
|---|---|
| First report | Block until all required consents are granted |
| Consent version change | Block new submissions until re-consent |
| Optional research withdrawn | Stop future research use; do not block reporting |
| Optional contact withdrawn | Stop future contact; do not block reporting |
| Account deletion | Resolve or discard queued reports first; then follow the deletion procedure |
| Offline queue | Do not sync a report created without required consent; surface the reason |

### 5.5 API touchpoints

From `feature-specs/03-auth-and-roles.md` §8:

- `GET /v1/me/consents`
- `POST /v1/me/consents`

The response must state, per consent type: current status, version, text hash, timestamp,
and whether re-consent is required.

### 5.6 Audit events

- `consent.granted`
- `consent.declined`
- `consent.withdrawn`
- `consent.version_changed`
- `consent.reconsent_required`
- `consent.capture_failed`

Audit events carry the user ID, consent type, version, channel and timestamp. They do not
carry the full free-text consent body in logs.

### 5.7 Acceptance criteria

- [ ] A new farmer cannot submit a report before granting all required consents.
- [ ] Optional research consent is unticked by default and does not gate reporting.
- [ ] The exact text shown is retrievable by version and matches the stored hash.
- [ ] Withdrawal creates a new append-only event and stops future processing.
- [ ] A consent version change blocks new submissions until re-consent.
- [ ] Declining or withdrawing optional consent does not block core reporting.
- [ ] Consent events are audited.
- [ ] No consent text is logged in full.
- [ ] The user can read the wording before granting.
- [ ] The withdrawal path is as easy to find as the grant path.

---

## 6. Open questions

1. Who is the data controller and what contact details appear in the notice? **Blocked on D10.**
2. Which jurisdiction and data-protection regime applies? `update.md` references India's
   DPDP Act 2023, but D1/D4 are unresolved and the controller decision is D10.
3. Which local language(s) must be provided, and who certifies the translation?
4. What are the retention periods and the deletion SLA? **Blocked on D10.**
5. Are images of people, faces or bystanders permitted? If so, what is the blurring and
   consent rule?
6. Is exact location ever collected? If yes, under which separate consent and role
   restriction?
7. What is the complaint and grievance route?
8. Is parental/guardian consent relevant for any field staff or participants under 18?
9. How is consent captured for paper-assisted or IVR channels?
10. What is the re-consent grace period, if any? The default is zero: block new
    submissions immediately.
