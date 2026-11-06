PS-03  |  AGRITECH & AI
AI-Based Early Pest and
Disease Outbreak Prediction Network
50+ Page Complete Project Report and Implementation Blueprint

PROJECT PURPOSE — Develop a farmer-centred early-warning platform that combines crop images, weather, historical records and regional observations to assess possible symptoms and estimate local pest and disease risk—while communicating uncertainty and recommending safe preventive next steps.

Detailed academic and engineering project document

 How to use this report
This report is a development blueprint. It is designed to support project planning, academic documentation, prototype development and pilot preparation. It does not assume that a particular crop, disease, weather provider or region has already been selected. Those decisions must be made with local agricultural experts.
•	Read Chapters 1–10 to understand the product, users, requirements and architecture.
•	Use Chapters 11–20 to establish the data foundation and model development approach.
•	Use Chapters 21–30 to plan forecasting, mapping, advisory and alert capabilities.
•	Use Chapters 31–40 to build secure, reliable and testable software.
•	Use Chapters 41–50 to plan the pilot, deployment, team, budget and evaluation.
•	Treat all example thresholds and sample outputs as design examples until locally validated.
Important scientific and operational note
A photo-based symptom assessment and a regional outbreak forecast are different outputs. The photo model estimates what may be visible on an individual plant. The forecast model estimates future risk for a defined crop, target, area and time window. Neither output should be represented as laboratory confirmation. The platform must be able to abstain and show insufficient data.

 Table of contents
01. Project overview and vision
02. Executive summary
03. Abstract and keywords
04. Background and agricultural context
05. Problem statement
06. Objectives and measurable outcomes
07. Scope and boundaries
08. Stakeholder analysis
09. User personas and needs
10. Use cases and user journeys
11. Functional requirements
12. Non-functional requirements
13. High-level system architecture
14. Technology stack selection
15. Farmer mobile application design
16. Expert review portal
17. Regional dashboard and GIS
18. Data strategy overview
19. Image dataset collection
20. Image labelling protocol
21. Data cleaning and preprocessing
22. Dataset splitting and leakage prevention
23. Weather and environmental data
24. Historical records and regional observations
25. Database design
26. Backend API design
27. Image diagnosis: problem formulation
28. Image model architectures
29. Image preprocessing and augmentation
30. Image model training workflow
31. Image model evaluation
32. Image confidence and explainability
33. Outbreak forecasting: task definition
34. Forecast feature engineering
35. Forecast model baselines
36. Forecast calibration and thresholds
37. Spatial and temporal forecasting
38. Combining image and forecast outputs
39. Risk map and geospatial analytics
40. Preventive advisory engine
41. Alert and notification design
42. Offline-first engineering
43. Security architecture
44. Privacy and responsible AI
45. Testing strategy
46. Pilot design and field validation
47. Deployment and infrastructure
48. Monitoring and model maintenance
49. Project team and responsibilities
50. Implementation roadmap
51. Budget and resource planning
52. Risk register and mitigation
53. Success metrics and impact evaluation
54. Demonstration scenario
55. Conclusion and future enhancements
Additional appendices: sample alert, sample image result, sample forecast payload, database entity checklist, API checklist, test plan, glossary and launch checklist.

 Project overview and vision
The project proposes a practical early-warning network that helps farmers and agricultural support teams identify possible crop problems sooner. It combines field photographs, crop context, weather, historical observations and verified regional reports. The system is intended to support decisions, not replace field inspection or expert diagnosis.
Vision
Create a trusted, accessible and locally relevant digital service that turns fragmented agricultural observations into useful early awareness. A farmer should be able to submit a photograph, understand what the system can and cannot infer, view area-level risk and take a sensible next step.
Mission
Deliver two distinct forms of intelligence: image-based symptom triage for an individual plant and time-bound outbreak risk estimation for a defined crop and geographic area. Connect them through shared case management, verified observations and responsible advisory delivery.
Guiding principles
•	Local validation before broad rollout.
•	Clear separation between observation, diagnosis and forecast.
•	Uncertainty and data coverage shown in the interface.
•	Human review for ambiguous or high-impact cases.
•	Offline-tolerant operation for rural connectivity conditions.
Implementation points
•	Choose a narrow first geography and crop set; broad coverage should follow demonstrated performance.
•	Define what an alert means operationally and who responds to it.
•	Treat farmer trust as a core product metric, not a marketing outcome.
PROJECT DEFINITION — An explainable, offline-tolerant AI decision-support platform for crop symptom assessment and geographically localised pest and disease early warning.


 Executive summary
Pest and disease damage often becomes costly when the first signs are missed or local information arrives too late. Farmers may face uncertainty about symptoms, limited access to experts and weak connectivity. This project responds by creating a coordinated reporting, prediction and advisory workflow.
What the platform does
A farmer selects a crop and approximate location, captures a clear image and submits a report. The image service checks quality and estimates likely visible symptom classes. Separately, the forecast service estimates whether environmental and regional conditions favour a defined crop threat over a future time window. The application displays each output with its own evidence and limitations.
Who benefits
Farmers receive understandable triage and local warnings. Extension workers gain a structured queue and area view. Agronomists can verify cases and curate advisory content. Programme administrators can monitor trends, data coverage and operational response.
Expected value
•	Earlier scouting and reporting.
•	More consistent evidence for extension teams.
•	Prioritisation of field visits.
•	A growing, quality-controlled local dataset.
•	More transparent communication of uncertainty.
Implementation points
•	Do not claim that an AI system prevents disease by itself; prevention depends on farmer action and local agronomic support.
•	Measure lead time, false-alert burden and verified outcomes alongside model metrics.

 Abstract and keywords
This report presents the design of an AI-Based Early Pest and Disease Outbreak Prediction Network. The proposed system integrates computer vision, machine learning, weather information, crop-stage context, historical records and regional observations to support early detection and risk communication.
Abstract
The platform contains an image diagnosis pipeline and a distinct outbreak forecasting pipeline. The image pipeline assesses whether a submitted field image resembles a supported disease, pest symptom, healthy condition or unknown class. The forecasting pipeline estimates risk for a defined crop, target, location and horizon. Outputs are combined in a farmer application, expert review portal and regional dashboard. The design includes data governance, human verification, offline synchronisation, uncertainty communication, monitoring and staged field validation.
Keywords
Agritech; artificial intelligence; computer vision; crop disease; pest monitoring; outbreak forecasting; geospatial analytics; weather data; early warning; decision support.
Research contribution
The main contribution is an end-to-end architecture and operating model that links image triage with regional forecasting without treating them as the same prediction task. It emphasises local data, verification, calibration and responsible alerts.
Implementation points
•	Use this abstract as a project synopsis and update it after the crop, region and target organisms are selected.

 Background and agricultural context
