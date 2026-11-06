# Strategic Update — Making the Project Best and Realistic

**Project:** PS-03 — AI-Based Early Pest and Disease Outbreak Prediction Network
**Document type:** Realism audit, scope decisions and recommended configuration
**Status:** Discussion draft — the six decisions in Section H remain open. They are tracked
as D1–D6 in [`docs-context/progress-tracker.md`](docs-context/progress-tracker.md) §4.
**Repository note:** this audit justifies the narrowed v1. It outranks the maximal
`totalcontent.md` for v1 scope. The chapter-to-file map is in [`README.md`](README.md).

---

## A. First, define "best"

"Best" pulls in three directions that conflict:

| Lens | What "best" means | What it optimises |
|---|---|---|
| **Field impact** | A farmer changes a decision because of it | Trust, timeliness, local relevance |
| **Academic rigour** | Defensible novelty + honest evaluation | Contribution, ablations, calibration, holdouts |
| **Sustainability** | Someone keeps paying after the pilot | Low operating cost, institutional owner |

A project that maximises one usually damages the others. The realistic "best" is: **narrow enough to validate, rigorous enough to publish, cheap enough to keep running.** Most failures come from choosing breadth (many crops, many districts) over depth (one crop done properly).

---

## B. The realism audit — eight hard truths

### 1. The forecast is the weak link, not the image model

Outbreak forecasting needs multiple seasons of verified, geolocated, surveillance-bias-corrected data. You will not have that at the start. Any claim of "outbreak prediction" in year one is not credible. The image model can reach useful performance in months; the forecast cannot.

### 2. Public image datasets will make your model look great and fail in the field

PlantVillage-style datasets are lab-condition, single-leaf, uniform-background. Models trained on them routinely drop 30–60 points of accuracy on farmer photos. Using them for the *baseline* is fine; using them for *validation* is a fatal methodological error.

### 3. Verification capacity is the real bottleneck

Every design assumes experts will review cases. In reality, one pathologist may cover 200 km. If the review queue isn't ruthlessly triaged, it becomes a backlog and the "verified" layer goes empty — which silently destroys the forecast track too.

### 4. "No reports" will be misread as "no disease"

This happens by users and possibly by your own model. Surveillance intensity must be a first-class feature *and* a visible UI element. Otherwise you build a system that is most confident where it is least informed.

### 5. Direct-to-farmer apps usually fail in smallholder contexts

Low install rates, data cost, digital literacy and trust barriers. The realistic channel is **B2B2C**: cooperatives, extension services, KVKs, NGOs, agri-input dealers or government departments push it to farmers. SMS/IVR/WhatsApp often outperform a native app for reach.

### 6. Advisory is a legal surface, not a content surface

Pesticide recommendations are regulated in most jurisdictions. One wrong dosage instruction creates liability and destroys trust. The safe design is non-chemical guidance + escalation, and that constraint should be architectural, not a policy note.

### 7. Offline-first is expensive and easy to get wrong

It is essential for the field, but conflict resolution, image compression, queue integrity and idempotency add real engineering cost. It is not a "phase 2 nice-to-have"; if you defer it, you will retrofit the data model.

### 8. A pilot without a counterfactual proves nothing

"Farmers who used it had less disease" is not evidence — they may have had less disease anyway. You need a silent phase, a comparison group, or at minimum a pre-registered lead-time measure.

---

## C. The recommended realistic configuration

This is the "sweet spot" worth defending:

```
Scope:        1 crop · 1 agro-climatic zone · 3–5 targets + healthy + abiotic look-alike + unknown
Image AI:     field-data fine-tuned lightweight CNN + quality gate + abstention + top-3
Forecast:     validated agronomic risk model (weather-driven) → ML only as a later overlay
Product:      mobile capture for field staff + farmer-facing SMS/WhatsApp outlook
Verification: extension-worker-first, pathologist only for escalations
Geography:    block/mandal level, not farm level
Timeline:     18 months to limited operational alerts
Team:         7–9 people
```

**The key inversion vs the blueprint:** lead with the **reporting + verification network and a rules-based risk model**, and let the image model be *assistive triage*. That gives you something useful in month 6 instead of month 18.

---

## D. The possibility space — options and trade-offs per layer

### D1. Crop and target selection

