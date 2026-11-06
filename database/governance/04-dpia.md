# Data Protection Impact Assessment (DPIA)

**Status:** Draft — **not completed, not signed, not legal advice.**
**Owner:** Programme lead + legal/privacy owner / DPO (TBD)
**Last updated:** 2026-11-06
**Scope:** v1 pilot processing of farmer/field-staff reports, images, approximate
location, weather, expert review, advisory and alerts.

> **Boundary:** a DPIA is an accountable-organisation document. This draft identifies
> the processing, risks and mitigations so the responsible humans can review and sign it.
> It must not be presented as evidence of compliance until the sign-off block is complete.

---

## 1. Screening

| Question | Answer | Note |
|---|---|---|
| Does the processing involve personal data? | **Yes** | Phone numbers, device data, reports, images, optional contact |
| Can images identify a person? | **Possibly** | Bystanders, hands, reflections, documents, unique field features |
| Is precise location involved? | **Optional** | Approximate area by default; exact coordinates only if separately consented |
| Is special-category data involved? | **Not intended** | No health data; images may accidentally capture people; confirm with counsel |
| Is there systematic monitoring? | **No** | Reports and weather, not continuous surveillance |
| Is there automated decision-making with legal/significant effect? | **No** | Outputs are assistive; human verification is required; no chemical advice |
| Is new technology used? | **Yes** | Image triage, forecast modelling, calibration and abstention |
| Is data combined across sources? | **Yes** | Images + area + weather + verified reports + historical records |
| Are vulnerable people involved? | **Potentially** | Smallholders, low digital literacy, power imbalance with extension staff |
| Is there cross-border transfer? | **TBD** | Depends on hosting and providers (D4) |
| Is large-scale processing involved? | **Pilot scale** | Confirm volume and duration at Gate 0 |

**Screening conclusion:** a DPIA is required. The processing combines images, location
and third-party data, and uses automated inference in a context where users may have low
digital literacy.

---

## 2. Processing description

### 2.1 Data flows

```
farmer / field staff
  → mobile capture (crop, area, photo, context)
  → local queue (offline)
  → API + object storage
  → quality gate + photo assessment
  → expert review queue
  → verification decision
  → verified projection
  → forecast features (verified only)
  → area outlook + advisory + alert
  → district dashboard / map (aggregated)
```

### 2.2 Data categories

| Category | Examples | Sensitivity | Source |
|---|---|---|---|
| Identity | Phone number, email, user ID, device ID | High | User, device |
| Consent | Type, version, grant/withdraw, text hash | High | User |
| Location | Block/mandal code; optional precise point | High | User, device |
| Images | Crop/leaf photos; possible bystanders or background identifiers | High | User |
| Case context | Crop, variety, stage, notes | Medium | User |
| Verification | Reviewer decision, evidence, corrected label | Medium | Staff |
| Weather | Grid/station observations | Low | Provider |
| Historical records | Past occurrence reports | Medium | Partner |
| Advisory/alert | Approved content, delivery status, feedback | Medium | Project |
| Audit | Actor, action, timestamp, hashed IP | Medium | System |
| Model artefacts | Versions, metrics, snapshots | Low–medium | ML pipeline |

### 2.3 Purpose and necessity

The processing is necessary to:

- assess a submitted image and return an honest, uncertain result;
- route uncertain or high-impact cases to a human;
- estimate area-level risk from verified reports and weather;
- deliver approved, non-chemical guidance and alerts;
- maintain audit and reproducibility.

Data minimisation rules:

- approximate location by default; exact coordinates optional and restricted;
- no advertising identifiers;
- no PII in dashboards, exports or logs;
- no raw farmer images in demo content or tests;
- no chemical advice;
- only verified reports enter forecast features.

### 2.4 Lawful basis

**TBD — legal decision.** The design assumes consent for core processing, with a separate
optional consent for research/model improvement. The lawful basis for:
- service delivery,
- expert review,
- public-health/agronomic aggregate reporting,
- research use,
- audit and security

must be confirmed by counsel for the pilot jurisdiction. `update.md` references India's
DPDP Act 2023, but D1/D4 are unresolved and the data-controller/retention decision is D10.

---

## 3. Risk assessment

Likelihood and impact use H/M/L. Residual risk is assessed **after** the mitigation is
implemented and verified.

