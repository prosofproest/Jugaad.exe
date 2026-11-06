# Phase 0 — Decision register

**Status:** In progress — architecture decided (ADR-009/010/011); D1, D2, D3 (role), D6,
D13, D14 and D15 answered; D1a, D3b, D4, D5 and D7–D12 open
**Started:** 2026-11-06
**Gate 0 calendar target:** 2026-11-20 (proposed; confirm at the decision workshop)
**Canonical decision history:** `progress-tracker.md` §4 (this file is the working record
for Phase 0 and must be reflected there)

---

## How to close a decision

A decision counts as answered only when it records:

1. the chosen option, not a range of options;
2. one named accountable owner;
3. the date it was decided;
4. the phase gate it must be in place before;
5. the documents and specs it changes.

Anything less stays `[?]`, and Gate 0 cannot close.

---

## 1. Answered decisions

### D1 — Crop and target set ✅

**Decision (2026-11-06):** Open, crop-agnostic catalogue with a **validated-target
allowlist**. Any crop can be submitted; an assessment is returned only for `crop × target`
pairs on the current release allowlist. Everything else returns an explicit abstention
(`unsupported_crop`, `unsupported_target`, `insufficient_quality`).

This preserves the product owner's "open for all crop diseases" intent without claiming
unmeasured coverage. See [ADR-011](adr/0011-open-crop-catalogue.md).

**Consequence:** D1 is answered at the architecture level. The **first concrete allowlist**
is split out as **D1a** and must be fixed before Gate 3.

**Owner:** Project owner + agronomist. **Date:** 2026-11-06. **Needs by:** Gate 0 (met).

### D2 — Nowcast or outlook ✅

**Decision (2026-11-06):** **Nowcast over the last 10 days** for v1. A 7-day outlook is
deferred until at least one season of verified outcomes exists.

**Owner:** Agronomist + ML lead. **Date:** 2026-11-06. **Needs by:** Gate 0 (met).

### D3 — Verifier role, capacity and SLA 🟡

**Role decision (2026-11-06):** **Extension-first.** `extension_worker` reviews cases;
`confirmed` requires the scoped `can_confirm` permission; `admin` does not verify
(separation of duties). See [ADR-010](adr/0010-v1-roles.md).

**Still open:** verification capacity per area, review SLA, escalation path, and the
minimum number of `can_confirm` holders per pilot area.

**Owner:** Programme lead + partner. **Needs by:** Gate 0 for SLA/capacity.

### D6 — Legal position on advisory content ✅

**Decision (2026-11-06):** **Non-chemical only.** Advisory content is expert-approved,
versioned and limited to scouting, monitoring, sanitation, crop management and escalation.
No pesticide, herbicide, fungicide, dosage, mixture or pre-harvest-interval content. This
keeps R5 intact and requires no legal relaxation.

**Owner:** Programme lead + legal. **Date:** 2026-11-06. **Needs by:** Gate 0 (met);
legal review still required before Gate 5.

---

## 2. Additional decisions resolved during Phase 0

### D13 — v1 languages ✅

**Decision (2026-11-06):** **English + Kannada** for v1, with language switching and
persistence. All user-facing strings externalized, including backend-generated errors and
alerts.

**Owner:** Product lead. **Date:** 2026-11-06. **Needs by:** Gate 2 (first farmer UI).

### D14 — Output semantics: confidence and severity ✅

**Decision (2026-11-06):**

- **Confidence:** qualitative band plus abstention by default. A numeric probability is
  displayed only when calibration has been measured and passed for that allowlist entry.
- **Severity:** an **expert-review field**, not a model claim. The model may output a
  candidate list and quality flags; it does not assert severity.
- The two outputs (photo assessment vs area outlook) stay separate (R1).

This resolves the conflict between the target diagram ("disease name + confidence +
severity") and the repository's safety model.

**Owner:** ML lead + product lead. **Date:** 2026-11-06. **Needs by:** Gate 3.

### D15 — Notification channels ✅

**Decision (2026-11-06):** **In-app is mandatory** on web and mobile. **Email** is used for
staff and institutional recipients. **SMS is optional** per pilot partner, behind an adapter
interface. **WhatsApp, push and IVR are deferred** beyond v1.

**Owner:** Product lead + programme lead. **Date:** 2026-11-06. **Needs by:** Gate 5.

---

## 3. Open decisions (blocking Gate 0)

| ID | Decision | Status | Recommended default | Owner | Needs by |
|---|---|---|---|---|---|
| D1a | First validated crop/target allowlist | `[?]` | One crop, 3–5 conditions, one agro-climatic zone | Agronomist + ML lead | Before Gate 3 |
| D3b | Verifier capacity + SLA | `[?]` | Extension-first; 48 h SLA; 2 `can_confirm` holders per area | Programme lead | Gate 0 |
| D4 | Owning / paying institution | `[?]` | Grant/NGO-funded pilot → cooperative or insurer operations | Product lead | Gate 0 |
| D5 | Primary outcome metric | `[?]` | Median lead time from first farmer report to verified confirmation | Product lead + evaluator | Gate 0 |
| D7 | Forecast event, negative class, label eligibility | `[?]` | Presence/first-verified-case event; `probable` eligible with evidence tier; `unverified` never eligible | ML lead + agronomist | Gate 0; frozen before Gate 4 |
| D8 | Abstention rule + numeric acceptance floors | `[?]` | Measure Phase-3 baseline, then pre-register floors before opening the frozen test set | ML lead + evaluator | Before Gate 3 exit |
| D9 | Coverage, freshness, suppression values | `[?]` | Define formula; set numbers after Phase 1 data profile | Data engineer + legal | Gate 4 |
| D10 | Retention, deletion, derived-data policy | `[?]` | Per-entity matrix; images and derived records included; tombstone erasure on restore | Programme lead + legal | Gate 2 |
| D11 | On-behalf identity + offline sessions | `[?]` | `reporter_id` separate from `subject_user_id`; 15-min token, 7-day offline cap | Backend lead | Gate 2 |
| D12 | Client-side quality pre-check | `[?]` | Deterministic heuristics; advisory only; server gate authoritative | Mobile lead + ML lead | Gate 2 |

---

## 4. Gate 0 exit checklist

- [x] Architecture stack decided — [ADR-009](adr/0009-data-platform.md)
- [x] v1 roles decided — [ADR-010](adr/0010-v1-roles.md)
- [x] Crop/target policy decided — [ADR-011](adr/0011-open-crop-catalogue.md)
- [x] D1 answered (policy level)
- [x] D2 answered
- [x] D6 answered
- [x] D13 (languages) answered
- [x] D14 (output semantics) answered
- [x] D15 (notification channels) answered
- [ ] D1a first allowlist fixed
- [ ] D3b verifier capacity + SLA
- [ ] D4 owning institution
- [ ] D5 primary metric
- [ ] D7 forecast event + negative class
- [ ] D8 abstention rule + floors
- [ ] D9 coverage/freshness/suppression values
- [ ] D10 retention/deletion policy
- [ ] D11 on-behalf identity + offline sessions
- [ ] D12 client-side quality pre-check
- [ ] All decisions recorded in `progress-tracker.md` §4 with owner + date
- [ ] Conflicting stack/role/language claims removed from PRD, TRD, architecture context
      and feature specs
- [ ] Clean-clone install and test command verified

**Gate 0 remains OPEN.**

---

## 5. Sign-off

| Role | Name | Date |
|---|---|---|
| Project owner | | |
| Engineering lead | | |
| Agronomist / pathologist | | |
| Programme lead | | |
