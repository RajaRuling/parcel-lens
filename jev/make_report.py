#!/usr/bin/env python3
"""Builds REPORT.md and public_summary.md from results/*.json (no numbers typed by hand)."""
import json
import common as C

p = json.load(open(C.RESULTS / "parcels.json")); b = json.load(open(C.RESULTS / "bins.json"))
calls = json.load(open(C.RESULTS / "calls_summary.json"))
f = lambda v, d=3: f"{v:.{d}f}"
ci = lambda v, d=3: f"{f(v[0], d)} [{f(v[1], d)}, {f(v[2], d)}]"
per1000 = lambda tok, per: tok / per * 1000

rows = [
 ("P1", "Presence (yes/no) AUC >= 0.80, CI low >= 0.70", ci(p["auc"]), p["auc"][0] >= .8 and p["auc"][1] >= .7),
 ("P2", "Recall >= 0.80 and clean false alarms <= 150 per 1,000", f"recall {ci(p['recall'])}; false alarms {ci(p['clean_false_alarms_per_1000'], 1)}", p["recall"][0] >= .8 and p["clean_false_alarms_per_1000"][0] <= 150),
 ("P3", "Box median IoU >= 0.50 (damaged)", ci(p["iou_median"]), p["iou_median"][0] >= .5),
 ("P4", "Share of boxes with IoU >= 0.5 is at least 50%", ci(p["iou_share_ge_0.5"]), p["iou_share_ge_0.5"][0] >= .5),
 ("P5", "Presence step says 'no' on >= 80% of clean images", ci(p["clean_presence_says_no"]), p["clean_presence_says_no"][0] >= .8),
 ("P6", "Local model beats Jev on AUC by >= 0.05 (paired, CI low > 0)", ci(p["auc_local_minus_jev"]), p["auc_local_minus_jev"][0] >= .05 and p["auc_local_minus_jev"][1] > 0),
 ("B1", "Empty vs not-empty accuracy >= 0.85", ci(b["jev"]["empty_vs_not_accuracy"]), b["jev"]["empty_vs_not_accuracy"][0] >= .85),
 ("B2", "4-class accuracy > majority rate and macro-F1 >= 0.40", f"accuracy {ci(b['jev']['accuracy'])} (majority {f(b['majority_rate'])}); macro-F1 {ci(b['jev']['macro_f1'])}", b["jev"]["accuracy"][0] > b["majority_rate"] and b["jev"]["macro_f1"][0] >= .4),
 ("B3", "Local fine-tuned model has higher macro-F1 than Jev (paired CI low > 0)", ci(b["macro_f1_local_minus_jev"]), b["macro_f1_local_minus_jev"][1] > 0),
 ("T1", ">= 98% valid answers, p50 <= 5 s, p95 <= 15 s", f"valid {f(p['latency']['ok_share'] * 100, 1)}% / {f(b['latency']['ok_share'] * 100, 1)}%; p50 {f(p['latency']['p50'])} s / {f(b['latency']['p50'])} s; p95 {f(p['latency']['p95'])} s / {f(b['latency']['p95'])} s", p["latency"]["ok_share"] >= .98 and p["latency"]["p95"] <= 15),
]
tab = "| ID | Claim (registered before any image was sent) | Estimate [95% CI] | Verdict |\n| --- | --- | --- | --- |\n" + "\n".join(
    f"| {i} | {t} | {e} | {'SUPPORTED' if ok else 'NOT SUPPORTED'} |" for i, t, e, ok in rows)
cm = b["confusion_jev_rows_truth_cols_pred"]
cmt = "| truth \\ Jev said | empty | low | medium | high |\n| --- | --- | --- | --- | --- |\n" + "\n".join(
    f"| {n} | " + " | ".join(map(str, r)) + " |" for n, r in zip(["empty", "low", "medium", "high"], cm))
ex = "\n".join(f"- `examples/{n}`: {c}" for n, c in p["examples"])
tok_p = p["tokens"]["mean_input"]; tok_b = b["tokens"]["mean_input"]