| ID | Risk | L | I | Mitigation | Residual | Owner |
|---|---|---|---|---|---|---|
| DP-01 | Re-identification from images, backgrounds, reflections or unique field features | M | H | Capture guidance; avoid faces/documents; blur on request; access control; no public raw images; aggregate map output | TBD | Data engineer + field ops |
| DP-02 | Precise farm location disclosed | M | H | Approximate location default; exact coordinates optional; field-level authorisation; no raw points in map layers | TBD | Eng lead |
| DP-03 | Small-count inference reveals an individual farm | H | H | Aggregate to admin unit; suppress small counts in a view/function; access control | TBD | Data engineer |
| DP-04 | Unauthorised access or insider misuse | M | H | RBAC; MFA for privileged roles; least privilege; audit; deny by default; object-level checks | TBD | Eng lead |
| DP-05 | Model error causes crop loss or unsafe action | H | H | Abstention; top-3 not single diagnosis; human review; no chemical advice; clear "not a diagnosis" wording; escalation | TBD | ML lead + agronomist |
| DP-06 | Output mistaken for a confirmed outbreak | M | H | Separate outputs; coverage always visible; explicit wording; no "outbreak confirmed" language | TBD | Product lead |
| DP-07 | Function creep or secondary use | M | M | Purpose limitation; versioned consent; governance review; no sale; no advertising | TBD | Programme lead |
| DP-08 | Retention overrun | M | M | Retention schedule; deletion jobs; audit; backup propagation procedure | TBD | Data engineer |
| DP-09 | Provider or processor breach | M | H | Contracts; security review; minimum data; breach notification; local hosting if required | TBD | Programme lead |
| DP-10 | Cross-border transfer without a valid mechanism | TBD | H | Map hosting and subprocessors; legal review; transfer mechanism; local-first option | TBD | Legal |
| DP-11 | Coercion or power imbalance in consent | M | H | Voluntary consent; no gating of essential service; private withdrawal path; local language; no incentives that undermine voluntariness | TBD | Field ops |
| DP-12 | Bystanders or children captured in images | M | M | Capture guidance; do not upload images of people; blurring; report-and-remove path | TBD | Field ops |
| DP-13 | Biased or unrepresentative data harms some regions | H | M | Sampling matrix; geographic holdout; per-region metrics; do not deploy where coverage is low | TBD | ML lead |
| DP-14 | Demo or synthetic data mistaken for real | M | M | `is_demo` everywhere; visible badge; excluded from operational alerts | TBD | Product lead |
| DP-15 | Account takeover via OTP or refresh token | M | H | OTP rate limits; hashed codes; refresh rotation; reuse detection; MFA for staff | TBD | Eng lead |
| DP-16 | Uncontrolled export leaks PII | M | H | Role check; purpose; row limit; no PII columns; audit | TBD | Admin owner |
| DP-17 | Retroactive boundary or taxonomy change misattributes records | M | M | Version boundaries; keep original code and version; no silent rewrite | TBD | Data engineer |
| DP-18 | Unverified reports treated as confirmed | H | H | Verification projection; forecast filters verified only; tests | TBD | ML lead + reviews |
| DP-19 | Archive images contain people, faces, documents or farm identifiers without the project's consent | M | H | Signed permission record; privacy review before ingest; PII detection; quarantine `pii_detected`; no archive images in farmer-facing output | TBD | Legal/privacy + data engineer |
| DP-20 | Archive data used outside its permission or mistaken for fresh field evidence | M | H | Permission-scope fields; archive/field separation rule; no archive records in field versions or frozen test set; provenance audit; separate reporting | TBD | Data engineer + legal/privacy |

---

## 4. Data-subject rights

| Right / request | Design response | Status |
|---|---|---|
| Access / export own data | Machine-readable export within a documented SLA | Procedure TBD |
| Correct profile | Self-service | Proposed |
| Correct a case label | Human review / correction with audit | Designed |
| Delete account | Resolve/discard queued reports; soft delete; hard-delete job; retain audit and non-identifying aggregates | Procedure drafted |
| Withdraw optional consent | Immediate for future processing; audited | Designed |
| Object to processing | Route to programme owner; documented response | Owner TBD |
| Complain | Route to be published in the notice | TBD |

No statutory response deadline is asserted here; counsel must set the applicable SLA.

---

## 5. Processors, transfers and security

### 5.1 Processors

| Processor type | Data | Contract status |
|---|---|---|
| Hosting / database | All records | Not selected |
| Object storage | Images, models, exports | Not selected |
| SMS / WhatsApp gateway | Phone number, message content | Not selected |
| Weather provider | Area/grid, no farmer identity | Terms not recorded |
| Map tiles | Aggregated geometry | Not selected |
| Error/monitoring service | Logs; no PII allowed | Not selected |

### 5.2 Security controls expected

- TLS in transit; encryption at rest.
- Private object storage; presigned URLs ≤ 10 minutes.
- Magic-byte validation; size and dimension limits.
- EXIF GPS stripped unless separately consented.
- Hashed OTPs and refresh tokens; no secrets in logs.
- Area-scoped queries; object-level ownership checks.
- Append-only audit for reviews, role changes, exports, admin record views and config.
- Backups with tested restore.
- No real farmer data in staging or demo.

---

## 6. Consultation and sign-off

| Role | Name | Decision | Date |
|---|---|---|---|
| Prepared by | AI drafting support | Draft only | 2026-11-06 |
| Data protection officer / privacy lead | TBD | Not reviewed | — |
| Legal counsel | TBD | Not reviewed | — |
| Programme lead | TBD | Not approved | — |
| Agronomist / domain lead | TBD | Not reviewed | — |

**DPIA decision:** `DRAFT — NOT APPROVED`. Processing must not begin on the basis of this
draft alone.

---

## 7. Open items before sign-off

1. Confirm the pilot jurisdiction and the applicable data-protection law.
2. Name the controller, DPO/privacy contact and grievance route.
3. Confirm the lawful basis for each purpose.
4. Set retention periods and the deletion SLA.
5. Decide whether exact location is collected at all; if yes, define the separate consent
   and access role.
6. Decide the policy for images containing people, faces or bystanders.
7. Select hosting, storage, messaging and monitoring providers; complete processor due
   diligence.
8. Confirm whether cross-border transfer occurs and the transfer mechanism.
9. Define the data-subject request workflow and response timeline.
10. Confirm whether any participant is under 18 and whether guardian consent applies.
11. Define the breach notification procedure and owner.
12. Re-assess residual risk after controls are implemented and tested.
13. Record the consultation outcome and any residual risk accepted by the accountable
    owner.
14. Confirm the lawful basis and handling rule for personal data inside any archive,
    including reviewer identity and any people visible in archive images.
15. Confirm archive retention, deletion and return/destruction obligations before ingest.

---

## 8. Change log

| Date | Change | Owner |
|---|---|---|
| 2026-11-06 | Initial draft created; no sign-off | Draft — legal/privacy (TBD) |
| 2026-11-06 | Added archive-specific risks DP-19/DP-20 and archive open items; still unsigned | Draft — legal/privacy (TBD) |