Agricultural production is exposed to biological and environmental risks. The same visible symptom can have different causes, and a pest or disease may spread under conditions that vary by crop, season and location. A digital platform must therefore combine visual evidence with contextual evidence.
Why timing matters
Early observations create an opportunity to scout, verify and apply locally appropriate preventive measures. Delayed recognition can allow damage to spread and may increase response cost. The value of an alert depends on whether it arrives early enough to change a decision.
Why local context matters
Crop variety, planting date, growth stage, irrigation, local weather and nearby confirmed cases influence risk. A generic risk statement may be too broad to guide a farmer. Local relevance requires explicit geographic units and locally validated relationships.
Why diagnosis is difficult
Disease symptoms overlap with nutrient deficiencies, water stress, heat, chemical injury, insects and physical damage. Image models may also be affected by lighting, phone quality, leaf age and background clutter.
Implementation points
•	Consult local agricultural universities and extension experts to define the initial target list.
•	Map the crop calendar and seasonal risk periods for the pilot geography.

 Problem statement
Farmers often lack timely, reliable and local information about possible pest and disease threats. Reports may be scattered across farms and extension offices, while expert resources are limited. Images alone are insufficient for regional outbreak prediction, and weather alone is insufficient to confirm disease presence.
Core problem
There is no integrated, accessible workflow that consistently captures field observations, provides cautious image-based triage, combines contextual data for local risk estimation and routes uncertain or important cases to experts.
Operational problem
Information may be delayed, unstructured or difficult to aggregate. A district-level team may not know where reports are emerging, whether the reports are verified or how much surveillance has occurred in each area.
Technical problem
The system must learn from imperfect labels, rare events, uneven reporting and data that changes over time. It must avoid overconfident outputs when evidence is sparse.
Implementation points
•	Frame the project as early warning and decision support, not autonomous diagnosis or treatment.
•	Define the user decision each feature is intended to improve.

 Objectives and measurable outcomes
The objectives translate the concept into measurable engineering and field outcomes. Each objective should have a test method, owner and acceptance threshold before pilot launch.
Primary objectives
•	Develop a mobile workflow for crop context and image reporting.
•	Build image quality checks and a multi-class visual triage model.
•	Build a forecast pipeline for selected crop-threat-area-horizon combinations.
•	Show reported cases and forecast risk as separate map layers.
•	Deliver approved preventive guidance and expert escalation.
•	Support offline capture, queued upload and safe synchronisation.
Outcome measures
Measure model quality, forecast calibration, alert lead time, field verification, user comprehension, reliability and operational workload. Avoid relying only on overall accuracy because it can conceal poor performance on rare classes.
Example indicators
Macro F1 and per-class recall for image diagnosis; PR-AUC and Brier score for forecasting; false alerts per area and time period; median time to expert review; percentage of reports successfully synchronised after offline capture.
Implementation points
•	Set target values with domain experts after establishing baseline performance.
•	Define how each metric will be collected and audited.

 Scope and boundaries
A realistic first release should be deliberately narrow. It should prove the reporting workflow and validate a small number of crop-threat combinations before expanding to many crops and districts.
Included in the first release
•	One or two priority crops chosen with local partners.
•	A small set of common, recognisable target conditions.
•	Healthy, abiotic look-alike and unknown classes.
•	Photo submission, quality feedback and case history.
•	Weather/context ingestion and a baseline risk score.
•	Expert review and a basic regional map.
•	Local-language text for key workflows.
Excluded initially
•	All-crop universal diagnosis.
•	Unverified farm-level outbreak certainty.
•	Autonomous chemical selection and dosage advice.
•	Drone or satellite analytics unless separately justified.
•	Complex spatiotemporal deep learning before data sufficiency.
Expansion rule
Add a crop or target only when data, expert labels, local advisory support and evaluation evidence are available.
Implementation points
•	Publish a supported-crop and supported-condition list in the app.
•	Return 'not supported' or 'insufficient evidence' rather than forcing a result.

 Stakeholder analysis
The project depends on a network of people and organisations. Technical delivery alone cannot establish trustworthy labels, local thresholds or appropriate field response.
Farmers
Provide observations, context and feedback. Their consent, trust and understanding are essential.
Extension workers
Help verify reports, explain local practice and coordinate field checks.
Plant pathologists and agronomists
Define taxonomy, review labels, validate thresholds and approve advisory content.
Agricultural institutions
May provide crop calendars, reference material, field expertise and pilot access.
Technology and operations team
Build and maintain the platform, data pipelines, models, security and monitoring.
Programme administrators
Define operational ownership, escalation routes, reporting and service-level expectations.
Implementation points
•	Create a responsibility matrix for data collection, verification, alert approval and incident response.
•	Hold periodic review meetings during the pilot.

 User personas and needs
Personas make the product concrete and help prioritise features. They should be validated through interviews and field observation rather than treated as assumptions.
Smallholder farmer
Needs a short, understandable flow, local language, low data consumption and a clear next action. Avoid technical probability jargon.
Progressive farmer or farm manager
May want crop-cycle history, multiple field reports, trend comparisons and exportable records.
Extension worker
Needs to review cases quickly, see location and crop context, record verification and share approved advice.
Plant pathologist
Needs original image quality, metadata, alternative classes, provenance, reviewer notes and label correction tools.
District administrator
Needs an aggregated map, time filters, reporting coverage, verified-case trends and alert audit history.
Implementation points
•	Prioritise one primary farmer persona for MVP interaction design.
•	Test the same screen with users who have different literacy and phone experience.

 Use cases and user journeys
