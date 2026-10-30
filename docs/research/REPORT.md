# Parcel Lens — version 2 evidence report

**Result scope: 4,800 original procedural scenes; zero real photographs. Real-world accuracy is untested.**

Frozen model: linear_r0.001; review threshold 0.354629. Learned binary image classification; no learned bounding-box, damage-type or severity performance is claimed.

## Registered claims

| ID | Claim | Estimate [95% CI] | Verdict |
| --- | --- | --- | --- |
| C1 | Standard-style damage ROC AUC >= 0.80 | 0.9512; [0.9368937037037037, 0.9637945679012346] | SUPPORTED |
| C2 | F1 improvement over classical >= 0.05 | 0.3004; [0.26621577597526164, 0.33556674300950495] | SUPPORTED |
| C3 | Recall >= 0.90 and <=100 alarms / 1,000 clean | {"recall": 0.8888888888888888, "alarms": 115.55555555555556}; {"recall": [0.86, 0.915611111111111], "alarms": [84.44444444444444, 146.72222222222217]} | NOT SUPPORTED |
| C4 | Held-out-style damage ROC AUC >= 0.75 | 0.6448; [0.6099096296296296, 0.6821377777777777] | NOT SUPPORTED |
| C5 | Useful real-photograph discrimination demonstrated | not measured; not available | INCONCLUSIVE |

## Frozen model comparison

Each candidate is evaluated once in the final pass. All thresholds and checkpoints were selected on validation only. Intervals below use 1,000 stratified scene-bootstrap resamples, fixed seed 20261029; prevalence is fixed at 50% within these resamples. C2 uses paired scene resamples. Undefined quantities are not measured. Bootstrap intervals are conditional on this generator and fitted model, not on alternate training sets or real networks.

### test: 900 images, 450 clean / 450 damaged

| Model | Precision | Recall | F1 | AUC | Average precision | Brier | ECE | Clean alarms / 1,000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linear_r0.001 | 0.8850 [0.8571, 0.9119] | 0.8889 [0.8600, 0.9156] | 0.8869 [0.8653, 0.9075] | 0.9512 [0.9369, 0.9638] | 0.9612 [0.9505, 0.9709] | 0.0819 [0.0701, 0.0945] | 0.0307 [0.0235, 0.0517] | 115.5556 [84.4444, 146.7222] |
| linear_r0.01 | 0.8764 [0.8479, 0.9044] | 0.8978 [0.8689, 0.9244] | 0.8869 [0.8652, 0.9071] | 0.9457 [0.9306, 0.9593] | 0.9572 [0.9459, 0.9675] | 0.0875 [0.0757, 0.1004] | 0.0457 [0.0333, 0.0659] | 126.6667 [95.5556, 160.0000] |
| neural32_r0.001 | 0.8769 [0.8498, 0.9047] | 0.8867 [0.8578, 0.9156] | 0.8818 [0.8596, 0.9021] | 0.9512 [0.9371, 0.9638] | 0.9618 [0.9519, 0.9713] | 0.0821 [0.0697, 0.0950] | 0.0311 [0.0244, 0.0523] | 124.4444 [93.2778, 155.5556] |
| neural32_r0.01 | 0.8458 [0.8189, 0.8742] | 0.9022 [0.8733, 0.9311] | 0.8731 [0.8503, 0.8927] | 0.9466 [0.9306, 0.9611] | 0.9581 [0.9463, 0.9683] | 0.0863 [0.0740, 0.1001] | 0.0281 [0.0228, 0.0507] | 164.4444 [128.8889, 197.7778] |
| ablate_spatial | 0.5507 [0.5336, 0.5682] | 0.8689 [0.8356, 0.9000] | 0.6741 [0.6541, 0.6934] | 0.6934 [0.6566, 0.7268] | 0.6915 [0.6525, 0.7300] | 0.2245 [0.2124, 0.2380] | 0.0349 [0.0345, 0.0786] | 708.8889 [666.6667, 748.8889] |
| ablate_normalization | 0.8790 [0.8505, 0.9038] | 0.9044 [0.8756, 0.9333] | 0.8916 [0.8696, 0.9105] | 0.9556 [0.9411, 0.9679] | 0.9661 [0.9561, 0.9749] | 0.0763 [0.0646, 0.0891] | 0.0294 [0.0241, 0.0510] | 124.4444 [95.5556, 157.8333] |
| always_review | 0.5000 [0.5000, 0.5000] | 1.0000 [1.0000, 1.0000] | 0.6667 [0.6667, 0.6667] | 0.5000 [0.5000, 0.5000] | 0.5000 [0.5000, 0.5000] | 0.5000 [0.5000, 0.5000] | 0.5000 [0.5000, 0.5000] | 1000.0000 [1000.0000, 1000.0000] |
| classical | 0.5169 [0.4949, 0.5401] | 0.6778 [0.6356, 0.7222] | 0.5865 [0.5580, 0.6135] | 0.5222 [0.4933, 0.5522] | 0.5115 [0.4967, 0.5282] | 0.4778 [0.4478, 0.5067] | 0.4778 [0.4478, 0.5067] | 633.3333 [591.1111, 677.7778] |

