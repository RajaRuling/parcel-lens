import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common as C, run_jev_parcels as P


class R:
    def __init__(s, code, body): s.status_code, s._b = code, body
    def json(s): return s._b


def fake(kind_by_q):
    def t(url, headers=None, files=None, **k):
        assert headers["TypeSafe-Danger-Zone-Images"] == "true" and "Authorization" in headers
        req = json.loads(files["request"][1]); q = req["questions"]["q"]
        assert req["model"] == "jev-1.14.0" and req["assets"]["img-1"]["part"] in files
        if q["type"] == "box":
            return R(200, {"answers": {"q": {"type": "box", "box": {"top": .2, "bottom": .6, "left": .1, "right": .5}, "confidence": .9}}, "usage": {"input_tokens": 3, "output_tokens": 1}})
        crit = list(q["criteria"])
        return R(200, {"answers": {"q": {"type": "choice", "choice": crit[0], "confidence": .8, "probabilities": {c: (.8 if i == 0 else .2 / (len(crit) - 1)) for i, c in enumerate(crit)}}}, "usage": {}})
    return t


def client(tmp, t):
    return C.Client(transport=t, env={"JEV_API_KEY": "x"}, sleep=lambda s: None, calls_log=tmp / "calls.jsonl")


def test_iou_and_auc():
    a = dict(top=0, bottom=1, left=0, right=1)
    assert C.iou(a, a) == 1 and C.iou(a, dict(top=0, bottom=1, left=1, right=2) if False else dict(top=0, bottom=.5, left=0, right=1)) == .5
    assert C.auc([.9, .8, .1], [1, 1, 0]) == 1 and C.auc([.5, .5], [1, 0]) == .5


def test_parcels_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "RAW", tmp_path / "raw.jsonl")
    from PIL import Image; Image.new("RGB", (8, 6)).save(tmp_path / "i.png")
    rec = {"id": "t0", "file": "i.png", "damaged": 1}
    P.run(client(tmp_path, fake(None)), [rec], root=tmp_path)
    rows = C.load_jsonl(tmp_path / "raw.jsonl")
    assert {r["kind"] for r in rows} == {"presence", "box"} and all(r["ok"] for r in rows)
    P.run(client(tmp_path, fake(None)), [rec], root=tmp_path)  # resume sends nothing
    assert len(C.load_jsonl(tmp_path / "calls.jsonl")) == 2


def test_abort_on_429_and_cap(tmp_path, monkeypatch):
    c = client(tmp_path, lambda *a, **k: R(429, {}))
    import pytest
    with pytest.raises(C.JevVisionError):
        for _ in range(3): c.ask(b"x", "image/png", "", {"q": P.BOX_Q}, "t")
    monkeypatch.setattr(C, "CALL_CAP", 0)
    with pytest.raises(C.JevVisionError, match="cap"):
        client(tmp_path, fake(None)).ask(b"x", "image/png", "", {"q": P.BOX_Q}, "t")


def test_refusal_text_kept_without_key(tmp_path):
    c = client(tmp_path, lambda *a, **k: R(400, {"error": "images need header"}))
    import pytest
    with pytest.raises(C.JevVisionError, match="images need header"):
        c.ask(b"x", "image/png", "", {"q": P.BOX_Q}, "t")


def test_size_rules(tmp_path):
    import io
    from PIL import Image
    b = io.BytesIO(); Image.new("RGB", (224, 168)).save(b, "PNG")
    assert Image.open(io.BytesIO(P.upscale2x(b.getvalue()))).size == (448, 336)


def test_key_comes_only_from_the_environment(monkeypatch):
    import pytest
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    with pytest.raises(C.JevVisionError, match="JEV_API_KEY"):
        C.Client(transport=lambda *a, **k: None)
    monkeypatch.setenv("JEV_API_KEY", "placeholder-not-a-key")
    C.Client(transport=lambda *a, **k: None)  # reads the variable, makes no call
