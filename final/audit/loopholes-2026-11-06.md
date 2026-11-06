# Loophole audit — 2026-11-06

**Scope:** all 31 working documents under `final/` (~8,900 lines). `totalcontent.md` (the
63 KB original blueprint) was not audited line by line; it is reference-only and superseded
for v1 scope by `update.md`.

**Method:** read every operating doc, feature spec, PRD and TRD; cross-checked each
requirement against the gates that are supposed to enforce it; traced every threshold,
state name and identifier to the place it is defined.

**Verdict:** the documentation is unusually disciplined about *what it must not claim*. The
structural weakness is the mirror image: almost nothing in it forces the project to
demonstrate that either output works. The safety rules (abstain, show coverage, never
conflate) are hard; the performance rules are soft. A system that abstained on every photo
and returned `insufficient_data` for every area would have satisfied every gate as written.

This audit closes that gap structurally and converts the unowned gaps into blocking
decisions D7–D12.

---

## 1. What changed as a result of this audit

| # | Change | Where |
|---|---|---|
| 1 | Gate 0 now has a calendar target and requires one named owner + date per decision | `docs-context/progress-tracker.md` §2, §4 |
| 2 | Gate 3 requires D8 floors to be **met**, not merely reported | `docs-context/progress-tracker.md` §2 |
| 3 | Gate 4 requires D7 event definition and D9 values frozen before the test season | `docs-context/progress-tracker.md` §2 |
| 4 | Gate 5 defines "unresolved safety issue" and ties evidence to the D5 metric | `docs-context/progress-tracker.md` §2 |
| 5 | D2–D6 gained `Needs by` dates; D7–D12 added | `docs-context/progress-tracker.md` §4 |
| 6 | Status tokens reconciled (removed phantom `status.verified` / `status.pending`) | `ui-context.md` §3, `01-design-system.md` §2 |
| 7 | Canonical UI copy no longer asserts calibration that does not exist | `ui-context.md` §2 |
| 8 | `AssessmentCard` state list reconciled to five states | `ui-context.md` §4 |
| 9 | Raw model scores removed from the documented response contract | `TRD.md` §7.4 |
| 10 | On-device pre-check separated from on-device model inference | `02-reporting-and-capture.md` §11, D12 |
| 11 | Flutter tooling marked provisional until ADR-006 is Accepted | `code-standards.md` §4 |
| 12 | Entry-point scope wording marked pending D1/D2/D4 | `docs-context/AGENTS.md` §1 |

---

## 2. Critical findings

### C-1 — Every gate could be passed by never predicting
`PRD.md:538` required "field-test performance at shipped threshold" with no minimum.
`TRD.md:1060` accepted only `insufficient_data` behaviour and snapshot reproduction.
`feature-specs/06-forecast-and-risk-map.md:242-254` contained no minimum scored-area share.

**Consequence:** a 100%-abstention classifier and a forecast engine that never scores would
have passed Gates 3, 4 and 5.

**Disposition:** D8 requires pre-registered numeric floors (per-class recall, max abstention,
minimum share of area-days scored, lift over climatology) and Gate 3 now fails a number that
does not clear them. R6 is respected: the numbers are set from the measured Phase-3
baseline, before the frozen test set is opened — the *rule* is the decision.

### C-2 — The forecast track had no observable negative class
`06:32` required "verified absence within coverage" as the negative label;
`data-foundation.md:305` forbade treating no-report as negative. The only described pipeline
(farmer photos + expert review) produces positives only. `06:230` nonetheless permitted a
scored band with zero verified reports.

**Consequence:** PR-AUC, Brier score and calibration had no legitimate denominator, and R3
could be violated by the forecast spec itself.

**Disposition:** D7. Either scheduled absence sampling exists, or the event is framed as
presence/first-verified-case under a positive-unlabelled design with an explicit statement
that discrimination metrics requiring negatives are not reported.

### C-3 — Abstention had no decision function
`ml-models.md:168` said only "set thresholds that allow the model to say it cannot assess".
No τ, no margin or entropy rule, no per-class thresholds, no risk–coverage target, no
override policy.

