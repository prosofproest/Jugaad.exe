# PS-03 — AI-Based Early Pest and Disease Outbreak Prediction Network

An explainable, offline-tolerant decision-support platform with **two separate outputs**:

- **Photo assessment** — what might be visible on one plant (one image + crop context).
- **Area outlook** — how likely a threat is in an area over a window
  (crop × target × geography × horizon).

Neither is a laboratory confirmation. Neither is a confirmed outbreak. The platform abstains
when evidence is insufficient and shows data coverage wherever risk is displayed.

**Status (2026-11-06):** documentation only. No application code exists yet.

---

## 1. Start here

| If you want to… | Read |
|---|---|
| Work on this repository | [`docs-context/AGENTS.md`](docs-context/AGENTS.md) — rules, hard stops, workflow |
| Understand the product and v1 scope | [`docs-context/project-overview.md`](docs-context/project-overview.md) |
| Change a feature | [`feature-specs/`](feature-specs/README.md) — the implementation contract |
| Know what is decided and what is next | [`docs-context/progress-tracker.md`](docs-context/progress-tracker.md) |
| See the detailed work in every phase | [`docs-context/phase-plan.md`](docs-context/phase-plan.md) |
| Read the original report | [`totalcontent.md`](totalcontent.md) — the supplied 55-chapter blueprint |
| Read the condensed report | [`summary.md`](summary.md) |
| Read the realism audit | [`update.md`](update.md) — why v1 is narrow |

---

## 2. Document map

### Operating context (`docs-context/`)

| File | Covers |
|---|---|
| `AGENTS.md` | Non-negotiable rules R1–R10, read order, definition of done, vocabulary |
| `project-overview.md` | Problem, vision, users, stakeholders, scope, use cases, objectives, programme shape |
| `architecture-context.md` | Stack, components, module boundaries, flows, invariants, security, deployment |
| `ui-context.md` | Wording, tokens, components, screens, states, maps, accessibility, surface detail |
| `code-standards.md` | Python/TS conventions (React Native + Next.js), API, security, ML reproducibility, testing, monitoring |
| `ai-workflow-rules.md` | Agent procedure, honesty rules, hard stops, handoff format |
| `data-foundation.md` | Data strategy, image collection, labelling, cleaning, splits, weather, history |
| `ml-models.md` | Image and forecast model design, training, evaluation, calibration, explainability |
| `operations-and-pilot.md` | Testing, pilot, deployment, monitoring, team, metrics, demo, future |
| `roadmap-and-resources.md` | Phase roadmap, budget logic, risk register rationale |
| `phase-plan.md` | Detailed work breakdown for every phase: workstreams, deliverables, gates, owners |
| `appendices.md` | Appendices A–H: templates, checklists, glossary, launch gates |
| `progress-tracker.md` | Phase gates, workstreams, decisions D1–D6, ADRs, risks, changelog |

### Feature specifications (`feature-specs/`)

| # | Spec | Covers |
|---|---|---|
| 01 | [Design system](feature-specs/01-design-system.md) | Tokens, components, states, accessibility |
| 02 | [Reporting and capture](feature-specs/02-reporting-and-capture.md) | Context, camera, quality gate, offline queue, result |
| 03 | [Auth, roles and consent](feature-specs/03-auth-and-roles.md) | Identity, sessions, RBAC, consent, privacy requests |
| 04 | [Expert review](feature-specs/04-expert-review.md) | Queue, triage, verification states, evidence, audit |
| 05 | [Data layer](feature-specs/05-data-layer.md) | Schema, constraints, PostGIS, storage, migrations, registry |
| 06 | [Forecast and risk map](feature-specs/06-forecast-and-risk-map.md) | Area outlook, no-score gate, risk bands, map layers |
| 07 | [Advisory and alerts](feature-specs/07-advisory-and-alerts.md) | Approved content, trigger policy, dedupe, delivery |

### Shared components (`components/`)

`components/README.md` states the rules for shared web components. The folder is empty until
scaffolding begins.

---

## 3. Blueprint chapter map

`totalcontent.md` is the supplied 50+ page report (55 chapters + Appendices A–H). This table
shows where each chapter is covered. **Coverage is documentation, not v1 scope approval**;
scope is decided in `progress-tracker.md` §4 and §2.

