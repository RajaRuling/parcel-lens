#!/usr/bin/env python3
"""Experiment 1: damaged parcels. Presence (typed yes/no choice) + box, jev-1.14.0. Resumable; raw answers in results/raw_parcels.jsonl."""
import argparse, io, json, random, sys
from pathlib import Path
import common as C

PARCELS = C.ROOT / "data/v2"
W, H = 224, 168
PRESENCE_Q = {"type": "choice",
              "instructions": "Is the cardboard parcel in `photo` damaged? Damage means a dent or crushed corner, a tear or puncture, "
                              "a water stain, or an open flap. Intact parcels with only labels, tape or scuffs are not damaged.",
              "criteria": {"yes": None, "no": None}}
BOX_Q = {"type": "box", "instructions": "the damaged area of the parcel in `photo`"}
RAW = C.RESULTS / "raw_parcels.jsonl"


def upscale2x(data: bytes) -> bytes:
    """Jev refused the native 224x168 scenes ("Invalid image dimensions."), so every parcel image is sent
    at exactly 2x (448x336, bicubic, PNG). Fixed before scoring; boxes are fractions so scale does not matter."""
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    out = io.BytesIO()
    im.resize((im.width * 2, im.height * 2), Image.BICUBIC).save(out, "PNG")
    return out.getvalue()


def sample():
    recs = [r for r in json.load(open(PARCELS / "annotations.json"))["records"] if r["split"] == "test"]
    rng = random.Random(C.SEED)
    dmg = sorted((r for r in recs if r["damaged"]), key=lambda r: r["id"])
    cln = sorted((r for r in recs if not r["damaged"]), key=lambda r: r["id"])
    return sorted(rng.sample(dmg, 75) + rng.sample(cln, 75), key=lambda r: r["id"])


def run(client, recs, root=PARCELS):
    done = {(r["id"], r["kind"]) for r in C.load_jsonl(RAW)}
    for rec in recs:
        data = upscale2x((root / rec["file"]).read_bytes())
        for kind, q in (("presence", PRESENCE_Q), ("box", BOX_Q)):
            if (rec["id"], kind) in done:
                continue
            row = {"id": rec["id"], "kind": kind, "damaged": rec["damaged"]}
            try:
                res = client.ask(data, "image/png", "", {"q": q}, f"parcel:{kind}")
                ans = res["answers"]["q"]
                if kind == "presence":
                    ch, conf, probs = C.parse_choice(ans, ["yes", "no"])
                    row.update(choice=ch, confidence=conf, p_yes=probs.get("yes"))
                else:
                    box, conf = C.parse_box(ans)
                    row.update(box=box, confidence=conf)
                row.update(latency_s=res["latency_s"], usage=res["usage"], ok=True)
            except C.JevVisionError as e:
                row.update(ok=False, error=str(e)[:500])
                if "abort" in str(e) or "cap" in str(e) or "HTTP 4" in str(e) and "429" not in str(e):
                    C.append_jsonl(RAW, row)
                    raise
            C.append_jsonl(RAW, row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="first N sampled images only (smoke)")
    a = ap.parse_args()
    recs = sample()
    if a.limit:
        recs = recs[: a.limit]
    C.RESULTS.mkdir(exist_ok=True)
    run(C.Client(), recs)
    print("done; calls so far:", C.Client().n_calls())


if __name__ == "__main__":
    main()
