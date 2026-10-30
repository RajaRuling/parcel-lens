# Parcel Lens — visible damage evidence lab

A local static demonstration and reproducible experiment for deciding which **single-parcel images** need review. Version 2 uses 4,800 original procedural scenes and compares a retained classical detector, a trivial baseline, trained linear/neural classifiers and two ablations. **Zero real photographs were tested.** The learned task is binary image classification, not learned damage-box detection.

The evidence supports discrimination within the standard generator, but fails both the review acceptance target and the held-out-style transfer target. Production auto-clear is disabled in the demonstration.

| Registered claim | Final estimate, 95% bootstrap CI | Verdict |
| --- | --- | --- |
| Standard ROC AUC >=0.80 | 0.9512 [0.9369, 0.9638] | SUPPORTED |
| F1 gain over classical >=0.05 | +0.3004 [0.2662, 0.3356] | SUPPORTED |
| Recall >=0.90 and <=100 false reviews / 1,000 clean | Recall 0.8889 [0.8600, 0.9156]; alarms 115.6 [84.4, 146.7] | NOT SUPPORTED |
| Held-out-style ROC AUC >=0.75 | 0.6448 [0.6099, 0.6821] | NOT SUPPORTED |
| Useful real-photograph discrimination | 0 real images; no metric | INCONCLUSIVE |

On the standard test the frozen model has TN=398, FP=52, FN=50, TP=400; F1=0.8869 [0.8653, 0.9075]. On the shift test it has TN=217, FP=233, FN=135, TP=315; F1=0.6313 [0.6036, 0.6587]. All intervals use 1,000 fixed-seed scene resamples. The F1 comparison uses paired resamples. Full precision, recall, AUC, average precision, Brier, calibration and subgroup intervals are in [REPORT.md](REPORT.md).

## Open the demonstration

Open [docs/index.html](docs/index.html) directly in a browser. No build step or server is needed. The site reads a local JavaScript snapshot of the measured JSON. It includes all five verdicts, baseline/ablation tables, both confusion matrices, reliability plots, threshold curves, prevalence sensitivity, subgroup slices, the iteration story, and a gallery of failures with optional synthetic truth boxes. It is static-host-ready but has not been published.

Gallery images are small, original CC0 drawings. The slider explores frozen test decisions; it does not retune the model, change claims, or authorize operational clearing. A clear simulation means score below threshold, not proof that a parcel is undamaged.

## Reproduce locally