The system should be designed around complete tasks. A prediction that is not connected to an action or follow-up is unlikely to provide sustained value.
Use case: submit a symptom report
Farmer selects crop and field, captures image, answers optional symptom questions, submits and receives a case reference. If offline, the report is queued.
Use case: inspect a forecast
Farmer opens local outlook, sees risk band, time horizon, data freshness and reasons. The farmer can read approved prevention guidance.
Use case: verify a report
Extension worker opens queue, reviews image and context, contacts farmer if needed, records status and evidence.
Use case: monitor an area
Administrator filters the map by crop, target, date and verification status, then exports aggregated data.
Implementation points
•	Write acceptance criteria for every user story.
•	Include failure paths such as unsupported crop, blurry image and unavailable weather feed.

 Functional requirements
Functional requirements define the system behaviour that users can observe. They should be prioritised as must-have, should-have or future enhancements.
Farmer functions
•	Account and language preferences.
•	Crop-cycle and approximate area setup.
•	Camera capture and gallery upload.
•	Image quality feedback.
•	Separate diagnosis and forecast views.
•	Advisory access and expert-review request.
•	Offline save and sync status.
Expert functions
•	Review queue and case detail.
•	Verification status and label correction.
•	Evidence notes and field-visit outcome.
•	Approved advisory selection.
•	Map and case filters.
Administrator functions
•	User and role management.
•	Crop/target/geography configuration.
•	Threshold and alert-policy management.
•	Audit, monitoring and export controls.
Implementation points
•	Maintain a traceability matrix from requirement to test case.
•	Do not expose admin-only controls in farmer interfaces.

 Non-functional requirements
Non-functional requirements describe qualities such as performance, security, reliability, accessibility and maintainability. They are especially important in a rural, low-connectivity deployment.
Performance
The app should remain responsive during capture and form entry. Server inference latency targets should be defined from device and network tests.
Availability and resilience
The service should handle temporary provider outages, retry safely and show stale-data status. Offline capture must not depend on server availability.
Usability and accessibility
Use readable text, clear labels, large touch targets, plain language and language localisation.
Maintainability
Use modular components, automated tests, versioned APIs, model registry and documented operations.
Scalability
Scale image inference and forecast generation independently if usage grows.
Implementation points
•	Set measurable service-level objectives for API availability, sync success and inference latency.
•	Test with low-cost Android devices and constrained networks.

 High-level system architecture
The architecture separates the user experience, application backend, AI services, data stores, external data sources and operational monitoring. A modular monolith is a sensible starting point for a small team; service boundaries can be separated as load and ownership grow.
Client layer
Farmer mobile app, expert web portal and administrative dashboard.
Application layer
Authentication, consent, case management, API validation, workflow orchestration and notifications.
AI layer
Image quality gate, image classifier, forecast feature pipeline, risk model, calibration and explanation.
Data layer
Relational records, geospatial data, image object storage, weather snapshots, audit logs and model artefacts.
Integration layer
Weather provider, boundary datasets, map provider, notification gateway and approved advisory repositories.
Implementation points
•	Keep image and forecast services independently versioned.
•	Store the source timestamp for every external feature.
•	Make data lineage available for every displayed prediction.

 Technology stack selection
Technology choices should reflect team skills, deployment cost, device constraints and maintainability. The report recommends practical, widely supported tools rather than a large collection of fashionable technologies.
Mobile
Flutter supports Android-first delivery and shared code (ADR-013). Native camera and local storage integrations must be tested.
Backend
Python FastAPI or Django REST are suitable for model integration and typed APIs. Select one framework and standardise validation.
ML
PyTorch or TensorFlow for training; ONNX Runtime or TensorFlow Lite for deployment where appropriate.
Database and maps
PostgreSQL with PostGIS supports structured and spatial queries. MapLibre or Leaflet can render map layers.
Operations
Containerised deployment, managed object storage, metrics, logs, backups and a model registry.
Implementation points
•	Choose tools based on skills and hosting constraints.
•	Avoid premature microservices and unnecessary infrastructure.

 Farmer mobile application design
The mobile app is the primary field interface. It must be quick, forgiving and usable in bright outdoor conditions. The design should reduce typing and clearly distinguish required from optional information.
Home screen
Show registered crops, local outlook, report button, recent cases and alert preferences.
Crop context screen
Ask for crop, optional variety, growth stage and approximate area. Allow unknown values without blocking a report.
Capture screen
Show framing guidance, focus and lighting tips. Offer retake and quality feedback.
Result screen
Separate image assessment from area forecast. Display uncertainty, reasons, next steps and expert escalation.
History screen
Show status, submission time, sync status and reviewer response.
Implementation points
•	Use local language labels and icons with text.
•	Do not use colour alone to communicate severity.
•	Make stale cached forecasts visibly different from fresh data.

 Expert review portal
The expert portal turns user-generated observations into verified evidence. It should make the review process efficient without hiding the original evidence or model limitations.
Queue management
Sort by urgency, geography, crop, target, age and uncertainty. Allow assignment and escalation.
Case detail
Show original image, crop context, capture date, image quality, model candidates, forecast context and previous reviews.
Verification workflow
Provide confirmed, probable, rejected, duplicate and needs-visit states. Require evidence notes for high-impact decisions.
Feedback capture
Record corrected class, severity, field observations and optional lab confirmation.
Governance
Log reviewer identity, timestamps, edits and advisory approvals.
Implementation points
•	Do not automatically convert a model prediction into a verified label.
•	Provide a way to request a better image or additional field details.

 Regional dashboard and GIS
A regional dashboard supports situational awareness. It must make the distinction between observed reports and modelled risk unmistakable.
Map layers
Separate verified reports, unverified reports, forecast risk, administrative boundaries and data coverage.
Filters
Crop, target, date range, risk band, verification status and administrative level.
Summary panels
Show new reports, verified cases, forecast distribution, data freshness and review backlog.
Privacy
Aggregate locations and suppress small counts where an individual farm could be inferred.
Interpretation
Display a legend, issue time, forecast horizon and explanation of what the layer represents.
Implementation points
•	Do not plot exact farm points publicly by default.
•	Show reporting activity alongside disease reports to reduce interpretation bias.

 Data strategy overview
Data is the foundation of both model tracks. The project must establish where information comes from, what each field means, how labels are verified and what limitations apply.
Data families
•	Field images and image quality labels.
•	Crop and crop-cycle context.
•	Weather observations and forecasts.
•	Historical occurrence records.
•	Farmer and extension observations.
•	Geographic boundaries and environmental context.
•	Expert advisories and follow-up outcomes.
Data quality dimensions
Completeness, accuracy, timeliness, consistency, representativeness, provenance and permission.
Data governance
Every dataset needs an owner, permitted use, update schedule, retention rule and quality checks.
Implementation points
•	Create a data dictionary before building complex models.
•	Track missingness and source reliability explicitly.

 Image dataset collection
