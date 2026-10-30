#!/usr/bin/env python3
"""Reads results/raw_*.jsonl, evaluates the pre-registered claims, writes results/*.json, examples/*.png."""
import json, statistics
import numpy as np
import common as C, run_jev_parcels as P

R = C.RESULTS


def verdict(ok): return "SUPPORTED" if ok else "NOT SUPPORTED"


def parcels():
    recs = {r["id"]: r for r in json.load(open(P.PARCELS / "results.json"))["test_records"]}
    ann = {r["id"]: r for r in json.load(open(P.PARCELS / "annotations.json"))["records"]}
    rows = C.load_jsonl(P.RAW)
    pres = {r["id"]: r for r in rows if r["kind"] == "presence"}
    box = {r["id"]: r for r in rows if r["kind"] == "box"}
    ids = [i for i in sorted(pres) if pres[i]["ok"]]
    y = [pres[i]["damaged"] for i in ids]
    s = [pres[i]["p_yes"] for i in ids]
    loc = [recs[i]["score"] for i in ids]
    yes = [pres[i]["choice"] == "yes" for i in ids]
    n = len(ids)
    pos = [k for k in range(n) if y[k]]; neg = [k for k in range(n) if not y[k]]
    strata = [pos, neg]

    def prec(idx): 
        tp = sum(1 for k in idx if y[k] and yes[k]); fp = sum(1 for k in idx if not y[k] and yes[k]); return tp / (tp + fp) if tp + fp else float("nan")
    def rec(idx):
        p = [k for k in idx if y[k]]; return sum(yes[k] for k in p) / len(p) if p else float("nan")
    def fa(idx):
        q = [k for k in idx if not y[k]]; return 1000 * sum(yes[k] for k in q) / len(q) if q else float("nan")
    def A(sc): return lambda idx: C.auc([sc[k] for k in idx], [y[k] for k in idx])
    out = {"n": n, "failed_calls": sum(1 for r in pres.values() if not r["ok"])}
    out["auc"] = [C.auc(s, y), *C.boot(A(s), n, strata=strata)]
    out["precision"] = [prec(range(n)), *C.boot(prec, n, strata=strata)]
    out["recall"] = [rec(range(n)), *C.boot(rec, n, strata=strata)]
    out["clean_false_alarms_per_1000"] = [fa(range(n)), *C.boot(fa, n, strata=strata)]
    out["accuracy"] = sum(yes[k] == bool(y[k]) for k in range(n)) / n
    out["local_auc"] = [C.auc(loc, y), *C.boot(A(loc), n, strata=strata)]
    lyes = [recs[i]["review"] for i in ids]
    out["local_recall"] = sum(lyes[k] for k in pos) / len(pos)
    out["local_false_alarms_per_1000"] = 1000 * sum(lyes[k] for k in neg) / len(neg)
    d = lambda idx: C.auc([loc[k] for k in idx], [y[k] for k in idx]) - C.auc([s[k] for k in idx], [y[k] for k in idx])
    out["auc_local_minus_jev"] = [d(range(n)), *C.boot(d, n, strata=strata)]
    # boxes
    ious = {}
    for i in ids:
        b = box.get(i)
        if b and b["ok"] and ann[i]["objects"]:
            g = C.xyxy_to_frac(ann[i]["objects"][0]["box"], P.W, P.H)
            ious[i] = C.iou(b["box"], g)
    dm = [i for i in ids if ann[i]["damaged"]]
    iv = [ious[i] for i in dm if i in ious]
    out["box_n_damaged"] = len(iv)
    med = lambda idx: statistics.median([iv[k] for k in idx])
    sh = lambda idx: sum(iv[k] >= .5 for k in idx) / len(idx)
    out["iou_median"] = [statistics.median(iv), *C.boot(med, len(iv))]
    out["iou_share_ge_0.5"] = [sh(range(len(iv))), *C.boot(sh, len(iv))]
    out["iou_mean"] = float(np.mean(iv))
    # a trivial reference: always the box covering the image centre third, to show what IoU is by chance
    cen = {"top": .33, "bottom": .67, "left": .33, "right": .67}
    cv = [C.iou(cen, C.xyxy_to_frac(ann[i]["objects"][0]["box"], P.W, P.H)) for i in dm]
    out["iou_median_centre_guess"] = statistics.median(cv)
    clean = [i for i in ids if not ann[i]["damaged"]]
    out["clean_boxes_returned"] = sum(1 for i in clean if box.get(i, {}).get("ok")); out["clean_n"] = len(clean)
    out["clean_presence_says_no"] = [sum(1 for i in clean if pres[i]["choice"] == "no") / len(clean)]
    out["clean_presence_says_no"] += C.boot(lambda idx: sum(1 for k in idx if pres[clean[k]]["choice"] == "no") / len(idx), len(clean))
    cc = [box[i]["confidence"] for i in clean if box.get(i, {}).get("ok")]; dc = [box[i]["confidence"] for i in dm if box.get(i, {}).get("ok")]
    out["box_confidence_mean_clean_vs_damaged"] = [float(np.mean(cc)), float(np.mean(dc))]
    out["box_confidence_auc_damaged_vs_clean"] = C.auc(dc + cc, [1] * len(dc) + [0] * len(cc))
    # IoU of the damaged images that presence also flagged ("presence-first pipeline")
    pf = [ious[i] for i in dm if i in ious and pres[i]["choice"] == "yes"]
    out["pipeline_damaged_found_with_box_ge_0.5"] = sum(v >= .5 for v in pf) / len(dm)
    out["pipeline_false_boxes_on_clean_per_1000"] = 1000 * sum(1 for i in clean if pres[i]["choice"] == "yes") / len(clean)
    out["_iou_by_id"] = ious
    lat = [r["latency_s"] for r in rows if r["ok"]]
    out["latency"] = {"p50": C.percentile(lat, .5), "p95": C.percentile(lat, .95), "n": len(lat),
                      "ok_share": sum(r["ok"] for r in rows) / len(rows)}
    tok = [r["usage"].get("input_tokens", 0) for r in rows if r["ok"]]
    out["tokens"] = {"mean_input": float(np.mean(tok)), "sum_input": int(sum(tok)),
                     "sum_output": int(sum(r["usage"].get("output_tokens", 0) for r in rows if r["ok"]))}
    return out, pres, box, ann, ious


