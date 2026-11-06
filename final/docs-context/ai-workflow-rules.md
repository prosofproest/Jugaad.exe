# AI workflow rules

**Purpose:** detailed operating procedure for AI agents (and humans using AI assistance)
in this repository. `AGENTS.md` states the rules; this file explains how to apply them.
**Last updated:** 2026-11-06

---

## 1. Precedence

```
explicit user instruction
  > AGENTS.md
  > feature-specs/<feature>.md
  > architecture-context.md / ui-context.md / code-standards.md
  > progress-tracker.md decisions
  > summary.md / totalcontent.md / update.md
```

- A user instruction that conflicts with a **hard stop** (§7) is refused, with the reason.
- A user instruction that changes scope (new crop, new role, new data source) requires a
  spec update and a decision-log entry, not just code.
- If two documents conflict and neither is a hard stop, prefer the more conservative
  option and record the ambiguity in the tracker.

---

## 2. Task intake

Before touching files, produce a short plan containing:

1. **Goal** — one sentence, in user terms.
2. **Requirement IDs** — from the relevant feature spec (e.g. `FR-02-04`).
3. **Files to touch** — concrete paths.
4. **Test that proves it** — the command and the expected result.
5. **Out of scope** — what you are deliberately not doing.
6. **Open questions** — anything that would change the design.

If the task is small and unambiguous (typo, single-line fix), the plan can be two lines.

If any of these are true, **stop and ask**:

- The task requires a decision from `progress-tracker.md` §4.
- The task changes a database schema, API contract or verification state machine.
- The task touches advisory wording, roles, permissions or audit.
- The task involves real farmer data or images.
- The task requires a new dependency or external service.
- Two source documents give incompatible instructions.

---

## 3. Implementation loop

```
read spec → write failing test → smallest implementation → pass test
          → add negative test → run suite → update docs → summarise
```

Rules:

- **One vertical slice at a time.** Do not scaffold six modules "for later".
- **Match existing patterns.** If no pattern exists, state the pattern you are
  introducing and why.
- **No drive-by refactors.** Note them as follow-ups instead.
- **No silent fallbacks.** If an external call fails, return the defined failure state;
  do not substitute a default value.
- **No invented constants.** Thresholds, cooldowns, limits and risk bands come from
  config with a documented source. If unknown, use a named placeholder and mark it
  `# TODO(D1)` or similar, never a magic number presented as final.
- **Feature flags for incomplete paths.** An unfinished forecast must not silently show
  a score.

### Definition of a complete slice

- Requirement implemented, including failure path.
- Tests: happy path + at least one negative case.
- API/schema/docs updated if touched.
- Tracker status updated.
- Commands run and their real output reported.

---

## 4. Data and model honesty rules

These are the most common ways this project could become misleading.

| Temptation | Required behaviour |
|---|---|
| Report accuracy from a random image split | Group by farm/field/event; state the split rule |
| Use PlantVillage as validation | Public data for pretraining/benchmark only; field-only test set |
| Quote the best threshold | Report at the shipped abstention threshold |
| Hide abstention rate | Always report it next to accuracy/F1 |
| Fill missing weather | Return `insufficient_data`; record the gap |
| Treat zero reports as negatives | Model coverage/surveillance; mark unobserved, not negative |
| Present a demo forecast | Label `demo` in data, API and UI |
| Auto-promote a model | Manual approval; registry status required |
| Tune on the test set | Freeze the test set before model selection |
| Report one aggregate number | Per-class, per-region, per-device where sample size allows |

If a number cannot be computed from available data, write **"not measured"**, not an
estimate.

---

## 5. Safety rules in code

- Advisory content is data, not generated text. No LLM call in the advisory path.
- The advisory validator rejects content containing chemical product names, doses, units
  per volume, or application intervals. Add a test for each rejection class.
- Risk bands are mapped from config with an approval record; no inline thresholds.
- Verification transitions are enforced server-side by a state machine; the client cannot
  set `confirmed` directly.
- A photo assessment row cannot exist with `status=assessed` unless a quality gate result
  is attached and passed.
- Forecast label queries must filter on evidence tier (`confirmed`, `probable`), `verified_at
  <= cutoff` and event date `<= cutoff`. Add tests that insert an `unverified` report, a
  `needs_visit` report and a `probable` report and assert the first two are excluded and the
  third is included with its evidence tier (D7).
- Any export endpoint requires a role check and writes an audit event before returning.

---

## 6. Offline and sync rules

- Every client-created entity carries a `client_id` (UUID v4) generated on device.
- Observation creation and upload completion require `Idempotency-Key`.
- The server returns the existing record for a repeated key; it never creates a second.
- Client state machine: `draft → queued → uploading → uploaded → assessed | failed`.
  `failed` is retryable; `uploaded` is terminal for the upload step.
- Local DB migrations must preserve unsent rows. Test upgrade with a populated queue.
- Never delete a local report because the server rejected it; mark it and surface why.
- Cached forecasts carry `valid_to`; the client computes `is_stale` locally and shows the
  stale banner even when offline.

---

## 7. Hard stops

Refuse, explain, and offer the compliant alternative:

1. Generating or paraphrasing pesticide/herbicide/fungicide dosage or application advice.
2. Describing a photo assessment as a diagnosis, lab result or confirmed outbreak.
3. Removing abstention, coverage, freshness or uncertainty indicators.
4. Auto-verifying cases or letting a model write verification status.
5. Training or evaluating on data without documented permission.
6. Putting real personal/farm data into fixtures, demos, screenshots or tests.
7. Weakening auth, RBAC, audit or upload validation for convenience.
8. Fabricating metrics, partner names, datasets or field results.
9. Building farm-level risk from block-level inputs.
10. Presenting synthetic/demo predictions as operational warnings.

Compliant alternatives:

- "Here is the approved non-chemical advisory content structure; wording must be supplied
  and approved by the local agronomist."
- "I can add the escalation path instead of a treatment recommendation."
- "I can show the result as a possible symptom match with a confidence band."
- "I can implement the no-score state for this case."

---

## 8. Documentation sync matrix

| Change | Update |
|---|---|
| New/changed requirement | Feature spec + tracker |
| New API field/endpoint | Feature spec + OpenAPI + architecture §9 |
| Schema/migration | `05-data-layer.md` + architecture §6 + tracker |
| New role/permission | `03-auth-and-roles.md` + architecture §7 |
| New user-facing copy | `ui-context.md` examples if canonical |
| New risk band/threshold | `06-...` + tracker decision |
| Advisory format change | `07-...` + validator tests |
| New dependency/provider | `architecture-context.md` §2/§8 + ADR |
| Decision resolved | `progress-tracker.md` §4 + relevant spec |
| Scope cut/addition | `project-overview.md` §7/§8 + tracker |

---

## 9. Testing expectations by change type

| Change | Minimum evidence |
|---|---|
| Domain rule | Unit test, positive + negative |
| API endpoint | Contract test + auth test (403 for wrong role) |
| Migration | Apply on empty DB + apply on seeded DB; rollback note |
| Sync/queue | Test duplicate retry, interrupted upload, offline start |
| Image pipeline | Quality-gate unit tests; abstention path; version recorded |
| Forecast | Snapshot immutability; no-score on stale input; unverified excluded |
| Map layer | Verified/unverified/risk separation test; suppression threshold |
| Advisory | Validator rejects chemical content; approval required before retrieval |
| UI screen | Component/golden test for each state in `ui-context.md` §6 |

Report commands exactly as run. If a suite was not run, say so and why.

---

## 10. Handoff format

End every task with:

```md
## Summary
- What changed (files, behaviour)
- Requirement IDs implemented

## Verification
- Commands run + result (pass/fail counts)
- Manual checks performed

## Not done / follow-ups
- Deliberate omissions and why
- Open questions or decisions needed

## Risks
- Anything that could mislead users, weaken an invariant, or needs review
```

No claims beyond what was verified. "Should work" is not a verification result.

---

## 11. Reviewing AI-generated changes

Reviewers should check, in order:

1. **Safety invariants** — R1–R10 in `AGENTS.md`.
2. **Failure paths** — does the change handle abstention, stale, offline, unauthorised?
3. **Data honesty** — any fabricated number, metric or unlabelled demo data?
4. **Contract** — API/schema/docs consistent?
5. **Tests** — do they prove the behaviour, including a negative case?
6. **Scope** — anything unrelated or pre-emptive?
7. **Style** — matches `code-standards.md`.

An AI-generated change that compiles but skips failure paths is not complete.

---

## 12. Data foundation rules

Applies to collection, labelling, cleaning and splitting. Detail in `data-foundation.md`.

| Temptation | Required behaviour |
|---|---|
| Collect only clean, centred leaves | Collect devices, districts, seasons, lighting, backgrounds, severity |
| Discard ambiguous images | Keep hard negatives and `unknown`; they teach abstention |
| Let one labeler define classes | Handbook + independent subset + adjudication; measure agreement |
| Delete suspicious records | Quarantine with an owner and resolution |
| Fill a missing weather value | `insufficient_data`; record the gap |
| Split images randomly | Group by farm/field/event; document the rule |
| Tune on the test set | Freeze it before model selection |
| Use PlantVillage as validation | Pretraining/benchmark only; field-only test set |
| Treat zero reports as negatives | Model coverage/surveillance; mark unobserved |

---

## 13. Model and pilot rules

| Temptation | Required behaviour |
|---|---|
| Quote the best threshold | Report at the shipped abstention threshold |
| Promote on training metrics | Manual registry approval; frozen evaluation suite |
| Add a complex model for novelty | Beat the rules baseline on the operational metric |
| Report one aggregate number | Per-class, per-region, per-device where sample size allows |
| Present a demo forecast | `is_demo: true` in data, API and UI; excluded from operational alerts |
| Claim impact from usage | Pre-registered design, silent phase, comparison; otherwise "not measured" |
| Launch outside the season | Time the pilot to the epidemic window |
| Expand by request | Expansion rule: data, labels, advisory support, evaluation evidence |

If a number cannot be computed from available data, write **"not measured"**, not an
estimate.

---

## 14. Documentation sync for this blueprint

`../README.md` maps the 55 chapters and Appendices A–H to repository files. When a chapter's
content changes:

1. Update the mapped document (not `totalcontent.md`, which is the supplied source).
2. Update the affected feature spec if a requirement changed.
3. Update `progress-tracker.md` if scope, a decision or status changed.
4. Do not promote a documented capability to "in scope" without a tracker decision.