Field images must represent the environment in which the model will be used. A dataset made only from clean, centred leaves on plain backgrounds will not adequately represent real farmer submissions.
Collection diversity
Capture different devices, districts, seasons, varieties, plant ages, lighting, backgrounds, distances and symptom severity.
Metadata
Record crop, plant part, date, approximate location, growth stage, image source and verification status where available.
Ethical collection
Explain why images are collected, obtain consent and avoid including identifiable people or unnecessary personal information.
Sampling
Include healthy controls, common diseases, pest damage and abiotic look-alikes. Deliberately seek examples from underrepresented conditions.
Implementation points
•	Use a standard capture protocol.
•	Retain original images securely and store processed derivatives separately.

 Image labelling protocol
A labelling handbook reduces inconsistency and makes model evaluation meaningful. Labels should describe the evidence available, not assume a disease solely because a model predicted it.
Taxonomy
Define crop-specific classes and whether classes refer to pathogen identity, visible symptom pattern or pest damage.
Review process
Use qualified reviewers for a representative subset and adjudicate disagreements.
Uncertainty
Allow unknown, mixed symptoms and insufficient evidence labels.
Severity
Define severity with crop-specific visual criteria and avoid a generic scale if it is not meaningful.
Provenance
Store reviewer, date, evidence type, label confidence and label revision history.
Implementation points
•	Separate suspected reports from expert-confirmed and laboratory-confirmed labels.
•	Measure inter-reviewer agreement and revise unclear label definitions.

 Data cleaning and preprocessing
Data cleaning should preserve traceability. Never discard records silently or change labels without recording why.
Image checks
Validate file type, dimensions, corruption, duplicates, blur, exposure and orientation.
Tabular checks
Validate units, date ranges, crop names, geographic codes, impossible values and duplicate reports.
Missing values
Distinguish unknown from zero. Apply imputation only where justified and record imputation flags.
Normalisation
Standardise units, time zones, crop taxonomy and administrative identifiers.
Versioning
Store raw, cleaned and model-ready dataset versions with reproducible transformation code.
Implementation points
•	Create automated data-quality reports for every ingestion batch.
•	Keep a quarantine path for suspicious records.

 Dataset splitting and leakage prevention
Evaluation can appear excellent when nearly identical images or future information leak into training. Split design must reflect the real deployment question.
Image split
Group by farm, field, collection event or plant so images from one source do not cross training and test partitions.
Forecast split
Use chronological training and testing. Features must be available at the forecast issue time.
Geographic test
Where feasible, hold out one or more locations to test spatial transfer.
Final test set
Freeze an untouched test set before model selection and threshold tuning.
Reporting
Publish per-class and per-region metrics, sample counts and uncertainty intervals where feasible.
Implementation points
•	Do not randomly split images alone when duplicates or same-field images exist.
•	Document every split seed and grouping rule.

 Weather and environmental data
Weather features can contribute to risk estimation when they are biologically relevant and sufficiently reliable. The system must understand the source resolution and timing.
Candidate variables
Temperature, relative humidity, rainfall, consecutive wet days, wind and leaf-wetness proxy where available.
Spatial matching
Associate a forecast grid or station with the selected administrative area and record the matching method.
Temporal aggregation
Generate lagged windows and rolling summaries that are available at prediction time.
Missing and stale data
Flag missing observations, provider outage and stale forecasts. Avoid silently substituting values.
Provider governance
Document licence, update frequency, historical depth, quality and service limits.
Implementation points
•	Validate weather features with local agronomic expertise.
•	Do not assume that a coarse weather grid describes every farm microclimate.

 Historical records and regional observations
Historical records help identify seasonality and local pressure, but reporting patterns can be uneven. A low number of reports may mean low disease pressure or low surveillance activity.
Sources
Extension records, plant clinics, field surveys, farmer submissions and approved institutional datasets.
Verification tiers
Store confirmed, probable, unverified and rejected status separately.
Spatial-temporal features
Use lagged counts, distance-weighted nearby reports and previous-season occurrence where appropriate.
Bias correction
Include surveillance intensity or reporting coverage as a feature or uncertainty indicator.
Deduplication
Merge duplicate reports carefully while retaining source links and audit history.
Implementation points
•	Never treat no report as a confirmed disease-free observation.
•	Preserve the difference between event date and report date.

 Database design
A relational database provides consistent records and supports case management, audit and reporting. Geospatial extensions support area matching and aggregation.
Core tables
Users, farms or growing areas, crop cycles, observations, image assets, image predictions, forecasts, feature snapshots, advisories, reviews, alerts and audit events.
Relationships
A crop cycle can have many observations; an observation can have many images; an image can have multiple model predictions across versions; a forecast is tied to target, crop, geography and time.
Data integrity
Use stable IDs, foreign keys, constraints, timestamps and status enumerations.
Geospatial handling
Store approximate geometry or administrative codes with explicit precision and access controls.
Implementation points
•	Keep prediction records immutable; create a new record for each model run.
•	Store source timestamps and model versions with every output.

 Backend API design
The API is the contract between clients, backend workflows and AI services. It should be versioned, documented and designed for unreliable networks.
Observation endpoints
Create an observation, upload image, retrieve case and request review.
Forecast endpoints
Query by crop, target, geography and horizon; return issue time, validity, risk band and coverage.
Advisory endpoints
Retrieve approved guidance by crop, target, language and location.
Review endpoints
Create or update expert review with role protection and audit trail.
Reliability
Use idempotency keys, pagination, request validation, rate limits and structured errors.
Implementation points
•	Publish OpenAPI documentation.
•	Avoid exposing internal model infrastructure to mobile clients.

 Image diagnosis: problem formulation
The image task should be formulated as cautious visual triage. The model estimates similarity to supported visual classes; it does not establish pathogen identity in every case.
Input
A field photograph plus optional crop and plant-part context.
Output
Candidate class scores, quality flags, confidence band, abstention state and model version.
Class design
Include supported conditions, healthy, abiotic look-alikes and unknown/other.
Abstention
Return no assessment when image quality is poor, crop is unsupported or input is outside the model's reliable domain.
Human escalation
Offer expert review for ambiguous, high-severity or high-impact reports.
Implementation points
•	Write the user-facing wording before choosing the model architecture.
•	Avoid presenting a ranked class as a confirmed diagnosis.

 Image model architectures