Confusion matrices are image-level: TN, FP, FN, TP.

- linear_r0.001: {"tn": 398, "fp": 52, "fn": 50, "tp": 400}
- linear_r0.01: {"tn": 393, "fp": 57, "fn": 46, "tp": 404}
- neural32_r0.001: {"tn": 394, "fp": 56, "fn": 51, "tp": 399}
- neural32_r0.01: {"tn": 376, "fp": 74, "fn": 44, "tp": 406}
- ablate_spatial: {"tn": 131, "fp": 319, "fn": 59, "tp": 391}
- ablate_normalization: {"tn": 394, "fp": 56, "fn": 43, "tp": 407}
- always_review: {"tn": 0, "fp": 450, "fn": 0, "tp": 450}
- classical: {"tn": 165, "fp": 285, "fn": 145, "tp": 305}

Selected model minus classical F1: 0.3004 [0.2662, 0.3356].

### shift: 900 images, 450 clean / 450 damaged

| Model | Precision | Recall | F1 | AUC | Average precision | Brier | ECE | Clean alarms / 1,000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linear_r0.001 | 0.5748 [0.5505, 0.6019] | 0.7000 [0.6600, 0.7400] | 0.6313 [0.6036, 0.6587] | 0.6448 [0.6099, 0.6821] | 0.6758 [0.6428, 0.7128] | 0.3527 [0.3256, 0.3794] | 0.3313 [0.3029, 0.3657] | 517.7778 [473.2778, 562.2778] |
| linear_r0.01 | 0.5661 [0.5420, 0.5920] | 0.7133 [0.6733, 0.7533] | 0.6313 [0.6039, 0.6590] | 0.6493 [0.6151, 0.6854] | 0.6840 [0.6501, 0.7210] | 0.3512 [0.3245, 0.3783] | 0.3268 [0.3012, 0.3622] | 546.6667 [500.0000, 591.1111] |
| neural32_r0.001 | 0.5870 [0.5576, 0.6173] | 0.6444 [0.6044, 0.6889] | 0.6144 [0.5846, 0.6487] | 0.6484 [0.6128, 0.6845] | 0.6818 [0.6471, 0.7201] | 0.3164 [0.2911, 0.3416] | 0.2794 [0.2518, 0.3138] | 453.3333 [406.6667, 497.8333] |
| neural32_r0.01 | 0.6033 [0.5741, 0.6322] | 0.6489 [0.6089, 0.6933] | 0.6253 [0.5941, 0.6582] | 0.6678 [0.6342, 0.7040] | 0.7061 [0.6710, 0.7413] | 0.2907 [0.2668, 0.3137] | 0.2397 [0.2106, 0.2719] | 426.6667 [384.4444, 471.1111] |
| ablate_spatial | 0.5000 [0.5000, 0.5000] | 1.0000 [1.0000, 1.0000] | 0.6667 [0.6667, 0.6667] | 0.6384 [0.6031, 0.6739] | 0.6418 [0.6056, 0.6808] | 0.4818 [0.4797, 0.4840] | 0.4846 [0.4832, 0.4861] | 1000.0000 [1000.0000, 1000.0000] |
| ablate_normalization | 0.5451 [0.5293, 0.5630] | 0.8467 [0.8133, 0.8800] | 0.6632 [0.6433, 0.6839] | 0.6744 [0.6408, 0.7094] | 0.6880 [0.6534, 0.7270] | 0.3558 [0.3320, 0.3813] | 0.3404 [0.3165, 0.3714] | 706.6667 [664.4444, 746.6667] |
| always_review | 0.5000 [0.5000, 0.5000] | 1.0000 [1.0000, 1.0000] | 0.6667 [0.6667, 0.6667] | 0.5000 [0.5000, 0.5000] | 0.5000 [0.5000, 0.5000] | 0.5000 [0.5000, 0.5000] | 0.5000 [0.5000, 0.5000] | 1000.0000 [1000.0000, 1000.0000] |
| classical | 0.4318 [0.3496, 0.5116] | 0.1267 [0.0977, 0.1556] | 0.1959 [0.1514, 0.2372] | 0.4800 [0.4556, 0.5033] | 0.4914 [0.4841, 0.5017] | 0.5200 [0.4967, 0.5444] | 0.5200 [0.4967, 0.5444] | 166.6667 [135.5556, 204.4444] |