| Chapter | Topic | Covered in |
|---|---|---|
| 01 | Project overview and vision | `project-overview.md` §1–3 |
| 02 | Executive summary | `summary.md` §1–3; `project-overview.md` |
| 03 | Abstract and keywords | `summary.md` §1–3 |
| 04 | Background and agricultural context | `project-overview.md` §2.1 |
| 05 | Problem statement | `project-overview.md` §2 |
| 06 | Objectives and measurable outcomes | `project-overview.md` §10 |
| 07 | Scope and boundaries | `project-overview.md` §7–8 |
| 08 | Stakeholder analysis | `project-overview.md` §5.1 |
| 09 | User personas and needs | `project-overview.md` §5 |
| 10 | Use cases and user journeys | `project-overview.md` §9 |
| 11 | Functional requirements | `feature-specs/02`–`07` |
| 12 | Non-functional requirements | `feature-specs/02`–`07`; `code-standards.md` |
| 13 | High-level system architecture | `architecture-context.md` §1–7 |
| 14 | Technology stack selection | `architecture-context.md` §2, §16 |
| 15 | Farmer mobile application design | `ui-context.md` §5, §12.1 |
| 16 | Expert review portal | `ui-context.md` §12.2; `feature-specs/04` |
| 17 | Regional dashboard and GIS | `ui-context.md` §7, §12.3; `feature-specs/06` |
| 18 | Data strategy overview | `data-foundation.md` §1–2 |
| 19 | Image dataset collection | `data-foundation.md` §3 |
| 20 | Image labelling protocol | `data-foundation.md` §4 |
| 21 | Data cleaning and preprocessing | `data-foundation.md` §5 |
| 22 | Dataset splitting and leakage prevention | `data-foundation.md` §6 |
| 23 | Weather and environmental data | `data-foundation.md` §7 |
| 24 | Historical records and regional observations | `data-foundation.md` §8 |
| 25 | Database design | `feature-specs/05`; `architecture-context.md` §6 |
| 26 | Backend API design | `feature-specs/05`; `architecture-context.md` §9; `code-standards.md` §6 |
| 27 | Image diagnosis: problem formulation | `ml-models.md` §1 |
| 28 | Image model architectures | `ml-models.md` §2 |
| 29 | Image preprocessing and augmentation | `ml-models.md` §3 |
| 30 | Image model training workflow | `ml-models.md` §4; `code-standards.md` §11 |
| 31 | Image model evaluation | `ml-models.md` §5 |
| 32 | Image confidence and explainability | `ml-models.md` §6 |
| 33 | Outbreak forecasting: task definition | `ml-models.md` §7; `feature-specs/06` §2 |
| 34 | Forecast feature engineering | `ml-models.md` §8 |
| 35 | Forecast model baselines | `ml-models.md` §9 |
| 36 | Forecast calibration and thresholds | `ml-models.md` §10; `feature-specs/06` §5 |
| 37 | Spatial and temporal forecasting | `ml-models.md` §11 |
| 38 | Combining image and forecast outputs | `ml-models.md` §12 |
| 39 | Risk map and geospatial analytics | `feature-specs/06` §7–8; `ui-context.md` §7 |
| 40 | Preventive advisory engine | `feature-specs/07` §2–4 |
| 41 | Alert and notification design | `feature-specs/07` §5–7 |
| 42 | Offline-first engineering | `feature-specs/02` §3, §7; `ai-workflow-rules.md` §6 |
| 43 | Security architecture | `architecture-context.md` §14; `feature-specs/03` |
| 44 | Privacy and responsible AI | `feature-specs/03` §5–7; `project-overview.md` §12 |
| 45 | Testing strategy | `operations-and-pilot.md` §1; `code-standards.md` §12 |
| 46 | Pilot design and field validation | `operations-and-pilot.md` §2 |
| 47 | Deployment and infrastructure | `architecture-context.md` §10; `operations-and-pilot.md` §3 |
| 48 | Monitoring and model maintenance | `operations-and-pilot.md` §4; `code-standards.md` §13 |
| 49 | Project team and responsibilities | `operations-and-pilot.md` §5; `progress-tracker.md` §9 |
| 50 | Implementation roadmap | `progress-tracker.md` §2; `roadmap-and-resources.md` §1 |
| 51 | Budget and resource planning | `roadmap-and-resources.md` §2; `progress-tracker.md` §10 |
| 52 | Risk register and mitigation | `progress-tracker.md` §6; `roadmap-and-resources.md` §3 |
| 53 | Success metrics and impact evaluation | `operations-and-pilot.md` §6; `progress-tracker.md` §11 |
| 54 | Demonstration scenario | `operations-and-pilot.md` §7; `project-overview.md` §17 |
| 55 | Conclusion and future enhancements | `operations-and-pilot.md` §8; `project-overview.md` §18 |
| A | Sample farmer-facing alert | `appendices.md` Appendix A |
| B | Sample image assessment wording | `appendices.md` Appendix B; `ui-context.md` §2 |
| C | Example forecast API response | `appendices.md` Appendix C; `feature-specs/06` §7 |
| D | Database entity checklist | `appendices.md` Appendix D; `feature-specs/05` §4 |
| E | API and integration checklist | `appendices.md` Appendix E; `feature-specs/05` §9 |
| F | Example test cases | `appendices.md` Appendix F |
| G | Glossary | `appendices.md` Appendix G; `docs-context/AGENTS.md` §10 |
| H | Final launch-readiness checklist | `appendices.md` Appendix H; `progress-tracker.md` §2 |

---

## 4. Non-negotiables (summary)

1. Photo assessment and area outlook are never merged.
2. The system abstains instead of guessing.
3. No report is not evidence of absence; coverage is always visible.
4. Human verification is mandatory; models never verify.
5. No chemical advice, ever.
6. No fabricated data, metrics or predictions; demo data is labelled.
7. Every prediction is traceable and append-only.
8. Offline-first is core, not an upgrade.
9. Privacy by default; approximate location, no PII in dashboards.
10. Spec before code; the tracker is updated in the same change.

Full text and hard stops: [`docs-context/AGENTS.md`](docs-context/AGENTS.md) §3 and §8.

---

## 5. Precedence

```
explicit user instruction
  > docs-context/AGENTS.md
  > feature-specs/
  > architecture-context.md / ui-context.md / code-standards.md
  > progress-tracker.md decisions
  > totalcontent.md / summary.md / update.md
```

For v1 scope conflicts, `update.md` wins over the maximal blueprint. Record the resolution
in `progress-tracker.md` §4.