Several architectures may be suitable. The correct choice depends on dataset size, device constraints, annotation depth and inference cost.
Transfer learning
Start with a lightweight pretrained image classifier such as MobileNet or EfficientNet for a practical baseline.
Larger classifiers
Compare ResNet, ConvNeXt or other architectures if server compute and data volume justify it.
Object detection
Use detection when locating multiple insects or symptomatic regions is a defined requirement and bounding-box labels exist.
Segmentation
Use segmentation when affected tissue area or lesion localisation is required and pixel masks can be produced.
Edge inference
Consider quantised mobile models only after testing memory, latency, battery and update constraints.
Implementation points
•	Use a baseline model first and compare against it fairly.
•	Do not assume a complex architecture will generalise better to local field conditions.

 Image preprocessing and augmentation
Preprocessing must be identical between training and inference. Augmentation can improve robustness, but unrealistic transformations can distort symptoms.
Preprocessing
Resize, colour conversion and normalisation must match the selected pretrained backbone and deployment code.
Augmentation
Use realistic rotations, crops, mild brightness and contrast changes, scale and modest blur.
Avoid
Do not apply aggressive hue changes, distortions or synthetic artefacts that change disease appearance.
Quality gate
Detect blur, low resolution, extreme exposure and absent plant content.
Reproducibility
Record preprocessing configuration and library versions with the model.
Implementation points
•	Build a visual review tool to inspect augmented samples.
•	Test preprocessing on actual low-cost phone images.

 Image model training workflow
Training should be reproducible and should prioritise generalisation over training-set performance.
Workflow
•	Freeze dataset and split versions.
•	Establish a simple baseline.
•	Train with transfer learning.
•	Tune hyperparameters on validation data only.
•	Inspect errors and class imbalance.
•	Calibrate outputs and choose abstention criteria.
•	Evaluate once on the untouched test set.
Imbalance
Use class weights or sampling carefully. Report per-class results because aggregate accuracy can hide minority-class failure.
Experiment tracking
Record code commit, data version, model architecture, hyperparameters, compute environment and random seed.
Implementation points
•	Keep a model registry with status and approval metadata.
•	Retain failed experiments when they inform design decisions.

 Image model evaluation
The evaluation report should describe how the model behaves in the field, not only how it performs on a curated benchmark.
Metrics
Macro F1, per-class precision and recall, confusion matrix, top-k accuracy and calibration measures.
Subgroups
Evaluate by crop variety, geography, season, device, lighting and image quality.
Error analysis
Review false positives, false negatives, look-alike conditions and confident mistakes with experts.
Robustness
Test blur, shadows, backgrounds, leaf age and image distance.
Operational acceptance
Set minimum class-level performance and abstention behaviour before alerts or advice rely on outputs.
Implementation points
•	Report sample counts beside every metric.
•	Do not use accuracy as the only acceptance measure.

 Image confidence and explainability
A model score is not automatically a reliable probability. Confidence must be calibrated or expressed qualitatively with careful wording.
Calibration
Use representative validation data to compare predicted confidence with observed correctness.
Abstention
Set thresholds that allow the model to say it cannot assess the image.
Visual explanations
Methods such as Grad-CAM may help inspect image regions but do not prove causal reasoning.
User communication
Explain likely visual match, uncertainty, image quality and next step in plain language.
Audit
Store score vector, threshold, model version and explanation metadata.
Implementation points
•	Do not display unsupported percentage confidence.
•	Treat explanation maps as debugging aids rather than proof.

 Outbreak forecasting: task definition
Forecasting requires a precise target. The model must know what event it is predicting, for which crop and area, and over what future period.
Prediction unit
Target organism or condition, crop, geography, issue time and forecast horizon.
Event definition
Define whether an event means a first verified case, incidence threshold, escalation or another operational outcome.
Negative labels
Absence of a report is not necessarily a negative event. Consider surveillance coverage and follow-up.
Horizon
Select a period that aligns with decisions and input reliability, such as a 7-day outlook if evidence supports it.
Spatial unit
Use the smallest geography that the input data can support without implying false precision.
Implementation points
•	Write target definitions before feature engineering.
•	Keep different event types as separate prediction tasks when necessary.

 Forecast feature engineering
Feature engineering transforms raw weather, crop and surveillance data into signals available at the time a forecast is issued.
Weather windows
Rolling rainfall, temperature ranges, humidity summaries and consecutive wet periods.
Crop features
Crop type, growth stage, planting window, variety and irrigation context.
Seasonal features
Week of year, monsoon period, days since planting and local crop calendar.
Historical pressure
Lagged verified cases, nearby reports and prior-season occurrence.
Coverage features
Number of active reporters, field visits and data completeness.
Implementation points
•	Prevent future information from entering historical training features.
•	Store the feature-generation timestamp and source lineage.

 Forecast model baselines
A forecast model should be compared against transparent baselines. A sophisticated algorithm is only useful if it improves on simple seasonal and expert-rule approaches.
Rules baseline
Agronomists define documented combinations of crop stage and conducive environmental conditions.
Statistical baseline
Logistic regression, seasonal averages or time-series baselines provide interpretable reference performance.
Tree-based models
Random Forest, XGBoost or LightGBM can capture non-linear interactions in structured data.
Advanced methods
Spatiotemporal neural models should be considered only when data volume and quality support them.
Selection
Choose the simplest model that meets the operational objective and passes local validation.
Implementation points
•	Version expert rules and record who approved them.
•	Keep the baseline available for fallback.

 Forecast calibration and thresholds
Risk bands should be derived from validated probabilities or a documented expert-approved score. Arbitrary thresholds create false confidence.
Calibration
Assess reliability diagrams, Brier score and log loss on temporal holdout data.
Threshold selection
Balance false alarms against missed outbreaks and consider the cost of each type of error.
Risk bands
Low, moderate, high and urgent bands should have operational meanings and approved actions.
Insufficient data
Display a no-score state when coverage or freshness is inadequate.
Refresh
Review thresholds when crop calendar, reporting patterns or model calibration changes.
Implementation points
•	Show the forecast issue time and expiry time.
•	Do not imply that low risk means no disease is present.

 Spatial and temporal forecasting
