# Version 2 verification — 2026-10-29

## Completed local checks

- **49 targeted tests passed**: tests/test_core.py and tests/test_v2.py. These are the project's small offline tests; no repository-wide suite ran. The final run took 2.96 seconds on this machine.
- **One-command reproduction passed**: `make results` completed from rendering through the site/report build. src/verify_artifacts.py compared the preserved first evaluation with the completed reproduction: identical scores, metrics, 1,000-resample intervals, claims, threshold curves, operating calculations and test records. No model/threshold selection rule was changed after seeing the test results.
- **4,800 image file hashes verified**, with 4,800 unique scene seeds and 4,800 unique image hashes. Split counts are 2,400 / 600 / 900 / 900. Lighting/class cross-counts are recorded in data/v2/data-audit.json; nuisance distributions are not exactly equal but lighting is not assigned from the class label.
- **Six model artifact hashes verified** against the final frozen manifest. All displayed gallery scores reproduce from the saved selected model to absolute tolerance 1e-12. Standardization means are covered by offline tests; runtime metadata is excluded from model serialization, and changing recorded fit time does not change a saved model's bytes.
- **Site/JSON parity passed**: every field in the site's evidence snapshot matches the measured results. All 39 redistributed gallery images exactly match their corresponding original generated images. Selected-model point metrics were independently recomputed from the saved test scores without fitting a model.
- **Browser checks passed at 390 px and 1280 px**: all 39 gallery examples across both splits, five claim verdicts, eight baseline/candidate rows, six iteration rows, truth toggle, previous/next navigation, threshold controls, confusion values, and local evidence links. Zero JavaScript errors, external requests or page-level horizontal overflow.
- **Local inference command passed** on test_0000: score 0.3946001962 at threshold 0.3546285831; simulated review. Production auto-clear false; no localization output or network call.
- **Public wording passed within this project** using both src/check_public.py and the shared scanner applied to this folder. The explicitly requested workspace-wide scanner command was also executed. It reported unrelated sibling-project raw/temporary-data findings outside the authorized edit scope; those files were not changed. The project-specific shared scan examined 49 text files before this verification note was added; the final scan is recorded in data/v2/public-word-scan.json.

## Screenshot inspection

The final screenshots are in docs/screenshots/. Visually inspected at both widths:

- desktop-1280.png: complete evidence narrative, comparison table, confusion/reliability panels, threshold curves, subgroup and iteration tables, and limits.
- claims-1280.png: all five measured outcomes and verdicts visible together.
- hero-390.png: navigation wraps cleanly; procedural-only notice and evidence cards remain legible.
- claims-390.png: all five claims stack into cards with visible verdicts; no sideways scrolling is required to discover negative results.
- policy-390.png: enlarged mobile SVG axis labels, slider state, conditional error counts and prevalence assumptions remain readable.
- inspector-390.png and inspector-1280.png: the parcel image, clean ground truth, confidently wrong review decision and limits are visible; the image is not presented as real photography.

Also inspected assets/error-contact-sheet.png: visible dent/stain misses and repeated shifted-corner misses are documented by scene ID in REPORT.md; several visibly clean drawings receive high review scores. No causal feature explanation is asserted.

Inspection prompted two UI corrections: stack the mobile claims table and enlarge mobile chart labels. The browser checks and screenshots were rerun after those corrections. Wide comparison/subgroup tables deliberately scroll inside keyboard-focusable labelled regions; the page itself does not overflow.

## Execution notes and boundaries

The initial numerical experiment completed before the site builder module was finished; the saved scores were then used to assemble the site without model re-selection. A preliminary reproduction was interrupted during rendering. The subsequent `make results` run completed successfully and passed the exact numerical comparison. The later model serialization change removes timing metadata only; predictions and frozen choices remain identical.

Dependencies are pinned in requirements-lock.txt and installed in the isolated project-local .venv (system-site-packages false). Tests place their temporary fixtures inside .pytest_cache. Chromium uses project-local temporary/profile directories and an existing installed browser. Its first launch was blocked by the restricted process sandbox; the authorized local browser check succeeded with the process sandbox restriction lifted. No browser installation or system Python change was made.

All project changes and generated deliverables are confined to this project. No source-control service, push, publication, remote device or outbound message was used. The retired project was untouched. Training was CPU-only; no local model was loaded, swapped or evicted. Public data metadata and dependency installation were the only external acquisition activities.

## What remains unverified

Real-image accuracy, synthetic-to-real gap, independently annotated severity/type/localization, live workflow benefit and local vision-model agreement remain unverified. No suitable real benchmark was acquired. The procedural fallback satisfies the experiment brief but cannot establish production readiness. See DATA.md for the acquisition evidence and REPORT.md for every acceptance verdict and interval.
