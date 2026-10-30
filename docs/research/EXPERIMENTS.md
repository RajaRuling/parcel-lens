# Registered experiment plan — version 2

Registered 2026-10-29, before generating version 2 data or fitting models. Version 1 results are exploratory and are not reused for model selection.

## Claims and stopping rule

| ID | Checkable claim | Split and success rule |
| --- | --- | --- |
| C1 | A learned image classifier separates procedurally damaged from clean parcels with ROC AUC at least 0.80. | 900 unseen standard-style scenes; lower bound of 1,000-resample 95% bootstrap CI >= 0.80. |
| C2 | The selected learned classifier improves F1 over the retained classical detector by at least 0.05. | Same standard test scenes; paired bootstrap lower bound of F1 difference >= 0.05. |
| C3 | At a validation-selected review threshold, recall is at least 0.90 and clean false alarms are at most 100 per 1,000 clean images. | Standard test; recall CI lower bound >= 0.90 AND false-alarm CI upper bound <= 100. |
| C4 | Damage discrimination transfers to held-out scene styles with ROC AUC at least 0.75. | 900 shift scenes with unseen palette, obliquity, clutter and stronger noise; AUC CI lower bound >= 0.75. |
| C5 | The learned system has demonstrated useful discrimination on real parcel photographs. | Requires >=100 independently sourced, licensed, labelled real images and AUC CI lower bound >=0.75; otherwise INCONCLUSIVE. |

SUPPORTED means the whole interval meets the registered rule. NOT SUPPORTED means a point estimate fails a rule. Otherwise INCONCLUSIVE. These are exploratory engineering acceptance rules, not corrected confirmatory significance tests.

## Data and selection discipline

Create 4,800 independent, single-parcel procedural scenes: 2,400 training, 600 validation, 900 standard test and 900 shift test. Assign split and unique scene/seed BEFORE rendering. Each scene has one rendering only. Damage prevalence is exactly 50%; five damage types are balanced within damaged scenes. Severity and lighting cycle independently of class; their joint distribution is checked. Standard-style train/validation/test share the generator; the shift style is entirely absent from training and validation. No scene is used in more than one split. Annotations come from generator intent and damage masks, without human labelling. Occluded damage remains positive. No claim of photorealism.

Retain version 1 classical pixel detector; image score is whether it finds any region. Trivial baseline always predicts damaged (ties resolved toward review). Train a linear logistic head on pixel-derived multiscale colour/gradient summaries, then a small 32-unit neural head. Ablate spatial information (global summaries only) and intensity normalization. All standardization fits use training only. Compare predetermined linear regularizations 0.001/0.01 and neural regularizations 0.001/0.01; maximum 160 epochs per fit, one CPU process, no GPU use, cap 20 minutes per fit. Checkpoints are chosen on validation log loss; choose final learned model by validation F1, then AUC, then simpler model. Ablations do not compete for final selection.

Each candidate threshold is selected on validation alone: among thresholds reaching recall >=0.90 choose the smallest false-positive rate, then greatest F1. If none qualifies, choose maximum F1. Probability temperature (0.5, 0.75, 1, 1.5, 2, 3) is selected on validation log loss; calibration is labelled validation-fitted. Save model and thresholds before final evaluation. Evaluate each frozen candidate exactly once on standard and shift tests in the final pass; selecting subsequent changes using those tests is prohibited. Reproduction may deterministically rerun the frozen protocol; it is not a new tuning pass.

## Required outputs

Image-level precision, recall, F1, ROC AUC, average precision, confusion matrices, Brier score, ten-bin calibration error and reliability bins; 1,000-resample percentile bootstrap 95% CIs with seed 20261029. Bootstrap at scene level, stratified by true class for two-class metrics; per-damage/severity positive-only subsets report recall, not meaningless AUC. Per-lighting metrics include both classes. Paired bootstrap for model differences. Empty denominators are null, not zero. Finite sample zero-error bootstrap intervals do not prove zero population error; show a one-sided exact 95% bound too.

Publish frozen test threshold curves as sensitivity analysis, never as a new selected operating point. Translate conditional clean alarms and damage misses per 1,000 separately, then illustrative total review load at 1%, 5%, 20% prevalence. No financial savings claim. Show high-confidence errors and an honest reviewer decision view. The image classifier does not localize damage: classical boxes are unvalidated suggestions and mask boxes are synthetic ground truth. No learned box accuracy is claimed.

## Real-data fallback and optional vision

Record all inspected sources, licence suitability and actual acquisition outcomes in DATA.md. If no suitable downloadable real benchmark is secured, execute the registered procedural fallback and leave C5 INCONCLUSIVE. A vision-model comparison is optional: inspect only safe existing helpers, do not read credentials, do not contact another machine or switch/evict a model. Skip if no safe local image-inference path can be demonstrated.