Confusion matrices are image-level: TN, FP, FN, TP.

- linear_r0.001: {"tn": 217, "fp": 233, "fn": 135, "tp": 315}
- linear_r0.01: {"tn": 204, "fp": 246, "fn": 129, "tp": 321}
- neural32_r0.001: {"tn": 246, "fp": 204, "fn": 160, "tp": 290}
- neural32_r0.01: {"tn": 258, "fp": 192, "fn": 158, "tp": 292}
- ablate_spatial: {"tn": 0, "fp": 450, "fn": 0, "tp": 450}
- ablate_normalization: {"tn": 132, "fp": 318, "fn": 69, "tp": 381}
- always_review: {"tn": 0, "fp": 450, "fn": 0, "tp": 450}
- classical: {"tn": 375, "fp": 75, "fn": 393, "tp": 57}

Selected model minus classical F1: 0.4354 [0.3870, 0.4895].

## Subgroup results

Type and severity subsets consist of damaged images only; the meaningful decision metric is recall. Clean rows contain only negatives; alarm rate is meaningful there. Lighting and tape subsets include both classes. All subgroup metrics and CIs, including undefined fields, are in the JSON. No adjustment for multiple comparisons; use these slices to find weaknesses, not to rank universal damage difficulty.

### test

| Slice | Value | N | Recall [95% CI] | Clean alarms / 1,000 [95% CI] |
| --- | --- | --- | --- | --- |
| label | clean | 450 | not measured | 115.5556 [88.8889, 146.6667] |
| label | crushed_corner | 90 | 0.8778 [0.8000, 0.9333] | not measured |
| label | dent_crush | 90 | 0.8556 [0.7778, 0.9222] | not measured |
| label | open_flap | 90 | 0.9778 [0.9444, 1.0000] | not measured |
| label | tear_puncture | 90 | 0.9667 [0.9222, 1.0000] | not measured |
| label | water_stain | 90 | 0.7667 [0.6778, 0.8556] | not measured |
| severity | mild | 160 | 0.7625 [0.6937, 0.8313] | not measured |
| severity | moderate | 152 | 0.9342 [0.8947, 0.9671] | not measured |
| severity | none | 450 | not measured | 115.5556 [88.8889, 146.6667] |
| severity | severe | 138 | 0.9855 [0.9638, 1.0000] | not measured |
| lighting | bright | 300 | 0.8707 [0.8095, 0.9185] | 130.7190 [84.8039, 183.0065] |
| lighting | dim | 300 | 0.8828 [0.8345, 0.9310] | 122.5806 [70.9677, 180.6452] |
| lighting | neutral | 300 | 0.9114 [0.8671, 0.9494] | 91.5493 [42.2535, 140.8451] |
| tape_occlusion | False | 720 | 0.9048 [0.8739, 0.9328] | 121.2121 [88.0854, 157.0248] |
| tape_occlusion | True | 180 | 0.8280 [0.7419, 0.8927] | 91.9540 [34.4828, 160.9195] |
### shift

| Slice | Value | N | Recall [95% CI] | Clean alarms / 1,000 [95% CI] |
| --- | --- | --- | --- | --- |
| label | clean | 450 | not measured | 517.7778 [471.0556, 564.4444] |
| label | crushed_corner | 90 | 0.4667 [0.3778, 0.5669] | not measured |
| label | dent_crush | 90 | 0.8889 [0.8222, 0.9444] | not measured |
| label | open_flap | 90 | 0.6778 [0.5778, 0.7778] | not measured |
| label | tear_puncture | 90 | 0.7889 [0.7000, 0.8667] | not measured |
| label | water_stain | 90 | 0.6778 [0.5778, 0.7669] | not measured |
| severity | mild | 151 | 0.6026 [0.5232, 0.6755] | not measured |
| severity | moderate | 153 | 0.7320 [0.6601, 0.8039] | not measured |
| severity | none | 450 | not measured | 517.7778 [471.0556, 564.4444] |
| severity | severe | 146 | 0.7671 [0.6918, 0.8425] | not measured |
| lighting | bright | 300 | 0.7423 [0.6748, 0.8098] | 576.6423 [489.0511, 656.9343] |
| lighting | dim | 300 | 0.6463 [0.5714, 0.7211] | 496.7320 [418.3007, 575.3268] |
| lighting | neutral | 300 | 0.7071 [0.6355, 0.7786] | 487.5000 [412.5000, 562.5000] |
| tape_occlusion | False | 721 | 0.7104 [0.6639, 0.7541] | 529.5775 [478.8732, 583.0986] |
| tape_occlusion | True | 179 | 0.6548 [0.5476, 0.7619] | 473.6842 [378.6842, 578.9474] |