**Disposition:** D8. R2 is untestable until the function and τ exist.

### C-4 — No open-set detection, so R2's core promise was unimplementable
`unknown` was treated as a supervised class (`ml-models.md:21`) while `ml-models.md:31`
forbade mapping an unknown input to the nearest supported class. A supervised `unknown`
class only recognises unknowns present in training; a novel pathogen is out-of-distribution
and scores confidently. `TRD.md:314` listed `out_of_domain` as an abstain reason that
nothing produced.

**Disposition:** D8 must define an out-of-distribution score and evaluate it on held-out
classes (unknown-vs-known AUROC and false-accept rate at the shipped threshold).

### C-5 — Labels leaked into the forecast evaluation
`feature-specs/04-expert-review.md:121` and `PRD.md:266` required reviewers to see "model
candidates… forecast context at report time". Those same reviews become the frozen test
labels. `04:285` put multi-reviewer consensus out of scope, so no agreement could be
measured either.

**Consequence:** confirmation bias plus leakage inflates every reported metric; the verified
layer then feeds the next forecast.

**Disposition:** D7 must include a blinded primary read (candidates and forecast context
hidden until the label is recorded) and a double-labelled subset with an agreement target.

### C-6 — Deletion could not be honoured
`TRD.md:265` made predictions, reviews and audit "never soft-deleted"; `TRD.md:419` retained
"audit and non-identifying aggregates"; `03-auth-and-roles.md:177` said deletion "propagates
on the next restore cycle". A deletion request could not reach `feature_snapshots`, the
frozen test set (`phase-plan.md:275`), backups, or trained weights.

**Consequence:** the deletion right promised in `PRD.md:329` is not deliverable, which is a
compliance defect rather than a documentation gap.

**Disposition:** D10. Per-entity deletion matrix, derived-data position, tombstone erasure
on restore, and on-device TTL/encryption/wipe-on-logout.

---

## 3. Contradictions that would have produced two different builds

| ID | Contradiction | Evidence | Disposition |
|---|---|---|---|
| X-1 | On-device pre-check was a MUST while on-device inference was explicitly rejected, with no mechanism, threshold or budget specified | `02:105` vs `02:292`, `architecture-context.md:45`, `TRD.md:154` | D12 + interim rule: pre-check is advisory, server gate authoritative |
| X-2 | "Four roles only" but an agronomist is required as advisory author, approver, forecast approver and D1 owner; `03:58` gates approval on an "agronomist sign-off role" that does not exist | `03:16,58`, `07:37,86`, `06:4` | **Open** — needs a role-model decision (see §5) |
| X-3 | `probable` ambiguity: the forecast filter is `verified_at IS NOT NULL`, and `probable` also sets `verified_at`, so probable cases enter as verified although R4 authorises only confirmed | `AGENTS.md:88`, `ai-workflow-rules.md:115`, `05:117`, `04:296` | D7 |
| X-4 | ADR-005/006 were "Proposed" while Flutter and ONNX were enforced as standards | `progress-tracker.md:215`, `architecture-context.md:329-330`, `code-standards.md:120` | Code standards now marked provisional until ADR-006 is Accepted |
| X-5 | Raw scores were returned to clients while three documents forbade exactly that | `TRD.md:523` vs `TRD.md:438`, `architecture-context.md:253`, `01:121` | `TRD.md` example replaced with band-only |
| X-6 | Status token namespaces disagreed; `status.verified` existed only in the UI doc and matched no state in the system | `ui-context.md:118` vs `01:43,68` | Both reconciled to the ten-value list |
| X-7 | Canonical UI copy asserted "calibrated on field data" before any calibration existed | `ui-context.md:76` | Replaced with "not yet calibrated" |
| X-8 | v1 scope was stated as settled in the entry-point document while D1/D2 were open | `AGENTS.md:23-25` vs `progress-tracker.md:151,163` | Wording marked pending D1/D2/D4 |
| X-9 | Timeline arithmetic: sequential phases summed to ~19–27 months inside an 18-month plan; "useful in month 6" preceded Phase 1 exit | `phase-plan.md:38-46`, `PRD.md:545`, `update.md:77` | **Open** — schedule reconciliation required |
| X-10 | Budget: $150k–400k for 7–9 FTE over 18 months is ~$1.2k–3.2k all-in per person-month | `update.md:177,74` | **Open** — needs a line-item WBS |
| X-11 | A root `DESIGN.md` defines a *Wise* fintech design language — lime green, 126 px display type, raw hex values — as a competing design authority. It is unrelated to field conditions and violates the semantic-token rule, the single-source rule and the accessibility targets | `DESIGN.md:2-28`, `01-design-system.md:25-27`, `ui-context.md:103-127` | **Open** — delete, or declare it non-authoritative and unrelated to `design/tokens.json` |
| X-12 | A `chatbot/` folder contradicts the architecture's explicit exclusion of "a general-purpose advisory chatbot" and R5's ban on generated or paraphrased advisory text. An empty folder is where that violation starts | `architecture-context.md:340`, `07-advisory-and-alerts.md:18-21`, `AGENTS.md:104-105` | **Open** — remove, or record an ADR that scopes it to non-advisory support only |
| X-13 | Placeholder folders `frontend/`, `chatbot/` do not match the declared target layout (`web/`; no chatbot), and `AGENTS.md` §4 forbids scaffolding that implies an unrecorded decision | tree, `AGENTS.md:129-146` | **Open** — align layout with `AGENTS.md` or update the layout via a recorded decision |