Choose on five criteria simultaneously: economic importance to smallholders, existing extension presence, visual distinctness of symptoms, availability of approved advisory content, and existence of a validated weather-driven risk model.

| Crop | Strong target candidates | Why realistic |
|---|---|---|
| **Tomato** | Late blight, early blight, leaf curl, bacterial spot | Huge public data, strong farmer familiarity, validated blight models exist |
| **Potato** | Late blight | BLITECAST / SimCast give a credible rules baseline immediately |
| **Rice** | Blast, bacterial leaf blight, brown spot | Enormous smallholder base; blast has weather models; strong public datasets |
| **Wheat** | Yellow/leaf/stem rust | CIMMYT rust surveillance infrastructure already exists to partner with |
| **Maize** | Fall armyworm | Pest (not disease) → detection + pheromone-trap data can substitute for history |
| **Cassava** | Mosaic, brown streak | High impact, but limited field data and harder logistics |
| **Banana** | Panama disease, BBW | Visually distinctive, but spread modelling is hard |

**Strongest single pick for a realistic pilot:** potato late blight or tomato late blight. Reason: a validated epidemiological model already exists, the disease is weather-driven (so forecast is tractable), symptoms are photographable, and advisory content is well established. You get a credible forecast on day one and improve it with data.

**Avoid** multi-crop "universal diagnosis" entirely in v1. It is the single most common way these projects become undeliverable.

### D2. Data acquisition — realistic paths, ranked

1. **Partner-collected field data** (extension workers, KVKs, plant clinics) — highest value, slowest; needs an MoU and per-image incentives.
2. **Existing plant clinic archives** (CABI Plantwise-style, university pathology departments) — often underused and already labelled by experts. Best ROI if you can get access.
3. **Public field datasets** (PlantDoc, Cassava, Rice Leaf, AgriPest, IP102 for pests) — good for pretraining and benchmarking, not validation.
4. **Farmer-submitted data from your own pilot** — starts sparse; useful after month 6.
5. **Synthetic / augmentation** — only to fix class imbalance, never to create a class.
6. **Satellite + weather proxies** — Sentinel-2 (free, 10 m, 5-day) for crop stage and vegetation anomalies; NASA POWER / ERA5-Land for weather; SoilGrids for soil context.

**Non-obvious move:** ask for *rejected* and *ambiguous* images too. Most datasets only keep confident labels, which teaches the model to never abstain. The abstention behaviour depends on having hard negatives.

### D3. Image AI — realistic approaches

| Approach | Realism | When to use |
|---|---|---|
| MobileNet/EfficientNet transfer learning | High | Default baseline, cheapest to deploy |
| ConvNeXt / ViT fine-tune | Medium | Only if you have >5k field images per crop |
| CLIP/DINOv2 embeddings + few-shot head | Medium-high | Great for rare classes and fast class expansion |
| Object detection (YOLO) | Medium | If pests (multiple insects) are a target and you can label boxes |
| Segmentation | Low initially | Only if lesion area is an operational requirement |
| On-device (TFLite/ONNX) | High value, medium effort | Essential for offline capture; quantise after accuracy is settled |

**Realistic quality target:** top-3 candidate classes + calibrated confidence band + abstention, not single-label diagnosis. This is both more honest and more useful.

Two technical additions that disproportionately improve field performance:

- **Quality gate as a separate model** (blur, exposure, no-leaf, distance) — arguably more valuable than the classifier itself.
- **Domain adaptation** from public → field data (fine-tune on a small field set, or use strong augmentation + consistency training).

### D4. Forecast — the realistic ladder

This is where most projects overreach. The ladder, in order:

1. **Agronomic risk index** (weather thresholds + crop stage). Examples: BLITECAST/SimCast (potato blight), Mills table (apple scab), DMCAST (grape), rice blast leaf-wetness models, rust weather models. **This is your day-one forecast and it is defensible.**
2. **Logistic regression** on weather windows + crop stage + lagged reports. Interpretable, calibratable.
3. **Gradient boosting** (XGBoost/LightGBM) once you have 2+ seasons.
4. **Spatiotemporal models** (ST-GNN, ConvLSTM) only with dense longitudinal data — realistically year 3+.

Also consider **nowcasting instead of forecasting** early on: "current risk given the last 10 days" is easier, more accurate, and still actionable. You can ship a 7-day outlook later.