Use Python 3.14 on Linux. Run from this project folder. The included `.venv` is project-local and isolated from system site packages. Top-level versions are in requirements.txt; all resolved runtime/check dependencies are pinned in requirements-lock.txt.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
make results
make test
make verify
make words
```

`make results` (equivalently `.venv/bin/python -m src.run_all`) regenerates split identities, 4,800 images, features, six fitted heads, checkpoint/temperature/threshold choices, all 1,000-resample intervals, JSON, gallery/contact sheet, report, and the site's research copies. It uses CPU only and fixed seed 20261029. Each fit caps at 160 epochs or about 19 minutes; observed fit times are recorded, not used for claims. Images occupy about 258 MB. The full protocol takes a few minutes on this machine; timings are not a portable performance claim. Repeating the frozen protocol is reproducibility checking, not permission to tune on test outcomes.

The first completed numerical evaluation is preserved in data/v2/first-evaluation.json when performing the documented reproduction check. Model scores and metrics should reproduce with the pinned packages on the same platform; timings may differ. Checkpoints, thresholds, model hashes and registered-plan hash are written to data/v2/frozen.json before test feature extraction. Model files contain inference parameters only, excluding runtime timing metadata.

For new-image local inference:

```sh
.venv/bin/python -m src.predict data/v2/images/test_0000.png
```

This prints the frozen image score and simulated action. There is no remote model call, upload or learned box output. The score's calibration was fitted on synthetic validation; no claim about real-image probabilities follows.

## Data and experiment discipline

[EXPERIMENTS.md](EXPERIMENTS.md) was written before version 2 rendering or training. Source scene/seed splits are fixed before image generation: 2,400 train, 600 validation, 900 standard test, 900 shifted test. Every split has 50% clean scenes, and 10% each dent/crush, tear/puncture, water stain, open flap and crushed corner. Unique image hashes are recorded; no related views or crops cross splits. No legacy scene enters version 2.

Features are 732 fixed multiscale colour, gradient and local residual summaries derived from pixels, with training-only standardization. Two linear logistic heads and two 32-unit tanh neural heads use regularizations 0.001/0.01. The final model, linear_r0.001, wins validation F1 after a validation-only recall-target threshold search. The neural head did not win the registered selection criterion. Global-only and no-normalization ablations are diagnostic and do not compete for selection. Per-epoch validation losses and all outcomes remain in [ITERATIONS.md](ITERATIONS.md) and data/v2/iterations.json.

The selected threshold is 0.3546285831; synthetic-validation temperature is recorded in the iteration log. On the standard test, mild-damage recall is 76.3%, versus 98.6% for severe generated damage. Water-stain recall is 76.7%. On the shift test, crushed-corner recall falls to 46.7%. These are programmed damage groups, not independently annotated field categories; full subgroup intervals are in the report.

The shift benchmark holds out larger viewpoint rotations, a cooler palette, darker/cluttered backgrounds and higher noise together. Its failure exposes fragility; it does not identify one causal reason or measure real-camera transfer. Temperature calibration also deteriorates: Brier rises from 0.0819 to 0.3527 and ECE from 0.0307 to 0.3313.

[DATA.md](DATA.md) records the serious multi-source search, checked licences, HTTP outcomes and why no real benchmark was secured. Public parcel sources returned 403 or had metadata-only images, unsuitable licences, insufficient independent photos or the wrong object domain. No external image was downloaded or redistributed. All version 2 images and mask-derived annotations are original CC0 1.0 data; see data/LICENSE.txt. Version 1's 40 synthetic scenes remain only as regression fixtures.

## Operational interpretation

At the frozen threshold, standard-style false reviews are 115.6 [84.4, 146.7] per 1,000 clean images; misses are 111.1 [84.4, 140.0] per 1,000 damaged images. Under held-out styles, those worsen to 517.8 [473.3, 562.3] and 300.0 [260.0, 340.0].

At an **assumed** 5% damaged share, standard-style errors imply about 154 reviews and 5.6 missed damaged parcels per 1,000 total images. Shift-style errors imply about 527 reviews and 15 misses. These calculations assume the measured conditional synthetic rates apply; they are not a carrier forecast. The site also shows 1% and 20% prevalence assumptions and threshold sensitivity. No dollar benefit is asserted.

## Targeted verification and screenshots

Only this project's offline tests and browser flow are run. No repository-wide test suite is needed. Tests use small deterministic fixtures and existing local regression data. They check non-overlapping splits, repeated rendering, tied-score AUC/AP, undefined metrics, paired uncertainty, threshold selection, actual learning, saved-model reload, old detector geometry, public wording and site/JSON parity.

```sh
make browser
```

The browser script uses an already installed Chromium if available. Otherwise install into this project, avoiding a system browser modification:

```sh
PLAYWRIGHT_BROWSERS_PATH=.browser-tmp/browsers .venv/bin/python -m playwright install chromium
make browser
```

The script prefers the project-local browser, then the existing user cache. CHROMIUM_EXECUTABLE can override discovery. Required screenshots are in docs/screenshots/: desktop, claims, policy and inspector views at 390 px and 1280 px. Browser checks cover all gallery images on both splits, threshold controls, truth toggle, navigation, claims, model tables, confusion counts, evidence links, horizontal overflow, JavaScript errors and absence of external requests. Verification details and visual inspection notes are recorded in [VERIFICATION.md](VERIFICATION.md). The shared workspace scanner also passed when scoped to this folder; its workspace-wide run reported unrelated sibling-data findings outside the allowed edit scope.

## Honest limits

No real-image accuracy, real synthetic-to-real gap, learned box accuracy, multi-parcel recognition, independent annotation audit, production calibration, live review trial or financial savings is established. All test images share a procedural renderer. Ground truth encodes intended damage and may remain positive under tape occlusion. Bootstrap intervals do not include retraining or annotation uncertainty; zero-error intervals do not prove zero population risk.

The optional JSON box adapter remains available and schema-tested. The existing application image helper was inspected, but no safe configured same-machine vision inference route was verified without restricted configuration or another machine; no vision experiment or model swap was run. Before operational use, obtain an independently annotated real capture set grouped by physical parcel and session, and test a frozen pipeline against the actual review budget.