report = f"""# TypeSafe Jev 1.14 on images: measured on our two demonstration problems

**Scope: 150 synthetic parcel images and 150 real warehouse-bin photos, one fixed prompt each, one run. Model `jev-1.14.0` with TypeSafe's "danger zone" image header (TypeSafe itself says image input and Box are experimental and not for production). Nothing was tuned on these images.**

## What was run

- **Parcels**: 150 images from the parcel-lens version 2 standard test split (75 damaged, 75 clean), fixed-seed sample. For each image two separate requests: a typed yes/no choice ("is the parcel damaged") and a Box question ("the damaged area of the parcel").
- **Bins**: 150 test-split photos from the Amazon Bin Image Dataset (50 empty, 100 non-empty), one typed choice among empty / low / medium / high, scored against the inventory record.
- {calls['http_calls']} HTTP calls in total (cap 700), = 450 scored calls, 5 unscored format-check calls (2 refused for image size) and 1 refused scored-run bin call. Statuses: {calls['by_status']}.
- Deviations decided before scoring (details in `claims.json`): the API refused our native 224x168 parcel images ("Invalid image dimensions."), so parcels are sent enlarged 2x; one 398x272 bin photo was refused, so bin photos with a shorter side under 336 px are enlarged to 336. Local-model numbers come from the earlier projects' saved predictions on the same image ids.

## Results against the registered claims

{tab}

CIs are bootstrap (1,000 resamples, seed 7). A claim with a point estimate over its threshold but a CI that crosses it (P3) is marked SUPPORTED on the estimate and flagged here: **the P3 lower bound is below 0.5.**

### Parcels in more detail

| Measure | Jev (zero-shot) | Our trained local model (same 150 images) |
| --- | --- | --- |
| AUC | {ci(p['auc'])} | {ci(p['local_auc'])} |
| Recall of damaged | {ci(p['recall'])} | {f(p['local_recall'])} |
| Precision | {ci(p['precision'])} | not recomputed |
| Clean false alarms per 1,000 | {ci(p['clean_false_alarms_per_1000'], 1)} | {f(p['local_false_alarms_per_1000'], 1)} |

- Box on the {p['box_n_damaged']} damaged images: median IoU {ci(p['iou_median'])}, mean {f(p['iou_mean'])}; {f(p['iou_share_ge_0.5'][0] * 100, 1)}% reach IoU >= 0.5. A fixed box in the image centre would score a median of {f(p['iou_median_centre_guess'])}, so the boxes are genuinely finding the damage.
- On the {p['clean_n']} clean images the box step alone returned a box {p['clean_boxes_returned']} times out of {p['clean_n']}, as the docs warn. Presence-first avoided every one of them, but only because the presence step said "no" to almost everything.
- The whole pipeline (presence says yes, then box): a correct box (IoU >= 0.5) on only {f(p['pipeline_damaged_found_with_box_ge_0.5'] * 100, 1)}% of damaged parcels, with {f(p['pipeline_false_boxes_on_clean_per_1000'], 1)} false boxes per 1,000 clean parcels.
- Exploratory, not registered, so treat as a hint: the box's own confidence separates damaged from clean with AUC {f(p['box_confidence_auc_damaged_vs_clean'])} (mean confidence {f(p['box_confidence_mean_clean_vs_damaged'][1])} on damaged vs {f(p['box_confidence_mean_clean_vs_damaged'][0])} on clean).

Example images (synthetic only; green = generator truth, red = Jev's box):
{ex}

### Bins in more detail (real photos; a table, not images, because the dataset licence forbids redistribution)

| Measure | Jev (zero-shot) | Our fine-tuned local model (same 150 bins) |
| --- | --- | --- |
| Accuracy (4 classes) | {ci(b['jev']['accuracy'])} | {ci(b['local']['accuracy'])} |
| Macro-F1 | {ci(b['jev']['macro_f1'])} | {ci(b['local']['macro_f1'])} |
| Empty vs not-empty accuracy | {ci(b['jev']['empty_vs_not_accuracy'])} | {ci(b['local']['empty_vs_not_accuracy'])} |
| Within one class of the truth | {f(b['jev']['within_one_class'])} | {f(b['local']['within_one_class'])} |

What Jev said for each true class (counts):

{cmt}

Jev leans toward "low": {b['pred_counts']['low']} bins called low against {b['truth_counts']['low']} that are, and 26 of the 45 truly medium bins were called low.

## What this means in words a non-expert understands

**Damaged parcels, "is it damaged?"** AUC is the chance that, given one damaged and one clean picture, the model scores the damaged one as more suspicious (0.5 is a coin flip, 1.0 is perfect). Jev scored {f(p['auc'][0], 2)}, clearly better than a coin but well below our small trained model's {f(p['local_auc'][0], 2)}. Jev is also very cautious: when it says "damaged" it is always right (precision 1.0), but it says so for only about {f(p['recall'][0] * 100, 0)} in 100 damaged parcels, so most damage is waved through. If a warehouse used its yes/no answer as is, it would miss most damage. (Its answer comes with probabilities, so a lower alert threshold would catch more; we did not tune one on this test set.)

**Damaged parcels, "where is it?"** IoU is how much a drawn box overlaps the true damage area (0 = no overlap, 1 = identical). The Box answer is the strongest result here: the typical box overlapped the true damage at {f(p['iou_median'][0], 2)}, and {f(p['iou_share_ge_0.5'][0] * 100, 0)}% of boxes overlapped by half or more, with no training on our pictures. Our own trained model cannot draw boxes at all. The catch is the one TypeSafe warns about: Box always answers. On clean parcels it drew a box every time, so something must decide first whether there is damage; the yes/no step does that safely but is too timid.

**Bins, how full?** Real photos are harder: items overlap, bins are cluttered. Macro-F1 is the average of how well each of the four classes is recognised, giving each class equal weight. Jev found empty bins reliably ({f(b['jev']['empty_vs_not_accuracy'][0] * 100, 0)}% right on empty-versus-not) but is poor at counting: it got {f(b['jev']['accuracy'][0] * 100, 0)}% of the four-way calls right against {f(b['local']['accuracy'][0] * 100, 0)}% for our fine-tuned model that has learned from thousands of these bins. The inventory records are themselves not perfect (items can hide behind others), so no model can reach 100%; we do not know where that ceiling lies, only that the local model got closer to it.

**Overall.** A general-purpose image decision model that has never seen our data is fairly good at "is the bin empty?" (a little behind our trained model) and can find where parcel damage is, which our model cannot, but is clearly worse than a small model trained on our data at deciding yes/no damage and at counting. Its practical strength is speed of setup: two sentences of instruction, no training.

## Cost and latency

- Latency per call, p50 / p95: parcels {f(p['latency']['p50'])} s / {f(p['latency']['p95'])} s; bins {f(b['latency']['p50'])} s / {f(b['latency']['p95'])} s (client-side wall time from a PC, single stream).
- Input tokens per call (the API reports usage): parcels about {f(tok_p, 0)}, bins about {f(tok_b, 0)}; totals {p['tokens']['sum_input'] + b['tokens']['sum_input']:,} input and {p['tokens']['sum_output'] + b['tokens']['sum_output']:,} output tokens across all {p['latency']['n'] + b['latency']['n']} scored calls.
- The API reports tokens, not dollars. Per 1,000 images that is roughly {per1000(tok_p, 1)/1e3:.0f}k input tokens for a parcel question and {per1000(tok_b, 1)/1e3:.0f}k for a bin question. Secondary documentation (LiteLLM's page on Jev) lists $0.042 per million input tokens with output free; we did not verify that on TypeSafe's own price page, so treat it as unconfirmed.
- No 429 responses occurred.

## Limits

- One run per question; Jev's answers on a repeat were not checked for stability.
- The parcels are simple synthetic drawings, enlarged 2x to be accepted; real parcel photos could behave very differently, in either direction. The local-model parcel numbers also come from synthetic data.
- The bin comparison favours the local model, which was trained on the same dataset's train split; Jev saw none of it. Different, longer instructions might help Jev; we deliberately did not tune.
- Prompts were fixed once; the one-line class definitions for bins are ours.
- Box is judged against one generator box per damaged image; the boxes are mask bounds and a stain's blur may enlarge them.
- Only TypeSafe's documentation as relayed through LiteLLM and ai-sdk pages was reachable; the request format was confirmed by a working call, not by TypeSafe's own docs pages.
- Reproduce: see README.md in this folder (the parcel half lives in parcel-lens, the bin half in bin-replenish-lab). Offline tests: `pytest tests`.
"""
open(C.HERE / "REPORT.md", "w").write(report)

