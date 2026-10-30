# TypeSafe Jev 1.14 on images: measured on our two demonstration problems

**Scope: 150 synthetic parcel images and 150 real warehouse-bin photos, one fixed prompt each, one run. Model `jev-1.14.0` with TypeSafe's "danger zone" image header (TypeSafe itself says image input and Box are experimental and not for production). Nothing was tuned on these images.**

## What was run

- **Parcels**: 150 images from the parcel-lens version 2 standard test split (75 damaged, 75 clean), fixed-seed sample. For each image two separate requests: a typed yes/no choice ("is the parcel damaged") and a Box question ("the damaged area of the parcel").
- **Bins**: 150 test-split photos from the Amazon Bin Image Dataset (50 empty, 100 non-empty), one typed choice among empty / low / medium / high, scored against the inventory record.
- 456 HTTP calls in total (cap 700), = 450 scored calls, 5 unscored format-check calls (2 refused for image size) and 1 refused scored-run bin call. Statuses: {'400': 3, '200': 453}.
- Deviations decided before scoring (details in `claims.json`): the API refused our native 224x168 parcel images ("Invalid image dimensions."), so parcels are sent enlarged 2x; one 398x272 bin photo was refused, so bin photos with a shorter side under 336 px are enlarged to 336. Local-model numbers come from the earlier projects' saved predictions on the same image ids.

## Results against the registered claims

| ID | Claim (registered before any image was sent) | Estimate [95% CI] | Verdict |
| --- | --- | --- | --- |
| P1 | Presence (yes/no) AUC >= 0.80, CI low >= 0.70 | 0.757 [0.679, 0.827] | NOT SUPPORTED |
| P2 | Recall >= 0.80 and clean false alarms <= 150 per 1,000 | recall 0.173 [0.107, 0.267]; false alarms 0.0 [0.0, 0.0] | NOT SUPPORTED |
| P3 | Box median IoU >= 0.50 (damaged) | 0.535 [0.488, 0.602] | SUPPORTED |
| P4 | Share of boxes with IoU >= 0.5 is at least 50% | 0.587 [0.467, 0.707] | SUPPORTED |
| P5 | Presence step says 'no' on >= 80% of clean images | 1.000 [1.000, 1.000] | SUPPORTED |
| P6 | Local model beats Jev on AUC by >= 0.05 (paired, CI low > 0) | 0.204 [0.131, 0.283] | SUPPORTED |
| B1 | Empty vs not-empty accuracy >= 0.85 | 0.933 [0.893, 0.973] | SUPPORTED |
| B2 | 4-class accuracy > majority rate and macro-F1 >= 0.40 | accuracy 0.580 [0.500, 0.660] (majority 0.333); macro-F1 0.538 [0.460, 0.608] | SUPPORTED |
| B3 | Local fine-tuned model has higher macro-F1 than Jev (paired CI low > 0) | 0.211 [0.110, 0.310] | SUPPORTED |
| T1 | >= 98% valid answers, p50 <= 5 s, p95 <= 15 s | valid 100.0% / 100.0%; p50 0.148 s / 0.139 s; p95 0.261 s / 0.258 s | SUPPORTED |

CIs are bootstrap (1,000 resamples, seed 7). A claim with a point estimate over its threshold but a CI that crosses it (P3) is marked SUPPORTED on the estimate and flagged here: **the P3 lower bound is below 0.5.**

### Parcels in more detail

| Measure | Jev (zero-shot) | Our trained local model (same 150 images) |
| --- | --- | --- |
| AUC | 0.757 [0.679, 0.827] | 0.961 [0.932, 0.985] |
| Recall of damaged | 0.173 [0.107, 0.267] | 0.920 |
| Precision | 1.000 [1.000, 1.000] | not recomputed |
| Clean false alarms per 1,000 | 0.0 [0.0, 0.0] | 173.3 |

- Box on the 75 damaged images: median IoU 0.535 [0.488, 0.602], mean 0.473; 58.7% reach IoU >= 0.5. A fixed box in the image centre would score a median of 0.069, so the boxes are genuinely finding the damage.
- On the 75 clean images the box step alone returned a box 75 times out of 75, as the docs warn. Presence-first avoided every one of them, but only because the presence step said "no" to almost everything.
- The whole pipeline (presence says yes, then box): a correct box (IoU >= 0.5) on only 13.3% of damaged parcels, with 0.0 false boxes per 1,000 clean parcels.
- Exploratory, not registered, so treat as a hint: the box's own confidence separates damaged from clean with AUC 0.802 (mean confidence 0.394 on damaged vs 0.189 on clean).