Outbreaks evolve over space and time. Forecasting should respect geographic boundaries, local movement patterns and reporting delays.
Spatial aggregation
Aggregate reports to the chosen administrative level and document the method.
Neighbour influence
Use nearby reports with transparent distance and time decay only when biologically and operationally justified.
Temporal dependence
Use lagged observations and seasonal context available at issue time.
Spatial validation
Test on held-out locations where possible.
Map interpretation
Display modelled risk separately from observed cases and data coverage.
Implementation points
•	Avoid precise farm-level maps from coarse district-level inputs.
•	Use stable geographic identifiers and boundary versions.

 Combining image and forecast outputs
The two AI tracks can support a common decision journey, but they must remain logically distinct.
Image output
Describes likely visible symptoms in one submitted photograph.
Forecast output
Estimates future risk for a crop-threat-area-time combination.
Evidence contribution
A farmer report may become a regional signal after quality checks and verification.
User interface
Show separate cards with separate timestamps, model versions and confidence descriptions.
Governance
Do not feed unverified image predictions into the forecast as confirmed cases.
Implementation points
•	Use explicit labels such as 'photo assessment' and 'area outlook'.
•	Preserve original report status throughout the workflow.

 Risk map and geospatial analytics
A risk map is useful only when the legend, geography, data freshness and evidence type are clear.
Map content
Verified reports, unverified reports, modelled risk and data coverage.
Aggregation
Use administrative boundaries or grid cells appropriate to input resolution.
Privacy
Avoid displaying exact farm coordinates to unauthorised users.
Temporal controls
Allow users to inspect issue date, forecast horizon and historical report period.
Performance
Use vector tiles or server-side aggregation when map data becomes large.
Implementation points
•	Add a map legend and plain-language explanation.
•	Do not merge reported cases and predicted risk into one undifferentiated heatmap.

 Preventive advisory engine
The advisory layer translates evidence into safe, locally appropriate action. It should use approved content rather than generative model improvisation for high-impact instructions.
Advisory structure
Crop, target, geography, season, language, validity period, author, approver and source.
Action types
Scouting, monitoring, sanitation, crop-management practices and escalation to extension services.
Local approval
Agronomists review wording and suitability for crop stage and region.
Chemical safety
The platform must not invent pesticide names, rates, mixtures, waiting periods or legal use instructions.
Versioning
Keep history of advisory changes and show when content expires.
Implementation points
•	Start with non-chemical prevention and monitoring guidance.
•	Route uncertain or severe cases to qualified local experts.

 Alert and notification design
Alerts should prompt useful action without creating fatigue. Every alert needs a clear reason, time window and response path.
Trigger policy
Use validated risk threshold, data freshness and minimum coverage conditions.
Deduplication
Combine repeated signals for the same area and target.
Cooldown
Set severity-specific quiet periods and avoid repeated identical messages.
Channels
Push notifications, SMS or approved messaging channels based on user preference and availability.
Feedback
Allow users to report inaccurate alerts, acknowledge them or change notification preferences.
Implementation points
•	Include area, crop, target, valid period, reason and next action.
•	Do not label a forecast as a confirmed outbreak.

 Offline-first engineering
Low connectivity must not prevent a farmer from recording an observation. The mobile app should support local persistence and later synchronisation.
Local storage
Cache crop lists, advisory content, recent forecast and unsent observations.
Upload queue
Store pending uploads with client-generated IDs, retry count and sync status.
Image compression
Compress to reduce data use while retaining diagnostic detail.
Stale data
Show last updated time and label cached forecasts as stale when validity has expired.
Conflict handling
Keep observations append-only and preserve expert verification changes.
Implementation points
•	Test airplane mode, intermittent network and interrupted uploads.
•	Use idempotency keys to prevent duplicate submissions.

 Security architecture
Security controls protect farmer information, images, expert accounts and operational integrity.
Identity
Use secure authentication, session management and role-based access.
Data protection
Encrypt data in transit and at rest; keep image storage private.
Application security
Validate uploads, rate-limit APIs, protect secrets and patch dependencies.
Audit
Log access to sensitive records, reviews, exports and model configuration changes.
Resilience
Maintain backups, test restoration and define incident response ownership.
Implementation points
•	Complete a threat model before production deployment.
•	Never embed provider secrets in a mobile application.

 Privacy and responsible AI
Trust depends on transparent data use and careful communication of model limits.
Data minimisation
Collect only information needed for reporting, forecast relevance and service delivery.
Consent
Explain image, location and profile use in understandable language.
Location privacy
Use approximate location by default and restrict exact farm coordinates.
Fairness
Evaluate errors across geography, device type, season and farmer groups where data permits.
Human oversight
Keep expert review and a process to correct inaccurate outputs.
Implementation points
•	Define retention and deletion procedures.
•	Do not expose personally identifiable farmer records in public dashboards.

 Testing strategy
Testing must cover software, data, models, user experience and field operations. A working prototype is not ready for deployment until its failure modes are understood.
Unit and integration tests
Validate input rules, feature engineering, model service contracts, database writes and notifications.
End-to-end tests
Test report creation, upload, inference, expert review, alert delivery and offline sync.
Security tests
Test authorisation boundaries, upload handling, data leakage and secrets management.
Usability tests
Observe farmers completing tasks in realistic outdoor and network conditions.
Model tests
Use spatial and temporal holdouts, subgroup metrics, calibration and error analysis.
Implementation points
•	Create a test matrix linking requirement, scenario, expected result and evidence.
•	Include negative and failure cases, not only successful paths.

 Pilot design and field validation
A controlled pilot is essential to learn whether the system helps real decisions. Start with silent predictions before issuing operational alerts.
Site selection
Choose representative locations with extension partners and a feasible verification process.
Silent phase
Generate predictions without farmer-facing alerts and compare with verified field observations.
Limited alert phase
Enable a small, approved set of alerts after thresholds and response workflows are reviewed.
Evaluation
Track lead time, false alerts, missed events, review workload, farmer comprehension and service reliability.
Decision
Expand only when evidence and operational capacity justify it.
Implementation points
•	Document baseline conditions and comparison method.
•	Do not claim yield impact without a suitable study design.

 Deployment and infrastructure