## Review decision and sensitivity

At or above the frozen threshold: flag the image for a person to inspect. Below it: the simulated policy clears the image. **Production auto-clear remains disabled:** this study does not validate real-image safety, content condition, claims liability or multi-parcel inspection. A reviewer needs the original image, image score, capture context, views of other sides and the physical parcel when ambiguous. Do not infer damage absence from a hidden face. Ground-truth overlays in the gallery are generator annotations, not predictions.

On test: 115.5556 [84.4444, 146.7222] false reviews per 1,000 clean images; 111.1111 [84.3889, 140.0000] misses per 1,000 damaged images.

| Assumed damaged share | False reviews / 1,000 total | Missed damage / 1,000 total | Total reviews / 1,000 |
| --- | --- | --- | --- |
| 1% | 114.4 | 1.1 | 123.3 |
| 5% | 109.8 | 5.6 | 154.2 |
| 20% | 92.4 | 22.2 | 270.2 |

On shift: 517.7778 [473.2778, 562.2778] false reviews per 1,000 clean images; 300.0000 [260.0000, 340.0000] misses per 1,000 damaged images.

| Assumed damaged share | False reviews / 1,000 total | Missed damage / 1,000 total | Total reviews / 1,000 |
| --- | --- | --- | --- |
| 1% | 512.6 | 3.0 | 519.6 |
| 5% | 491.9 | 15.0 | 526.9 |
| 20% | 414.2 | 60.0 | 554.2 |

The 1%, 5% and 20% shares are assumptions, not observed field prevalence. The site slider shows the already frozen test predictions at alternative thresholds: descriptive sensitivity only, not a new tuned operating point. Numerical threshold curves and calibration bins are stored in results.json. No dollar benefit is asserted.

## Error analysis and iteration

The gallery intentionally includes the four most confidently flagged clean examples and four lowest-scoring missed damage examples per style when available, plus class controls. These are cherry-picked to expose errors, not to estimate performance. Check the original pixels and optional synthetic truth boxes. Printing/tape, dark backgrounds, faint stains and occluded intent are plausible confounders; individual causes are hypotheses, not independently verified explanations.

Visual inspection of the error contact sheet found visible dark dent patches in test_0874 and test_0785 that the frozen model nevertheless clears; test_0023 contains a visible stain and is also missed. In shifted scenes such as shift_0618 and shift_0646, contrasting corner patches can receive near-zero damage scores. Conversely, shift_0050 is visibly an intact rendered parcel but receives a near-one score. These examples directly show that even obvious drawn damage and clean geometry are not sufficient for reliable decisions under this pipeline. They do not establish which feature caused an individual error.

The complete candidate grid and validation-only checkpoint decisions are in ITERATIONS.md and data/v2/iterations.json. The global-only and no-normalization ablations use the selected architecture and regularization; each gets its own validation-selected checkpoint, temperature and threshold. They quantify pipeline removal, not a causal effect of one weight. Six CPU fits; no GPU occupation.

## Limits and next evidence required

- No real-image test, synthetic-to-real gap, independent annotation audit or live carrier experiment. C5 remains INCONCLUSIVE.
- Shared synthetic generator creates common shortcuts; more synthetic examples cannot prove real-world transfer.
- The shift benchmark bundles changes and remains synthetic; it is neither an independent renderer nor a real held-out session.
- Learned model predicts one binary label per single-parcel image. Damage boxes, type labels and severity are not learned outputs.
- Severity is programmed contrast/extent. Partially hidden intended damage can be unobservable.
- Score temperature is selected on synthetic validation. Calibration does not transfer by assumption to production prevalence.
- Bootstrap intervals omit training-set uncertainty and label ambiguity. Degenerate zero-error intervals must not be read as population certainty; the JSON provides the exact one-sided zero-alarm bound where applicable.
- No safe configured same-machine vision inference path was verified; no vision-model comparison was run.
- Obtain a licensed, independently annotated real capture set grouped by parcel/session, use it as a new untouched test, and retrain using separate real training/validation sources before operational acceptance.