def draw(pres, box, ann, ious):
    from PIL import Image, ImageDraw
    dm = [i for i in sorted(ious) if ann[i]["damaged"]]
    pick = [dm[0], max(dm, key=lambda i: ious[i]), min(dm, key=lambda i: ious[i])]
    clean = [i for i in sorted(pres) if not ann[i]["damaged"] and box.get(i, {}).get("ok")]
    pick.append(clean[0])
    (C.HERE / "examples").mkdir(exist_ok=True)
    names = []
    for k, i in enumerate(pick):
        im = Image.open(P.PARCELS / ann[i]["file"]).convert("RGB").resize((448, 336)); d = ImageDraw.Draw(im)
        if ann[i]["damaged"]:
            x0, y0, x1, y1 = ann[i]["objects"][0]["box"]; d.rectangle([x0 * 2, y0 * 2, x1 * 2, y1 * 2], outline=(0, 160, 0), width=3)
        b = box[i]["box"]; d.rectangle([b["left"] * 448, b["top"] * 336, b["right"] * 448, b["bottom"] * 336], outline=(230, 0, 0), width=3)
        cap = (f"IoU {ious[i]:.2f}" if i in ious else "clean image: box returned anyway") + f"; presence says {pres[i]['choice']}"
        d.rectangle([0, 0, 448, 16], fill=(255, 255, 255)); d.text((4, 2), "green=truth red=Jev: " + cap, fill=(0, 0, 0))
        fn = f"example_{k+1}_{i}.png"; im.save(C.HERE / "examples" / fn); names.append((fn, cap))
    return names


def main():
    po, pres, box, ann, ious = parcels()
    names = draw(pres, box, ann, ious)
    po["examples"] = names
    json.dump({k: v for k, v in po.items() if not k.startswith("_")}, open(R / "parcels.json", "w"), indent=1)
    calls = C.load_jsonl(R / "calls.jsonl")
    json.dump({"http_calls": len(calls), "by_status": {str(s): sum(1 for c in calls if c["status"] == s) for s in {c["status"] for c in calls}}}, open(R / "calls_summary.json", "w"), indent=1)
    print(json.dumps({"parcels": {k: v for k, v in po.items() if not k.startswith("_") and k != "examples"}}, indent=1))


if __name__ == "__main__":
    main()