**Novelty hook that is both academic and useful:** *surveillance-bias-aware risk estimation* — modelling the probability that an area is unobserved rather than disease-free. This is genuinely under-addressed and publishable, and it fixes hard truth #4.

### D5. Product and channel

| Channel | Reach | Cost | Trust | Verdict |
|---|---|---|---|---|
| Native app | Low | High | Medium | Build for field staff, not all farmers |
| WhatsApp bot | High | Low | High | Strong candidate for farmer-facing |
| SMS | Highest | Very low | High | Best for alerts in low-smartphone areas |
| IVR / voice | High (low literacy) | Medium | High | Underrated; strong for advisory |
| USSD | Medium | Low | Medium | Where data is very expensive |
| Web dashboard | Admin only | Low | — | For district officers |

**Realistic architecture:** native/Flutter app for capture (needs camera + offline), **SMS/WhatsApp for delivery** of outlook and alerts. Don't force one channel to do both jobs.

### D6. Business model — who actually pays

| Funder | Fit | Risk |
|---|---|---|
| Government agriculture department | Strong — public good, surveillance value | Procurement cycles, political change |
| Cooperative / FPO | Strong — direct member value | Small budgets |
| NGO / development programme | Strong for pilot | Time-bound funding |
| Crop insurer | Strong — risk data for index insurance | Different incentive structure |
| Agri-input company | Weak ethically | Advisory bias toward products they sell |
| Farmer subscription | Very weak at smallholder scale | Willingness to pay near zero |

**Realistic path:** grant/NGO/government funded pilot → cooperative or insurer funded operations. Avoid input-company funding for the advisory layer; it corrupts the trust model.

### D7. Deployment and cost

- **Inference:** CPU is sufficient for MobileNet-class models at pilot scale. GPU only for training. This cuts operating cost dramatically.
- **Hosting:** one small VM + managed Postgres + object storage is enough for a district pilot.
- **Maps:** MapLibre + PostGIS + vector tiles; don't build custom GIS.
- **MLOps:** a model registry table + artefact storage is enough; don't stand up Kubeflow.
- **Weather:** NASA POWER/ERA5-Land are free — avoid paid providers until you need resolution.

Rough realistic pilot cost envelope (order of magnitude, 18 months, South Asia): **$150k–$400k**, dominated by people and field data collection, not infrastructure. Infrastructure is usually <10%.

---

## E. What to actually cut from the blueprint for v1

The blueprint is a 55-chapter maximal system; a realistic v1 should implement maybe 40% of it.

**Keep**

- Reporting
- Offline queue
- Quality gate
- Image triage with abstention
- Expert review
- Rules-based risk
- Separate map layers
- Approved advisory
- Audit
- Basic monitoring

**Defer**

- Spatiotemporal deep learning
- Drone/satellite analytics
- On-device inference
- Multi-language beyond one
- Multi-crop
- IoT sensors
- Complex RBAC beyond three roles
- Automated retraining

**Cut entirely from v1**

- Generative AI advisory
- Autonomous chemical guidance
- Farm-level risk precision
- Universal diagnosis

**Sequencing principle:** each phase must produce something a real user would use on its own, not a stepping stone that only makes sense once the next phase lands.

---

## F. Evaluation design that will actually convince people

- **Image:** group-held-out by farm/field, field-only test set, per-class recall + macro F1 + calibration (ECE/reliability), abstention rate reported alongside accuracy. Report performance *at the abstention threshold you ship*, not the best threshold.
- **Forecast:** chronological holdout, spatial holdout by district, Brier + PR-AUC + reliability, and **lead time distribution** vs the existing advisory system.
- **Pilot:** silent phase (predictions not shown) → limited alert phase → comparison with a matched control area or a stepped-wedge design. Pre-register the primary outcome (e.g., median lead time to first verified report) before launch.
- **Trust/usability:** task completion, comprehension of uncertainty wording, alert opt-out rate.
- **Negative results are publishable** — "image triage did not improve lead time but did improve prioritisation" is a legitimate and useful finding.

**The most credible single metric:** median lead time from first farmer report to verified expert confirmation, compared with baseline. It is measurable, meaningful, and hard to fake.

---

## G. Domain-specific risks the blueprint under-weights