Example images (synthetic only; green = generator truth, red = Jev's box):
- `examples/example_1_test_0004.png`: IoU 0.60; presence says no
- `examples/example_2_test_0159.png`: IoU 0.89; presence says no
- `examples/example_3_test_0093.png`: IoU 0.00; presence says no
- `examples/example_4_test_0021.png`: clean image: box returned anyway; presence says no

### Bins in more detail (real photos; a table, not images, because the dataset licence forbids redistribution)

| Measure | Jev (zero-shot) | Our fine-tuned local model (same 150 bins) |
| --- | --- | --- |
| Accuracy (4 classes) | 0.580 [0.500, 0.660] | 0.780 [0.713, 0.840] |
| Macro-F1 | 0.538 [0.460, 0.608] | 0.749 [0.670, 0.819] |
| Empty vs not-empty accuracy | 0.933 [0.893, 0.973] | 0.993 [0.980, 1.000] |
| Within one class of the truth | 0.867 | 0.987 |

What Jev said for each true class (counts):

| truth \ Jev said | empty | low | medium | high |
| --- | --- | --- | --- | --- |
| empty | 47 | 2 | 0 | 1 |
| low | 2 | 14 | 4 | 0 |
| medium | 2 | 26 | 12 | 5 |
| high | 3 | 14 | 4 | 14 |

Jev leans toward "low": 56 bins called low against 20 that are, and 26 of the 45 truly medium bins were called low.

## What this means in words a non-expert understands

**Damaged parcels, "is it damaged?"** AUC is the chance that, given one damaged and one clean picture, the model scores the damaged one as more suspicious (0.5 is a coin flip, 1.0 is perfect). Jev scored 0.76, clearly better than a coin but well below our small trained model's 0.96. Jev is also very cautious: when it says "damaged" it is always right (precision 1.0), but it says so for only about 17 in 100 damaged parcels, so most damage is waved through. If a warehouse used its yes/no answer as is, it would miss most damage. (Its answer comes with probabilities, so a lower alert threshold would catch more; we did not tune one on this test set.)

**Damaged parcels, "where is it?"** IoU is how much a drawn box overlaps the true damage area (0 = no overlap, 1 = identical). The Box answer is the strongest result here: the typical box overlapped the true damage at 0.54, and 59% of boxes overlapped by half or more, with no training on our pictures. Our own trained model cannot draw boxes at all. The catch is the one TypeSafe warns about: Box always answers. On clean parcels it drew a box every time, so something must decide first whether there is damage; the yes/no step does that safely but is too timid.

**Bins, how full?** Real photos are harder: items overlap, bins are cluttered. Macro-F1 is the average of how well each of the four classes is recognised, giving each class equal weight. Jev found empty bins reliably (93% right on empty-versus-not) but is poor at counting: it got 58% of the four-way calls right against 78% for our fine-tuned model that has learned from thousands of these bins. The inventory records are themselves not perfect (items can hide behind others), so no model can reach 100%; we do not know where that ceiling lies, only that the local model got closer to it.

**Overall.** A general-purpose image decision model that has never seen our data is fairly good at "is the bin empty?" (a little behind our trained model) and can find where parcel damage is, which our model cannot, but is clearly worse than a small model trained on our data at deciding yes/no damage and at counting. Its practical strength is speed of setup: two sentences of instruction, no training.

## Cost and latency

- Latency per call, p50 / p95: parcels 0.148 s / 0.261 s; bins 0.139 s / 0.258 s (client-side wall time from a PC, single stream).
- Input tokens per call (the API reports usage): parcels about 698, bins about 962; totals 353,882 input and 14,400 output tokens across all 450 scored calls.
- The API reports tokens, not dollars. Per 1,000 images that is roughly 698k input tokens for a parcel question and 962k for a bin question. Secondary documentation (LiteLLM's page on Jev) lists $0.042 per million input tokens with output free; we did not verify that on TypeSafe's own price page, so treat it as unconfirmed.
- No 429 responses occurred.

## Limits

- One run per question; Jev's answers on a repeat were not checked for stability.
- The parcels are simple synthetic drawings, enlarged 2x to be accepted; real parcel photos could behave very differently, in either direction. The local-model parcel numbers also come from synthetic data.
- The bin comparison favours the local model, which was trained on the same dataset's train split; Jev saw none of it. Different, longer instructions might help Jev; we deliberately did not tune.
- Prompts were fixed once; the one-line class definitions for bins are ours.
- Box is judged against one generator box per damaged image; the boxes are mask bounds and a stain's blur may enlarge them.
- Only TypeSafe's documentation as relayed through LiteLLM and ai-sdk pages was reachable; the request format was confirmed by a working call, not by TypeSafe's own docs pages.
- Reproduce: see README.md in this folder (the parcel half lives in parcel-lens, the bin half in bin-replenish-lab). Offline tests: `pytest tests`.