Deployment should be staged and reversible. Use separate development, staging and production environments.
Environments
Development supports rapid iteration; staging mirrors production; production has strict access, backups and monitoring.
Release
Package services, automate tests, run migrations safely and use controlled rollout.
Scaling
Scale image inference separately from API traffic if required.
Backup
Back up database, object metadata, model artefacts and configuration.
Recovery
Test restore procedures and document recovery time objectives.
Implementation points
•	Use infrastructure-as-code where practical.
•	Keep rollback procedures documented and tested.

 Monitoring and model maintenance
Monitoring must detect both software failures and model/data degradation. A model that worked during development may perform differently after seasonal or geographic change.
Data monitoring
Missingness, freshness, duplicates, source changes and geography coverage.
Model monitoring
Prediction distribution, abstention rate, verified performance and calibration drift.
Product monitoring
Latency, error rates, upload backlog, sync success and notification delivery.
Feedback loop
Review user complaints, expert corrections and field outcomes.
Retraining
Retrain only with governed, verified data and repeat the frozen evaluation suite.
Implementation points
•	Retain previous model versions for rollback.
•	Do not automatically promote a model based only on training metrics.

 Project team and responsibilities
The project needs cross-functional ownership. Agronomy and field operations are as important as software engineering.
Product lead
Scope, user research, milestones, stakeholder communication and acceptance.
Agronomist / pathologist
Target selection, taxonomy, labels, risk rules and advisory approval.
Data engineer
Ingestion, storage, data quality, geospatial processing and lineage.
ML engineer
Image and forecast modelling, evaluation, calibration and monitoring.
Application engineers
Mobile, backend, portal, APIs and offline synchronisation.
QA and field researcher
Test strategy, usability studies, field pilot and issue reporting.
Implementation points
•	Assign one accountable owner to each deliverable.
•	Plan regular field feedback sessions throughout development.

 Implementation roadmap
The roadmap is phased so that the team establishes trustworthy data and workflows before relying on complex predictions.
Phase 0 — discovery
Select crop, target, geography, stakeholders, event definitions and pilot success measures.
Phase 1 — data foundation
Secure data access, collect images, define labels, ingest weather and build database.
Phase 2 — platform MVP
Deliver mobile reporting, case management, expert portal and offline queue.
Phase 3 — image AI
Train and validate a field-image model with quality gate and abstention.
Phase 4 — forecasting
Build rules baseline, feature pipeline, model, calibration and risk map.
Phase 5 — pilot
Run silent evaluation, limited alerts, field verification and usability refinement.
Phase 6 — rollout
Complete operational readiness, monitoring, training and controlled expansion.
Implementation points
•	Treat data access and expert annotation as critical-path activities.
•	Do not promise a reliable forecast before enough historical evidence exists.

 Budget and resource planning
Budget depends on geography, crop scope, data availability, staffing and deployment model. Cost estimates should be created from a work breakdown structure rather than a single technology guess.
People
Product, engineering, data, ML, agronomy, field collection, QA and support.
Data acquisition
Field visits, enumerators, expert labelling, laboratory confirmation and licences.
Infrastructure
Cloud compute, GPU, database, storage, maps, monitoring and backups.
Operations
Connectivity, devices, training, translation, user support and maintenance.
Risk reserve
Allow for seasonal delays, provider changes and additional data collection.
Implementation points
•	Prepare low, expected and high cost scenarios.
•	Track recurring operating cost separately from one-time development cost.

 Risk register and mitigation
The main risks are data scarcity, domain shift, look-alike symptoms, uneven reporting, poor connectivity, false alarms and unsafe advice.
Data scarcity
Begin with rules and a reporting network; do not overstate model capability.
Domain shift
Collect diverse field data and evaluate by district, season and device.
Reporting bias
Track surveillance intensity and verified status.
False alarms
Calibrate thresholds, use cooldowns and collect feedback.
Missed events
Review false negatives and maintain extension escalation.
Unsafe advice
Use expert-approved local content and prohibit autonomous chemical prescriptions.
Implementation points
•	Maintain a live risk register with owner, likelihood, impact and mitigation status.
•	Review risks at every project milestone.

 Success metrics and impact evaluation
Success must be measured at multiple levels. Model accuracy is only one part of whether the platform creates value.
Technical
Image macro F1, per-class recall, forecast PR-AUC, Brier score, calibration and inference latency.
Operational
Report-to-review time, review backlog, verified case rate, notification delivery and sync success.
User
Task completion, comprehension, repeat use, alert usefulness and opt-out rate.
Agricultural
Lead time, field inspection prioritisation and outcome indicators where credible data exists.
Equity
Performance and adoption by geography, device and user segment.
Implementation points
•	Set a baseline before pilot deployment.
•	Report limitations and sample sizes alongside claimed impact.

 Demonstration scenario
A demonstration should show the entire chain from field observation to cautious assessment, local forecast, human verification and regional visibility.
Scenario
A farmer selects a supported crop and area, photographs a leaf and submits a report. The app flags blur and requests a retake. A clearer image receives a possible symptom match with medium confidence.
Forecast context
The local outlook separately shows a moderate risk for a supported target over the next seven days, with recent weather and crop stage listed as contributing factors.
Action
The farmer receives scouting guidance and an option to request expert review. The report appears as unverified in the expert queue.
Verification
An extension worker reviews the evidence and records a confirmed, probable or unresolved status.
Dashboard
The regional dashboard updates the verified-report layer without conflating it with the forecast layer.
Implementation points
•	Use synthetic demo data clearly labelled as demonstration data.
•	Do not present fabricated predictions as real local outbreak warnings.

 Conclusion and future enhancements
The proposed network can provide a strong foundation for early agricultural warning if it is built around local evidence, cautious AI outputs and human-supported operations. The highest-value first step is not the most complex model; it is a dependable reporting and verification workflow that produces trustworthy data.
Conclusion
The project integrates computer vision, structured agricultural data, weather context, geospatial analysis and approved guidance. Its success depends on local validation, transparent uncertainty and an operational response network.
Future enhancements
•	Additional crops and target organisms after data readiness.
•	On-device inference for selected models.
•	Satellite or drone observations where validated.
•	IoT sensors for local microclimate where economically justified.
•	Advanced spatiotemporal forecasting after sufficient longitudinal data.
•	Interoperability with institutional agricultural information systems.
Final recommendation
Start with a narrow pilot, establish a high-quality dataset and expert workflow, then expand only when each new crop and region has evidence to support reliable service.
Implementation points
•	Treat trust, usability and field outcomes as first-class success criteria.

 Appendix A — Sample farmer-facing alert