| Risk | Why it matters | Mitigation |
|---|---|---|
| **Advisory liability** | Wrong dosage → crop loss or health harm | Non-chemical only; escalation path; legal review; disclaimers |
| **Data protection** | Farm locations + identities are sensitive (DPDP Act 2023 in India, GDPR-like elsewhere) | Approximate location, consent, retention policy, DPIA |
| **Biosecurity** | Public disease maps could be used to infer farm vulnerability | Aggregation thresholds, access control |
| **Adversarial input** | Farmers may submit others' images or game compensation | Provenance metadata, duplicate detection, spot checks |
| **Model monoculture** | Everyone uses the same public datasets → same blind spots | Field data collection is the moat |
| **Partner dependency** | Extension partner withdraws mid-pilot | Dual partnerships, data ownership agreement upfront |
| **Seasonality** | You may launch outside the disease season and learn nothing | Time the pilot to the epidemic window |
| **Expert burnout** | Review queue becomes unpaid labour | Compensation, workload caps, triage |

**The seasonality point is underrated:** a 12-month pilot that misses the epidemic season produces zero forecast evidence. Plan the calendar around the disease, not the funding cycle.

---

## H. The decisions that determine everything

Before any code, these six answers fix the architecture:

1. **Which crop + which 3–5 targets + which agro-climatic zone?**
   → Determines data needs, forecast feasibility, advisory content, partner.
2. **Is the forecast a *nowcast* or a *7-day outlook* in v1?**
   → Determines whether you need historical data at all in year one.
3. **Who verifies, how many cases/day, and what's the SLA?**
   → Determines queue design, staffing, and whether the verified layer is viable.
4. **Who is the paying/owning institution after the pilot?**
   → Determines deployment model and cost ceiling.
5. **What is the single primary outcome metric?**
   → Determines pilot design; must be pre-registered.
6. **What is the legal position on advisory content?**
   → Determines whether the advisory engine is even in v1.

---

## I. Academic project vs startup — different "best"

### If this is an academic/student deliverable

- Novelty should come from the **coupling + uncertainty handling**, not from a new architecture. "Calibrated abstention in field crop triage" and "surveillance-bias-aware risk" are defensible contributions.
- Realistic dataset: public data + 500–2,000 field images + expert labels. That is enough for a strong thesis.
- A working prototype + rigorous evaluation on a frozen field test set + a rules-based forecast baseline is a complete, credible project.
- Publishable artefacts: a field-image dataset paper, a calibration study, a pilot protocol.

### If this is a real deployment

- The moat is the **verification network and field data**, not the model.
- The first hire after engineering is a **field operations lead**, not another ML engineer.
- Success in year one = a functioning reporting → verification → advisory loop, not forecast accuracy.

---

## J. Bottom line

The blueprint is sound but written as a *maximal* system. The best realistic version is a **deliberately minimal** one:

> One crop, one zone, three to five targets, a rules-based weather risk model, an assistive image triage with honest abstention, extension-worker verification, and SMS/WhatsApp delivery — validated over one full epidemic season against a pre-registered lead-time metric.

Everything else in the 55 chapters is a roadmap for years 2–4, not for v1. The project's real innovation is not the model — it is proving that **a verified reporting loop plus calibrated uncertainty beats a fancy predictor with no ground truth.**

---

## Next artefacts to produce

- [ ] **Decision sheet** — the six decisions in Section H, each with options, consequences and a recommended default. (Options and defaults are drafted in `docs-context/progress-tracker.md` §4; resolution still required.)
- [x] **Realistic 18-month phase plan** — deliverables, dependencies and go/no-go gates per phase (`docs-context/progress-tracker.md` §2; `docs-context/phase-plan.md`; `docs-context/roadmap-and-resources.md` §1).
- [ ] **Pilot protocol** — site selection, silent/limited-alert phases, comparison design, pre-registered outcome. (Structure in `docs-context/operations-and-pilot.md` §2; sites and dates not yet set.)
- [ ] **Data acquisition plan** — partner MoUs, archive access, field collection targets, labelling throughput. (Method in `docs-context/data-foundation.md`; partners and targets not yet set.)

---

*This document records strategic analysis, not committed scope. The six decisions in Section H must be resolved with local agricultural experts before implementation begins.*