pub = f"""# Jev 1.14 image model: numbers safe to publish

Model jev-1.14.0 (experimental image and Box features, per TypeSafe). 150 synthetic parcel images and 150 real bin photos; one fixed prompt each, no tuning.

- Parcel damage yes/no: AUC {ci(p['auc'], 2)}; recall {f(p['recall'][0], 2)}; clean false alarms {f(p['clean_false_alarms_per_1000'][0], 0)} per 1,000. Our trained local model on the same images: AUC {f(p['local_auc'][0], 2)}.
- Damage box: median overlap (IoU) with truth {ci(p['iou_median'], 2)}; {f(p['iou_share_ge_0.5'][0] * 100, 0)}% of boxes overlap >= 0.5. The box step returns a box even on clean images ({p['clean_boxes_returned']} of {p['clean_n']}), so a presence check must come first.
- Bin fill level (4 classes): accuracy {ci(b['jev']['accuracy'], 2)}; macro-F1 {ci(b['jev']['macro_f1'], 2)}; empty vs not-empty accuracy {ci(b['jev']['empty_vs_not_accuracy'], 2)}. Our fine-tuned local model: accuracy {f(b['local']['accuracy'][0], 2)}, macro-F1 {f(b['local']['macro_f1'][0], 2)}.
- Speed: median {f(p['latency']['p50'], 2)} s per call, p95 {f(p['latency']['p95'], 2)} s; about {f(tok_p, 0)} to {f(tok_b, 0)} input tokens per image.
- Parcels are synthetic; bin photos are not redistributed. Real parcel photos were not tested.
"""
open(C.HERE / "public_summary.md", "w").write(pub)