MODERATE LOCAL RISK. Conditions in the selected area may be favourable for [supported crop issue] during [forecast period]. This is an early warning, not confirmation that your field is infected.
Why this alert was issued
Recent weather conditions and the current crop stage match factors associated with increased risk. The area currently has [coverage status] data coverage. The most recent input was updated at [timestamp].
What to do now
Inspect a sample of plants across the field, record whether symptoms are increasing, follow the locally approved prevention advisory and contact an extension worker if matching symptoms are observed.
Required metadata
Forecast issue time, valid-from and valid-to time, crop, target, administrative area, model version, coverage status and advisory version.
Implementation points
•	Never recommend pesticide application solely because a forecast alert was issued.

 Appendix B — Sample image assessment wording
POSSIBLE SYMPTOM MATCH. The submitted image appears most similar to [condition A]. The assessment confidence is [validated band] and the photo quality is [status]. This is an automated visual assessment, not a confirmed diagnosis.
Next step
Inspect additional plants and compare symptoms with the locally approved advisory. If the image is unclear, the crop is unsupported or symptoms do not match, request expert review.
Separate forecast context
An area-level forecast may provide additional context but does not confirm the condition on the photographed plant.
Result metadata
Image ID, model version, generated timestamp, supported class set, quality flags, abstention status and score calibration status.
Implementation points
•	Use plain language and translate with local agricultural experts.

 Appendix C — Example forecast API response
The following is a schema illustration, not a real forecast. It shows the fields needed to make a forecast interpretable and auditable.
Example payload
{
  "forecast_id": "fcst_demo_001",
  "crop": "example_crop",
  "target": "example_target",
  "geography": {"level": "administrative_block", "code": "DEMO_BLOCK"},
  "issue_time": "2026-11-06T06:00:00Z",
  "valid_from": "2026-11-06T06:00:00Z",
  "valid_to": "2026-11-13T06:00:00Z",
  "risk_band": "moderate",
  "probability": null,
  "confidence": "medium",
  "data_coverage": "good",
  "drivers": ["recent_rainfall", "crop_stage"],
  "model_version": "forecast-demo-0.1"
}
Interpretation
Probability is null because a calibrated probability has not been approved in this illustrative payload. A real production response should include a probability only when validation supports it.
Implementation points
•	Keep example data visibly marked as demo or synthetic.

 Appendix D — Database entity checklist
The following entities form a practical starting point for a relational data model. The final schema should be reviewed against the chosen workflows and privacy requirements.
Core entities
•	User and role.
•	Growing area and approximate geometry.
•	Crop cycle and crop-stage history.
•	Observation and image asset.
•	Image prediction and model metadata.
•	Forecast and feature snapshot.
•	Advisory and approval history.
•	Expert review and verification evidence.
•	Alert and delivery status.
•	Audit event and consent record.
Integrity requirements
Stable identifiers, foreign keys, status constraints, source timestamps, model versions and append-only prediction history.
Implementation points
•	Use PostGIS only where spatial queries are required.
•	Restrict access to precise location fields.

 Appendix E — API and integration checklist
Before connecting the mobile app and AI services, agree the API contract and error behaviour.
API checklist
•	Versioned routes and documented schemas.
•	Authentication and role-based access.
•	Idempotency for report creation and uploads.
•	Pagination and filtering for case queues.
•	Structured error codes and retry guidance.
•	Request size and file validation.
•	Audit trail for expert changes.
Integration checklist
•	Weather source licence and freshness.
•	Boundary dataset version and area codes.
•	Map provider terms and offline behaviour.
•	Notification opt-in and delivery receipts.
•	Approved advisory source and content review.
Implementation points
•	Test external provider outage and delayed responses.

 Appendix F — Example test cases
These examples can be converted into formal test cases in a quality-management tool.
Functional tests
•	Submit a supported crop image with a valid network.
•	Submit a blurry image and confirm the app requests a retake.
•	Submit an unsupported crop and confirm no unsupported diagnosis is forced.
•	Save a report offline and synchronise after reconnecting.
•	Retry an upload and confirm no duplicate observation is created.
•	Verify that only authorised experts can change review status.
Forecast tests
•	Return a current forecast with issue and expiry times.
•	Return insufficient-data state when weather feed is stale.
•	Confirm map layers distinguish verified reports and predictions.
•	Confirm an expired cached forecast is marked stale.
Security tests
•	Attempt unauthorised access to another farmer's report.
•	Upload an invalid file type.
•	Attempt access to a private image URL after expiry.
•	Confirm sensitive exports are role-restricted and audited.
Implementation points
•	Record expected result, actual result, evidence and defect reference.

 Appendix G — Glossary
A shared vocabulary helps technical and agricultural stakeholders discuss the same system behaviour.
Terms
•	Image diagnosis: automated assessment of visible symptoms in an individual image.
•	Outbreak forecast: estimated future risk for a target, crop, geography and horizon.
•	Calibration: agreement between predicted probabilities and observed frequencies.
•	Abstention: a model decision not to provide an assessment when evidence is insufficient.
•	Data leakage: use of information during training that would not be available at prediction time.
•	Temporal holdout: evaluation on a later time period not used for training.
•	Surveillance intensity: amount of reporting or inspection activity in an area.
•	Data coverage: completeness, freshness and representativeness of inputs.
•	Model drift: change in input patterns or performance over time.

 Appendix H — Final launch-readiness checklist
The project should not be launched as an operational early-warning service until the following gates have been reviewed and signed off.
Agronomy and data
•	Crop and target scope approved by local experts.
•	Label handbook and verification workflow active.
•	Data permissions and provenance documented.
•	Weather and boundary data freshness monitored.
AI and product
•	Image and forecast models evaluated separately.
•	Calibration and abstention behaviour tested.
•	Risk map distinguishes reports, predictions and coverage.
•	Advisories approved and versioned.
•	Offline queue and stale-data handling tested.
Operations and governance
•	Consent, privacy and retention procedures active.
•	Security review completed.
•	Alert thresholds and escalation owners approved.
•	Monitoring, rollback and incident response ready.
•	Pilot findings reviewed and documented.
Implementation points
•	If a gate is not met, keep the affected feature in a non-operational or silent pilot mode.