---

## 4. Register of remaining gaps (severity ordered)

| ID | Gap | Evidence | Owner |
|---|---|---|---|
| G-01 | Coverage gates scoring and alerts but has no formula, window, denominator or value; gameable by registering reporters without more farm observations | `06:49,97,275`, `TRD.md:368`, `05:129` | D9 |
| G-02 | "Approximate location" and "suppress small counts" undefined; spec enforces against columns that do not exist (`geo_code`, `precision`, `view_precise_location`) | `AGENTS.md:115`, `05:100` vs `05:198-200` | D9 |
| G-03 | Offline-first (≥7 days, `02:249`) incompatible with a 15-minute access token and online-only refresh; role revocation cannot reach an offline device | `02:249`, `03:114-119` | D11 |
| G-04 | On-behalf capture has no data model; `02:301` leaves `user_id` semantics open while `03:151` hard-codes `observation.user_id == current_user.id` | `02:301`, `03:151` | D11 |
| G-05 | Conflict rule covers status only, not offline edits to crop, stage, notes or area | `TRD.md:606` | D11 |
| G-06 | Advisory withdrawal cannot recall content already cached on device | `07:99`, `TRD.md:682` | D10 |
| G-07 | SMS must carry eight mandatory fields plus a disclaimer while described as a "short template"; no bytes or cost-per-message budget | `07:165`, `ui-context.md:26` | Product |
| G-08 | No dataset, licence or permission registry, so "no training without permission" is unenforceable and models cannot be traced to dataset versions | `data-foundation.md:49`, `05:47-67` | Data engineer |
| G-09 | Calibration method never named (ECE is a diagnostic, not a method); calibration shares the model-selection validation set | `ml-models.md:99-101,137` | ML lead |
| G-10 | 500–2,000 images across 6–9 classes and six subgroup dimensions cannot support per-class calibration or abstention claims | `update.md:273`, `ml-models.md:42,139` | ML lead |
| G-11 | Day-one rules model has no historical backtest, minimum history, or comparison against climatology | `06:17,62,201` | ML lead |
| G-12 | Spatial holdout is optional three times over despite distance-weighted neighbour features and spatial autocorrelation | `data-foundation.md:220`, `06:202`, `ml-models.md:221,270` | ML lead |
| G-13 | No as-of label rule (`verified_at <= cutoff`) and no right-censoring handling for the most recent season | `data-foundation.md:214,306`, `06:201` | ML lead |
| G-14 | No numeric SLO, RTO or RPO anywhere, while `summary.md:145` claims "measurable SLOs" — an R6 violation inside the doc set | `TRD.md:949`, `PRD.md:372-384` | Eng lead |
| G-15 | Single VM against an availability expectation for review during field hours | `architecture-context.md:21`, `04:249` | Eng lead |
| G-16 | Three different definitions of done, none satisfiable by a documentation change | `AGENTS.md:169`, `ai-workflow-rules.md:73`, `code-standards.md:244` | Product lead |
| G-17 | Every spec is Draft with no acceptance process, so R10 either blocks forever or is ignored | `feature-specs/README.md:19-25`, `AGENTS.md:119` | Product lead |
| G-18 | Team plan omits annotators, design, support/on-call, security and legal, while gates assign work to those roles | `operations-and-pilot.md:132-142`, `phase-plan.md:419,799` | Programme lead |
| G-19 | Pilot is executed and certified by the same people; the model is approved by its developer | `phase-plan.md:736`, `operations-and-pilot.md:139`, `phase-plan.md:519` | Programme lead |
| G-20 | Legal review of advisory content is a "route", never a gate | `phase-plan.md:121,636`, `progress-tracker.md:201` | D6 |
| G-21 | Appendix F test catalogue and Appendix H launch checklist have no requirement IDs, owners, evidence or signature fields, so traceability and "signed" cannot be verified | `appendices.md:164,236`, `phase-plan.md:814` | QA lead |
| G-22 | Device, app-distribution and SMS/WhatsApp provisioning are unscheduled long-lead dependencies | `phase-plan.md:393,607,663`, `roadmap-and-resources.md:133` | Field ops |
| G-23 | Drift monitoring names signals but sets no threshold, window, minimum sample or action | `operations-and-pilot.md:108,122` | ML lead |
| G-24 | Shipped abstention threshold is not a column on `image_predictions`, so abstention cannot be reproduced or audited | `TRD.md:753`, `05:103` | Backend lead |
| G-25 | Retention undefined for the most sensitive data class; backups resurrect deleted rows; no on-device TTL or encryption requirement | `05:274,279`, `TRD.md:684` | D10 |

