# D4 — Owning and paying institution

**Decision ID:** D4 (policy), with the named counterparty tracked as **D4a**.
**Status:** `[~]` Policy decided 2026-11-06; named counterparty and signed MoU pending.
**Owner:** Product lead, with the programme lead.
**Needs by:** Gate 0 for the named counterparty; Gate 6 for the operating transition.
**Changes:** `progress-tracker.md` §4, `phase-0-decisions.md` §3,
`partner-and-data-permission-register.md`, `budget-and-staffing-scenarios.md`.

> **No invented counterparty.** This document chooses the *owner class*, funding path and
> transition rules. It does not name an institution as a partner, because no institution has
> been contacted, has agreed, or has signed. `D4a` is the external act that closes Gate 0.

---

## 1. Decision

**Post-pilot owner class:** a public agricultural extension or plant-health institution
(for example a state agriculture department, a university plant-pathology department, or a
publicly mandated plant-clinic network) that can hold the service after the grant ends.
**Operating partner if no public owner is ready:** a farmer-producer organisation (FPO) or
cooperative, supported by the same technical team.
**Funding path:** grant/NGO/public-good funding for Phases 0–5; transition to the owner's
institutional recurrent budget plus partner cost-share for Phase 6. A per-farmer
subscription is not the v1 model.
**Rejected:** input-company funding for the advisory layer. It creates a conflict of interest
with the non-chemical advisory rule (R5) and the trust model.

**D4a — named counterparty:** the specific institution, signatory, governing-law jurisdiction
and effective date are recorded only when an MoU/LOI is drafted or signed. Until then the
status is `candidate` in the partner register, and Gate 0 cannot close on D4.

---

## 2. Options considered

| Option | Consequence | Verdict |
|---|---|---|
| **Public extension / plant-health institution (chosen owner class)** | Public-good mandate, existing field staff, durable after grant; slower procurement and political risk | Preferred |
| Cooperative / FPO operating partner | Close to farmers, direct member value; small budgets and variable professional capacity | Fallback / operating partner |
| NGO or development programme | Fast pilot start, strong field capability; time-bound funding and exit risk | Pilot funder, not long-term owner |
| Crop insurer | Strong risk-data incentive; different incentive structure and possible pressure to overstate risk | Possible future partner, not v1 owner |
| Input-company funding | Deep pockets and distribution; advisory bias and liability conflict | Rejected for the advisory layer |

---

## 3. Ownership, hosting and service life

| Question | Decision |
|---|---|
| Who owns farmer-submitted images and case data? | The farmer retains ownership of the original content; the project receives a limited, revocable licence for the stated purposes. The MoU records the exact wording. |
| Who owns derived labels, features and model artefacts? | The project/owner holds them under the data-sharing agreement, subject to the source licence and the farmer's optional research consent. No redistribution of raw farmer images. |
| Who owns the software? | The project/licensor; the operating institution receives a licence to operate, maintain and localise it. The licence text is a legal deliverable. |
| Who is the data controller? | Interim: the project sponsor. Post-pilot: the D4a owner, recorded in the DPIA and privacy notice before any transfer. |
| Who hosts? | Project-controlled cloud in an India region for the pilot; the operating institution takes hosting responsibility at transition, or a written processing agreement keeps the project as processor. The final choice is recorded in the DPIA. |
| What is the service-life assumption? | Minimum three years of operation after the pilot, with a five-year design life for data retention and model maintenance. Re-assessed at Gate 6. |
| What happens if the owner withdraws? | Data return/deletion per the MoU; model artefacts and code escrow; a documented wind-down and farmer-notification plan. |
| What is the publication rule? | Aggregate, non-identifying results may be published with attribution; raw images, farm locations and case-level data are never published without separate consent. |

---

## 4. Funding path and cost responsibility

| Phase | Funder | What it covers | Exit condition |
|---|---|---|---|
| Phase 0–1 | Grant / programme budget | Discovery, partner agreements, data collection, labelling | Gate 1 |
| Phase 2–3 | Grant / programme budget | Platform, image model, evaluation | Gate 3 |
| Phase 4–5 | Grant / programme budget + partner in-kind | Forecast, pilot operations, verification time | Gate 5 |
| Phase 6 | Owner institutional budget + partner cost-share | Hosting, support, maintenance, retraining | Gate 6 |
| Post-pilot | Owner | Recurring service; no per-farmer fee in the public-good model | Annual review |

**Rules:**

- The budget must show reviewer compensation as a real line, not an in-kind assumption.
- No funding is accepted that requires chemical promotion, exclusive product recommendation or
  suppression of negative results.
- A funding gap pauses expansion; it does not justify removing abstention, coverage or review.

---

## 5. D4a selection criteria

The named counterparty must satisfy all of the following. The programme lead records the
evidence in the partner register.

- [ ] Legal mandate to operate an agricultural advisory or plant-health service in the pilot
      zone.
- [ ] Named signatory with authority to commit staff time and data sharing.
- [ ] At least two `can_confirm` holders or a written route to them.
- [ ] Ability to host or contract the service after the grant, or a credible transition plan.
- [ ] Data-protection contact and a documented incident route.
- [ ] Agreement to the non-chemical advisory rule and the human-verification rule.
- [ ] Agreement to publish aggregate results, including negative results.
- [ ] A named field operations lead and a backup.

**Preferred order:** public extension/plant-health institution → university plant clinic →
FPO/cooperative with a technical partner → NGO (pilot only).

---

## 6. Consequences and risks

| Risk | Consequence | Mitigation |
|---|---|---|
| No owner signs before Gate 0 | Pilot cannot start; season may be missed | Parallel outreach to two candidate classes; contingency Kharif window |
| Owner lacks verification capacity | Confirmed layer stays empty; alerts unsupported | D3b capacity clause in the MoU; training and compensation line |
| Funding ends mid-pilot | Service stops; farmer trust damaged | Written transition and wind-down plan; no promises beyond funded period |
| Hosting transfer is unsafe | Privacy or availability incident | DPIA, processing agreement, tested restore before transfer |
| Owner changes scope to chemical advice | R5 breach | Contract clause; advisory validator; right to pause the service |

---

## 7. Gate 0 evidence

- [ ] D4 policy recorded (this document).
- [ ] D4a counterparty named in the partner register.
- [ ] Draft MoU/LOI includes data ownership, hosting, publication, retention, deletion and
      service-life clauses.
- [ ] Funding path and reviewer compensation line recorded in the budget scenario.
- [ ] Data controller named for the pilot period.

**Sign-off**

| Role | Name | Decision | Date |
|---|---|---|---|
| Product lead | TBD at workshop | Pending | — |
| Programme lead | TBD at workshop | Pending | — |
| Counterparty signatory (D4a) | TBD at MoU | Pending | — |
