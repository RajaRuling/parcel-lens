"""Shared pieces: a multipart Jev client (images + box), sampling, statistics.
The API key is read ONLY from the environment variable JEV_API_KEY; it is never printed, logged or stored.
Running the experiment makes real, paid network calls (the full study was 456 calls, about 354,000 input tokens);
the tests never do: they pass a stub transport."""
from __future__ import annotations
import json, math, random, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # the repository root
RESULTS = HERE / "results"
URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.14.0"
CALL_CAP = 700
SEED = 20261030


class JevVisionError(Exception):
    """Short message only: never a body, header, URL or key."""


class Client:
    def __init__(self, *, transport=None, env=None, sleep=None, calls_log=None, interval=0.3):
        self.transport = transport
        if transport is None:
            def _post(*a, **k):
                import requests
                return requests.post(*a, **k)
            self.transport = _post
        if env is None:
            import os
            env = os.environ
        key = env.get("JEV_API_KEY", "")
        if not key:
            raise JevVisionError("set the environment variable JEV_API_KEY")
        self._headers = {"Authorization": f"Bearer {key}", "TypeSafe-Danger-Zone-Images": "true"}
        self.sleep = sleep or time.sleep
        self.calls_log = Path(calls_log) if calls_log else RESULTS / "calls.jsonl"
        self.interval = interval
        self.consecutive_429 = 0

    def n_calls(self) -> int:
        try:
            return sum(1 for _ in open(self.calls_log))
        except OSError:
            return 0

    def _log(self, rec):
        self.calls_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.calls_log, "a") as f:
            f.write(json.dumps(rec) + "\n")

    def ask(self, image_bytes: bytes, media: str, state_text: str, questions: dict, tag: str) -> dict:
        """One request. Returns {'answers','usage','latency_s','attempts'}; raises JevVisionError."""
        body = {"model": MODEL, "state": {"photo": "img-1"},
                "assets": {"img-1": {"type": "image", "part": "photo-part"}}, "questions": questions}
        # state_text goes in the instructions of each question (the image is referenced as `photo`)
        for attempt in range(3):
            if self.n_calls() >= CALL_CAP:
                raise JevVisionError("call cap reached")
            self.sleep(self.interval)
            files = {"request": (None, json.dumps(body), "application/json"),
                     "photo-part": ("photo", image_bytes, media)}
            t0 = time.monotonic()
            try:
                r = self.transport(URL, headers=self._headers, files=files, timeout=60, allow_redirects=False)
                code = getattr(r, "status_code", None)
            except Exception as exc:
                self._log({"tag": tag, "status": f"exc:{type(exc).__name__}", "t": round(time.monotonic() - t0, 3)})
                raise JevVisionError(f"transport failure ({type(exc).__name__})") from None
            lat = time.monotonic() - t0
            self._log({"tag": tag, "status": code, "t": round(lat, 3)})
            if code in (429, 529):
                self.consecutive_429 += 1
                if self.consecutive_429 >= 5:
                    raise JevVisionError("abort: 5 consecutive 429 responses")
                self.sleep(min(30, 2 ** (attempt + 1)))
                continue
            self.consecutive_429 = 0
            if code != 200:
                msg = ""
                try:  # the API's error text is the exact refusal the brief asks to record; no key is in it
                    msg = json.dumps(r.json())[:400]
                except Exception:
                    pass
                raise JevVisionError(f"HTTP {code} {msg}")
            try:
                data = r.json()
                data = data.get("result", data)
                return {"answers": data["answers"], "usage": data.get("usage", {}),
                        "latency_s": lat, "attempts": attempt + 1}
            except Exception:
                raise JevVisionError("invalid JSON answer") from None
        raise JevVisionError("retries exhausted")


# ---------- parsing ----------
def parse_choice(ans, criteria):
    c = ans["choice"]
    if c not in criteria:
        raise JevVisionError("choice not in criteria")
    return c, float(ans["confidence"]), {k: float(v) for k, v in ans["probabilities"].items()}


def parse_box(ans):
    b = ans["box"]
    top, bottom, left, right = (float(b[k]) for k in ("top", "bottom", "left", "right"))
    if not (0 <= top < bottom <= 1 and 0 <= left < right <= 1):
        raise JevVisionError("box out of range")
    return {"top": top, "bottom": bottom, "left": left, "right": right}, float(ans.get("confidence", float("nan")))


def iou(a, b):
    """Boxes as dicts top/bottom/left/right (fractions)."""
    iw = max(0.0, min(a["right"], b["right"]) - max(a["left"], b["left"]))
    ih = max(0.0, min(a["bottom"], b["bottom"]) - max(a["top"], b["top"]))
    inter = iw * ih
    ua = (a["right"] - a["left"]) * (a["bottom"] - a["top"]) + (b["right"] - b["left"]) * (b["bottom"] - b["top"]) - inter
    return inter / ua if ua > 0 else 0.0


def xyxy_to_frac(box, w, h):
    x0, y0, x1, y1 = box
    return {"top": y0 / h, "bottom": y1 / h, "left": x0 / w, "right": x1 / w}


# ---------- statistics ----------
def auc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg:
        return float("nan")
    w = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return w / (len(pos) * len(neg))


def boot(fn, n, seed=7, resamples=1000, strata=None):
    """Percentile 95% CI of fn(index_list). strata: list of index groups resampled separately."""
    rng = random.Random(seed)
    groups = strata or [list(range(n))]
    vals = []
    for _ in range(resamples):
        idx = [rng.choice(g) for g in groups for _ in g]
        v = fn(idx)
        if v == v:
            vals.append(v)
    vals.sort()
    if not vals:
        return [float("nan")] * 2
    return [vals[int(0.025 * (len(vals) - 1))], vals[int(round(0.975 * (len(vals) - 1)))]]


def percentile(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def macro_f1(y, p, classes):
    fs = []
    for c in classes:
        tp = sum(1 for a, b in zip(y, p) if a == c and b == c)
        fp = sum(1 for a, b in zip(y, p) if a != c and b == c)
        fn = sum(1 for a, b in zip(y, p) if a == c and b != c)
        d = 2 * tp + fp + fn
        fs.append(2 * tp / d if d else 0.0)
    return sum(fs) / len(fs)


def append_jsonl(path, rec):
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in open(p) if l.strip()]