---

## 5. What this audit could not fix

These need a human decision, not an edit. They are recorded as open above; nothing here
should be resolved by an agent picking a default.

1. **The role model (X-2).** Whether "agronomist" is a fifth role, an attribute of
   `pathologist`, or an external approver who never logs in. Every advisory approval path
   depends on the answer, and `update.md:38` says expert capacity is the binding constraint.
2. **Scheduled absence sampling (C-2).** Whether field capacity exists to collect verified
   negatives. If not, the product must stop implying discrimination metrics.
3. **Numeric floors (C-1, C-3).** Must come from measurement under D8, not from this audit.
   R6 forbids inventing them, and inventing them here would have created the very defect
   this audit exists to find.
4. **Schedule and budget (X-9, X-10).** Both are currently unachievable as written and need
   re-basing against the actual team and the actual season window.
5. **Data controller (G-25, D10).** Determines consent wording, retention values and the
   lawful basis for image collection.
6. **The design authority and the chatbot folder (X-11 to X-13).** Two artifacts appeared
   during this audit that the rules forbid or exclude. Neither can be reconciled by editing
   a spec: `DESIGN.md` must either go or be formally demoted, and `chatbot/` needs an ADR or
   deletion before someone scaffolds into it.
7. **Whether to keep the forecast track in v1 at all.** Given C-2, C-5 and G-11, the honest
   options are: invest in absence sampling and a blinded label pipeline, or ship photo
   assessment only and move the area outlook to v2. That is a scope decision above this
   audit's authority.

---

## 6. How to re-run this audit

The checks that found the critical issues were mechanical, not clever:

1. For each gate, ask: *what number would have to be true for this to fail?* If there is no
   number, the gate is decorative.
2. For each safety rule, find the code path that enforces it. If the enforcement point is a
   UI label, the rule is not enforced.
3. For each state name, grep it across the repository. Names that appear once are usually
   phantoms.
4. For each threshold, find its value. If the value lives in an open question, the feature is
   blocked — record it as a decision, not a note.
5. For each decision, check it has one owner and a date. Joint ownership with no tie-breaker
   and no date is not a decision.
